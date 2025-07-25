# services/processador_pedido_item.py
import sys
import os
# Adiciona o diretório raiz do projeto ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from typing import Dict, Any
from models.pedido_item_sobel import PedidoItemSobel
from services.validador_produto import ValidadorProduto

class ProcessadorPedidoItem:
    def __init__(self, validador_produto: ValidadorProduto):
        self.validador_produto = validador_produto

    def processar_item(self, item_json: Dict[str, Any]) -> PedidoItemSobel:
        """
        Processa um item do pedido:
        1. Extrai os códigos (EAN13, DUN14, código interno)
        2. Valida o produto usando o ValidadorProduto
        3. Retorna um PedidoItemSobel com os dados processados
        """
        ean13 = item_json.get("ean13", "").strip()
        dun14 = item_json.get("dun14", "").strip()
        codprod = item_json.get("codprod", "").strip()
        
        # Buscar produto usando os validadores
        produto = self.validador_produto.validar_produto(ean13, dun14, codprod)
        
        if not produto:
            raise ValueError(
                f"Produto não encontrado - EAN13: '{ean13}', DUN14: '{dun14}', "
                f"CodProd: '{codprod}'"
            )
        
        # Criar o item processado
        return PedidoItemSobel.from_json(item_json, produto)
    
    def processar_lote_itens(self, itens_json: list) -> list:
        """
        Processa uma lista de itens, retornando apenas os válidos
        e coletando erros para log
        """
        itens_processados = []
        erros = []
        
        for i, item in enumerate(itens_json):
            try:
                item_processado = self.processar_item(item)
                itens_processados.append(item_processado)
            except ValueError as e:
                erros.append(f"Item {i+1}: {str(e)}")
        
        if erros:
            print(f"Erros encontrados ao processar itens: {'; '.join(erros)}")
        
        return itens_processados, erros