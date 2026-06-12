# StebCutz — Webhook de WhatsApp (AWS CDK)

Webhook de la **WhatsApp Cloud API** sobre **API Gateway + una sola Lambda**, con una
tabla **DynamoDB** para registrar/deduplicar mensajes. La infraestructura se levanta con
**AWS CDK (Python)** y se despliega con **GitHub Actions**.

Objetivo de esta primera etapa: conectar el número de Meta al webhook para que responda **"Hola"**.

## Arquitectura

```
Meta (WhatsApp Cloud API)
        │  GET /webhook  (verificación)
        │  POST /webhook (mensajes entrantes)
        ▼
   API Gateway (REST)  ──►  Lambda (handler.py)  ──►  DynamoDB (MessagesTable)
                                   │
                                   └─► Graph API: responde "Hola"
```

## Estructura

| Ruta | Qué es |
|------|--------|
| `app.py` | Entrypoint de CDK; carga config de `.env` / GitHub Secrets |
| `stebcutz/stebcutz_stack.py` | Stack: DynamoDB + Lambda + API Gateway |
| `lambda/webhook/handler.py` | Código de la Lambda (verificación + responder "Hola") |
| `.github/workflows/deploy.yml` | CI/CD: `cdk deploy` en cada push a `main` |
| `requirements.txt` | Dependencias de CDK (Python) |

## Variables de entorno / Secrets

El despliegue necesita estas variables (en `.env` local y como **GitHub Secrets** en CI):

| Variable | Origen |
|----------|--------|
| `WHATSAPP_TOKEN` | Token permanente del System User (Meta) |
| `WHATSAPP_PHONE_NUMBER_ID` | ID del número emisor |
| `WHATSAPP_VERIFY_TOKEN` | Palabra secreta del webhook (la inventas tú) |
| `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` | Credenciales del usuario IAM de despliegue (solo CI) |

## Despliegue por CI/CD (recomendado)

1. En GitHub: **Settings → Secrets and variables → Actions → New repository secret** y crea:
   `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `WHATSAPP_TOKEN`,
   `WHATSAPP_PHONE_NUMBER_ID`, `WHATSAPP_VERIFY_TOKEN`.
2. Haz `push` a `main` (o lanza el workflow manualmente desde la pestaña **Actions**).
3. Al terminar, el log muestra `cdk-outputs.json` con la **URL del webhook**.

> ⚠️ Usa un **usuario IAM dedicado** para el despliegue, no la *root key*.

## Despliegue local (opcional)

Requiere **Python 3.12+**, **Node.js** y **AWS CLI** configurado:

```bash
python -m venv .venv && .venv\Scripts\activate   # Windows
pip install -r requirements.txt
npm install -g aws-cdk
cdk bootstrap        # una sola vez por cuenta/región
cdk deploy
```

## Conectar el webhook en Meta

1. Copia la URL del output `WebhookUrl` (algo como
   `https://xxxx.execute-api.us-east-1.amazonaws.com/prod/webhook`).
2. En **Meta for Developers → tu app → WhatsApp → Configuration → Webhook**:
   - **Callback URL**: la URL anterior.
   - **Verify token**: el mismo valor de `WHATSAPP_VERIFY_TOKEN`.
   - Pulsa **Verify and save** (Meta hará un `GET` de verificación).
3. En **Webhook fields**, suscríbete a **messages**.
4. Escribe un WhatsApp a tu número → debe responder **"Hola"**.
