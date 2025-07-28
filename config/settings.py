# config/settings.py
import sys
import os
# Adiciona o diretório raiz do projeto ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from dotenv import load_dotenv
import os

load_dotenv()

class Settings:
    DB_HOST = os.getenv("DB_HOST", "10.0.132.3")
    DB_USER = os.getenv("DB_USER", "sa")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "Totvs@452525!")
    DB_NAME_AFV = os.getenv("DB_NAME_AFV", "AFVServer_SOBEL_PRD")
    DB_NAME_PROTHEUS = os.getenv("DB_NAME_PROTHEUS", "Protheus_Producao")
    DB_DRIVER = os.getenv("DB_DRIVER", "ODBC Driver 17 for SQL Server")

    NEOGRID_USERNAME = os.getenv("NEOGRID_USERNAME", "NG#00000172168716111535")
    NEOGRID_PASSWORD = os.getenv("NEOGRID_PASSWORD", "SObel#24")
    NEOGRID_URL = os.getenv(
        "NEOGRID_URL",
        "https://integration-br-prd.neogrid.com/rest/neogrid/ngproxy/Neogrid/restNew/receiverDocsFromNGProxy",
    )
    NEOGRID_STATUS_URL = os.getenv(
        "NEOGRID_STATUS_URL",
        "https://integration-br-prd.neogrid.com/rest/neogrid/ngproxy/Neogrid/restNew/setStatusToNGProxy",
    )

    @property
    def DB_CONN_STRING_AFV(self):
        """String de conexão para o banco AFV"""
        return (
            f"DRIVER={{{self.DB_DRIVER}}};"
            f"SERVER={self.DB_HOST};"
            f"DATABASE={self.DB_NAME_AFV};"
            f"UID={self.DB_USER};"
            f"PWD={self.DB_PASSWORD};"
            f"TrustServerCertificate=yes;"
        )
    
    @property
    def DB_CONN_STRING_PROTHEUS(self):
        """String de conexão para o banco Protheus"""
        return (
            f"DRIVER={{{self.DB_DRIVER}}};"
            f"SERVER={self.DB_HOST};"
            f"DATABASE={self.DB_NAME_PROTHEUS};"
            f"UID={self.DB_USER};"
            f"PWD={self.DB_PASSWORD};"
            f"TrustServerCertificate=yes;"
        )

    def get_db_connection_string(self, database_name: str) -> str:
        """Retorna string de conexão para um banco específico"""
        return (
            f"DRIVER={{{self.DB_DRIVER}}};"
            f"SERVER={self.DB_HOST};"
            f"DATABASE={database_name};"
            f"UID={self.DB_USER};"
            f"PWD={self.DB_PASSWORD};"
            f"TrustServerCertificate=yes;"
        )

settings = Settings()