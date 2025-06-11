import os
import pandas as pd
import base64
import io
from typing import List, Tuple
from werkzeug.utils import safe_join


class DataManager:
    def __init__(self, data_directory: str = "./data"):
        self.data_directory = data_directory
        self.supported_extensions = ['.csv', '.xlsx', '.xls', '.json']
        
        if not os.path.exists(data_directory):
            os.makedirs(data_directory)
    
    def get_available_files(self) -> List[dict]:
        files = []
        try:
            for filename in os.listdir(self.data_directory):
                file_path = os.path.join(self.data_directory, filename)
                if os.path.isfile(file_path):
                    _, ext = os.path.splitext(filename)
                    if ext.lower() in self.supported_extensions:
                        files.append({
                            "label": filename,
                            "value": filename
                        })
        except Exception as e:
            print(f"Error: {e}")
        
        return sorted(files, key=lambda x: x["label"])
    
    def load_from_directory(self, filename: str) -> Tuple[List[dict], str]:
        if not filename:
            raise ValueError("No name for file")
        
        file_path = os.path.join(self.data_directory, filename)
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File {filename} not founded")
        
        try:
            _, ext = os.path.splitext(filename)
            ext = ext.lower()
            
            if ext == '.csv':
                df = pd.read_csv(file_path)
            elif ext in ['.xlsx', '.xls']:
                df = pd.read_excel(file_path)
            elif ext == '.json':
                df = pd.read_json(file_path)
            else:
                raise ValueError(f"Incompatible file type: {ext}")
            
            records = df.to_dict('records')

            preview = self._create_preview(df, filename)
            
            return records, preview
            
        except Exception as e:
            raise Exception(f"Error {filename}: {str(e)}")
    
    def _create_preview(self, df: pd.DataFrame, filename: str) -> str:
        info = f"**Fle:** {filename}\n\n"
        info += f"**Size:** {df.shape[0]} rows, {df.shape[1]} columns\n\n"
        info += f"**Columns:** {', '.join(df.columns)}\n\n"
        info += "**First 5 rows:**\n\n"
        info += df.head().to_markdown(index=False)
        return info
    
    def load(self, contents, filename):
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        
        try:
            if 'csv' in filename:
                df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
            elif 'xls' in filename:
                df = pd.read_excel(io.BytesIO(decoded))
            else:
                raise ValueError("Incompatible file type")
            
            records = df.to_dict('records')
            preview = self._create_preview(df, filename)
            return records, preview
            
        except Exception as e:
            raise Exception(f"Error: {str(e)}")

    def get_file_path(self, filename: str) -> str:
            """Возвращает безопасный путь к файлу для скачивания"""
            if not filename:
                raise ValueError("Filename is required")
            
            safe_path = safe_join(self.data_directory, filename)
            if not os.path.exists(safe_path):
                raise FileNotFoundError(f"File {filename} not found")
            
            _, ext = os.path.splitext(filename)
            if ext.lower() not in self.supported_extensions:
                raise ValueError(f"Unsupported file type: {ext}")
            
            return safe_path