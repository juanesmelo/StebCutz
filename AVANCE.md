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

## 🔜 Próximos pasos

- [ ] Definir el `WHATSAPP_VERIFY_TOKEN` (palabra secreta para el webhook).
- [ ] Activar GitHub Pages y poner la URL de privacidad en la configuración de la app de Meta.
- [ ] Enviar un mensaje de prueba real a un número de WhatsApp registrado.
- [ ] Desarrollar el esqueleto del bot:
  - [ ] Webhook (verificación `GET` + recepción `POST` de mensajes).
  - [ ] Función de envío de mensajes a la WhatsApp Cloud API.
  - [ ] Integración con Google Sheets (lectura de disponibilidad).
- [ ] Configurar despliegue serverless en AWS.
- [ ] Configurar CI/CD con GitHub Actions.

---

## 🔐 Notas de seguridad

- El archivo `.env` está listado en `.gitignore` y **nunca** debe subirse al repositorio.
- Los secretos (App Secret y tokens de acceso) **no** se documentan en este archivo.
- En producción, las credenciales deberían gestionarse con un gestor de secretos
  (ej. AWS Secrets Manager) en lugar de un `.env`.
