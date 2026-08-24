# Configuración de Google Cloud (GCP)

Para que el sistema funcione, debemos preparar el entorno en tu proyecto `wearecontent-gsc-391421`.

## 1. Habilitar APIs
Desde la consola de GCP, busca y habilita las siguientes APIs:
- [x] Google Sheets API
- [x] Google Drive API
- [x] Google Search Console API
- [x] Google Analytics Data API

## 2. Crear Cuenta de Servicio (Service Account)
1. Ve a **IAM y administración** > **Cuentas de servicio**.
2. Haz clic en **Crear cuenta de servicio**.
3. Nombre: `seo-analyst-bot`.
4. **Roles**: 
   - Administrador de Vertex AI (Vertex AI Administrator)
   - Lector de Proyecto (Project Viewer)
5. Al finalizar, ve a la pestaña **Claves** > **Agregar clave** > **Crear clave nueva** (Formato JSON).
6. **MUY IMPORTANTE**: Guarda ese archivo como `service_account.json` dentro de la carpeta `SEO_Auto_Analyst/cloud/`.

## 3. Autorizar en los Sheets
Copia el correo de la cuenta de servicio (ej: `seo-analyst-bot@wearecontent...`) y dale acceso como **Editor** en los 5 archivos de Google Sheets que me proporcionaste.

> [!NOTE]
> Para la Inteligencia Artificial y la automatización, consulta la nueva guía [SETUP_FREE_TOOLS.md](file:///c:/Users/Sist-JPinto/.gemini/antigravity/scratch/SEO_Auto_Analyst/docs/SETUP_FREE_TOOLS.md).
