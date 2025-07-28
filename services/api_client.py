# services/api_client.py

import sys
import os
# Adiciona o diretório raiz do projeto ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import requests
from requests.auth import HTTPBasicAuth
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from config.settings import settings
from utils.error_handler import APIError
from typing import Dict, Any
import json

class NeogridAPIClient:
    def __init__(self):
        self.url = settings.NEOGRID_URL
        self.status_url = settings.NEOGRID_STATUS_URL
        self.auth = HTTPBasicAuth(settings.NEOGRID_USERNAME, settings.NEOGRID_PASSWORD)
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "TOTVS-Neogrid-Importer/2.1.0"
        }
        
        # Configurar sessão com retry automático
        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        """Cria sessão HTTP com retry automático e timeouts"""
        session = requests.Session()
        
        # Configurar retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "POST"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session

    def buscar_pedidos(self, doc_type: str = "5", docs_qty: str = "50") -> Dict[str, Any]:
        """
        Consulta pedidos via API Neogrid com tratamento robusto de erros
        """
        payload = {
            "docType": doc_type,
            "docsQty": docs_qty
        }

        try:
            print(f"🔍 Consultando API Neogrid - URL: {self.url}")
            print(f"📋 Parâmetros: docType={doc_type}, docsQty={docs_qty}")
            
            response = self.session.post(
                self.url,
                auth=self.auth,
                headers=self.headers,
                json=payload,
                timeout=(30, 60)  # (connection_timeout, read_timeout)
            )
            
            print(f"📡 Response Status: {response.status_code}")
            
            # Verificar status HTTP
            if response.status_code == 401:
                raise APIError(
                    "Credenciais inválidas ou expiradas",
                    response.status_code,
                    response.text[:500] if response.text else None
                )
            elif response.status_code == 403:
                raise APIError(
                    "Acesso negado - verifique permissões",
                    response.status_code,
                    response.text[:500] if response.text else None
                )
            elif response.status_code == 404:
                raise APIError(
                    "Endpoint não encontrado - verifique URL",
                    response.status_code,
                    response.text[:500] if response.text else None
                )
            elif response.status_code >= 400:
                raise APIError(
                    f"Erro HTTP {response.status_code}",
                    response.status_code,
                    response.text[:500] if response.text else None
                )
            
            # Tentar fazer parse do JSON
            try:
                json_response = response.json()
            except json.JSONDecodeError as e:
                raise APIError(
                    f"Resposta não é um JSON válido: {str(e)}",
                    response.status_code,
                    response.text[:500] if response.text else None
                )
            
            # Validar estrutura da resposta
            if not isinstance(json_response, dict):
                raise APIError(
                    "Resposta da API não é um objeto JSON válido",
                    response.status_code,
                    str(json_response)[:500]
                )
            
            # Log de sucesso
            documents_count = len(json_response.get("documents", []))
            print(f"✅ API respondeu com sucesso: {documents_count} documento(s) encontrado(s)")
            
            return json_response
            
        except requests.exceptions.Timeout:
            raise APIError("Timeout na requisição - API não respondeu no tempo esperado")
        except requests.exceptions.ConnectionError:
            raise APIError("Erro de conexão - não foi possível conectar à API")
        except requests.exceptions.RequestException as e:
            raise APIError(f"Erro na requisição HTTP: {str(e)}")
        except APIError:
            # Re-raise custom API errors
            raise
        except Exception as e:
            raise APIError(f"Erro inesperado ao consultar API: {str(e)}")

    def atualizar_status(self, documents: list) -> Dict[str, Any]:
        """Envia atualização de status para a Neogrid."""
        payload = {"documents": documents}

        try:
            response = self.session.post(
                self.status_url,
                auth=self.auth,
                headers=self.headers,
                json=payload,
                timeout=(30, 60),
            )

            if response.status_code >= 400:
                raise APIError(
                    f"Erro HTTP {response.status_code}",
                    response.status_code,
                    response.text[:500] if response.text else None,
                )

            try:
                return response.json()
            except json.JSONDecodeError:
                return {"status_code": response.status_code}

        except requests.exceptions.Timeout:
            raise APIError("Timeout na requisição - API não respondeu no tempo esperado")
        except requests.exceptions.ConnectionError:
            raise APIError("Erro de conexão - não foi possível conectar à API")
        except requests.exceptions.RequestException as e:
            raise APIError(f"Erro na requisição HTTP: {str(e)}")

    def test_connection(self) -> bool:
        """
        Testa a conectividade com a API Neogrid
        """
        try:
            # Fazer uma requisição simples para testar conectividade
            response = self.session.post(
                self.url,
                auth=self.auth,
                headers=self.headers,
                json={"docType": "5", "docsQty": "1"},
                timeout=(10, 30)
            )
            return response.status_code < 500
        except:
            return False

    def get_connection_info(self) -> Dict[str, str]:
        """
        Retorna informações de conexão (sem credenciais sensíveis)
        """
        return {
            "url": self.url,
            "username": self.auth.username[:10] + "..." if self.auth.username else "N/A",
            "headers": {k: v for k, v in self.headers.items() if k != "Authorization"}
        }