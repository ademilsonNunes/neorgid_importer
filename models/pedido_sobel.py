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
    """Representa o cabeçalho do pedido de acordo com a tabela
    ``T_PEDIDO_SOBEL`` do Protheus. Os campos utilizados pelo restante do
    projeto permanecem disponíveis (``num_pedido``, ``hora_inicio`` etc.),
    enquanto os demais são opcionais para possibilitar a gravação completa
    do registro."""

    # Campos principais já utilizados pelo projeto
    num_pedido: str
    data_pedido: str
    hora_inicio: str
    hora_fim: Optional[str] = None
    data_entrega: Optional[str] = None
    codigo_cliente: str
    nome_cliente: str
    loja_cliente: Optional[str] = None
    observacao: Optional[str] = None
    valor_total: float
    qtde_itens: int
    itens: List[PedidoItemSobel]

    # Novos campos presentes na tabela do Protheus
    num_pedido_afv: Optional[str] = None
    codigo_tipo_pedido: Optional[str] = None
    codigo_cond_pagto: Optional[str] = None
    codigo_nome_endereco: Optional[str] = None
    codigo_unidade_faturamento: Optional[str] = None
    codigo_tabela_preco: Optional[str] = None
    ordem_compra: Optional[str] = None
    observacao_1: Optional[str] = None
    observacao_2: Optional[str] = None
    valor_liquido: Optional[float] = None
    valor_bruto: Optional[float] = None
    codigo_motivo_tipo_pedido: Optional[str] = None
    codigo_vendedor_resp: Optional[str] = None
    data_entrega_fim: Optional[str] = None
    num_pedido_assoc: Optional[str] = None
    data_gravacao_acacia: Optional[str] = None
    data_integracao_erp: Optional[str] = None
    mensagem_importacao: Optional[str] = None
    volume: Optional[int] = None

    @classmethod
    def from_json(cls, pedido_json: dict, cliente: Cliente, itens: List[PedidoItemSobel]) -> "PedidoSobel":
        total = sum(item.valor_total for item in itens)
        return cls(
            num_pedido=pedido_json.get("num_pedido", ""),
            data_pedido=pedido_json.get("data_pedido", ""),
            hora_inicio=pedido_json.get("hora_inicio", ""),
            hora_fim=pedido_json.get("hora_fim"),
            data_entrega=pedido_json.get("data_entrega"),
            codigo_cliente=cliente.codigo,
            nome_cliente=cliente.nome,
            loja_cliente=pedido_json.get("loja_cliente"),
            observacao=pedido_json.get("observacao"),
            valor_total=total,
            qtde_itens=len(itens),
            itens=itens,
            num_pedido_afv=pedido_json.get("num_pedido_afv"),
            codigo_tipo_pedido=pedido_json.get("codigo_tipo_pedido"),
            codigo_cond_pagto=pedido_json.get("codigo_cond_pagto"),
            codigo_nome_endereco=pedido_json.get("codigo_nome_endereco"),
            codigo_unidade_faturamento=pedido_json.get("codigo_unidade_faturamento"),
            codigo_tabela_preco=pedido_json.get("codigo_tabela_preco"),
            ordem_compra=pedido_json.get("ordem_compra"),
            observacao_1=pedido_json.get("observacao_1"),
            observacao_2=pedido_json.get("observacao_2"),
            valor_liquido=pedido_json.get("valor_liquido"),
            valor_bruto=total,
            codigo_motivo_tipo_pedido=pedido_json.get("codigo_motivo_tipo_pedido"),
            codigo_vendedor_resp=pedido_json.get("codigo_vendedor_resp"),
            data_entrega_fim=pedido_json.get("data_entrega_fim"),
            num_pedido_assoc=pedido_json.get("num_pedido_assoc"),
            data_gravacao_acacia=pedido_json.get("data_gravacao_acacia"),
            data_integracao_erp=pedido_json.get("data_integracao_erp"),
            mensagem_importacao=pedido_json.get("mensagem_importacao"),
            volume=pedido_json.get("volume")
        )

