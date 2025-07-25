import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from services.processador_pedido import ProcessadorPedido
from models.cliente import Cliente
from models.pedido_item_sobel import PedidoItemSobel


def test_processamento_pedido_completo():
    # Fake validador de cliente
    class FakeValidadorCliente:
        def validar_cliente(self, cnpj):
            return Cliente(
                codigo="276134",
                nome="LOJA265-CARRETA",
                cnpj=cnpj
            )

    # Fake processador de item
    class FakeProcessadorPedidoItem:
        def processar_item(self, item_json):
            return PedidoItemSobel(
                cod_produto="1001",
                descricao_produto="Água Sanitária Suprema",
                quantidade=item_json["qtd"],
                valor_unitario=item_json["valor"],
                valor_total=item_json["qtd"] * item_json["valor"],
                unidade="CX",
                ean13=item_json.get("ean13", "")
            )

    pedido_json = {
        "num_pedido": "W512407251801490",
        "data_pedido": "2025-07-24",
        "hora_inicio": "18:01",
        "hora_fim": "18:08",
        "data_entrega": "2025-07-31",
        "loja_cliente": "1",
        "observacao": "Entrega via carreta",
        "cnpj": "12345678000199",
        "itens": [
            {
                "ean13": "7896524726150",
                "dun14": "",
                "codprod": "1001.01.03X05L",
                "qtd": 10,
                "valor": 25.0
            },
            {
                "ean13": "7896524726151",
                "dun14": "",
                "codprod": "1002.01.03X05L",
                "qtd": 5,
                "valor": 30.0
            }
        ]
    }

    processador = ProcessadorPedido(FakeValidadorCliente(), FakeProcessadorPedidoItem())
    pedido = processador.processar(pedido_json)

    assert pedido.num_pedido == "W512407251801490"
    assert pedido.codigo_cliente == "276134"
    assert pedido.qtde_itens == 2
    assert pedido.valor_total == 10 * 25 + 5 * 30  # 400.0
    assert pedido.itens[0].descricao_produto == "Água Sanitária Suprema"
