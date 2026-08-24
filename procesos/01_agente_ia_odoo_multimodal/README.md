# 🤖 Proceso 01: Agente de IA Multimodal para Odoo ERP

## Descripción del Proceso
Este proceso automatizado independiente conecta un **Asistente de IA Multimodal (Voz, Panel Web y WhatsApp)** directamente con la base de datos de **Odoo ERP** mediante la API XML-RPC. Permite a los usuarios consultar inventarios, validar estados de pedidos y generar reportes mediante lenguaje natural.

## Componentes Clave
- **Integración Odoo XML-RPC:** Conexión directa a los modelos `stock.quant`, `sale.order`, `res.partner`.
- **Soporte Multimodal:** Procesamiento de voz (PyAudio / SpeechRecognition), chat web y bot de mensajería.
- **Motor de IA:** Google Gemini API para interpretar intenciones y estructurar consultas ERP.

## Guía de Inicio Rápido
1. Copia `.env.example` a `.env`:
   ```bash
   cp .env.example .env
   ```
2. Configura las variables de entorno (`GEMINI_API_KEY`, `ODOO_URL`, `ODOO_DB`, `ODOO_USERNAME`, `ODOO_PASSWORD`).
3. Instala dependencias y ejecuta:
   ```bash
   pip install -r requirements.txt
   python app.py
   ```
