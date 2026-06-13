# StebCutz — Bitácora de avance

> **StebCutz** es un bot de citas para barbería que funciona por **WhatsApp**.
> Consulta disponibilidad en tiempo real desde **Google Sheets**, gestiona confirmaciones
> de reservas vía la **WhatsApp Cloud API de Meta**, corre **serverless en AWS** y se
> automatiza con **GitHub Actions (CI/CD)**.

---

## 📅 Sesión: 10 de junio de 2026

### ✅ 1. Conexión con GitHub
- Repositorio remoto conectado: `https://github.com/juanesmelo/StebCutz.git`
- Rama principal: `main`
- Identidad de git configurada para el repo.

### ✅ 2. Cuenta y App de Meta
- Creada la cuenta de **Meta Business** (*StebCutz*).
- Creada la app de desarrollador **`StebCutz-Bot`** en [Meta for Developers](https://developers.facebook.com).
- Agregado el producto/caso de uso **WhatsApp**, que generó automáticamente:
  - Una **cuenta de WhatsApp Business (WABA)**.
  - Un **número de prueba** gratuito: `+1 555-640-4443`.

### ✅ 3. Credenciales obtenidas
Todas guardadas de forma segura en el archivo `.env` (ignorado por git, **no** se sube a GitHub):

| Credencial | Descripción | Estado |
|------------|-------------|--------|
| `META_APP_ID` | Identificador público de la app (`1480431579971115`) | ✅ |
| `META_APP_SECRET` | Clave secreta de la app | ✅ (secreto) |
| `WHATSAPP_PHONE_NUMBER_ID` | ID del número emisor (`1162759626920067`) | ✅ |
| `WHATSAPP_BUSINESS_ACCOUNT_ID` | ID de la WABA (`2016799138949573`) | ✅ |
| `WHATSAPP_TOKEN` | Token de acceso **permanente** (System User) | ✅ (secreto) |
| `WHATSAPP_VERIFY_TOKEN` | Token de verificación del webhook | ⏳ Pendiente |

### ✅ 4. Token de acceso permanente
- Creado un **Usuario del Sistema (System User)** en Meta Business.
- Generado un **token que nunca expira** con los permisos:
  - `whatsapp_business_messaging`
  - `whatsapp_business_management`
- Validado contra la Graph API: token **válido**, tipo `SYSTEM_USER`, caducidad **NUNCA**. ✅

### ✅ 5. Política de Privacidad (GitHub Pages)
- Creada la página `index.html` con la Política de Privacidad requerida por Meta.
- Publicada en el repositorio.
- URL prevista de GitHub Pages: `https://juanesmelo.github.io/StebCutz/`
- ⏳ *Pendiente:* activar GitHub Pages en *Settings → Pages* y reemplazar el correo
  de contacto de ejemplo (`contacto@stebcutz.com`) por el real.

---

## 📅 Sesión: 11–12 de junio de 2026

### ✅ 1. Número de producción de WhatsApp
- Registrado el número de negocio real **+57 311 8330285** (nombre verificado: *StebCutz*).
- Actualizados los IDs en `.env` (número de prueba dejado comentado):
  - `WHATSAPP_PHONE_NUMBER_ID = 1176015402258622`
  - `WHATSAPP_BUSINESS_ACCOUNT_ID = 1594122622136580`
- **Activado en la Cloud API** vía Graph API (`/register` con PIN de dos pasos):
  `status: CONNECTED`, `platform_type: CLOUD_API`. (Antes estaba `PENDING` y por eso
  `wa.me` lo daba como inexistente.)
- Definido `WHATSAPP_VERIFY_TOKEN` y `WHATSAPP_REGISTRATION_PIN` (ambos en `.env`).

### ✅ 2. GitHub Pages — home del proyecto
- `index.html`: landing minimal de StebCutz (hero, features, pasos, stack).
- `privacy.html`: política de privacidad (antes era el `index.html`), enlazada desde el home.
- ⚠️ La URL de privacidad cambió a `…/StebCutz/privacy.html` (actualizar en Meta si se usa).

### ✅ 3. Infraestructura AWS con CDK (Python)
- `stebcutz/stebcutz_stack.py`: **DynamoDB** (PAY_PER_REQUEST) + **una Lambda** (Python 3.12)
  + **API Gateway REST** con `/webhook` (GET verificación, POST mensajes).
- `lambda/webhook/handler.py`: verifica el webhook y responde **"Hola"**, con deduplicación
  de mensajes en DynamoDB (idempotencia ante reintentos de Meta).
- Región: **us-east-1**. Cuenta AWS: `435506672463`.
- **URL del webhook:** `https://fhdh73cche.execute-api.us-east-1.amazonaws.com/prod/webhook`

### ✅ 4. CI/CD con GitHub Actions
- `.github/workflows/deploy.yml`: en push a `main` corre `cdk bootstrap` + `cdk deploy`.
- Usuario IAM dedicado **`stebcutz-deploy`** (AdministratorAccess) creado vía AWS CLI.
- **GitHub Secrets** cargados (vía `gh secret set`): `AWS_ACCESS_KEY_ID`,
  `AWS_SECRET_ACCESS_KEY`, `WHATSAPP_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID`, `WHATSAPP_VERIFY_TOKEN`.
- PR **#1** mergeado → primer despliegue **exitoso**.

### ✅ 5. Webhook conectado a Meta (vía Graph API, sin consola)
- `POST /{app-id}/subscriptions` → callback URL + verify token + campo `messages` (`active: true`).
- `POST /{waba-id}/subscribed_apps` → WABA suscrita a la app StebCutz.
- Verificación del webhook probada contra AWS: token correcto → 200 + challenge; token malo → 403.

---

## 📅 Sesión: 12 de junio de 2026 (parte 2)

### ✅ Prueba real del webhook
- Se escribió al número de producción y el bot respondió **"Hola"**. Flujo Meta →
  API Gateway → Lambda → DynamoDB → Graph API confirmado end-to-end.

### 🛠️ Integración con Google Sheets (en progreso)
- **Decisiones:** GCP desde cero · acceso **lectura + escritura**
  (scope `https://www.googleapis.com/auth/spreadsheets`) · clave JSON como
  **variable de entorno** de la Lambda (vía GitHub Secrets, igual que `WHATSAPP_TOKEN`).
- **Código añadido:**
  - `lambda/webhook/requirements.txt`: `google-auth` + `requests` (Python puro, sin Docker).
  - `lambda/webhook/sheets.py`: cliente REST v4 (`read_range`, `append_row`, `update_range`)
    con sesión autenticada perezosa y cacheada entre invocaciones.
  - `lambda/webhook/handler.py`: añade `./vendor` al `sys.path` y un comando temporal
    `ping sheet` para verificar la conexión desde el propio WhatsApp.
  - `stebcutz_stack.py` + `app.py`: nuevas env vars `SHEET_ID` y `GOOGLE_SERVICE_ACCOUNT_JSON`.
  - `.github/workflows/deploy.yml`: paso que **vendoriza** las deps en
    `lambda/webhook/vendor/` + inyección de los 2 nuevos secrets.
  - `.gitignore`: ignora `lambda/webhook/vendor/`.
- **⚠️ Pendiente del usuario (GCP):** crear proyecto, habilitar Sheets API, crear
  service account + clave JSON, compartir el Sheet con su email, y cargar
  `SHEET_ID` / `GOOGLE_SERVICE_ACCOUNT_JSON` en `.env` y GitHub Secrets.
- **⚠️ Límite a vigilar:** el total de env vars de una Lambda no puede pasar de **4 KB**;
  la clave JSON ocupa ~2.4 KB. Si se acerca al límite, mover a Secrets Manager.

---

## 📅 Sesión: 12 de junio de 2026 (parte 3)

### ✅ Conexión con Google Sheets verificada (vía API)
- Service account `stebcutzsheets@stebcutz.iam.gserviceaccount.com` lee el Sheet
  (proyecto `stebcutz`). Probado con un JWT RS256 firmado en local (Node) → token →
  lectura del rango. Mismo flujo que usa la Lambda.
- El Sheet es una **matriz de disponibilidad** `Horas × Días` (Lun→Dom, 9AM→9PM);
  **celda vacía = libre**, con texto = ocupado.

### ✅ Parser de disponibilidad
- `lambda/webhook/availability.py`: `parse()`, `free_slots()`, `find_day()`,
  `summary_text()`, `reply_for()`. Maneja **filas irregulares** (la API omite celdas
  vacías al final → días faltantes = libres), normaliza tildes/mayúsculas e ignora
  puntuación al detectar el día.
- `lambda/webhook/handler.py`: enruta mensajes con `availability.reply_for()`
  (día → horarios libres; `disponibilidad`/`horarios` → resumen; resto → "Hola").
- `lambda/webhook/test_availability.py`: tests del parser (sin red).
- Algoritmo validado con un port en Node (asserts sobre filas irregulares + datos
  reales). Bug detectado y corregido: el día pegado a un signo (`¿…sábado?`) no se
  detectaba; ahora se tokeniza ignorando puntuación.

---

## 📅 Sesión: 12 de junio de 2026 (parte 4)

### 🧠 Agente conversacional ("CODEX") con OpenAI Agents SDK
- **Investigación previa:** se evaluó usar *OpenAI Codex* (lo que pidió el usuario). Codex
  es un agente de **programación** (CLI/SDK que envuelve un binario + sandbox, requiere
  repo git, procesos largos) → **no encaja** en una Lambda de chat. Se eligió el
  **OpenAI Agents SDK** (`openai-agents`), que da tools + memoria + comportamiento en `.md`
  y corre limpio en la Lambda. Decisiones: **modelo mini** (`gpt-4o-mini`, configurable
  por `OPENAI_MODEL`) y alcance **consultar + agendar**.
- **Estructura nueva** `lambda/webhook/agent/`:
  - `behavior.md` (persona/reglas), `core.py` (`Agent` + `run()` con `Runner.run_sync`),
    `memory.py` (`DynamoDBSession` implementa `SessionABC`), `tools/schedule.py`
    (`consultar_disponibilidad`, `agendar_cita` con `@function_tool`).
  - `handler.py` ahora enruta todo mensaje al agente (mantiene `ping sheet` de debug).
- **Memoria:** nueva tabla DynamoDB `ConversationsTable` (PK = `phone`); guarda los
  últimos 40 items por usuario.
- **Escritura validada:** mapeo (día, hora) → celda A1 verificado contra el Sheet real
  (B2 ocupado, G2/H4 libres, tolera espacios, día/hora inválidos → None). **Sin escribir.**
- **OpenAI:** `OPENAI_API_KEY` validada contra la API (200 OK). Se corrigió un `.env`
  mal formado (la key venía con comillas tipográficas y pegada a `OPENAI_MODEL`). Key
  reconstruida (164 chars) y secrets `OPENAI_API_KEY`/`OPENAI_MODEL` subidos a GitHub.
- **Infra Lambda:** timeout 15s→60s y memoria 256→512 MB (el agente hace varias llamadas
  + cold start de `openai-agents`).
- **⚠️ Vigilar límite de 4 KB de env vars** (la clave de Google + ahora OpenAI suman
  ~3.1 KB). Si se excede, mover `GOOGLE_SERVICE_ACCOUNT_JSON` a Secrets Manager.

---

## 🔜 Próximos pasos

- [x] **Prueba real:** el bot responde "Hola". ✅
- [x] **GCP:** service account + secretos cargados; lectura del Sheet verificada. ✅
- [x] **Parser de disponibilidad** construido y testeado. ✅
- [x] **Agente (OpenAI Agents SDK)** con memoria DynamoDB + tools de agenda. ✅
- [ ] **Desplegar y probar por WhatsApp**: conversación real, consultar y agendar.
- [ ] Afinar el comportamiento (`behavior.md`) según las pruebas.
- [ ] **Seguridad:** eliminar/rotar la *access key de root* (`AKIAWKZRYONHSG2JPV6J`)
  ahora que existe `stebcutz-deploy`; mover `WHATSAPP_TOKEN` a Secrets Manager/SSM.
- [ ] Activar GitHub Pages en *Settings → Pages* y poner la URL de privacidad en Meta.
- [ ] Desarrollar la lógica del bot:
  - [ ] Conversación real (más allá de "Hola").
  - [ ] Integración con Google Sheets (lectura de disponibilidad).
  - [ ] Agendamiento / confirmaciones de citas.

---

## 🔐 Notas de seguridad

- El archivo `.env` está listado en `.gitignore` y **nunca** debe subirse al repositorio.
- Los secretos (App Secret y tokens de acceso) **no** se documentan en este archivo.
- En producción, las credenciales deberían gestionarse con un gestor de secretos
  (ej. AWS Secrets Manager) en lugar de un `.env`.
