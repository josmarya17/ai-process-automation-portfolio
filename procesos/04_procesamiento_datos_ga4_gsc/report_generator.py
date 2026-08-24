import os
import pandas as pd
import time
import sys
import io
from PIL import Image

# Robust loading for both SDK versions
try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None

try:
    import google.generativeai as legacy_genai
except ImportError:
    legacy_genai = None

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import config

class GeminiClient:
    def __init__(self, api_keys):
        self.api_keys = api_keys if isinstance(api_keys, list) else [api_keys]
        self.current_key_index = 0
        self.model_id = 'gemini-3.5-flash'
        self._init_client()

    def _init_client(self):
        key = self.api_keys[self.current_key_index]
        print(f"Initializing Gemini Engine with Key #{self.current_key_index + 1}...")
        
        # Prioritize Legacy SDK for stability
        if legacy_genai:
            try:
                self.client_type = 'LEGACY'
                legacy_genai.configure(api_key=key)
                self.gemini_engine = legacy_genai.GenerativeModel(self.model_id)
            except Exception as e:
                print(f"Legacy SDK failed to init: {e}")
                self.client_type = 'NONE'
        # Fallback to New SDK
        elif genai:
            try:
                self.client_type = 'NEW'
                self.gemini_engine = genai.Client(api_key=key)
            except Exception as e:
                print(f"New SDK failed to init: {e}")
                self.client_type = 'NONE'
        else:
            raise ImportError("Ningún SDK de Gemini encontrado.")


    def rotate_key(self):
        if len(self.api_keys) > 1:
            self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
            self._init_client()

    def generate_report(self, prompt_text, image_path=None):
        for _ in range(len(self.api_keys)):
            try:
                contents = [prompt_text]
                if image_path:
                    ext = image_path.lower()
                    if ext.endswith(('.png', '.jpg', '.jpeg', '.webp')):
                        with Image.open(image_path) as img:
                            img_byte_arr = io.BytesIO()
                            img.save(img_byte_arr, format=img.format if img.format else 'PNG')
                            if self.client_type == 'NEW':
                                part = types.Part.from_bytes(data=img_byte_arr.getvalue(), mime_type=f'image/{img.format.lower() if img.format else "png"}')
                                contents.append(part)
                            else:
                                contents.append(img)
                    elif ext.endswith('.pdf'):
                        with open(image_path, "rb") as f:
                            pdf_data = f.read()
                            if self.client_type == 'NEW':
                                # Fix: Ensure model path is correct for generate_content
                                part = types.Part.from_bytes(data=pdf_data, mime_type='application/pdf')
                                contents.append(part)
                            else:
                                contents.append({"mime_type": "application/pdf", "data": pdf_data})

                if self.client_type == 'NEW':
                    # Use models/ prefix if needed, but the Client should handle it. 
                    # Trying gemini-1.5-flash directly.
                    response = self.gemini_engine.models.generate_content(model=self.model_id, contents=contents)
                    return response.text
                else:
                    response = self.gemini_engine.generate_content(contents)
                    return response.text

            except Exception as e:
                print(f"Error calling Gemini ({self.client_type} Key #{self.current_key_index+1}): {e}", file=sys.stderr)
                if "404" in str(e) or "429" in str(e):
                    # If 404, maybe the model name is wrong for this key? 
                    # Let's try to fallback to models/gemini-1.5-flash
                    if "404" in str(e) and self.model_id == 'gemini-1.5-flash':
                        self.model_id = 'gemini-1.5-flash' # Usually correct, but maybe it needs specific version
                    
                    self.rotate_key()
                else:
                    return f"Error: {e}"
        return "Error: Failed after trying all keys."


class SheetsManager:
    def __init__(self, credentials):
        self.service = build('sheets', 'v4', credentials=credentials)

    def get_sheet_titles(self, sheet_id):
        sheet_metadata = self.service.spreadsheets().get(spreadsheetId=sheet_id).execute()
        sheets = sheet_metadata.get('sheets', '')
        return [sheet.get('properties', {}).get('title') for sheet in sheets]

    def read_sheet(self, sheet_id, tab_name):
        range_name = f"{tab_name}!A:Z"
        result = self.service.spreadsheets().values().get(spreadsheetId=sheet_id, range=range_name).execute()
        values = result.get('values', [])
        if not values: return pd.DataFrame()
        return pd.DataFrame(values[1:], columns=values[0])

    def read_config_sheet(self, sheet_id, tab_name):
        # Alias for backward compatibility with main.py
        return self.read_sheet(sheet_id, tab_name)

    def append_history(self, sheet_id, tab_name, row_data, headers=None):
        # Verifica si hay encabezados para asegurar la estructura
        range_name_check = f"{tab_name}!A1:Z1"
        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=sheet_id, range=range_name_check).execute()
            existing_values = result.get('values', [])
            
            requests_body = {'values': []}
            if not existing_values and headers:
                requests_body['values'].append(headers)
            
            requests_body['values'].append(row_data)
            
            range_name_append = f"{tab_name}!A:AA"
            self.service.spreadsheets().values().append(
                spreadsheetId=sheet_id, range=range_name_append,
                valueInputOption='USER_ENTERED', body=requests_body).execute()
            return True
        except Exception as e:
            print(f"Error in append_history: {e}")
            return False

class DocsManager:
    def __init__(self, credentials):
        self.service = build('docs', 'v1', credentials=credentials)

    def append_report(self, doc_id_or_url, text, heading=None):
        doc_id = doc_id_or_url
        if 'docs.google.com/document/d/' in doc_id_or_url:
            doc_id = doc_id_or_url.split('/d/')[1].split('/')[0]
            
        requests = []
        if heading:
            requests.append({
                'insertText': {
                    'location': {'index': 1},
                    'text': f"\n{heading}\n"
                }
            })
            requests.append({
                'updateParagraphStyle': {
                    'range': {'startIndex': 1, 'endIndex': len(heading) + 2},
                    'paragraphStyle': {'namedStyleType': 'HEADING_2'},
                    'fields': 'namedStyleType'
                }
            })
            
        requests.append({
            'insertText': {
                'location': {'index': 1 if not heading else len(heading) + 3},
                'text': f"\n{text}\n"
            }
        })
        
        try:
            self.service.documents().batchUpdate(documentId=doc_id, body={'requests': requests}).execute()
            return True
        except Exception as e:
            print(f"Error appending to doc: {e}")
            return False
