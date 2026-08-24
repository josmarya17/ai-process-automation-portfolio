# Guía de Herramientas Gratuitas (Plan B)

Sigue estos pasos para activar la inteligencia artificial y la automatización sin costo.

## 1. Obtener Gemini API Key (Gratis)
1. Ve a [Google AI Studio](https://aistudio.google.com/).
2. Identifícate con tu cuenta de Google.
3. Haz clic en el botón **"Get API key"** en la barra lateral izquierda.
4. Haz clic en **"Create API key in new project"**.
5. **Copia esa clave** y guárdala un momento.

## 2. Configurar GitHub Actions (Automatización)
Para que el bot corra solo cada mes, necesitamos "subir" dos secretos a tu repositorio de GitHub:

1. Ve a tu repositorio en GitHub.
2. Haz clic en **Settings** > **Secrets and variables** > **Actions**.
3. Haz clic en **New repository secret**.
4. Agrega estos dos secretos:
   - **Nombre**: `GEMINI_API_KEY` | **Valor**: (La clave que copiaste de AI Studio).
   - **Nombre**: `SERVICE_ACCOUNT_JSON` | **Valor**: (Todo el contenido de tu archivo `service_account.json`).

## 3. Desplegar el Dashboard (Streamlit Cloud)
1. Ve a [share.streamlit.io](https://share.streamlit.io/).
2. Conecta tu cuenta de GitHub.
3. Haz clic en **"Create app"**.
4. Selecciona tu repositorio y la rama principal.
5. **Main file path**: Escribe `app.py`.
6. **Configurar Secretos**:
   - En el dashboard de Streamlit Cloud, ve a **Settings** > **Secrets**.
   - Pega el contenido de tu `service_account.json` en un formato TOML como este:
     ```toml
     [gcp_service_account]
     type = "service_account"
     project_id = "tu-proyecto"
     private_key_id = "..."
     private_key = "..."
     client_email = "..."
     ... (copia todo lo del JSON aquí)
     ```
7. Haz clic en **Deploy**.

---

¡Listo! Con esto, el bot analizará tus datos el día 1 de cada mes y podrás ver el Dashboard en la URL que te dé Streamlit Cloud, todo sin gastar un centavo.
