import sys
from data_extractor import ClientManager
from report_generator import SheetsManager
import config

def main():
    try:
        print("Initializing ClientManager...")
        client_manager_master = ClientManager(account_key='DEFAULT')
        creds_master = client_manager_master.get_creds()
        
        print("Initializing SheetsManager...")
        sheets_manager_master = SheetsManager(creds_master)
        
        print(f"Reading properties sheet: {config.SHEET_ID_PROPIEDADES}...")
        df_props = sheets_manager_master.read_config_sheet(config.SHEET_ID_PROPIEDADES, config.TAB_NAME_PROPIEDADES)
        
        print("\nActive clients found:")
        if config.COL_ACTIVO in df_props.columns:
            active_df = df_props[df_props[config.COL_ACTIVO].astype(str).str.strip().str.upper() == 'TRUE']
            for idx, row in active_df.iterrows():
                print(f"  - Brand: {row.get(config.COL_CLIENTE)}, GA4 ID: {row.get(config.COL_GA4)}, GSC URL: {row.get(config.COL_GSC)}, Cuenta: {row.get(config.COL_CUENTA)}")
        else:
            for idx, row in df_props.iterrows():
                print(f"  - Brand: {row.get(config.COL_CLIENTE)}, GA4 ID: {row.get(config.COL_GA4)}, GSC URL: {row.get(config.COL_GSC)}, Cuenta: {row.get(config.COL_CUENTA)}")
                
    except Exception as e:
        print(f"Error listing clients: {e}")

if __name__ == "__main__":
    main()
