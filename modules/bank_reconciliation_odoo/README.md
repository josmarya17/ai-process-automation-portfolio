# 🏦 Intelligent Bank Reconciliation Engine for Odoo ERP

## Overview
Automates the complex and time-consuming task of matching raw bank statement entries against open customer and vendor invoices in **Odoo ERP**. Uses a hybrid approach combining LLM classification and fuzzy string matching.

## Key Features
- **Bank Statement Processing:** Parses Excel (`.xlsx`) and CSV statement formats.
- **Fuzzy & AI Matching:** Matches partner names, invoice reference codes, and amounts with high confidence scores.
- **Automated Odoo Posting:** Posts reconciliation entries directly via Odoo XML-RPC API.

## Setup & Environment
1. Configure credentials in `.env.example`.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Launch dashboard:
   ```bash
   streamlit run dashboard.py
   ```
