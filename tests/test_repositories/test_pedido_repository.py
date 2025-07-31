import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from unittest.mock import MagicMock
from repositories.pedido_repository import PedidoRepository
from models.pedido_sobel import PedidoSobel
from models.pedido_item_sobel import PedidoItemSobel


def test_inserir_itens_pedido_executes_queries():
    repo = PedidoRepository.__new__(PedidoRepository)
    repo.cursor = MagicMock()
    repo._execute_with_logging = MagicMock()
    # Bind helper methods
    repo._tratar_data = PedidoRepository._tratar_data.__get__(repo)
    repo._tratar_valor_decimal = PedidoRepository._tratar_valor_decimal.__get__(repo)

    item = PedidoItemSobel(
        cod_produto="1001",
        descricao_produto="Produto",
        quantidade=2,
        valor_unitario=10.0,
        valor_total=20.0,
        unidade="CX"
    )

    pedido = PedidoSobel(
        num_pedido="123",
        data_pedido="2025-05-15",
        hora_inicio="10:00",
        codigo_cliente="C1",
        nome_cliente="Cliente",
        valor_total=20.0,
        qtde_itens=1,
        itens=[item],
    )
    pedido.num_pedido_afv = "123"

    # Simular resultado para _get_next_numitem
    repo.cursor.fetchone.return_value = (0,)

    inserted = repo._inserir_itens_pedido(pedido)
    assert inserted == 1
    # Deve executar uma consulta para obter o próximo NUMITEM e outra para inserir
    assert repo._execute_with_logging.call_count == 2
