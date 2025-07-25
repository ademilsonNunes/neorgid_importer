# services/api_client.py

import sys
import os
# Adiciona o diretório raiz do projeto ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import requests
from requests.auth import HTTPBasicAuth
from config.settings import settings


class NeogridAPIClient:
    def __init__(self):
        self.url = settings.NEOGRID_URL
        self.auth = HTTPBasicAuth(settings.NEOGRID_USERNAME, settings.NEOGRID_PASSWORD)
        self.headers = {
            "Content-Type": "application/json"
        }

    def buscar_pedidos(self, doc_type="5", docs_qty="50"):
        """Consulta pedidos via API Neogrid"""
        payload = {
            "docType": doc_type,
            "docsQty": docs_qty
        }

        try:
            response = requests.post(
                self.url,
                auth=self.auth,
                headers=self.headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise RuntimeError(f"Erro ao buscar pedidos na Neogrid: {e}")
