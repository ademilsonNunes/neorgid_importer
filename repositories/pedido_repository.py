# repositories/pedido_repository.py
import sys
import os
# Adiciona o diretório raiz do projeto ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import pyodbc
from models.pedido_sobel import PedidoSobel
from services.database import Database
from config.settings import settings
from datetime import datetime

class PedidoRepository:
    def __init__(self):
        self.db = Database(settings.DB_NAME_PROTHEUS)
        self.conn = None
        self.cursor = None
        self._connect()

    def _connect(self):
        """Estabelece conexão com o banco"""
        try:
            self.conn = self.db.connect()
            self.cursor = self.conn.cursor()
        except Exception as e:
            print(f"Erro ao conectar no banco: {e}")
            raise

    def pedido_existe(self, num_pedido: str) -> bool:
        """Verifica se o pedido já existe na base"""
        try:
            self.cursor.execute(
                "SELECT 1 FROM T_PEDIDO_SOBEL WHERE NUMPEDIDOSOBEL = ?",
                num_pedido
            )
            return self.cursor.fetchone() is not None
        except Exception as e:
            print(f"Erro ao verificar existência do pedido {num_pedido}: {e}")
            return False

    def inserir_pedido(self, pedido: PedidoSobel) -> bool:
        """
        Insere pedido completo (cabeçalho + itens) no banco de dados
        com controle de transação
        """
        if self.pedido_existe(pedido.num_pedido):
            print(f"⚠️ Pedido {pedido.num_pedido} já existe. Ignorando inserção.")
            return False

        try:
            # Iniciar transação
            self.conn.autocommit = False
            
            # Inserir cabeçalho do pedido
            self._inserir_cabecalho_pedido(pedido)
            
            # Inserir itens do pedido
            self._inserir_itens_pedido(pedido)
            
            # Confirmar transação
            self.conn.commit()
            print(f"✅ Pedido {pedido.num_pedido} gravado com sucesso!")
            return True
            
        except Exception as e:
            # Desfazer transação em caso de erro
            self.conn.rollback()
            print(f"❌ Erro ao gravar pedido {pedido.num_pedido}: {e}")
            return False
        finally:
            self.conn.autocommit = True

    def _inserir_cabecalho_pedido(self, pedido: PedidoSobel):
        """Insere o cabeçalho do pedido"""
        # As tabelas do ambiente Protheus utilizam outros nomes de colunas.
        # Mapeamos os campos do modelo ``PedidoSobel`` para as colunas reais
        # existentes no banco.
        query = """
            INSERT INTO T_PEDIDO_SOBEL (
                NUMPEDIDOSOBEL,
                LOJACLIENTE,
                DATAPEDIDO,
                HORAINICIAL,
                HORAFINAL,
                DATAENTREGA,
                CODIGOCLIENTE,
                QTDEITENS,
                VALORBRUTO,
                OBSERVACAOI,
                DATAGRAVACAOACACIA
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        self.cursor.execute(
            query,
            pedido.num_pedido,      # NUMPEDIDOSOBEL
            pedido.loja_cliente,
            pedido.data_pedido,
            pedido.hora_inicio,
            pedido.hora_fim,
            pedido.data_entrega,
            pedido.codigo_cliente,
            pedido.qtde_itens,
            pedido.valor_total,
            pedido.observacao,
            datetime.now()
        )

    def _inserir_itens_pedido(self, pedido: PedidoSobel):
        """Insere os itens do pedido"""
        # Inserção de itens utilizando as colunas presentes na base Protheus
        query = """
            INSERT INTO T_PEDIDOITEM_SOBEL (
                NUMPEDIDOAFV,
                DATAPEDIDO,
                HORAINICIAL,
                CODIGOCLIENTE,
                CODIGOPRODUTO,
                QTDEVENDA,
                QTDEBONIFICADA,
                VALORVENDA,
                VALORBRUTO,
                DESCONTOI,
                DESCONTOII,
                VALORVERBA,
                CODIGOVENDEDORESP,
                MSGIMPORTACAO
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        for item in pedido.itens:
            self.cursor.execute(
                query,
                pedido.num_pedido,          # NUMPEDIDOAFV
                pedido.data_pedido,
                pedido.hora_inicio,
                pedido.codigo_cliente,
                item.cod_produto,
                item.quantidade,
                0,                           # QTDEBONIFICADA
                item.valor_unitario,
                item.valor_total,
                0,                           # DESCONTOI
                0,                           # DESCONTOII
                0,                           # VALORVERBA
                None,                        # CODIGOVENDEDORESP
                None                         # MSGIMPORTACAO
            )

    def buscar_pedido(self, num_pedido: str) -> dict:
        """Busca um pedido específico com seus itens"""
        try:
            # Buscar cabeçalho
            self.cursor.execute("""
                SELECT NUMPEDIDOSOBEL, CODIGOCLIENTE, DATAPEDIDO, DATAENTREGA,
                       QTDEITENS, VALORBRUTO, OBSERVACAOI, DATAGRAVACAOACACIA
                FROM T_PEDIDO_SOBEL
                WHERE NUMPEDIDOSOBEL = ?
            """, num_pedido)
            
            cabecalho = self.cursor.fetchone()
            if not cabecalho:
                return None
            
            # Buscar itens
            self.cursor.execute("""
                SELECT CODIGOPRODUTO, QTDEVENDA, VALORVENDA, VALORBRUTO,
                       QTDEBONIFICADA, DESCONTOI, DESCONTOII, VALORVERBA,
                       MSGIMPORTACAO
                FROM T_PEDIDOITEM_SOBEL
                WHERE NUMPEDIDOAFV = ?
            """, num_pedido)
            
            itens = self.cursor.fetchall()
            
            return {
                'cabecalho': cabecalho,
                'itens': itens
            }
            
        except Exception as e:
            print(f"Erro ao buscar pedido {num_pedido}: {e}")
            return None

    def listar_pedidos_por_periodo(self, data_inicio: str, data_fim: str) -> list:
        """Lista pedidos por período"""
        try:
            query = """
                SELECT NUMPEDIDOSOBEL, CODIGOCLIENTE, DATAPEDIDO,
                       QTDEITENS, VALORBRUTO, DATAGRAVACAOACACIA
                FROM T_PEDIDO_SOBEL
                WHERE DATAPEDIDO BETWEEN ? AND ?
                ORDER BY DATAPEDIDO DESC, DATAGRAVACAOACACIA DESC
            """
            
            self.cursor.execute(query, data_inicio, data_fim)
            return self.cursor.fetchall()
            
        except Exception as e:
            print(f"Erro ao listar pedidos: {e}")
            return []

    def log_processamento(self, tipo: str, mensagem: str, num_pedido: str = None):
        """Registra log de processamento"""
        try:
            query = """
                INSERT INTO T_LOG_PROCESSAMENTO (TIPO, MENSAGEM, NUM_PEDIDO)
                VALUES (?, ?, ?)
            """
            self.cursor.execute(query, tipo, mensagem, num_pedido)
            self.conn.commit()
        except Exception as e:
            print(f"Erro ao registrar log: {e}")

    def close(self):
        """Fecha conexões"""
        try:
            if self.cursor:
                self.cursor.close()
            if self.conn:
                self.conn.close()
        except Exception as e:
            print(f"Erro ao fechar conexão: {e}")

    def __enter__(self):
        """Context manager - entrada"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager - saída"""
        self.close()