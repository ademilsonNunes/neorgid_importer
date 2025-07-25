# tests/test_cliente.py

import sys
import os
# Adiciona o diretório raiz do projeto ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import pytest
from models.cliente import Cliente

@pytest.fixture
def cliente_dict():
    return {
        "CODIGO": "123456",
        "RAZAOSOCIAL": "EMPRESA XYZ LTDA",
        "CGCCPF": "12345678000199",
        "INSCR_ESTADUAL": "123456789",
        "ENDERECO": "Rua das Flores",
        "CODIGONOMECIDADE": "1234",
        "ESTADO": "SP",
        "BAIRRO": "Centro",
        "TELEFONE": "11999999999",
        "FAX": "1133334444",
        "CEP": "01234000",
        "CODIGOSTATUSCLI": "1",
        "NOMEFANTASIA": "EMP XYZ",
        "DATACADASTRO": "2020-01-01",
        "CODIGOENDENTREGA": "7890",
        "CODIGOREGIAO": 10,
        "CODIGOANALCLIENTE": "789",
        "CODIGOTABPRECO": "01",
        "CODIGOCONDPAGTO": "30",
        "CODIGOCLIENTEPAI": "0001",
        "OBSFETCHATURAMENTO": "Nenhuma",
        "EMAILCOPIAPEDIDO": "compras@xyz.com",
        "FLAGENVIACOPIAPEDIDO": "S",
        "CESP_FLAGENTREGAAGENDADA": 1,
        "Cesp_QtdeDiasMinEntrega": "3"
    }

def test_from_dict_cria_cliente_completo(cliente_dict):
    cliente = Cliente.from_dict(cliente_dict)

    assert cliente.codigo == "123456"
    assert cliente.razao_social == "EMPRESA XYZ LTDA"
    assert cliente.cnpj == "12345678000199"
    assert cliente.estado == "SP"
    assert cliente.qtde_dias_min_entrega == "3"
