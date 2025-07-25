import sys
import os
# Adiciona o diretório raiz do projeto ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# services/produto_validator_service.py
from typing import Optional
from repositories.produto_repository import ProdutoRepository
from models.produto import Produto

class ProdutoValidatorService:
    def __init__(self, produto_repo: ProdutoRepository):
        self.produto_repo = produto_repo

    def validar_produto(self, ean13: str, dun14: str, codprod: str) -> Optional[Produto]:
        return self.produto_repo.buscar_produto(ean13, dun14, codprod)
