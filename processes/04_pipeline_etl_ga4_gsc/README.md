# 📊 Proceso 04: Pipeline ETL de Analítica Web GA4 y Search Console
# 📊 Process 04: GA4 & Search Console Analytics ETL Pipeline

[![Español](#-español)] | [![English](#-english)]

---

## 🇪🇸 Español

### Descripción del Proceso
Pipeline ETL automatizado que extrae métricas de tráfico y posicionamiento orgánico de **Google Analytics 4 (GA4)** y **Google Search Console (GSC)**, filtra tendencias relevantes mediante IA y genera reportes ejecutivos automatizados.

### Componentes Clave
- **Extractor API GA4 / GSC:** Descarga automatizada de clics, impresiones, CTR y conversiones.
- **Destilador de Datos IA:** Identificación automática de desviaciones y patrones de crecimiento.
- **Generador de Reportes:** Creación de resúmenes ejecutivos en Markdown e imágenes de control.

### Guía de Inicio Rápido
1. Configura tus credenciales en `service_account.json` o `.env`.
2. Ejecuta el análisis:
   ```bash
   python main.py
   ```

---

## 🇬🇧 English

### Process Overview
Automated ETL data pipeline that extracts organic search and traffic performance metrics from **Google Analytics 4 (GA4)** and **Google Search Console (GSC)**, distills key trends using LLMs, and formats executive reports.

### Key Components
- **GA4 & GSC API Extractor:** Pulls clicks, impressions, CTR, average position, and conversions.
- **AI Data Distiller:** Automatically flags monthly shifts and keyword performance changes.
- **Report Generator:** Exports clean executive summaries and metric visuals.

### Quick Start
1. Place credentials in `.env` or `service_account.json`.
2. Run extraction pipeline:
   ```bash
   python main.py
   ```
