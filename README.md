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
| `SHEET_ID` | ID del Google Sheet (lo que va entre `/d/` y `/edit` en la URL) |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | Clave JSON de la service account de GCP, **minificada en una sola línea** |
| `OPENAI_API_KEY` | Clave de la API de OpenAI (para el agente) |
| `OPENAI_MODEL` | Modelo de OpenAI a usar (opcional, default `gpt-4o-mini`) |
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

## Conectar Google Sheets (GCP)

El bot lee/escribe un Google Sheet mediante una **service account** de GCP.

1. En [Google Cloud Console](https://console.cloud.google.com) crea un proyecto y
   **habilita la Google Sheets API** (*APIs & Services → Library*).
2. Crea una **service account** (*IAM & Admin → Service Accounts*) y, dentro de ella,
   una **clave JSON** (*Keys → Add key → JSON*). Descárgala.
3. Abre tu Sheet y **compártelo** (botón *Share*) con el email de la service account
   (`...@<proyecto>.iam.gserviceaccount.com`) como **Editor**.
4. Carga los secretos `SHEET_ID` y `GOOGLE_SERVICE_ACCOUNT_JSON` (este último con el
   JSON minificado en una sola línea) en `.env` y en **GitHub Secrets**.
5. Tras desplegar, escribe **`ping sheet`** por WhatsApp → el bot responde con las
   primeras filas del Sheet (comando temporal de prueba).

### Consultar disponibilidad por WhatsApp

Con el parser de disponibilidad (`lambda/webhook/availability.py`) el bot ya entiende:

| Mensaje | Respuesta |
|---------|-----------|
| un día (`sábado`, `viernes`, …) | horarios **libres** de ese día |
| `disponibilidad` / `horarios` | resumen de cupos libres por día |
| cualquier otra cosa | `Hola` |

> El Sheet es una matriz `Horas × Días`; **celda vacía = libre**, con texto = ocupado.
> La API omite celdas vacías al final de cada fila, por lo que el parser trata las filas
> "cortas" como días libres. Tests: `python lambda/webhook/test_availability.py`.

## Agente conversacional (OpenAI Agents SDK)

A partir de aquí el bot no solo responde "Hola": un **agente** procesa cada mensaje con
GPT, mantiene memoria por usuario y puede consultar y agendar citas.

```
lambda/webhook/agent/
  behavior.md          ← comportamiento/persona del agente (system prompt)
  core.py              ← arma el Agent + run(phone, texto) con Runner.run_sync
  memory.py            ← memoria por número en DynamoDB (SessionABC del SDK)
  tools/
    schedule.py        ← consultar_disponibilidad / agendar_cita (@function_tool)
```

Flujo: **Meta → Lambda → `agent.run(número, texto)` → (OpenAI + tools + memoria) → respuesta a Meta.**

- **Memoria:** tabla DynamoDB `ConversationsTable`, particionada por `phone` (el número
  de WhatsApp); guarda los últimos turnos de la conversación.
- **Tools:** leen/escriben el Google Sheet vía `availability.py` + `sheets.py`.
- **Modelo:** configurable con `OPENAI_MODEL` (default `gpt-4o-mini`).
- La librería `openai-agents` se vendoriza en `vendor/` en el deploy (igual que el resto).

> La librería de la Lambda (`google-auth`, `requests`) se **vendoriza** en
> `lambda/webhook/vendor/` durante el deploy (paso del workflow). En local, instálalas
> con `pip install -r lambda/webhook/requirements.txt -t lambda/webhook/vendor`.
