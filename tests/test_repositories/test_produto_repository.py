# tests/test_produto_repository.py
import sys
import os
# Adiciona o diretório raiz do projeto ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import pytest
from unittest.mock import MagicMock
from repositories.produto_repository import ProdutoRepository

@pytest.fixture
def mock_conn():
    conn = MagicMock()
    cursor = MagicMock()
    conn.cursor.return_value = cursor
    return conn

def test_busca_por_ean13(mock_conn):
    row_mock = MagicMock()
    row_mock.CODIGO = "1001.01.03X05L .01"
    row_mock.DESCRICAO = "AGUA SANITARIA"
    row_mock.EAN13 = "7896524726150"
    row_mock.DUN14 = "27896524726154"
    row_mock.PESOBRUTO = 16.47
    row_mock.PESOLIQUIDO = 16.12
    row_mock.QTDEEMBALAGEM = 0
    row_mock.UNIDPRODUTO = "CX"
    row_mock.PERCACRESCMAX = 10.0
    row_mock.FLAGUSO = 1
    row_mock.CESP_FLAGVERBA = 0

    mock_conn.cursor.return_value.execute.return_value.fetchone.return_value = row_mock

    repo = ProdutoRepository(mock_conn)
    produto = repo.buscar_produto("7896524726150", "", "")

    assert produto is not None
    assert produto.ean13 == "7896524726150"
    assert produto.descricao == "AGUA SANITARIA"
