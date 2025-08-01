# repositories/produto_repository.py
import sys
import os
# Adiciona o diretório raiz do projeto ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import re
from typing import Optional
import pyodbc
from models.produto import Produto
from utils.logger import logger

class ProdutoRepository:
    def __init__(self, conn: pyodbc.Connection):
        self.conn = conn

    def buscar_produto(self, ean13: str, dun14: str, codprod: str) -> Optional[Produto]:
        cursor = self.conn.cursor()

        # 1ª tentativa: EAN13
        query_ean = "SELECT * FROM SB1010 WHERE B1_CODBAR = ?"
        logger.sql(query_ean, ean13)
        row = cursor.execute(query_ean, ean13).fetchone()
        if row:
            return self._mapear(row)

        # 2ª tentativa: DUN14
        query_dun = "SELECT * FROM SB1010 WHERE B1_ZZCODBA = ?"
        logger.sql(query_dun, dun14)
        row = cursor.execute(query_dun, dun14).fetchone()
        if row:
            return self._mapear(row)

        # 3ª tentativa: CODPROD (sem sufixo)
        cod_sem_sufixo = re.sub(r"\.\w+$", "", codprod)
        query_cod = "SELECT * FROM SB1010 WHERE B1_COD LIKE ?"
        logger.sql(query_cod, f"{cod_sem_sufixo}.%")
        row = cursor.execute(query_cod, f"{cod_sem_sufixo}.%").fetchone()
        if row:
            return self._mapear(row)

        return None

    def _mapear(self, row) -> Produto:
        return Produto(
            codigo=row.CODIGO.strip(),
            descricao=row.DESCRICAO.strip(),
            ean13=row.EAN13.strip(),
            dun14=row.DUN14.strip(),
            peso_bruto=row.PESOBRUTO,
            peso_liquido=row.PESOLIQUIDO,
            qtde_embalagem=row.QTDEEMBALAGEM,
            unidade=row.UNIDPRODUTO.strip(),
            perc_acresc_max=row.PERCACRESCMAX,
            flag_uso=row.FLAGUSO,
            flag_verba=row.CESP_FLAGVERBA
        )
