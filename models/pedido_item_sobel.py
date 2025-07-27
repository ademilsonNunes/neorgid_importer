# models/pedido_item_sobel.py

import sys
import os
# Adiciona o diretório raiz do projeto ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from pydantic import BaseModel
from models.produto import Produto

class PedidoItemSobel(BaseModel):
    cod_produto: str
    descricao_produto: str
    quantidade: float
    valor_unitario: float
    valor_total: float
    unidade: str
    ean13: str = ""
    dun14: str = ""

    @classmethod
    def from_json(cls, item_json: dict, produto: Produto) -> "PedidoItemSobel":
        qtd = float(item_json.get("qtd", 0))
        valor_unit = float(item_json.get("valor", 0))
        return cls(
            cod_produto=produto.codigo,
            descricao_produto=produto.descricao,
            quantidade=qtd,
            valor_unitario=valor_unit,
            valor_total=qtd * valor_unit,
            unidade=produto.unidade,
            ean13=produto.ean13 or "",
            dun14=produto.dun14 or ""
        )