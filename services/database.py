import sys
import os
# Adiciona o diretório raiz do projeto ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import pyodbc
from config.settings import settings
from utils.logger import logger
import time
from typing import Optional

class Database:
    def __init__(self, db_name: str):
        self.conn_str = (
            f"DRIVER={{{settings.DB_DRIVER}}};"
            f"SERVER={settings.DB_HOST};"
            f"DATABASE={db_name};"
            f"UID={settings.DB_USER};"
            f"PWD={settings.DB_PASSWORD};"
            f"TrustServerCertificate=yes;"
            f"Connection Timeout=30;"
            f"Command Timeout=30;"
        )
        self._connection: Optional[pyodbc.Connection] = None

    def connect(self, retry_count: int = 3) -> pyodbc.Connection:
        """
        Conecta ao banco com retry automático em caso de falha
        """
        for attempt in range(retry_count):
            try:
                if self._connection is None or self._is_connection_closed():
                    self._connection = pyodbc.connect(
                        self.conn_str,
                        autocommit=True,
                        timeout=30
                    )
                    
                    # Configurações de otimização
                    self._connection.setdecoding(pyodbc.SQL_CHAR, encoding='utf-8')
                    self._connection.setdecoding(pyodbc.SQL_WCHAR, encoding='utf-8')
                    self._connection.setencoding(encoding='utf-8')
                
                return self._connection
                
            except Exception as e:
                print(f"Tentativa {attempt + 1} de conexão falhou: {e}")
                if attempt < retry_count - 1:
                    time.sleep(2 ** attempt)  # Backoff exponencial
                else:
                    raise RuntimeError(f"Falha ao conectar após {retry_count} tentativas: {e}")

    def _is_connection_closed(self) -> bool:
        """Verifica se a conexão está fechada"""
        if self._connection is None:
            return True
        
        try:
            # Tenta executar uma query simples para verificar se a conexão está ativa
            cursor = self._connection.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            return False
        except:
            return True

    def execute_query(self, query: str, params=None, fetch_one=False, fetch_all=False):
        """
        Executa uma query com tratamento de erro robusto
        """
        conn = None
        cursor = None
        try:
            conn = self.connect()
            cursor = conn.cursor()

            logger.sql(query, params)

            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            if fetch_one:
                return cursor.fetchone()
            elif fetch_all:
                return cursor.fetchall()
            else:
                return cursor
                
        except Exception as e:
            logger.error(f"Erro ao executar query: {e}")
            logger.error(f"Query: {query}")
            if params:
                logger.error(f"Params: {params}")
            raise
        finally:
            if cursor:
                cursor.close()

    def test_connection(self) -> bool:
        """
        Testa a conectividade com o banco
        """
        try:
            conn = self.connect()
            cursor = conn.cursor()
            cursor.execute("SELECT 1 as test")
            result = cursor.fetchone()
            cursor.close()
            return result is not None
        except Exception as e:
            print(f"Erro no teste de conexão: {e}")
            return False

    def close(self):
        """Fecha a conexão"""
        if self._connection and not self._is_connection_closed():
            try:
                self._connection.close()
            except:
                pass
            finally:
                self._connection = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()