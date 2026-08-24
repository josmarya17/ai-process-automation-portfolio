import os
import json
import time
from datetime import date, timedelta, datetime
import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    DateRange,
    Dimension,
    Metric,
    RunReportRequest,
    FilterExpression,
    Filter
)
from playwright.sync_api import sync_playwright
import config

# Fix for Windows Playwright Assertion Failed: process_title
os.environ["PLAYWRIGHT_SKIP_BROWSER_GC"] = "1"

class ClientManager:
    def __init__(self, account_key='DEFAULT'):
        self.account_key = account_key
        self.creds_file = 'token.json'
        self.scopes = [
            'https://www.googleapis.com/auth/webmasters.readonly',
            'https://www.googleapis.com/auth/analytics.readonly',
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/documents'
        ]
        self.creds = None
        
    def get_creds(self):
        if not self.creds:
            key = str(self.account_key).lower() if self.account_key else 'default'
            token_file = f'token_{key}.json'
            
            if os.path.exists(token_file):
                from google.oauth2.credentials import Credentials
                print(f"Loading credentials from {token_file}")
                try:
                    self.creds = Credentials.from_authorized_user_file(token_file, self.scopes)
                except Exception as e:
                    print(f"Error loading OAuth token from {token_file}: {e}")
                    self.creds = None
            elif os.path.exists('token.json'):
                print(f"Token file '{token_file}' not found. Trying default 'token.json'...")
                from google.oauth2.credentials import Credentials
                try:
                    self.creds = Credentials.from_authorized_user_file('token.json', self.scopes)
                except Exception as e:
                    print(f"Error loading default token.json: {e}")
                    self.creds = None
            
            if not self.creds:
                sa_map = {
                    'wac': 'service_account.json',
                    'wac2': 'conexion-service-account.json',
                    'default': 'service_account.json'
                }
                sa_file = sa_map.get(key, 'service_account.json')
                if os.path.exists(sa_file):
                    print(f"Falling back to Service Account: {sa_file}")
                    from google.oauth2 import service_account as google_sa
                    self.creds = google_sa.Credentials.from_service_account_file(sa_file, scopes=self.scopes)
                else:
                    raise FileNotFoundError(f"Neither {token_file} nor {sa_file} found/valid.")
        return self.creds

class GSCClient:
    def __init__(self, credentials):
        self.service = build('searchconsole', 'v1', credentials=credentials)

    def get_metrics(self, site_url, start_date, end_date):
        request_totals = {
            'startDate': start_date,
            'endDate': end_date,
            'dimensions': [] 
        }
        try:
            response = self.service.searchanalytics().query(siteUrl=site_url, body=request_totals).execute()
            rows = response.get('rows', [])
            if rows:
                return rows[0]
            return {'clicks': 0, 'impressions': 0, 'ctr': 0, 'position': 0}
        except Exception as e:
            print(f"Error GSC Totals for {site_url}: {e}")
            return {'clicks': 0, 'impressions': 0, 'ctr': 0, 'position': 0}

    def get_top_data(self, site_url, start_date, end_date, dimension='page', limit=3):
        request = {
            'startDate': start_date,
            'endDate': end_date,
            'dimensions': [dimension],
            'rowLimit': limit
        }
        try:
            response = self.service.searchanalytics().query(siteUrl=site_url, body=request).execute()
            return response.get('rows', [])
        except Exception as e:
            print(f"Error GSC Top {dimension} for {site_url}: {e}")
            return []
            
    def get_total_keywords(self, site_url, start_date, end_date):
        request = {
            'startDate': start_date,
            'endDate': end_date,
            'dimensions': ['query'],
            'rowLimit': 5000
        }
        try:
            response = self.service.searchanalytics().query(siteUrl=site_url, body=request).execute()
            return len(response.get('rows', []))
        except Exception as e:
            print(f"Error GSC Keywords Count for {site_url}: {e}")
            return 0

class GA4Client:
    def __init__(self, credentials):
        self.client = BetaAnalyticsDataClient(credentials=credentials)

    def get_organic_traffic(self, property_id, start_date, end_date):
        request = RunReportRequest(
            property=f"properties/{property_id}",
            dimensions=[],
            metrics=[
                Metric(name="sessions"), 
                Metric(name="newUsers"),
                Metric(name="engagementRate"),
                Metric(name="bounceRate"),
                Metric(name="averageSessionDuration"),
                Metric(name="conversions")
            ],
            date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
            dimension_filter=FilterExpression(
                filter=Filter(
                    field_name="sessionDefaultChannelGroup",
                    string_filter=Filter.StringFilter(
                        value="Organic Search",
                        match_type=Filter.StringFilter.MatchType.EXACT
                    )
                )
            )
        )
        try:
            response = self.client.run_report(request)
            if response.rows:
                return {
                    'sessions': int(response.rows[0].metric_values[0].value),
                    'new_users': int(response.rows[0].metric_values[1].value),
                    'engagement_rate': float(response.rows[0].metric_values[2].value) * 100,
                    'bounce_rate': float(response.rows[0].metric_values[3].value) * 100,
                    'avg_session_duration': float(response.rows[0].metric_values[4].value),
                    'conversions': float(response.rows[0].metric_values[5].value)
                }
            return {
                'sessions': 0, 'new_users': 0, 'engagement_rate': 0, 
                'bounce_rate': 0, 'avg_session_duration': 0, 'conversions': 0
            }
        except Exception as e:
            print(f"Error GA4 for {property_id}: {e}")
            return {'sessions': 0, 'new_users': 0}

