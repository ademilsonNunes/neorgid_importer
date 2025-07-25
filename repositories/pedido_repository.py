# repository/pedido_repository.py
import sys
import os
# Adiciona o diretório raiz do projeto ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import pyodbc
from models.pedido_sobel import PedidoSobel
from config.settings import settings

class PedidoRepository:
    def __init__(self):
        self.conn = pyodbc.connect(settings.DB_CONN_STRING)
        self.cursor = self.conn.cursor()

    def pedido_existe(self, num_pedido: str) -> bool:
        self.cursor.execute("SELECT 1 FROM T_PEDIDO_SOBEL WHERE NUM_PEDIDO = ?", num_pedido)
        return self.cursor.fetchone() is not None

    def inserir_pedido(self, pedido: PedidoSobel):
        if self.pedido_existe(pedido.num_pedido):
            print(f"Pedido {pedido.num_pedido} já existe. Ignorando.")
            return

        # Inserir o cabeçalho
        self.cursor.execute("""
            INSERT INTO T_PEDIDO_SOBEL (
                NUM_PEDIDO, CODIGO_CLIENTE, DATA_PEDIDO, DATA_ENTREGA, QTDE_ITENS, VALOR_TOTAL, OBSERVACAO
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, pedido.num_pedido, pedido.codigo_cliente, pedido.data_pedido, pedido.data_entrega,
             pedido.qtde_itens, pedido.valor_total, pedido.observacao)
        
        # Inserir os itens
        for item in pedido.itens:
            self.cursor.execute("""
                INSERT INTO T_PEDIDOITEM_SOBEL (
                    NUM_PEDIDO, COD_PRODUTO, DESCRICAO_PRODUTO, QUANTIDADE, VALOR_UNITARIO, VALOR_TOTAL,
                    UNIDADE, EAN13, DUN14
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, pedido.num_pedido, item.cod_produto, item.descricao_produto, item.quantidade,
                 item.valor_unitario, item.valor_total, item.unidade, item.ean13, item.dun14)
        
        self.conn.commit()
        print(f"Pedido {pedido.num_pedido} gravado com sucesso.")

    def close(self):
        self.cursor.close()
        self.conn.close()
