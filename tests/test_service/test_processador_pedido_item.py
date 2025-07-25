# tests/test_processador_pedido_item.py
import sys
import os
# Adiciona o diretório raiz do projeto ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from models.produto import Produto
from services.processador_pedido_item import ProcessadorPedidoItem


def test_processamento_com_produto_valido():
    class FakeValidador:
        def validar_produto(self, ean13, dun14, codprod):
            return Produto(
                codigo="123",
                descricao="Produto Teste",
                ean13=ean13,
                dun14=dun14,
                peso_bruto=2,
                peso_liquido=2,
                qtde_embalagem=1,
                unidade="CX",
                perc_acresc_max=10,
                flag_uso=1,
                flag_verba=0
            )

    processor = ProcessadorPedidoItem(FakeValidador())

    item = {
        "ean13": "7896524726150",
        "dun14": "",
        "codprod": "1001.01.03X05L",
        "qtd": 10,
        "valor": 25.0
    }

    resultado = processor.processar_item(item)

    assert resultado.cod_produto == "123"
    assert resultado.descricao_produto == "Produto Teste"
    assert resultado.quantidade == 10
    assert resultado.valor_unitario == 25.0
    assert resultado.valor_total == 250.0
    assert resultado.unidade == "CX"
    assert resultado.ean13 == "7896524726150"

