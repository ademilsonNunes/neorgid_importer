# models/pedido_sobel.py
import sys
import os
# Adiciona o diretório raiz do projeto ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from typing import List, Optional
from pydantic import BaseModel
from models.pedido_item_sobel import PedidoItemSobel
from models.cliente import Cliente


class PedidoSobel(BaseModel):
    num_pedido: str
    doc_id: Optional[str] = None
    ordem_compra: Optional[str] = None
    data_pedido: str
    hora_inicio: str
    hora_fim: Optional[str]
    data_entrega: Optional[str]
    codigo_cliente: str
    nome_cliente: str
    loja_cliente: Optional[str]
    observacao: Optional[str]
    valor_total: float
    qtde_itens: int
    itens: List[PedidoItemSobel]

    @classmethod
    def from_json(cls, pedido_json: dict, cliente: Cliente, itens: List[PedidoItemSobel]) -> "PedidoSobel":
        return cls(
            num_pedido=pedido_json.get("num_pedido", ""),
            doc_id=pedido_json.get("doc_id"),
            ordem_compra=pedido_json.get("ordem_compra"),
            data_pedido=pedido_json.get("data_pedido", ""),
            hora_inicio=pedido_json.get("hora_inicio", ""),
            hora_fim=pedido_json.get("hora_fim"),
            data_entrega=pedido_json.get("data_entrega"),
            codigo_cliente=cliente.codigo,
            nome_cliente=cliente.nome,
            loja_cliente=pedido_json.get("loja_cliente"),
            observacao=pedido_json.get("observacao"),
            valor_total=sum(item.valor_total for item in itens),
            qtde_itens=len(itens),
            itens=itens
        )
