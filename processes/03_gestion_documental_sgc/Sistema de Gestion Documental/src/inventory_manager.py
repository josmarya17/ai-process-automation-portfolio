import os
import re
import urllib.request
import pandas as pd
import io
from src import config
from src import google_client

# URLs de exportación pública en caso de fallback (sin credenciales)
URL_INVENTARIO_CSV = f"https://docs.google.com/spreadsheets/d/{config.SPREADSHEET_ID}/export?format=csv&gid=0"
URL_MATRIZ_CSV = f"https://docs.google.com/spreadsheets/d/{config.SPREADSHEET_ID}/export?format=csv&gid=858014120"

class InventoryManager:
    def __init__(self):
        self.areas_df = None
        self.matriz_df = None
        self.proc_flujos_df = None
        self.normas_df = None
        self.areas_mapping = {}  # Nombre -> Codigo (ej: Compras -> CMP)
        self.types_mapping = {}  # Nombre -> Codigo (ej: Procedimiento -> PR)
        self.title_nomenclatura = "Nomenclatura Documentos " # Nombre por defecto con espacio al final
        self.title_matriz = "Orden Matriz de Documentos " # Nombre por defecto con espacio al final
        self.load_data()

    def load_data(self):
        """Intenta cargar los datos desde Google Sheets (OAuth), fallback a CSV público, y fallback final a local."""
        try:
            self._load_from_api()
            config.logger.info("Datos cargados correctamente usando la API oficial de Google Sheets.")
        except Exception as e:
            config.logger.warning(f"No se pudo usar la API de Sheets ({e}). Usando fallback de descarga CSV pública...")
            try:
                self._load_from_public_csv()
                config.logger.info("Datos cargados correctamente desde exportación CSV pública.")
            except Exception as e_csv:
                config.logger.error(f"Error al descargar CSV pública ({e_csv}). Usando cache local si existe...")
                self._load_from_local_cache()

        # Procesar mapeos de nomenclaturas a partir de la hoja "Inventario Documentos" (hoja 1)
        self._build_mappings()

        # Cargar de local matriz_proceso_y_flujos.csv y matriz_normas.csv si no se pudieron cargar o vienen vacíos
        pf_local_path = os.path.join(config.OUTPUTS_DIR, "matriz_proceso_y_flujos.csv")
        n_local_path = os.path.join(config.OUTPUTS_DIR, "matriz_normas.csv")

        # Cargar Matriz Proceso y Flujos
        if self.proc_flujos_df is None or self.proc_flujos_df.empty:
            if os.path.exists(pf_local_path):
                try:
                    self.proc_flujos_df = pd.read_csv(pf_local_path)
                    config.logger.info("Matriz de proceso y flujos cargada de CSV local de salidas.")
                except Exception as e:
                    config.logger.error(f"Error al leer local matriz_proceso_y_flujos.csv: {e}")
                    self.proc_flujos_df = pd.DataFrame()
            else:
                self.proc_flujos_df = pd.DataFrame()

        # Cargar Matriz Normas
        if self.normas_df is None or self.normas_df.empty:
            if os.path.exists(n_local_path):
                try:
                    self.normas_df = pd.read_csv(n_local_path)
                    config.logger.info("Matriz de normas cargada de CSV local de salidas.")
                except Exception as e:
                    config.logger.error(f"Error al leer local matriz_normas.csv: {e}")
                    self.normas_df = pd.DataFrame()
            else:
                self.normas_df = pd.DataFrame()

    def _load_from_api(self):
        """Lee directamente de las hojas usando la API de Google Sheets con OAuth."""
        sheets_service = google_client.get_sheets_service()
        
        # Obtener los nombres reales de las pestañas dinámicamente para evitar errores por espacios en blanco al final
        sheet_metadata = sheets_service.spreadsheets().get(spreadsheetId=config.SPREADSHEET_ID).execute()
        sheets = sheet_metadata.get('sheets', [])
        
        for s in sheets:
            title = s['properties']['title']
            if title.strip() == "Nomenclatura Documentos":
                self.title_nomenclatura = title
            elif title.strip() == "Orden Matriz de Documentos":
                self.title_matriz = title

        config.logger.info(f"Pestañas detectadas en Sheets API: Nomenclatura='{self.title_nomenclatura}', Matriz='{self.title_matriz}'")

        # 1. Leer hoja "Nomenclatura Documentos"
        res_inventario = sheets_service.spreadsheets().values().get(
            spreadsheetId=config.SPREADSHEET_ID,
            range=f"'{self.title_nomenclatura}'!A1:E50"
        ).execute()
        rows_inv = res_inventario.get('values', [])
        
        # Asegurar longitud uniforme de 5 columnas para evitar errores de pandas
        max_cols_inv = 5
        clean_rows_inv = []
        for r in rows_inv:
            if len(r) < max_cols_inv:
                r = r + [''] * (max_cols_inv - len(r))
            clean_rows_inv.append(r[:max_cols_inv])
            
        self.areas_df = pd.DataFrame(clean_rows_inv) if clean_rows_inv else pd.DataFrame()

        # 2. Leer hoja "Orden Matriz de Documentos"
        res_matriz = sheets_service.spreadsheets().values().get(
            spreadsheetId=config.SPREADSHEET_ID,
            range=f"'{self.title_matriz}'!A1:H200"
        ).execute()
        rows_mat = res_matriz.get('values', [])
        # Rellenar con vacíos si hay filas más cortas que 8 columnas
        max_cols = 8
        clean_rows = []
        for r in rows_mat:
            if len(r) < max_cols:
                r = r + [''] * (max_cols - len(r))
            clean_rows.append(r[:max_cols])
            
        self.matriz_df = pd.DataFrame(clean_rows[1:], columns=clean_rows[0]) if clean_rows else pd.DataFrame()

        # 3. Leer hoja "Matriz final_Proceso y flujos"
        try:
            res_proc_flujos = sheets_service.spreadsheets().values().get(
                spreadsheetId=config.SPREADSHEET_ID,
                range="'Matriz final_Proceso y flujos'!A1:H1000"
            ).execute()
            rows_pf = res_proc_flujos.get('values', [])
            if rows_pf:
                max_cols_pf = 8
                clean_rows_pf = []
                for r in rows_pf:
                    if len(r) < max_cols_pf:
                        r = r + [''] * (max_cols_pf - len(r))
                    clean_rows_pf.append(r[:max_cols_pf])
                self.proc_flujos_df = pd.DataFrame(clean_rows_pf[1:], columns=clean_rows_pf[0])
            else:
                self.proc_flujos_df = pd.DataFrame(columns=['Area', 'Flujo', 'Proceso', 'Link flujo', 'Link proceso', 'Codigo Proceso', 'Codigo flujo', 'Observación'])
        except Exception as e_pf:
            config.logger.warning(f"No se pudo cargar la hoja 'Matriz final_Proceso y flujos' desde API: {e_pf}")
            self.proc_flujos_df = pd.DataFrame()

        # 4. Leer hoja "Matriz final_Normas"
        try:
            res_normas = sheets_service.spreadsheets().values().get(
                spreadsheetId=config.SPREADSHEET_ID,
                range="'Matriz final_Normas'!A1:E500"
            ).execute()
            rows_n = res_normas.get('values', [])
            if rows_n:
                max_cols_n = 5
                clean_rows_n = []
                for r in rows_n:
                    if len(r) < max_cols_n:
                        r = r + [''] * (max_cols_n - len(r))
                    clean_rows_n.append(r[:max_cols_n])
                self.normas_df = pd.DataFrame(clean_rows_n[1:], columns=clean_rows_n[0])
            else:
                self.normas_df = pd.DataFrame(columns=['Area', 'Norma', 'Link documento', 'Codigo Norma', 'Observación'])
        except Exception as e_n:
            config.logger.warning(f"No se pudo cargar la hoja 'Matriz final_Normas' desde API: {e_n}")
            self.normas_df = pd.DataFrame()
        
        # Guardar en cache local para offline
        os.makedirs(os.path.join(config.BASE_DIR, "cache"), exist_ok=True)
        self.areas_df.to_csv(os.path.join(config.BASE_DIR, "cache", "areas.csv"), index=False)
        self.matriz_df.to_csv(os.path.join(config.BASE_DIR, "cache", "matriz.csv"), index=False)
        if self.proc_flujos_df is not None:
            self.proc_flujos_df.to_csv(os.path.join(config.BASE_DIR, "cache", "matriz_proceso_y_flujos.csv"), index=False)
        if self.normas_df is not None:
            self.normas_df.to_csv(os.path.join(config.BASE_DIR, "cache", "matriz_normas.csv"), index=False)

    def _load_from_public_csv(self):
        """Descarga los CSV públicos usando urllib."""
        # 1. Leer Inventario
        req_inv = urllib.request.Request(URL_INVENTARIO_CSV, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req_inv) as response:
            csv_data = response.read().decode('utf-8')
            self.areas_df = pd.read_csv(io.StringIO(csv_data))
            
        # 2. Leer Matriz
        req_mat = urllib.request.Request(URL_MATRIZ_CSV, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req_mat) as response:
            csv_data = response.read().decode('utf-8')
            self.matriz_df = pd.read_csv(io.StringIO(csv_data))
            
        # Guardar en cache local para offline
        os.makedirs(os.path.join(config.BASE_DIR, "cache"), exist_ok=True)
        self.areas_df.to_csv(os.path.join(config.BASE_DIR, "cache", "areas.csv"), index=False)
        self.matriz_df.to_csv(os.path.join(config.BASE_DIR, "cache", "matriz.csv"), index=False)

    def _load_from_local_cache(self):
        """Carga los CSV guardados en cache."""
        areas_path = os.path.join(config.BASE_DIR, "cache", "areas.csv")
        matriz_path = os.path.join(config.BASE_DIR, "cache", "matriz.csv")
        pf_path = os.path.join(config.BASE_DIR, "cache", "matriz_proceso_y_flujos.csv")
        n_path = os.path.join(config.BASE_DIR, "cache", "matriz_normas.csv")
        
        if os.path.exists(areas_path) and os.path.exists(matriz_path):
            self.areas_df = pd.read_csv(areas_path)
            self.matriz_df = pd.read_csv(matriz_path)
            if os.path.exists(pf_path):
                self.proc_flujos_df = pd.read_csv(pf_path)
            if os.path.exists(n_path):
                self.normas_df = pd.read_csv(n_path)
            config.logger.info("Datos cargados correctamente de la cache local.")
        else:
            raise FileNotFoundError("No se encontró la cache local de inventario y no hay internet.")

    def _build_mappings(self):
        """Extrae la nomenclatura de áreas y tipos de documentos de la primera hoja."""
        if self.areas_df is None or self.areas_df.empty:
            # Mapeo hardcodeado de respaldo si falla todo
            self.areas_mapping = {
                'Compras': 'CMP', 'Inventario': 'INV', 'Ventas': 'VEN', 
                'Almacen': 'ALM', 'Contabilidad': 'CNT', 'Servicios Generales': 'SEG',
                'Aseguramiento del efectivo': 'ASE', 'Tesoreria': 'TES',
                'Cuentas por pagar': 'CXP', 'Cuentas por cobrar': 'CXC',
                'Tecnología': 'TEC', 'Recursos Humanos': 'RRHH',
                'Soporte al cliente': 'SP'
            }
            self.types_mapping = {
                'Procedimiento': 'PR', 'Politicas y Lineamientos': 'PO', 'Norma': 'PO',
                'Instruccion de Trabajo': 'IT', 'Flujo de Trabajo': 'FT'
            }
            return

        # Limpiar nombres de columnas
        df = self.areas_df.copy()
        # En base al CSV que vimos:
        # Columna 0 es "Areas", Columna 1 es "Codigo", Columna 3 es "Tipo de Documento", Columna 4 es "Codigo"
        # Limpiamos filas vacías
        df.dropna(how='all', inplace=True)
        
        # Mapeo de Áreas
        for _, row in df.iterrows():
            area_name = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else None
            area_code = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else None
            if area_name and area_code and area_name != 'nan' and area_code != 'nan' and area_name != 'Areas':
                self.areas_mapping[area_name] = area_code
                
            type_name = str(row.iloc[3]).strip() if pd.notna(row.iloc[3]) else None
            type_code = str(row.iloc[4]).strip() if pd.notna(row.iloc[4]) else None
            if type_name and type_code and type_name != 'nan' and type_code != 'nan' and type_name != 'Tipo de Documento':
                self.types_mapping[type_name] = type_code
                
        # Aliases adicionales para robustez
        self.types_mapping['Norma'] = 'PO'
        self.types_mapping['Políticas y Lineamientos'] = 'PO'
        self.types_mapping['Instructivo'] = 'IT'
        self.areas_mapping['Almacen/Inventario'] = 'INV'
        self.areas_mapping['Oficina central'] = 'SG'

    def get_areas(self):
        """Retorna la lista de nombres de áreas."""
        return list(self.areas_mapping.keys())

    def get_document_types(self):
        """Retorna la lista de tipos de documentos."""
        return ["Procedimiento", "Norma", "Instrucción de Trabajo", "Flujo de Trabajo"]

    def get_area_code(self, area_name):
        """Busca el código de área resolviendo coincidencias parciales de forma robusta."""
        area_name_norm = area_name.lower().strip()
        # Casos especiales de mapeo común
        if "ventas" in area_name_norm:
            return "VEN"
        if "inventario" in area_name_norm or "almacen" in area_name_norm:
            return "INV"
        if "compras" in area_name_norm:
            return "CMP"
            
        for k, v in self.areas_mapping.items():
            k_norm = k.lower().strip()
            if area_name_norm in k_norm or k_norm in area_name_norm:
                return v
        return None

    def suggest_next_code(self, area_name, doc_type_name):
        """
        Calcula el siguiente código secuencial disponible para un Área y Tipo de Documento.
        Ej: suggest_next_code("Compras", "Procedimiento") -> "SGC-CMP-PR-06"
        """
        area_code = self.get_area_code(area_name)
        type_code = self.types_mapping.get(doc_type_name)
        
        if not area_code or not type_code:
            # Fallback seguro
            area_code = area_code or "XXX"
            type_code = type_code or "XX"
            
        prefix = f"SGC-{area_code}-{type_code}-"
        
        # Buscar en todas las columnas de códigos de la matriz
        existing_numbers = []
        
        if self.matriz_df is not None and not self.matriz_df.empty:
            # Columnas del excel: 'Normas', 'Procedimiento', 'Insructivos' (sic)
            columns_to_search = ['Normas', 'Procedimiento', 'Instructivos', 'Insructivos']
            
            for col in self.matriz_df.columns:
                if col in columns_to_search:
                    for val in self.matriz_df[col].dropna():
                        val_str = str(val).strip()
                        if val_str.startswith(prefix):
                            # Extraer la numeración
                            match = re.search(r'-(\d+)$', val_str)
                            if match:
                                existing_numbers.append(int(match.group(1)))
                            else:
                                # A veces termina con texto (ej. SGC-CMP-PR-01 V1.0)
                                match_mid = re.search(rf'{prefix}(\d+)', val_str)
                                if match_mid:
                                    existing_numbers.append(int(match_mid.group(1)))

        next_number = max(existing_numbers) + 1 if existing_numbers else 1
        return f"{prefix}{next_number:02d}"

    def save_new_document(self, area_name, parent_proc, child_proc, flow_link, code, doc_type_name, doc_link=None, related_code=None):
        """
        Guarda el nuevo documento agregando una fila en la hoja de Google Sheets y en las matrices específicas.
        Si no hay conexión por OAuth, lo guarda en un CSV local.
        """
        # Formatear como hipervínculo si el link de Drive está disponible
        val_doc = f'=HYPERLINK("{doc_link}", "{code}")' if doc_link else code
        val_flow = f'=HYPERLINK("{flow_link}", "{child_proc}")' if flow_link and flow_link.startswith("http") else flow_link
        
        col_normas = val_doc if doc_type_name == "Norma" else ""
        col_proc = val_doc if doc_type_name == "Procedimiento" else ""
        col_inst = val_doc if doc_type_name == "Instrucción de Trabajo" else ""
        
        row_data = [
            area_name,
            parent_proc,
            child_proc,
            val_flow,
            col_normas,
            col_proc,
            col_inst,
            "Generado automáticamente por el Agente BPM"
        ]

        google_sheets_success = False
        try:
            # 1. Intento de guardado en la hoja principal de la API de Google Sheets
            sheets_service = google_client.get_sheets_service()
            body = {
                'values': [row_data]
            }
            sheets_service.spreadsheets().values().append(
                spreadsheetId=config.SPREADSHEET_ID,
                range=f"'{self.title_matriz}'!A1:H",
                valueInputOption="USER_ENTERED",
                body=body
            ).execute()
            config.logger.info("Fila agregada correctamente a la hoja principal de Google Sheets.")
            google_sheets_success = True
        except Exception as e:
            config.logger.warning(f"No se pudo guardar en la hoja principal de Google Sheets ({e}).")

        # 2. Intento de guardado en las hojas de matriz correspondientes
        if doc_type_name in ["Procedimiento", "Flujo de Trabajo", "Norma"]:
            try:
                self._upsert_matrix_document(
                    area_name=area_name,
                    parent_proc=parent_proc,
                    child_proc=child_proc,
                    flow_link=flow_link,
                    code=code,
                    doc_type_name=doc_type_name,
                    doc_link=doc_link,
                    related_code=related_code
                )
            except Exception as e_matrix:
                config.logger.warning(f"No se pudo guardar en la matriz de Google Sheets ({e_matrix}). Se usará guardado local.")
                google_sheets_success = False

        if google_sheets_success:
            # Recargar datos si todo fue exitoso en Sheets
            self.load_data()
            return True
        else:
            # Guardado local de respaldo
            config.logger.warning("Usando respaldos locales debido a fallas de Google API.")
            
            # Guardar en local salidas/nuevos_documentos.csv
            local_file = os.path.join(config.OUTPUTS_DIR, "nuevos_documentos.csv")
            new_row_df = pd.DataFrame([row_data], columns=[
                'Area', 'Procedimiento Padre', 'Procedimientos Hijos / Sub Procedimientos',
                'Link de los flujos', 'Normas', 'Procedimiento', 'Instructivos', 'Observación'
            ])
            
            try:
                if os.path.exists(local_file):
                    new_row_df.to_csv(local_file, mode='a', header=False, index=False)
                else:
                    new_row_df.to_csv(local_file, mode='w', header=True, index=False)
                config.logger.info(f"Registro guardado localmente en {local_file}")
            except Exception as e_local:
                config.logger.error(f"Error al guardar nuevos_documentos.csv localmente: {e_local}")

            # Guardar en las matrices locales correspondientes
            if doc_type_name in ["Procedimiento", "Flujo de Trabajo", "Norma"]:
                try:
                    self._upsert_local_matrix_document(
                        area_name=area_name,
                        parent_proc=parent_proc,
                        child_proc=child_proc,
                        flow_link=flow_link,
                        code=code,
                        doc_type_name=doc_type_name,
                        doc_link=doc_link,
                        related_code=related_code
                    )
                except Exception as e_local_matrix:
                    config.logger.error(f"Error al guardar matriz local: {e_local_matrix}")
                    
            return False

    def _upsert_matrix_document(self, area_name, parent_proc, child_proc, flow_link, code, doc_type_name, doc_link=None, related_code=None):
        """
        Inserta o sobrescribe un proceso/flujo o norma en sus respectivas hojas de matriz final.
        Si la hoja/rango no está disponible, lanza una excepción para que el llamador lo maneje.
        """
        sheets_service = google_client.get_sheets_service()
        spreadsheet_id = config.SPREADSHEET_ID

        if doc_type_name == "Norma":
            sheet_name = "Matriz final_Normas"
            # Formato de fila: ['Area', 'Norma', 'Link documento', 'Codigo Norma', 'Observación']
            val_doc_link = f'=HYPERLINK("{doc_link}", "Ver norma")' if doc_link else ""
            observacion = "Generado automáticamente por el Agente BPM"
            
            # Obtener datos existentes para ver si el código ya existe
            res = sheets_service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range=f"'{sheet_name}'!A1:E500"
            ).execute()
            rows = res.get('values', [])
            
            match_row_idx = -1
            if rows:
                for idx, row in enumerate(rows):
                    if len(row) > 3 and row[3] == code:
                        match_row_idx = idx
                        break
            
            new_row = [
                area_name,
                child_proc,
                val_doc_link,
                code,
                observacion
            ]
            
            if match_row_idx != -1:
                # Sobrescribir
                # Mantener campos existentes si los nuevos vienen vacíos (merge)
                existing_row = rows[match_row_idx]
                while len(existing_row) < 5:
                    existing_row.append("")
                
                merged_row = [
                    new_row[0] if new_row[0] else existing_row[0],
                    new_row[1] if new_row[1] else existing_row[1],
                    new_row[2] if new_row[2] else existing_row[2],
                    new_row[3] if new_row[3] else existing_row[3],
                    new_row[4] if new_row[4] else existing_row[4]
                ]
                
                range_to_update = f"'{sheet_name}'!A{match_row_idx + 1}:E{match_row_idx + 1}"
                sheets_service.spreadsheets().values().update(
                    spreadsheetId=spreadsheet_id,
                    range=range_to_update,
                    valueInputOption="USER_ENTERED",
                    body={'values': [merged_row]}
                ).execute()
                config.logger.info(f"Fila actualizada en {sheet_name} (Renglon {match_row_idx + 1})")
            else:
                # Agregar
                sheets_service.spreadsheets().values().append(
                    spreadsheetId=spreadsheet_id,
                    range=f"'{sheet_name}'!A1:E",
                    valueInputOption="USER_ENTERED",
                    body={'values': [new_row]}
                ).execute()
                config.logger.info(f"Fila agregada en {sheet_name}")

        elif doc_type_name in ["Procedimiento", "Flujo de Trabajo"]:
            sheet_name = "Matriz final_Proceso y flujos"
            # Formato de fila: ['Area', 'Flujo', 'Proceso', 'Link flujo', 'Link proceso', 'Codigo Proceso', 'Codigo flujo', 'Observación']
            val_flow_link = f'=HYPERLINK("{flow_link}", "Ver flujo")' if flow_link else ""
            val_doc_link = f'=HYPERLINK("{doc_link}", "Ver proceso")' if doc_link else ""
            observacion = "Generado automáticamente por el Agente BPM"
            
            code_proceso = code if doc_type_name == "Procedimiento" else (related_code if related_code else code.replace("-FT-", "-PR-"))
            code_flujo = code if doc_type_name == "Flujo de Trabajo" else (related_code if related_code else code.replace("-PR-", "-FT-"))

            # Obtener datos existentes
            res = sheets_service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range=f"'{sheet_name}'!A1:H1000"
            ).execute()
            rows = res.get('values', [])
            
            match_row_idx = -1
            if rows:
                for idx, row in enumerate(rows):
                    # Buscamos coincidencia en Codigo Proceso (index 5) o Codigo flujo (index 6)
                    # Si cualquiera de los dos coincide, consideramos que es el mismo registro relacionado
                    has_proc_match = len(row) > 5 and code_proceso and row[5] == code_proceso
                    has_flow_match = len(row) > 6 and code_flujo and row[6] == code_flujo
                    if has_proc_match or has_flow_match:
                        match_row_idx = idx
                        break
            
            new_row = [
                area_name,
                parent_proc,
                child_proc,
                val_flow_link,
                val_doc_link,
                code_proceso,
                code_flujo,
                observacion
            ]
            
            if match_row_idx != -1:
                # Sobrescribir y combinar
                existing_row = rows[match_row_idx]
                while len(existing_row) < 8:
                    existing_row.append("")
                
                merged_row = [
                    new_row[0] if new_row[0] else existing_row[0],
                    new_row[1] if new_row[1] else existing_row[1],
                    new_row[2] if new_row[2] else existing_row[2],
                    new_row[3] if new_row[3] else existing_row[3],
                    new_row[4] if new_row[4] else existing_row[4],
                    new_row[5] if new_row[5] else existing_row[5],
                    new_row[6] if new_row[6] else existing_row[6],
                    new_row[7] if new_row[7] else existing_row[7]
                ]
                
                range_to_update = f"'{sheet_name}'!A{match_row_idx + 1}:H{match_row_idx + 1}"
                sheets_service.spreadsheets().values().update(
                    spreadsheetId=spreadsheet_id,
                    range=range_to_update,
                    valueInputOption="USER_ENTERED",
                    body={'values': [merged_row]}
                ).execute()
                config.logger.info(f"Fila actualizada en {sheet_name} (Renglon {match_row_idx + 1})")
            else:
                # Agregar
                sheets_service.spreadsheets().values().append(
                    spreadsheetId=spreadsheet_id,
                    range=f"'{sheet_name}'!A1:H",
                    valueInputOption="USER_ENTERED",
                    body={'values': [new_row]}
                ).execute()
                config.logger.info(f"Fila agregada en {sheet_name}")

    def _upsert_local_matrix_document(self, area_name, parent_proc, child_proc, flow_link, code, doc_type_name, doc_link=None, related_code=None):
        """
        Guarda o sobrescribe localmente en CSV en caso de que no haya conexión con la API de Sheets.
        """
        os.makedirs(config.OUTPUTS_DIR, exist_ok=True)
        observacion = "Generado automáticamente por el Agente BPM (Local)"

        if doc_type_name == "Norma":
            local_file = os.path.join(config.OUTPUTS_DIR, "matriz_normas.csv")
            headers = ['Area', 'Norma', 'Link documento', 'Codigo Norma', 'Observación']
            
            link_doc = doc_link or ""
            new_row = {
                'Area': area_name,
                'Norma': child_proc,
                'Link documento': link_doc,
                'Codigo Norma': code,
                'Observación': observacion
            }
            
            if os.path.exists(local_file):
                try:
                    df = pd.read_csv(local_file)
                except Exception:
                    df = pd.DataFrame(columns=headers)
            else:
                df = pd.DataFrame(columns=headers)
                
            # Buscar coincidencia
            match_mask = df['Codigo Norma'] == code
            if match_mask.any():
                # Sobrescribir - combinar
                idx = df[match_mask].index[0]
                for col in headers:
                    val = new_row[col]
                    if val:
                        df.at[idx, col] = val
            else:
                # Agregar
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                
            df.to_csv(local_file, index=False)
            config.logger.info(f"Registro de norma guardado localmente en {local_file}")

        elif doc_type_name in ["Procedimiento", "Flujo de Trabajo"]:
            local_file = os.path.join(config.OUTPUTS_DIR, "matriz_proceso_y_flujos.csv")
            headers = ['Area', 'Flujo', 'Proceso', 'Link flujo', 'Link proceso', 'Codigo Proceso', 'Codigo flujo', 'Observación']
            
            code_proceso = code if doc_type_name == "Procedimiento" else (related_code if related_code else code.replace("-FT-", "-PR-"))
            code_flujo = code if doc_type_name == "Flujo de Trabajo" else (related_code if related_code else code.replace("-PR-", "-FT-"))
            
            new_row = {
                'Area': area_name,
                'Flujo': parent_proc,
                'Proceso': child_proc,
                'Link flujo': flow_link or "",
                'Link proceso': doc_link or "",
                'Codigo Proceso': code_proceso,
                'Codigo flujo': code_flujo,
                'Observación': observacion
            }
            
            if os.path.exists(local_file):
                try:
                    df = pd.read_csv(local_file)
                except Exception:
                    df = pd.DataFrame(columns=headers)
            else:
                df = pd.DataFrame(columns=headers)
                
            # Buscar coincidencia por cualquiera de los dos códigos
            match_mask = (df['Codigo Proceso'] == code_proceso) | (df['Codigo flujo'] == code_flujo)
            
            if match_mask.any():
                idx = df[match_mask].index[0]
                for col in headers:
                    val = new_row[col]
                    if val:
                        df.at[idx, col] = val
            else:
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                
            df.to_csv(local_file, index=False)
            config.logger.info(f"Registro de proceso/flujo guardado localmente en {local_file}")
