import sys
import os
# Adiciona o diretório raiz do projeto ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from typing import Any, Dict
from models.pedido_sobel import PedidoSobel
from services.processador_pedido_item import ProcessadorPedidoItem
from services.validador_cliente import ValidadorCliente


class ProcessadorPedido:
    def __init__(self, validador_cliente: ValidadorCliente, processador_item: ProcessadorPedidoItem):
        self.validador_cliente = validador_cliente
        self.processador_item = processador_item

    def processar(self, pedido_json: Dict[str, Any]) -> PedidoSobel:
        """
        Processa um pedido completo a partir do JSON recebido da API Neogrid.
        Valida o cliente e os itens, retornando um objeto PedidoSobel pronto para ser gravado.
        """
        cnpj = pedido_json.get("cnpj", "")
        cliente = self.validador_cliente.validar_cliente(cnpj)

        if not cliente:
            raise ValueError(f"Cliente com CNPJ {cnpj} não encontrado.")

        itens_json = pedido_json.get("itens", [])
        itens_processados = []

        for item in itens_json:
            try:
                item_processado = self.processador_item.processar_item(item)
                itens_processados.append(item_processado)
            except ValueError as e:
                raise ValueError(f"Erro ao processar item {item}: {e}")

        return PedidoSobel.from_json(pedido_json, cliente, itens_processados)