class LookerClient:
    def capture_looker_report(self, looker_url, base_filename):
        """Downloads Looker report as PDF with extreme robustness. Returns (success, text, pdf_path)"""
        final_path = f"{base_filename}.pdf"
        print(f"DEBUG: Starting Looker PDF Flow for {looker_url}")
        
        try:
            with sync_playwright() as p:
                print(f"DEBUG: Lanzando navegador con técnicas anti-detección para: {looker_url}")
                browser = p.chromium.launch(
                    headless=True, 
                    slow_mo=150,
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                        '--disable-infobars',
                        '--window-position=0,0',
                        '--ignore-certifcate-errors',
                        '--ignore-certifcate-errors-spki-list',
                        '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
                    ]
                )
                
                context = browser.new_context(
                    viewport={'width': 1366, 'height': 768},
                    accept_downloads=True,
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
                )

                # Aplicar Stealth
                try:
                    from playwright_stealth import stealth
                    page = context.new_page()
                    stealth(page)
                except Exception as e:
                    print(f"DEBUG: Error al aplicar stealth: {e}")
                    page = context.new_page()
                
                print(f"DEBUG: Navegando a {looker_url}")
                try:
                    page.goto(looker_url, timeout=120000, wait_until="load", referer="https://www.google.com/")
                except Exception as e:
                    print(f"DEBUG: Goto timeout (continuando): {e}")
                
                print("DEBUG: Esperando estabilidad de Looker (40s)...")
                time.sleep(40)
                
                # Cerrar posibles avisos o diálogos iniciales que bloqueen clics
                try:
                    close_btn = page.locator('button:has-text("Entendido"), button[aria-label="Cerrar"], .md-dialog-container button:has-text("Cerrar")').first
                    if close_btn.is_visible(timeout=5000):
                        print("DEBUG: Cerrando diálogo intrusivo inicial...")
                        close_btn.click()
                except: pass
                
                if "No puedes acceder" in page.content() or "rejected" in page.url:
                    print("DEBUG: ¡AVISO! Google bloquea acceso. Tomando captura de aviso...")
                    page.screenshot(path=f"{base_filename}_blocked.png")
                
                # 4. SECUENCIA DE DESCARGA
                try:
                    # Paso A: Botón de opciones (tres puntos)
                    print("DEBUG: Paso A: Clic en menú de opciones...")
                    more_btn_selector = 'button[aria-label*="More"], button[aria-label*="opciones"], .more-options-button'
                    page.wait_for_selector(more_btn_selector, timeout=60000) # Más paciencia para el primer menú
                    page.locator(more_btn_selector).first.click()
                    time.sleep(5)
                    
                    # Paso B: Descargar informe (share-dl-button)
                    print("DEBUG: Paso B: Clic en 'Descargar informe'...")
                    dl_opt_selector = 'button.share-dl-button, [role="menuitem"]:has-text("Descargar informe"), button:has-text("Descargar informe")'
                    page.wait_for_selector(dl_opt_selector, timeout=30000)
                    page.locator(dl_opt_selector).first.click()
                    time.sleep(8)
                    
                    # Captura del modal para el usuario
                    page.screenshot(path=f"{base_filename}_modal.png")
                    print("DEBUG: Captura del modal realizada.")

                    # Paso C: Botón azul del modal "Descargar"
                    print("DEBUG: Paso C: Clic en botón final 'Descargar' y esperando generación de PDF (puede tardar)...")
                    final_dl_selector = 'button[data-test-id="download-button"], .export-pdf-dialog button:has-text("Descargar"), md-dialog-actions button:has-text("Descargar")'
                    page.wait_for_selector(final_dl_selector, timeout=30000)
                    
                    # Usamos un timeout mayor para la descarga (600s = 10 minutos)
                    with page.expect_download(timeout=600000) as download_info:
                        print("DEBUG: Enviando clic final de descarga...")
                        page.locator(final_dl_selector).last.click(force=True)
                        print("DEBUG: Clic enviado, esperando a que el navegador inicie la descarga...")
                    
                    download = download_info.value
                    print(f"DEBUG: Descarga iniciada: {download.suggested_filename}. Guardando en {final_path}...")
                    download.save_as(final_path)
                    
                    # Verificación extra
                    if os.path.exists(final_path):
                        print(f"DEBUG: ¡CONTRATADO! PDF verificado en disco: {os.path.getsize(final_path)} bytes.")
                        time.sleep(5) # Pequeña espera extra por seguridad
                        browser.close()
                        return True, "Descarga exitosa", final_path
                    else:
                        print("DEBUG: El archivo no se encontró después de save_as.")
                        browser.close()
                        return False, "Error al guardar el archivo", None

                except Exception as dl_err:
                    print(f"DEBUG: Fallo en secuencia: {dl_err}")
                    final_path = f"{base_filename}_final_err.png"
                    page.screenshot(path=final_path, full_page=True)
                    browser.close()
                    return False, f"Fallo descarga: {dl_err}", None

        except Exception as e:
            print(f"DEBUG: ERROR General: {e}")
            return False, str(e), None


def get_date_ranges():
    today = date.today()
    last_month_end = today.replace(day=1) - timedelta(days=1)
    last_month_start = last_month_end.replace(day=1)
    prev_month_end = last_month_start - timedelta(days=1)
    prev_month_start = prev_month_end.replace(day=1)
    return {
        'current_start': last_month_start.strftime('%Y-%m-%d'),
        'current_end': last_month_end.strftime('%Y-%m-%d'),
        'prev_start': prev_month_start.strftime('%Y-%m-%d'),
        'prev_end': prev_month_end.strftime('%Y-%m-%d')
    }
