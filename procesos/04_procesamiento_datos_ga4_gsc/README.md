# 📊 Proceso 04: Pipeline ETL de Analítica Web GA4 y Search Console

## Descripción del Proceso
Pipeline ETL automatizado que extrae métricas de tráfico y posicionamiento orgánico de **Google Analytics 4 (GA4)** y **Google Search Console (GSC)**, filtra tendencias relevantes mediante IA y genera reportes ejecutivos automatizados.

## Componentes Clave
- **Extractor API GA4 / GSC:** Descarga automatizada de clics, impresiones, CTR y conversiones.
- **Destilador de Datos IA:** Identificación automática de desviaciones y patrones de crecimiento.
- **Generador de Reportes:** Creación de resúmenes ejecutivos en Markdown.

## Guía de Inicio Rápido
1. Configura tus credenciales en `.env` o `service_account.json`.
2. Ejecuta el análisis:
   ```bash
   python main.py
   ```
