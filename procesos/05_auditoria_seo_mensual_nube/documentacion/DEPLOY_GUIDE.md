# Guía de Despliegue con Cloud Code

Ya tienes todo el código listo. Aquí te explico cómo subirlo a la nube usando tu extensión **Cloud Code** en VS Code.

## 1. Desplegar la Cloud Function (Motor SEO)
1. En VS Code, abre la carpeta `SEO_Auto_Analyst/cloud`.
2. Haz clic en el icono de **Cloud Code** en la barra lateral.
3. Selecciona **Cloud Functions** y elige **Deploy function**.
4. Configuración:
   - **Name**: `seo-monthly-analysis`
   - **Runtime**: `python310`
   - **Entry point**: `main`
   - **Trigger**: `HTTP` (con autenticación activada o IAP).

## 2. Desplegar el Dashboard (Streamlit)
El dashboard se despliega en **Cloud Run**:
1. Abre la carpeta `SEO_Auto_Analyst/dashboard`.
2. En Cloud Code, selecciona **Cloud Run** > **Deploy to Cloud Run**.
3. Elige tu proyecto y región.
4. **IMPORTANTE**: Asegúrate de que el puerto esté configurado en `8501` (el default de Streamlit).

## 3. Configurar el Programador (Cloud Scheduler)
Para que sea automático cada mes:
1. Ve a la consola de GCP > **Cloud Scheduler**.
2. Crear tarea:
   - **Frecuencia**: `0 9 1 * *` (Día 1 de cada mes a las 9:00 AM).
   - **Target**: `HTTP` (pega la URL de tu Cloud Function desplegada).
   - **Body**: `{}`
