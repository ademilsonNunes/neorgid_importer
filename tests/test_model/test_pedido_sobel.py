# tests/test_models/test_pedido_sobel.py
from models.pedido_sobel import PedidoSobel
from models.pedido_item_sobel import PedidoItemSobel
from models.cliente import Cliente


def test_criacao_pedido_sobel_completo():
    cliente = Cliente(
        codigo="276134",
        nome="LOJA265-CARRETA",
        cnpj="12345678000199"
    )

    itens = [
        PedidoItemSobel(
            cod_produto="1001",
            descricao_produto="Água Sanitária Suprema",
            quantidade=10,
            valor_unitario=25.00,
            valor_total=250.00,
            unidade="CX",
            ean13="7896524726150"
        ),
        PedidoItemSobel(
            cod_produto="1002",
            descricao_produto="Desinfetante Suprema",
            quantidade=5,
            valor_unitario=30.00,
            valor_total=150.00,
            unidade="CX",
            ean13="7896524726151"
        )
    ]

    pedido_json = {
        "num_pedido": "W512407251801490",
        "data_pedido": "2025-07-24",
        "hora_inicio": "18:01",
        "hora_fim": "18:08",
        "data_entrega": "2025-07-31",
        "loja_cliente": "1",
        "observacao": "Entrega via carreta"
    }

    pedido = PedidoSobel.from_json(pedido_json, cliente, itens)

    assert pedido.num_pedido == "W512407251801490"
    assert pedido.data_pedido == "2025-07-24"
    assert pedido.hora_inicio == "18:01"
    assert pedido.data_entrega == "2025-07-31"
    assert pedido.codigo_cliente == "276134"
    assert pedido.nome_cliente == "LOJA265-CARRETA"
    assert pedido.qtde_itens == 2
    assert pedido.valor_total == 400.00
    assert pedido.itens[0].descricao_produto == "Água Sanitária Suprema"
