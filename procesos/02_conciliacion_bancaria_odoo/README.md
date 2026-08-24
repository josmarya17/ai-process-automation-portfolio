# 🏦 Proceso 02: Motor Inteligente de Conciliación Bancaria en Odoo ERP

## Descripción del Proceso
Proceso automático concebido para conciliar extractos bancarios en formato Excel/CSV con las facturas pendientes de cobro y pago en **Odoo ERP**. Combina algoritmos de coincidencia difusa (*Fuzzy Matching*) con un clasificador LLM para identificar pagos con un 99% de precisión.

## Componentes Clave
- **Lector de Extractos Bancarios:** Parser universal de formatos `.xlsx` y `.csv`.
- **Emparejador Difuso (Fuzzy Matcher):** Coincidencia inteligente por código de factura, referencia y monto.
- **Conector Remoto Odoo:** Registro automatizado de pagos conciliados mediante API XML-RPC.

## Guía de Inicio Rápido
1. Copia `.env.example` a `.env` y configura tus credenciales de Odoo.
2. Instala dependencias:
   ```bash
   pip install -r requirements.txt
   ```
3. Ejecuta el tablero de conciliación:
   ```bash
   streamlit run dashboard.py
   ```
