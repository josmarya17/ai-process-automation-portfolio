import os
import sys
import json
import pandas as pd
from datetime import date, timedelta
import config
from data_extractor import ClientManager, GSCClient, GA4Client, LookerClient, get_date_ranges
from report_generator import SheetsManager

def get_client_data(client_name):
    print(f"Buscando datos técnicos para: {client_name}...", file=sys.stderr)
    
    try:
        # 1. Setup creds and get properties (Initial discovery with default or WAC)
        temp_mgr = ClientManager(account_key='wac')
        temp_creds = temp_mgr.get_creds()
        sheets_mgr = SheetsManager(temp_creds)
        
        df = sheets_mgr.read_config_sheet(config.SHEET_ID_PROPIEDADES, config.TAB_NAME_PROPIEDADES)
        
        # Exact or partial match
        row = df[df[config.COL_CLIENTE].str.contains(client_name, case=False, na=False)]
        if row.empty:
            return {"error": f"Cliente '{client_name}' no encontrado en el inventario."}
        
        row = row.iloc[0]
        acc_key = str(row.get(config.COL_CUENTA, 'wac')).strip().lower()
        
        # Re-init with correct account if needed
        if acc_key != 'wac':
            print(f"Cambiando a cuenta: {acc_key} para {client_name}", file=sys.stderr)
            client_mgr = ClientManager(account_key=acc_key)
            creds = client_mgr.get_creds()
            # Update sheets_mgr with new creds for subsequent calls
            sheets_mgr = SheetsManager(creds)
        else:
            client_mgr = temp_mgr
            creds = temp_creds

        ga4_id = str(row.get(config.COL_GA4, '')).strip()
        gsc_url = row.get(config.COL_GSC, '').strip()
        doc_url = row.get(config.COL_DOC, '').strip()
        site_url = row.get(config.COL_URL, '').strip()
        
        # 2. Get dates (Default to last month)
        dates = get_date_ranges()
        
        # 3. Connect to clients
        gsc_client = GSCClient(creds)
        ga4_client = GA4Client(creds)
        looker_client = LookerClient()
        
        # 4. Extract Metrics
        print(f"Extrayendo métricas de {dates['current_start']} a {dates['current_end']}...", file=sys.stderr)
        current_gsc = gsc_client.get_metrics(gsc_url, dates['current_start'], dates['current_end'])
        prev_gsc = gsc_client.get_metrics(gsc_url, dates['prev_start'], dates['prev_end'])
        
        top_urls = gsc_client.get_top_data(gsc_url, dates['current_start'], dates['current_end'], limit=10)
        top_kws = gsc_client.get_top_data(gsc_url, dates['current_start'], dates['current_end'], dimension='query', limit=10)
        total_kws = gsc_client.get_total_keywords(gsc_url, dates['current_start'], dates['current_end'])
        
        current_ga4 = ga4_client.get_organic_traffic(ga4_id, dates['current_start'], dates['current_end'])
        prev_ga4 = ga4_client.get_organic_traffic(ga4_id, dates['prev_start'], dates['prev_end'])

        # 5. Looker PDF Discovery and Download
        print(f"Buscando y descargando PDF de Looker para {client_name}...", file=sys.stderr)
        looker_url = None
        try:
            looker_titles = sheets_mgr.get_sheet_titles(config.SHEET_ID_LOOKER_LINKS)
            target_tab = next((t for t in looker_titles if "Migra" in t), None)
            if target_tab:
                result = sheets_mgr.service.spreadsheets().values().get(
                    spreadsheetId=config.SHEET_ID_LOOKER_LINKS, range=f"'{target_tab}'!A:Z").execute()
                rows = result.get('values', [])
                if rows:
                    headers = [str(h).strip() for h in rows[0]]
                    brand_idx = 0
                    for possible_brand in ["Marca", "CLIENTE", "Cliente", "Marca/Cliente"]:
                        if possible_brand in headers:
                            brand_idx = headers.index(possible_brand)
                            break
                    
                    # Intentamos buscar "Link Looker V2" o nombres similares
                    link_idx = 11  # Columna L por defecto
                    for possible_name in ["Link Looker V2", "Link Looker", "Looker Link", "Link Looker V1"]:
                        if possible_name in headers:
                            link_idx = headers.index(possible_name)
                            break
                    else:
                        for idx, h in enumerate(headers):
                            if "Looker" in h:
                                link_idx = idx
                                break
                    
                    for r in rows[1:]:
                        if len(r) > brand_idx and str(r[brand_idx]).strip().upper() == client_name.upper():
                            if len(r) > link_idx and str(r[link_idx]).strip().startswith("http"):
                                looker_url = r[link_idx].strip()
                                break
        except Exception as le:
            print(f"Error buscando Looker URL: {le}", file=sys.stderr)

        looker_file = None
        if looker_url:
            print(f"Iniciando descarga de Looker: {looker_url}", file=sys.stderr)
            _, _, looker_file = looker_client.capture_looker_report(looker_url, f"reporte_{client_name.replace(' ', '_')}")
        else:
            print(f"No se encontró URL de Looker para {client_name}", file=sys.stderr)

        def delta(c, p):
            if not p: return 0.0
            return ((c - p) / p) * 100

        result = {
            "cliente": client_name,
            "url": site_url,
            "periodo": f"{dates['current_start']} a {dates['current_end']}",
            "doc_url": doc_url,
            "looker_file": looker_file,
            "metrics": {
                "clics": {"actual": current_gsc.get('clicks', 0), "prev": prev_gsc.get('clicks', 0), "delta": delta(current_gsc.get('clicks',0), prev_gsc.get('clicks',0))},
                "impresiones": {"actual": current_gsc.get('impressions', 0), "prev": prev_gsc.get('impressions', 0), "delta": delta(current_gsc.get('impressions',0), prev_gsc.get('impressions',0))},
                "sesiones": {"actual": current_ga4.get('sessions', 0), "prev": prev_ga4.get('sessions', 0), "delta": delta(current_ga4.get('sessions',0), prev_ga4.get('sessions',0))},
                "usuarios_nuevos": {"actual": current_ga4.get('new_users', 0), "prev": prev_ga4.get('new_users', 0)},
                "keywords_totales": total_kws
            },
            "top_urls": [{"url": u['keys'][0], "clics": u['clicks']} for u in top_urls],
            "top_keywords": [{"kw": k['keys'][0], "pos": k['position']} for k in top_kws]
        }
        
        return result

    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Uso: python fast_extractor.py 'Nombre Cliente'"}))
    else:
        name = sys.argv[1]
        data = get_client_data(name)
        print(json.dumps(data, indent=2))
