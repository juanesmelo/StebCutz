"""Infraestructura de StebCutz en AWS (CDK).

Levanta:
  - Una tabla DynamoDB para registrar/deduplicar mensajes.
  - Una unica Lambda (el webhook).
  - Un API Gateway REST con el recurso /webhook (GET + POST) hacia la Lambda.
"""

from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
    CfnOutput,
    aws_lambda as _lambda,
    aws_apigateway as apigw,
    aws_dynamodb as dynamodb,
)
from constructs import Construct


class StebcutzStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        config: dict,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # --- DynamoDB: registro de mensajes (PK simple) ---
        table = dynamodb.Table(
            self,
            "MessagesTable",
            partition_key=dynamodb.Attribute(
                name="pk", type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            # En dev borramos la tabla al destruir el stack. En prod usar RETAIN.
            removal_policy=RemovalPolicy.DESTROY,
        )

        # --- Lambda: el webhook ---
        webhook_fn = _lambda.Function(
            self,
            "WebhookFunction",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="handler.handler",
            code=_lambda.Code.from_asset("lambda/webhook"),
            timeout=Duration.seconds(15),
            memory_size=256,
            environment={
                "TABLE_NAME": table.table_name,
                "WHATSAPP_TOKEN": config["WHATSAPP_TOKEN"],
                "WHATSAPP_PHONE_NUMBER_ID": config["WHATSAPP_PHONE_NUMBER_ID"],
                "WHATSAPP_VERIFY_TOKEN": config["WHATSAPP_VERIFY_TOKEN"],
                "GRAPH_API_VERSION": config.get("GRAPH_API_VERSION", "v21.0"),
            },
        )
        table.grant_read_write_data(webhook_fn)

        # --- API Gateway REST: /webhook (GET verificacion, POST mensajes) ---
        api = apigw.LambdaRestApi(
            self,
            "WebhookApi",
            handler=webhook_fn,
            proxy=False,
            deploy_options=apigw.StageOptions(stage_name="prod"),
        )
        webhook = api.root.add_resource("webhook")
        webhook.add_method("GET")
        webhook.add_method("POST")

        # URL final que se registra en Meta (App > WhatsApp > Configuration).
        CfnOutput(
            self,
            "WebhookUrl",
            value=f"{api.url}webhook",
            description="URL del webhook para configurar en Meta",
        )
        CfnOutput(self, "MessagesTableName", value=table.table_name)
