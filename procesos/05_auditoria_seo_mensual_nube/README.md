# 🌐 Proceso 05: Auditoría SEO Mensual Automatizada y Workers Nube

## Descripción del Proceso
Sistema automatizado de diagnóstico SEO diseñado para ejecutarse periódicamente mediante Google Cloud Functions o GitHub Actions. Realiza chequeos técnicos del sitio web, analiza rendimiento y envía recomendaciones estructuradas a los interesados.

## Estructura de Carpetas
- `nube/`: Funciones de Cloud Functions / Lambda y configuraciones de despliegue.
- `panel_control/`: Dashboard en Streamlit para monitoreo visual.
- `documentacion/`: Guías de arquitectura y despliegue técnico.

## Guía de Inicio Rápido
1. Configura la API Key de Gemini en `.env`.
2. Inicia el panel de control interactivo:
   ```bash
   streamlit run panel_control/app.py
   ```
