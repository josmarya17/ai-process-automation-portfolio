import os
import sys
import warnings
import json

# Silenciar advertencias informacionales de librerías
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)

# Playwright Windows Fix - Must be set before importing/starting playwright
os.environ["PLAYWRIGHT_SKIP_BROWSER_GC"] = "1"

import time
import argparse
from datetime import date, timedelta, datetime
import pandas as pd
import config
from data_extractor import ClientManager, GSCClient, GA4Client, LookerClient, get_date_ranges
from report_generator import GeminiClient, SheetsManager, DocsManager
import concurrent.futures

STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "STATE.json")

def update_state(progress=None, message=None, metrics=None, analysis=None, done=False, error=None):
    if not os.path.exists(STATE_FILE): return
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            state = json.load(f)
        
        if progress is not None: state["progress"] = progress
        if message is not None: state["message"] = message
        if metrics is not None: state.setdefault("metrics", {}).update(metrics)
        if analysis is not None: state["analysis"] = analysis
        if done: state["done"] = True
        if error: state["error"] = error
        
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=4)
    except:
        pass
# Force UTF-8 encoding for terminal output
if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

def process_client(client_row, dates, client_manager, gemini_client, sheets_manager, docs_manager, mode='full', looker_url=None):
    client_name = client_row.get(config.COL_CLIENTE)
    ga4_id = str(client_row.get(config.COL_GA4, '')).strip()
    gsc_url = client_row.get(config.COL_GSC, '').strip()
    doc_url = client_row.get(config.COL_DOC, '').strip()
    
    print(f"\n--- Processing {client_name} (Mode: {mode.upper()}) ---")
    
    if not gsc_url or not ga4_id:
        print(f"Skipping {client_name}: Missing GSC URL or GA4 ID")
        return

    try:
        creds = client_manager.get_creds()
        gsc_client = GSCClient(creds)
        ga4_client = GA4Client(creds)
    except Exception as e:
        print(f"Auth Error for {client_name}: {e}")
        return

    # 1. Extract Data (Common for both modes)
    update_state(progress=20, message="Extrayendo métricas de GSC...")
    current_gsc = gsc_client.get_metrics(gsc_url, dates['current_start'], dates['current_end'])
    prev_gsc = gsc_client.get_metrics(gsc_url, dates['prev_start'], dates['prev_end'])
    
    update_state(progress=40, message="Obteniendo Top URLs y Keywords...")
    top_urls = gsc_client.get_top_data(gsc_url, dates['current_start'], dates['current_end'], dimension='page')
    top_keywords = gsc_client.get_top_data(gsc_url, dates['current_start'], dates['current_end'], dimension='query')
    total_keywords = gsc_client.get_total_keywords(gsc_url, dates['current_start'], dates['current_end'])
    
    update_state(progress=60, message="Consultando tráfico en GA4...")
    current_ga4 = ga4_client.get_organic_traffic(ga4_id, dates['current_start'], dates['current_end'])
    prev_ga4 = ga4_client.get_organic_traffic(ga4_id, dates['prev_start'], dates['prev_end'])

    def safe_div(a, b):
        if not b: return 0.0
        return ((a - b) / b) * 100

    data = {
        'clicks': current_gsc.get('clicks', 0),
        'delta_clicks': safe_div(current_gsc.get('clicks', 0), prev_gsc.get('clicks', 0)),
        'impressions': current_gsc.get('impressions', 0),
        'delta_impressions': safe_div(current_gsc.get('impressions', 0), prev_gsc.get('impressions', 0)),
        'ctr': current_gsc.get('ctr', 0) * 100,
        'delta_ctr': safe_div(current_gsc.get('ctr', 0), prev_gsc.get('ctr', 0)),
        'sessions': current_ga4.get('sessions', 0),
        'delta_sessions': safe_div(current_ga4.get('sessions', 0), prev_ga4.get('sessions', 0)),
        'new_users': current_ga4.get('new_users', 0),
        'delta_users': safe_div(current_ga4.get('new_users', 0), prev_ga4.get('new_users', 0)),
        'engagement_rate': current_ga4.get('engagement_rate', 0),
        'bounce_rate': current_ga4.get('bounce_rate', 0),
        'conversions': current_ga4.get('conversions', 0),
        'total_keywords': total_keywords
    }

    # Month Names
    spanish_months = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
    today = date.today()
    last_month = today.replace(day=1) - timedelta(days=1)
    month_name = spanish_months[last_month.month - 1]

    # Enviar métricas al Dashboard
    update_state(progress=80, message="Métricas procesadas.", metrics={
        "Clics": f"{data['clicks']} ({data['delta_clicks']:.1f}%)",
        "Sesiones": f"{data['sessions']} ({data['delta_sessions']:.1f}%)",
        "Keywords": data['total_keywords']
    })

    # --- MODO: MÉTRICAS (Guardado en Historial) ---
    if mode == 'metrics':
        print(f"Actualizando Hoja de Historial para {client_name}...")
        history_row = [
            client_name, month_name, datetime.now().strftime('%Y-%m-%d'),
            data['clicks'], f"{data['delta_clicks']:.1f}%",
            data['impressions'], f"{data['delta_impressions']:.1f}%",
            f"{data['ctr']:.2f}%", f"{data['delta_ctr']:.1f}%",
            data['sessions'], f"{data['delta_sessions']:.1f}%",
            data['new_users'], f"{data['delta_users']:.1f}%",
            top_urls[0]['keys'][0] if len(top_urls) > 0 else '', top_urls[0]['clicks'] if len(top_urls) > 0 else '',
            top_urls[0]['impressions'] if len(top_urls) > 0 else '', top_urls[0]['position'] if len(top_urls) > 0 else '',
            top_urls[1]['keys'][0] if len(top_urls) > 1 else '', top_urls[1]['clicks'] if len(top_urls) > 1 else '',
            top_urls[1]['impressions'] if len(top_urls) > 1 else '', top_urls[1]['position'] if len(top_urls) > 1 else '',
            top_urls[2]['keys'][0] if len(top_urls) > 2 else '', top_urls[2]['clicks'] if len(top_urls) > 2 else '',
            top_urls[2]['impressions'] if len(top_urls) > 2 else '', top_urls[2]['position'] if len(top_urls) > 2 else '',
            data['total_keywords'],
            top_keywords[0]['keys'][0] if len(top_keywords) > 0 else '', top_keywords[0]['position'] if len(top_keywords) > 0 else '',
            top_keywords[1]['keys'][0] if len(top_keywords) > 1 else '', top_keywords[1]['position'] if len(top_keywords) > 1 else '',
            top_keywords[2]['keys'][0] if len(top_keywords) > 2 else '', top_keywords[2]['position'] if len(top_keywords) > 2 else ''
        ]
        try:
            sheets_manager.append_history(config.SHEET_ID_METRICS, config.TAB_NAME_METRICS, history_row, headers=config.HEADERS_HISTORICO)
            print(f"✅ Métricas guardadas exitosamente para {client_name}")
        except Exception as e:
            print(f"Error guardando historial: {e}")

    # --- EXTRACCIÓN DE LOOKER (Solo para Análisis/Contexto) ---
    looker_image_path = None
    looker_text_content = ""
    if mode in ['full', 'context'] and looker_url:
        print(f"Capturando Reporte Looker (Vista Técnica)...")
        looker_client = LookerClient()
        base_name = f"looker_report_{client_name.replace(' ', '_')}"
        try:
            success, looker_text_content, looker_image_path = looker_client.capture_looker_report(looker_url, base_name)
        except Exception as e:
            print(f"Error Looker para {client_name}: {e}")

    # Formatear textos de apoyo
    top_urls_text = "\n".join([f"{r['keys'][0]} -> {r['clicks']} clics, pos {r['position']:.1f}" for r in top_urls[:5]])
    top_keywords_text = "\n".join([f"'{r['keys'][0]}' -> Pos {r['position']:.1f}" for r in top_keywords[:5]])
    data_summary = f"Clics: {data['clicks']} ({data['delta_clicks']:.1f}%)\nImpresiones: {data['impressions']}\nSesiones: {data['sessions']}\nEngagement Rate: {data['engagement_rate']:.1f}%\nBounce Rate: {data['bounce_rate']:.1f}%\nConversiones: {data['conversions']}\nLooker: {looker_text_content[:2000]}"

    # --- MODO: CONTEXTO (Para Antigravity) ---
    if mode == 'context':
        print("\n" + "="*80)
        print(f"📦 PAQUETE DE DATOS PARA ANTIGRAVITY | CLIENTE: {client_name}")
        print("="*80)
        print(f"DOMINIO: {client_row.get(config.COL_URL, '')}")
        print(f"PERIODO: {dates['current_start']} a {dates['current_end']}")
        print(f"MÉTRICAS TÉCNICAS:\n{data_summary}")
        print(f"\nTOP URLS:\n{top_urls_text}")
        print(f"\nTOP KEYWORDS:\n{top_keywords_text}")
        print(f"\nTOTAL KEYWORDS INDEXADAS: {data['total_keywords']}")
        print(f"DOC_URL: {doc_url}")
        print("="*80)
        print("--- FIN DEL PAQUETE ---")
        
        # Limpieza inmediata (Desactivada para análisis manual por Antigravity)
        # if looker_image_path and os.path.exists(looker_image_path):
        #     os.remove(looker_image_path)

        return

    # --- MODO: FULL (Análisis Antigravity Exclusive - AUTÓNOMO) ---
    if mode == 'full':
        update_state(progress=90, message="🧠 Antigravity analizando datos técnicos...")
        print(f"Invocando motor Antigravity local para {client_name}...")
        try:
            # Prepare Prompt
            prompt = config.GEMINI_PROMPT_TEMPLATE.format(
                cliente=client_name,
                dominio=client_row.get(config.COL_URL, ''),
                data_summary=data_summary,
                top_urls_text=top_urls_text,
                top_keywords_text=top_keywords_text,
                total_keywords=data['total_keywords']
            )
            
            # 1. Generar Análisis IA (Usa la instancia pasada)
            analysis_text = gemini_client.generate_report(prompt, image_path=looker_image_path)
            
            if not analysis_text or "Error:" in analysis_text or "Cuota agotada" in analysis_text:
                if "Cuota agotada" in str(analysis_text):
                    update_state(progress=92, message="⚠️ Cuota local agotada. Redirigiendo al Núcleo Antigravity...", analysis="⏳ Antigravity está tomando el control del análisis.")
                    print("RESCUE_HINT: API_QUOTA_EXHAUSTED")
                else:
                    update_state(error=f"Fallo en análisis IA: {analysis_text}")
                return

            update_state(progress=95, message="✍️ Publicando informe en Google Doc...", analysis=analysis_text)
            
            # 2. Publicar en Google Doc
            current_month = date.today().strftime('%B') # Ejemplo: February
            pub_success = docs_manager.append_report(doc_url, analysis_text, current_month)
            
            if pub_success:
                update_state(progress=100, message="✅ Informe publicado exitosamente.", done=True)
                print(f"✅ Proceso completo para {client_name}")
            else:
                 update_state(error="Error al publicar en Google Doc.")
                 return

        except Exception as e:
            print(f"❌ Error en motor Antigravity: {e}")
            update_state(error=str(e))
            return

    # Cleanup Final: Asegurar eliminación del PDF y TXT para no embasurar (Desactivado para análisis manual)
    # temp_files = [looker_image_path, "DATOS_PARA_ANALISIS.txt"]
    # for f_path in temp_files:
    #     if f_path and os.path.exists(f_path):
    #         for _ in range(3): # 3 Intentos de borrado
    #             try:
    #                 time.sleep(1)
    #                 os.remove(f_path)
    #                 print(f"✅ Archivo temporal eliminado: {os.path.basename(f_path)}")
    #                 break
    #             except:
    #                 time.sleep(1)


