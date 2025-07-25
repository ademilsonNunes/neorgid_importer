# models/pedido.py
import sys
import os
# Adiciona o diretório raiz do projeto ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from typing import List
from datetime import datetime
from decimal import Decimal

class ItemPedido:
    def __init__(self, item_data: dict):
        self.codigo_produto = item_data.get("codigoProduto").strip()
        self.descricao_produto = item_data.get("descricaoProduto").strip()
        self.quantidade = Decimal(item_data.get("quantidadePedida").replace(".", "").lstrip("0") or "0")
        self.preco_unitario = Decimal(item_data.get("precoLiquidoUnitario").replace(".", "").lstrip("0") or "0") / 100
        self.valor_total = Decimal(item_data.get("valorLiquidoItem").replace(".", "").lstrip("0") or "0") / 100
        self.aliquota_ipi = Decimal(item_data.get("aliquotaIPI").strip() or "0")
        self.valor_ipi = Decimal(item_data.get("valorUnitarioIPI").replace(".", "").lstrip("0") or "0") / 100
        self.referencia_produto = item_data.get("referenciaProduto").strip()
        self.unidade = item_data.get("unidadeMedida").strip()

    def __repr__(self):
        return f"<ItemPedido {self.codigo_produto} - {self.quantidade} x {self.preco_unitario}>"


class Pedido:
    def __init__(self, raw_data: dict):
        cabecalho = raw_data["order"]["cabecalho"]
        pagamento = raw_data["order"]["pagamento"]
        sumario = raw_data["order"]["sumario"]
        itens = raw_data["order"]["itens"]["item"]

        self.numero_pedido = cabecalho["numeroPedidoComprador"]
        self.cnpj_destino = cabecalho["cnpjComprador"]
        self.cnpj_fornecedor = cabecalho["cnpjFornecedor"]
        self.data_emissao = self._formatar_data(cabecalho["dataHoraEmissao"])
        self.data_entrega = self._formatar_data(cabecalho["dataHoraInicialEntrega"])
        self.condicao_entrega = cabecalho["condicaoEntrega"]
        self.valor_total = Decimal(sumario["valorTotalPedido"].replace(".", "").lstrip("0") or "0") / 100
        self.valor_ipi_total = Decimal(sumario["valorTotalIPI"].replace(".", "").lstrip("0") or "0") / 100

        self.condicao_pagamento = pagamento["condicaoPagamento"]
        self.data_vencimento = self._formatar_data(pagamento["dataVencimento"])

        self.itens: List[ItemPedido] = [ItemPedido(i) for i in itens]

    def _formatar_data(self, data_str: str) -> datetime:
        try:
            return datetime.strptime(data_str[:8], "%d%m%Y")
        except Exception:
            return None

    def __repr__(self):
        return f"<Pedido {self.numero_pedido} - {len(self.itens)} itens - R$ {self.valor_total:.2f}>"
