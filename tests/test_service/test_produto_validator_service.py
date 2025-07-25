# tests/test_produto_validator_service.py
import sys
import os
# Adiciona o diretório raiz do projeto ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import pytest
from services.produto_validator_service import ProdutoValidatorService
from models.produto import Produto

@pytest.fixture
def mock_repo():
    class FakeRepo:
        def __init__(self):
            self.calls = []

        def buscar_produto(self, ean13, dun14, codprod):
            self.calls.append((ean13, dun14, codprod))
            if ean13 == "VALID_EAN":
                return Produto(
                    codigo="1001.01.03X05L .01",
                    descricao="Produto A",
                    ean13=ean13,
                    dun14=dun14,
                    peso_bruto=1,
                    peso_liquido=1,
                    qtde_embalagem=1,
                    unidade="CX",
                    perc_acresc_max=10,
                    flag_uso=1,
                    flag_verba=0
                )
            return None

    return FakeRepo()

def test_valida_por_ean(mock_repo):
    service = ProdutoValidatorService(mock_repo)
    produto = service.validar_produto("VALID_EAN", "", "")
    assert produto is not None
    assert produto.ean13 == "VALID_EAN"
