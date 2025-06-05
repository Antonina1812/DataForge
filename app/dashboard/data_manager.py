import pandas as pd
import base64, io, chardet
from typing import Tuple, Optional


class DataManager:
    def __init__(self):
        self.df: Optional[pd.DataFrame] = None
        self.filename: str = ""

    def load(self, contents: str, filename: str) -> Tuple[dict, str]:
        """Вернёт dict для dcc.Store и html для предпросмотра"""
        self.filename = filename
        self.df = self._parse_contents(contents, filename)
        preview = self._html_preview()
        return self.df.to_dict('records'), preview

    def _parse_contents(self, contents, filename) -> pd.DataFrame:
        header, encoded = contents.split(',')
        decoded = base64.b64decode(encoded)

        enc = chardet.detect(decoded[:10_000])['encoding'] or 'utf-8'

        if filename.endswith('.csv'):
            return pd.read_csv(io.StringIO(decoded.decode(enc)))
        if filename.endswith(('.xls', '.xlsx')):
            return pd.read_excel(io.BytesIO(decoded))
        raise ValueError("Unsupported file type")

    def _html_preview(self) -> str:
        rows, cols = self.df.shape
        return (
            f"<h5>Файл: {self.filename}</h5>"
            f"<p>Размер: {rows} × {cols}</p>"
            f"<pre>{self.df.head().to_string()}</pre>"
        )