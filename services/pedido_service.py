# services/pedido_service.py
import sys
import os
# Adiciona o diretório raiz do projeto ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from typing import List
from models.pedido import Pedido
from services.api_client import NeogridAPIClient


class PedidoService:
    def __init__(self):
        self.api_client = NeogridAPIClient()

    def buscar_pedidos_e_processar(self) -> List[Pedido]:
        """
        Busca pedidos da Neogrid e transforma em instâncias da classe Pedido
        """
        dados_api = self.api_client.buscar_pedidos()
        documentos = dados_api.get("documents", [])

        pedidos_processados = []
        for doc in documentos:
            conteudos = doc.get("content", [])
            for conteudo in conteudos:
                try:
                    pedido = Pedido(conteudo)
                    pedidos_processados.append(pedido)
                except Exception as e:
                    print(f"Erro ao processar pedido: {e}")

        return pedidos_processados
