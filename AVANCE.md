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

## 🔜 Próximos pasos

- [ ] **Prueba real:** escribir al número y confirmar que responde "Hola"
  (revisar CloudWatch / DynamoDB si falla).
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
