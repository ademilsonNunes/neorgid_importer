# models/pedido_item_sobel.py

import sys
import os
# Adiciona o diretório raiz do projeto ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from typing import Optional
from pydantic import BaseModel
from models.produto import Produto

class PedidoItemSobel(BaseModel):
    """Representa um item de pedido conforme a tabela ``T_PEDIDOITEM_SOBEL``.
    Os campos originais continuam presentes e novos atributos opcionais foram
    adicionados para refletir todas as colunas existentes no Protheus."""

    # Campos já utilizados
    cod_produto: str
    descricao_produto: str
    quantidade: float
    valor_unitario: float
    valor_total: float
    unidade: str
    ean13: str = ""
    dun14: str = ""

    # Novas colunas da tabela no banco
    num_pedido: Optional[int] = None
    num_item: Optional[int] = None
    num_pedido_afv: Optional[str] = None
    data_pedido: Optional[str] = None
    hora_inicial: Optional[str] = None
    codigo_cliente: Optional[str] = None
    qtde_bonificada: float = 0
    valor_bruto: Optional[float] = None
    desconto_i: float = 0
    desconto_ii: float = 0
    valor_verba: float = 0
    codigo_vendedor_resp: Optional[str] = None
    msg_importacao: Optional[str] = None

    @classmethod
    def from_json(cls, item_json: dict, produto: Produto) -> "PedidoItemSobel":
        qtd = float(item_json.get("qtd", 0))
        valor_unit = float(item_json.get("valor", 0))
        valor_total = qtd * valor_unit
        return cls(
            cod_produto=produto.codigo,
            descricao_produto=produto.descricao,
            quantidade=qtd,
            valor_unitario=valor_unit,
            valor_total=valor_total,
            unidade=produto.unidade,
            ean13=produto.ean13 or "",
            dun14=produto.dun14 or "",
            num_pedido_afv=item_json.get("num_pedido_afv"),
            data_pedido=item_json.get("data_pedido"),
            hora_inicial=item_json.get("hora_inicial"),
            codigo_cliente=item_json.get("codigo_cliente"),
            qtde_bonificada=float(item_json.get("qtde_bonificada", 0)),
            valor_bruto=item_json.get("valor_bruto", valor_total),
            desconto_i=float(item_json.get("desconto_i", 0)),
            desconto_ii=float(item_json.get("desconto_ii", 0)),
            valor_verba=float(item_json.get("valor_verba", 0)),
            codigo_vendedor_resp=item_json.get("codigo_vendedor_resp"),
            msg_importacao=item_json.get("msg_importacao"),
        )
