# StebCutz 💈🤖

> **StebCutz** is a WhatsApp appointment bot for a barbershop. It receives messages
> through the **Meta WhatsApp Cloud API**, processes them with an **AI agent** (codename
> *CODEX*, built on the **OpenAI Agents SDK**), reads/writes availability in **Google
> Sheets**, keeps per‑user memory in **DynamoDB**, runs **serverless on AWS**, and ships
> via **GitHub Actions (CI/CD)**.

**🌐 Language / Idioma: [English](#-english) · [Español](#-español)**

---

## 🇬🇧 English

### What it does
A customer writes on WhatsApp ("Do you have a slot on Saturday?"), the bot answers in
natural language with the real free slots, and can **book the appointment** by writing the
client's name and phone number into the barbershop's Google Sheet.

### Architecture

```
                         WhatsApp user
                              │  message
                              ▼
            Meta WhatsApp Cloud API  ◄──────────────── reply (Graph API)
                              │  POST /webhook                        ▲
                              ▼                                       │
                  Amazon API Gateway (REST)                           │
                              │  GET = verification · POST = messages │
                              ▼                                       │
                 AWS Lambda · Python 3.12 · handler.py ───────────────┘
                              │
        ┌─────────────────────┼──────────────────────────┐
        ▼                     ▼                           ▼
   Agent "CODEX"          Amazon DynamoDB            Google Sheets (GCP)
   OpenAI Agents SDK      ├ MessagesTable  (dedup)   service account:
        │                 └ ConversationsTable        availability matrix
        ▼                   (memory per phone)        + write bookings
   OpenAI API (gpt-5-mini)
```

**Message flow**
1. Meta delivers the incoming message to `POST /webhook` (API Gateway → Lambda).
2. The Lambda **deduplicates** by message id in DynamoDB (Meta retries on non‑200).
3. The **agent** loads the conversation history for that phone number, calls the LLM
   with its tools, and may **read availability** or **book** in Google Sheets.
4. The reply is sent back to the user through the Meta **Graph API**.

### Tech stack & services

| Service / Tool | Role in StebCutz |
|----------------|------------------|
| **Meta WhatsApp Cloud API** (Graph API) | Messaging channel: receives user messages and sends replies. |
| **Webhook** | Meta calls our HTTPS endpoint (`/webhook`) on every event. |
| **Amazon API Gateway** (REST) | Public HTTPS endpoint that fronts the Lambda (`GET` verify, `POST` messages). |
| **AWS Lambda** (Python 3.12) | Serverless compute that runs the webhook + the agent. |
| **Amazon DynamoDB** | `MessagesTable` (idempotency / dedup) + `ConversationsTable` (per‑phone chat memory). |
| **OpenAI Agents SDK** (`openai-agents`) | Framework for the agent *CODEX*: tools, tool‑calling loop, sessions. |
| **OpenAI API** (`gpt-5-mini`) | The LLM that understands the user and decides which tool to call. |
| **CODEX (the agent)** | Our conversational agent: behavior in `behavior.md`, tools in `tools/`, memory in DynamoDB. *(Codename — not the OpenAI Codex coding product; it is built on the OpenAI Agents SDK.)* |
| **GCP service account + Google Sheets API** | Server‑to‑server auth (signed JWT) to read/write the schedule. |
| **Google Sheets** | The barber's schedule: a `Hours × Days` matrix (empty cell = free). |
| **AWS CDK** (Python) | Infrastructure as code (Lambda + API Gateway + DynamoDB). |
| **GitHub** | Source repository and encrypted **Secrets** for the deploy. |
| **GitHub Actions** | CI/CD: runs `cdk deploy` on every push to `main`. |
| **Claude Code** | AI pair‑programmer used to build, test and deploy this project. |
| **Visual Studio Code** | Editor / IDE used for development. |

### Project structure

```
StebCutz/
├─ app.py                       # CDK entrypoint; loads config from .env / GitHub Secrets
├─ cdk.json                     # CDK config
├─ requirements.txt             # CDK (Python) dependencies
├─ stebcutz/
│  └─ stebcutz_stack.py         # Stack: DynamoDB (x2) + Lambda + API Gateway
├─ lambda/webhook/
│  ├─ handler.py                # Webhook: verification + route messages to the agent
│  ├─ sheets.py                 # Google Sheets REST client (read/append/update)
│  ├─ availability.py           # Parse the schedule matrix + (day,hour) → A1 cell
│  ├─ test_availability.py      # Parser tests (no network)
│  ├─ requirements.txt          # Lambda deps (vendored into ./vendor at deploy)
│  └─ agent/                    # The "CODEX" agent
│     ├─ behavior.md            # Agent persona & rules (system prompt)
│     ├─ core.py                # Builds the Agent + run(phone, text)
│     ├─ memory.py              # DynamoDBSession (SessionABC) — memory per phone
│     └─ tools/
│        └─ schedule.py         # consultar_disponibilidad / agendar_cita (@function_tool)
├─ .github/workflows/deploy.yml # CI/CD (cdk deploy)
├─ index.html / privacy.html    # GitHub Pages: landing + privacy policy
└─ AVANCE.md                    # Progress log (Spanish)
```

### Environment variables / Secrets

Stored in `.env` locally (git‑ignored) and as **GitHub Secrets** for CI.

| Variable | Description |
|----------|-------------|
| `WHATSAPP_TOKEN` | Permanent System‑User token (Meta). |
| `WHATSAPP_PHONE_NUMBER_ID` | Sender phone number id. |
| `WHATSAPP_VERIFY_TOKEN` | Webhook verification secret (you choose it). |
| `SHEET_ID` | Google Sheet id (between `/d/` and `/edit`). |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | GCP service‑account JSON key, **minified to one line**. |
| `OPENAI_API_KEY` | OpenAI API key (the agent). |
| `OPENAI_MODEL` | OpenAI model (optional, default `gpt-5-mini`). |
| `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` | Deploy IAM user credentials (CI only). |

> ⚠️ Lambda environment variables must total **≤ 4 KB**. The Google key (~2.4 KB) plus the
> rest is close to that limit; if exceeded, move `GOOGLE_SERVICE_ACCOUNT_JSON` to AWS
> Secrets Manager.

### Deployment

**CI/CD (recommended).** Push to `main` → GitHub Actions vendors the Lambda deps into
`vendor/`, runs `cdk bootstrap` + `cdk deploy`, and prints the webhook URL.

**Local.** Requires Python 3.12+, Node.js and AWS CLI:
```bash
python -m venv .venv && .venv\Scripts\activate     # Windows
pip install -r requirements.txt
pip install -r lambda/webhook/requirements.txt -t lambda/webhook/vendor
npm install -g aws-cdk
cdk bootstrap        # once per account/region
cdk deploy
```

### External services — quick setup
- **Meta:** create a Meta app + WhatsApp product, get the permanent token, set the
  webhook **Callback URL** (the API Gateway URL) and **Verify token**, subscribe to
  `messages`.
- **GCP:** create a project, enable the **Google Sheets API**, create a **service account**
  and a **JSON key**, then **share the Sheet** with the service‑account email as *Editor*.
- **OpenAI:** create an API key at `platform.openai.com/api-keys`.

### Tests
```bash
python lambda/webhook/test_availability.py
```

### Development
Built with **Claude Code** (AI pair‑programming) in **Visual Studio Code**: code, tests,
infra, secret management and deploys were done iteratively, validating each step against
the live Google Sheet and AWS Lambda before shipping.

### Debugging
The agent logs to **CloudWatch** (`[agent]` / `[tool]` lines). Toggle with the
`AGENT_DEBUG` env var (`1` = verbose, `0` = off).

---

## 🇪🇸 Español

### Qué hace
Un cliente escribe por WhatsApp ("¿Tienes turno el sábado?"), el bot responde en lenguaje
natural con los horarios libres reales y puede **agendar la cita**, escribiendo el nombre
y el número del cliente en el Google Sheet de la barbería.

### Arquitectura

```
                         Usuario de WhatsApp
                              │  mensaje
                              ▼
            Meta WhatsApp Cloud API  ◄──────────────── respuesta (Graph API)
                              │  POST /webhook                        ▲
                              ▼                                       │
                  Amazon API Gateway (REST)                           │
                              │  GET = verificación · POST = mensajes │
                              ▼                                       │
                 AWS Lambda · Python 3.12 · handler.py ───────────────┘
                              │
        ┌─────────────────────┼──────────────────────────┐
        ▼                     ▼                           ▼
   Agente "CODEX"         Amazon DynamoDB            Google Sheets (GCP)
   OpenAI Agents SDK      ├ MessagesTable (dedup)    cuenta de servicio:
        │                 └ ConversationsTable        matriz de disponibilidad
        ▼                   (memoria por número)      + escribir reservas
   OpenAI API (gpt-5-mini)
```

**Flujo de un mensaje**
1. Meta entrega el mensaje entrante a `POST /webhook` (API Gateway → Lambda).
2. La Lambda **deduplica** por id de mensaje en DynamoDB (Meta reintenta si no recibe 200).
3. El **agente** carga el historial de esa conversación (por número), llama al LLM con sus
   tools, y puede **consultar disponibilidad** o **agendar** en Google Sheets.
4. La respuesta se envía al usuario por la **Graph API** de Meta.

### Servicios y tecnologías

| Servicio / Herramienta | Rol en StebCutz |
|------------------------|-----------------|
| **Meta WhatsApp Cloud API** (Graph API) | Canal de mensajería: recibe mensajes y envía respuestas. |
| **Webhook** | Meta llama a nuestro endpoint HTTPS (`/webhook`) en cada evento. |
| **Amazon API Gateway** (REST) | Endpoint HTTPS público frente a la Lambda (`GET` verificación, `POST` mensajes). |
| **AWS Lambda** (Python 3.12) | Cómputo serverless que corre el webhook + el agente. |
| **Amazon DynamoDB** | `MessagesTable` (idempotencia / dedup) + `ConversationsTable` (memoria por número). |
| **OpenAI Agents SDK** (`openai-agents`) | Framework del agente *CODEX*: tools, bucle de tool‑calling, sesiones. |
| **OpenAI API** (`gpt-5-mini`) | El LLM que entiende al cliente y decide qué tool usar. |
| **CODEX (el agente)** | Nuestro agente conversacional: comportamiento en `behavior.md`, tools en `tools/`, memoria en DynamoDB. *(Nombre interno — no es el producto OpenAI Codex de programación; está construido con el OpenAI Agents SDK.)* |
| **Cuenta de servicio de GCP + Google Sheets API** | Autenticación server‑to‑server (JWT firmado) para leer/escribir la agenda. |
| **Google Sheets** | La agenda de la barbería: matriz `Horas × Días` (celda vacía = libre). |
| **AWS CDK** (Python) | Infraestructura como código (Lambda + API Gateway + DynamoDB). |
| **GitHub** | Repositorio de código y **Secrets** cifrados para el despliegue. |
| **GitHub Actions** | CI/CD: corre `cdk deploy` en cada push a `main`. |
| **Claude Code** | Programación asistida por IA usada para construir, probar y desplegar el proyecto. |
| **Visual Studio Code** | Editor / IDE usado para el desarrollo. |

### Estructura del proyecto

```
StebCutz/
├─ app.py                       # Entrypoint CDK; carga config de .env / GitHub Secrets
├─ cdk.json                     # Configuración de CDK
├─ requirements.txt             # Dependencias de CDK (Python)
├─ stebcutz/
│  └─ stebcutz_stack.py         # Stack: DynamoDB (x2) + Lambda + API Gateway
├─ lambda/webhook/
│  ├─ handler.py                # Webhook: verificación + enruta mensajes al agente
│  ├─ sheets.py                 # Cliente REST de Google Sheets (leer/append/update)
│  ├─ availability.py           # Parser de la matriz + (día,hora) → celda A1
│  ├─ test_availability.py      # Tests del parser (sin red)
│  ├─ requirements.txt          # Deps de la Lambda (se vendorizan en ./vendor al desplegar)
│  └─ agent/                    # El agente "CODEX"
│     ├─ behavior.md            # Persona y reglas del agente (system prompt)
│     ├─ core.py                # Arma el Agent + run(phone, texto)
│     ├─ memory.py              # DynamoDBSession (SessionABC) — memoria por número
│     └─ tools/
│        └─ schedule.py         # consultar_disponibilidad / agendar_cita (@function_tool)
├─ .github/workflows/deploy.yml # CI/CD (cdk deploy)
├─ index.html / privacy.html    # GitHub Pages: landing + política de privacidad
└─ AVANCE.md                    # Bitácora de avance
```

### Variables de entorno / Secrets

Se guardan en `.env` localmente (ignorado por git) y como **GitHub Secrets** para CI.

| Variable | Descripción |
|----------|-------------|
| `WHATSAPP_TOKEN` | Token permanente del System User (Meta). |
| `WHATSAPP_PHONE_NUMBER_ID` | ID del número emisor. |
| `WHATSAPP_VERIFY_TOKEN` | Secreto de verificación del webhook (lo eliges tú). |
| `SHEET_ID` | ID del Google Sheet (entre `/d/` y `/edit`). |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | Clave JSON de la cuenta de servicio de GCP, **minificada en una línea**. |
| `OPENAI_API_KEY` | Clave de la API de OpenAI (el agente). |
| `OPENAI_MODEL` | Modelo de OpenAI (opcional, default `gpt-5-mini`). |
| `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` | Credenciales del usuario IAM de despliegue (solo CI). |

> ⚠️ Las variables de entorno de la Lambda no pueden superar **4 KB** en total. La clave de
> Google (~2.4 KB) más el resto está cerca del límite; si se excede, mover
> `GOOGLE_SERVICE_ACCOUNT_JSON` a AWS Secrets Manager.

### Despliegue

**CI/CD (recomendado).** Push a `main` → GitHub Actions vendoriza las deps de la Lambda en
`vendor/`, corre `cdk bootstrap` + `cdk deploy` y muestra la URL del webhook.

**Local.** Requiere Python 3.12+, Node.js y AWS CLI:
```bash
python -m venv .venv && .venv\Scripts\activate     # Windows
pip install -r requirements.txt
pip install -r lambda/webhook/requirements.txt -t lambda/webhook/vendor
npm install -g aws-cdk
cdk bootstrap        # una vez por cuenta/región
cdk deploy
```

### Servicios externos — configuración rápida
- **Meta:** crea una app de Meta + producto WhatsApp, obtén el token permanente, configura
  el **Callback URL** del webhook (la URL de API Gateway) y el **Verify token**, y
  suscríbete al campo `messages`.
- **GCP:** crea un proyecto, habilita la **Google Sheets API**, crea una **cuenta de
  servicio** y una **clave JSON**, y **comparte el Sheet** con el email de la cuenta de
  servicio como *Editor*.
- **OpenAI:** crea una API key en `platform.openai.com/api-keys`.

### Tests
```bash
python lambda/webhook/test_availability.py
```

### Desarrollo
Construido con **Claude Code** (programación asistida por IA) en **Visual Studio Code**: el
código, los tests, la infraestructura, la gestión de secretos y los despliegues se hicieron
de forma iterativa, validando cada paso contra el Google Sheet real y la Lambda en AWS antes
de publicar.

### Depuración
El agente registra logs en **CloudWatch** (líneas `[agent]` / `[tool]`). Se activa/desactiva
con la env var `AGENT_DEBUG` (`1` = detallado, `0` = apagado).