def main():
    parser = argparse.ArgumentParser(description="WAC SEO Automation")
    parser.add_argument("--mode", choices=["full", "metrics", "context"], default="full", help="Execution mode")
    parser.add_argument("--client", help="Process a single client (case insensitive)")
    args = parser.parse_args()

    print("="*50)
    print(f"🚀 INICIANDO AUTOMATIZACIÓN SEO | MODO: {args.mode.upper()}")
    print(f"📅 Fecha de Análisis: {date.today()}")
    print("="*50)
    dates = get_date_ranges()
    master_account = 'wac'
    client_manager_master = ClientManager(account_key=master_account)
    gemini_client = GeminiClient(api_keys=config.GEMINI_API_KEYS)
    
    # Read Properties
    print("Reading Properties Sheet...")
    try:
        creds_master = client_manager_master.get_creds()
        sheets_manager_master = SheetsManager(creds_master)
        df_props = sheets_manager_master.read_config_sheet(config.SHEET_ID_PROPIEDADES, config.TAB_NAME_PROPIEDADES)
        
        # Filter for ACTIVE clients only
        if config.COL_ACTIVO in df_props.columns:
            initial_count = len(df_props)
            df_props = df_props[df_props[config.COL_ACTIVO].astype(str).str.strip().str.upper() == 'TRUE']
            print(f"Filtered for Active clients: {len(df_props)} of {initial_count} total.")
        
    except Exception as e:
        print(f"Error reading properties: {e}")
        return

    # Looker Map
    client_looker_map = {}
    try:
        print(f"Reading Looker Links from Sheet: {config.SHEET_ID_LOOKER_LINKS}")
        looker_titles = sheets_manager_master.get_sheet_titles(config.SHEET_ID_LOOKER_LINKS)
        target_tab = next((t for t in looker_titles if "Migra" in t), None)
        if target_tab:
            print(f"Found Tab: {target_tab}")
            result = sheets_manager_master.service.spreadsheets().values().get(spreadsheetId=config.SHEET_ID_LOOKER_LINKS, range=f"'{target_tab}'!A:Z").execute()
            rows = result.get('values', [])
            print(f"Read {len(rows)} rows from Looker Links tab.")
            if rows:
                headers = [str(h).strip() for h in rows[0]]
                brand_idx = 0
                for possible_brand in ["Marca", "CLIENTE", "Cliente", "Marca/Cliente"]:
                    if possible_brand in headers:
                        brand_idx = headers.index(possible_brand)
                        break
                
                # Intentamos buscar "Link Looker V2" o nombres similares
                link_idx = 11  # Columna L por defecto (índice 11)
                for possible_name in ["Link Looker V2", "Link Looker", "Looker Link", "Link Looker V1"]:
                    if possible_name in headers:
                        link_idx = headers.index(possible_name)
                        break
                else:
                    for idx, h in enumerate(headers):
                        if "Looker" in h:
                            link_idx = idx
                            break
                            
                print(f"Using columns: Marca -> index {brand_idx}, Link Looker -> index {link_idx}")
                
                for i, r in enumerate(rows[1:]):
                    if len(r) > link_idx and str(r[link_idx]).strip().startswith("http"):
                        brand_name = str(r[brand_idx]).strip().upper() if len(r) > brand_idx else ""
                        if brand_name:
                            url = r[link_idx].strip()
                            client_looker_map[brand_name] = url
            print(f"Mapped {len(client_looker_map)} Looker URLs.")
        else:
            print(f"WARNING: No tab with 'Migra' found in Looker Links sheet. Titles: {looker_titles}")
    except Exception as e:
        print(f"ERROR reading Looker Links: {e}")

    if args.client:
        df_props = df_props[df_props[config.COL_CLIENTE].astype(str).str.strip().str.upper() == args.client.upper()]
        print(f"Filtered to single client: {args.client} (Found: {len(df_props)})")

    if df_props.empty:
        print("No clients to process. Exit.")
        return

    processed_count = 0
    start_time_total = time.time()
    
    for _, row in df_props.iterrows():
        name = str(row.get(config.COL_CLIENTE, '')).strip()
        looker_url = client_looker_map.get(name.upper())
        if not looker_url:
            for k, v in client_looker_map.items():
                if name.upper() in k or k in name.upper():
                    looker_url = v
                    break
        account_key = str(row.get(config.COL_CUENTA, 'wac')).strip().lower()
        if account_key == 'nan': account_key = 'wac'
        
        try:
            client_mgr = ClientManager(account_key=account_key)
            creds = client_mgr.get_creds()
            process_client(row, dates, client_mgr, gemini_client, SheetsManager(creds), DocsManager(creds), mode=args.mode, looker_url=looker_url)
            processed_count += 1
        except Exception as e:
            print(f"Error {name}: {e}")

    end_time_total = time.time()
    duration = end_time_total - start_time_total
    print("="*50)
    # En modo full, el éxito se reporta dentro de process_client
    if args.mode != 'full':
        update_state(done=True, message=f"Proceso completado en {duration:.1f}s.")

if __name__ == "__main__":
    main()
