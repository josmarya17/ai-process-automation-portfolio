import sys
import os
import json
from datetime import date
from data_extractor import ClientManager
from report_generator import DocsManager

def publish_to_doc(doc_url, report_text, month_name, account_key='wac'):
    try:
        print(f"Attempting to publish using account: {account_key}")
        client_mgr = ClientManager(account_key=account_key)
        creds = client_mgr.get_creds()
        docs_mgr = DocsManager(creds)
        
        success = docs_mgr.append_report(doc_url, report_text, month_name)
        return success
    except Exception as e:
        print(f"Error publishing with {account_key}: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: python direct_publisher.py 'URL_DOC' 'CONTENIDO_REPORTE' [MES]")
    else:
        url = sys.argv[1]
        content = sys.argv[2]
        
        # Spanish Month
        spanish_months = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
        default_month = spanish_months[date.today().month - 1] # Current month
        
        month = sys.argv[3] if len(sys.argv) > 3 else default_month
        
        success = publish_to_doc(url, content, month, account_key='wac')
        if not success:
            print("Trying wac2...")
            success = publish_to_doc(url, content, month, account_key='wac2')
            
        if success:
            print("REPORT_PUBLISHED_SUCCESSFULLY")
        else:
            print("REPORT_PUBLISH_FAILED")
