import sys
import os
# Adiciona o diretório raiz do projeto ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import pyodbc
from config.settings import settings

class Database:
    def __init__(self, db_name: str):
        self.conn_str = (
            f"DRIVER={{{settings.DB_DRIVER}}};"
            f"SERVER={settings.DB_HOST};"
            f"DATABASE={db_name};"
            f"UID={settings.DB_USER};"
            f"PWD={settings.DB_PASSWORD}"
        )

    def connect(self):
        return pyodbc.connect(self.conn_str)
