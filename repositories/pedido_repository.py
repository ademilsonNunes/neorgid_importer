# repositories/pedido_repository.py
import sys
import os
# Adiciona o diretório raiz do projeto ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import pyodbc
from utils.logger import logger
from models.pedido_sobel import PedidoSobel
from services.database import Database
from config.settings import settings
from utils.error_handler import BancoDadosError, ErrorHandler, PedidoDuplicadoError
from datetime import datetime

class PedidoRepository:
    def __init__(self):
        self.db = Database(settings.DB_NAME_PROTHEUS)
        self.conn = None
        self.cursor = None
        self._connect()

    def _connect(self):
        """Estabelece conexão com o banco com retry automático"""
        try:
            self.conn = self.db.connect()
            self.cursor = self.conn.cursor()
        except Exception as e:
            raise BancoDadosError(f"Falha ao conectar no banco: {str(e)}", e, "conexão inicial")

    def _reconnect_if_needed(self):
        """Reconecta se a conexão foi perdida"""
        try:
            if self.conn is None or self.db._is_connection_closed():
                print("🔄 Reconectando ao banco de dados...")
                self._connect()
        except Exception as e:
            raise BancoDadosError(f"Falha ao reconectar: {str(e)}", e, "reconexão")

    def pedido_existe(self, num_pedido: str) -> bool:
        """Verifica se o pedido já existe na base com tratamento robusto"""
        if not num_pedido or num_pedido.strip() == "":
            return False
            
        try:
            self._reconnect_if_needed()
            
            query = "SELECT 1 FROM T_PEDIDO_SOBEL WHERE NUMPEDIDOSOBEL = ?"
            self.cursor.execute(query, num_pedido.strip())
            result = self.cursor.fetchone()
            
            existe = result is not None
            if existe:
                print(f"📋 Pedido {num_pedido} já existe no banco")
            
            return existe
            
        except pyodbc.Error as e:
            # Erro específico do banco
            raise BancoDadosError(
                f"Erro ao verificar existência do pedido {num_pedido}: {str(e)}", 
                e, 
                "verificar_existencia"
            )
        except Exception as e:
            # Outros erros
            raise BancoDadosError(
                f"Erro inesperado ao verificar pedido {num_pedido}: {str(e)}", 
                e, 
                "verificar_existencia"
            )

    def inserir_pedido(self, pedido: PedidoSobel) -> bool:
        """
        Insere pedido completo (cabeçalho + itens) no banco de dados
        com controle de transação e tratamento robusto de erros
        """
        if not pedido or not pedido.num_pedido:
            raise BancoDadosError("Pedido inválido para inserção", ValueError("Pedido vazio"), "validação")
        
        # Verificar se já existe
        if self.pedido_existe(pedido.num_pedido):
            raise PedidoDuplicadoError(pedido.num_pedido)

        try:
            self._reconnect_if_needed()
            
            # Iniciar transação explícita
            self.conn.autocommit = False
            print(f"💾 Iniciando gravação do pedido {pedido.num_pedido}...")
            
            # Inserir cabeçalho do pedido
            self._inserir_cabecalho_pedido(pedido)
            print(f"✅ Cabeçalho do pedido {pedido.num_pedido} inserido")
            
            # Inserir itens do pedido
            self._inserir_itens_pedido(pedido)
            print(f"✅ {len(pedido.itens)} itens do pedido {pedido.num_pedido} inseridos")
            
            # Confirmar transação
            self.conn.commit()
            print(f"✅ Pedido {pedido.num_pedido} gravado com sucesso!")
            
            return True
            
        except pyodbc.IntegrityError as e:
            # Erro de integridade (chave duplicada, etc.)
            self.conn.rollback()
            if "duplicate key" in str(e).lower() or "primary key" in str(e).lower():
                raise PedidoDuplicadoError(pedido.num_pedido)
            else:
                raise BancoDadosError(
                    f"Violação de integridade ao gravar pedido {pedido.num_pedido}: {str(e)}", 
                    e, 
                    "inserir_pedido"
                )
        except pyodbc.Error as e:
            # Outros erros do banco
            self.conn.rollback()
            raise BancoDadosError(
                f"Erro de banco ao gravar pedido {pedido.num_pedido}: {str(e)}", 
                e, 
                "inserir_pedido"
            )
        except Exception as e:
            # Erros inesperados
            self.conn.rollback()
            raise BancoDadosError(
                f"Erro inesperado ao gravar pedido {pedido.num_pedido}: {str(e)}", 
                e, 
                "inserir_pedido"
            )
        finally:
            # Sempre restaurar autocommit
            try:
                self.conn.autocommit = True
            except:
                pass

    def _inserir_cabecalho_pedido(self, pedido: PedidoSobel):
        """Insere o cabeçalho do pedido com validação de dados"""
        try:
            # Validar dados obrigatórios
            if not pedido.codigo_cliente:
                raise ValueError(f"Código do cliente não pode ser vazio para pedido {pedido.num_pedido}")
            
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
            
            # Preparar valores com tratamento de None e limites de tamanho
            valores = (
                str(pedido.num_pedido)[:50],
                str(pedido.num_pedido)[:50],
                (pedido.loja_cliente or "1")[:10],
                str(pedido.data_pedido)[:10],
                (pedido.hora_inicio or "")[:8],
                (pedido.hora_fim or "")[:8],
                (pedido.data_entrega or "")[:10],
                str(pedido.codigo_cliente)[:20],
                pedido.qtde_itens,
                pedido.valor_total,
                (pedido.observacao or "")[:500],
                datetime.now()
            )

            logger.sql(query, valores)

            self.cursor.execute(query, valores)
            
        except pyodbc.Error as e:
            raise BancoDadosError(
                f"Erro ao inserir cabeçalho do pedido {pedido.num_pedido}: {str(e)}", 
                e, 
                "inserir_cabecalho"
            )

    def _inserir_itens_pedido(self, pedido: PedidoSobel):
        """Insere os itens do pedido com validação individual"""
        if not pedido.itens:
            raise ValueError(f"Pedido {pedido.num_pedido} não possui itens para inserir")
        
        try:
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
            
            itens_inseridos = 0
            for i, item in enumerate(pedido.itens):
                try:
                    # Validar item
                    if not item.cod_produto:
                        print(f"⚠️ Item {i+1} sem código de produto - ignorando")
                        continue
                    
                    valores = (
                        str(pedido.num_pedido)[:50],
                        str(pedido.data_pedido)[:10],
                        (pedido.hora_inicio or "")[:8],
                        str(pedido.codigo_cliente)[:20],
                        str(item.cod_produto)[:30],
                        item.quantidade,
                        0,  # QTDEBONIFICADA
                        item.valor_unitario,
                        item.valor_total,
                        0,  # DESCONTOI
                        0,  # DESCONTOII
                        0,  # VALORVERBA
                        None,  # CODIGOVENDEDORESP
                        f"Importado Neogrid - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"[:100]
                    )

                    logger.sql(query, valores)

                    self.cursor.execute(query, valores)
                    itens_inseridos += 1
                    
                except Exception as e:
                    print(f"⚠️ Erro ao inserir item {i+1} do pedido {pedido.num_pedido}: {str(e)}")
                    # Continua com próximo item
                    continue
            
            if itens_inseridos == 0:
                raise ValueError(f"Nenhum item válido foi inserido para o pedido {pedido.num_pedido}")
            
            print(f"📦 {itens_inseridos} de {len(pedido.itens)} itens inseridos com sucesso")
            
        except pyodbc.Error as e:
            raise BancoDadosError(
                f"Erro ao inserir itens do pedido {pedido.num_pedido}: {str(e)}", 
                e, 
                "inserir_itens"
            )

    def buscar_pedido(self, num_pedido: str) -> dict:
        """Busca um pedido específico com seus itens"""
        if not num_pedido:
            return None
            
        try:
            self._reconnect_if_needed()
            
            # Buscar cabeçalho
            query_cabecalho = """
                SELECT NUMPEDIDOSOBEL, CODIGOCLIENTE, DATAPEDIDO, DATAENTREGA,
                       QTDEITENS, VALORBRUTO, OBSERVACAOI, DATAGRAVACAOACACIA
                FROM T_PEDIDO_SOBEL
                WHERE NUMPEDIDOSOBEL = ?
            """
            
            self.cursor.execute(query_cabecalho, num_pedido)
            cabecalho = self.cursor.fetchone()
            
            if not cabecalho:
                return None
            
            # Buscar itens
            query_itens = """
                SELECT CODIGOPRODUTO, QTDEVENDA, VALORVENDA, VALORBRUTO,
                       QTDEBONIFICADA, DESCONTOI, DESCONTOII, VALORVERBA,
                       MSGIMPORTACAO
                FROM T_PEDIDOITEM_SOBEL
                WHERE NUMPEDIDOAFV = ?
            """
            
            self.cursor.execute(query_itens, num_pedido)
            itens = self.cursor.fetchall()
            
            return {
                'cabecalho': cabecalho,
                'itens': itens
            }
            
        except Exception as e:
            raise BancoDadosError(
                f"Erro ao buscar pedido {num_pedido}: {str(e)}", 
                e, 
                "buscar_pedido"
            )

    def listar_pedidos_por_periodo(self, data_inicio: str, data_fim: str) -> list:
        """Lista pedidos por período com tratamento de erro"""
        try:
            self._reconnect_if_needed()
            
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
            raise BancoDadosError(
                f"Erro ao listar pedidos no período {data_inicio} - {data_fim}: {str(e)}", 
                e, 
                "listar_pedidos"
            )

    def _get_log_table_columns(self):
        """Verifica as colunas disponíveis na tabela de log"""
        try:
            query = """
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = 'T_LOG_PROCESSAMENTO'
                ORDER BY ORDINAL_POSITION
            """
            self.cursor.execute(query)
            columns = [row[0] for row in self.cursor.fetchall()]
            return columns
        except:
            return []

    def log_processamento(self, tipo: str, mensagem: str, num_pedido: str = None):
        """Registra log de processamento com detecção automática de colunas"""
        try:
            self._reconnect_if_needed()
            
            # Verificar se tabela existe e quais colunas estão disponíveis
            try:
                columns = self._get_log_table_columns()
                
                if not columns:
                    # Tabela não existe ou sem permissão
                    print(f"📝 Log local: [{tipo}] {mensagem}")
                    return
                
                # Preparar query baseada nas colunas disponíveis
                base_columns = ['TIPO', 'MENSAGEM']
                base_values = [tipo, mensagem[:500]]  # Limitar mensagem
                
                # Adicionar colunas opcionais se existirem
                if 'NUM_PEDIDO' in columns and num_pedido:
                    base_columns.append('NUM_PEDIDO')
                    base_values.append(num_pedido)
                
                # Verificar possíveis nomes para coluna de data
                date_column = None
                for col_name in ['DATA_LOG', 'DATETIME_LOG', 'DATA_HORA', 'TIMESTAMP_LOG', 'CREATED_AT']:
                    if col_name in columns:
                        date_column = col_name
                        break
                
                if date_column:
                    base_columns.append(date_column)
                    base_values.append(datetime.now())
                
                # Montar query
                placeholders = ', '.join(['?' for _ in base_values])
                query = f"""
                    INSERT INTO T_LOG_PROCESSAMENTO ({', '.join(base_columns)})
                    VALUES ({placeholders})
                """
                
                self.cursor.execute(query, base_values)
                self.conn.commit()
                
            except pyodbc.Error as e:
                error_msg = str(e).lower()
                if any(x in error_msg for x in ["invalid object", "table", "não existe", "invalid column"]):
                    print(f"📝 Log local (tabela não disponível): [{tipo}] {mensagem}")
                else:
                    print(f"⚠️ Erro ao registrar log no banco: {e}")
                    print(f"📝 Log local: [{tipo}] {mensagem}")
                    
        except Exception as e:
            # Não falhar o processo principal por causa de log
            print(f"⚠️ Erro no sistema de log: {e}")
            print(f"📝 Log local: [{tipo}] {mensagem}")

    def get_estatisticas(self) -> dict:
        """Retorna estatísticas básicas dos pedidos"""
        try:
            self._reconnect_if_needed()
            
            stats = {}
            
            # Total de pedidos
            self.cursor.execute("SELECT COUNT(*) FROM T_PEDIDO_SOBEL")
            stats['total_pedidos'] = self.cursor.fetchone()[0]
            
            # Pedidos hoje
            self.cursor.execute("""
                SELECT COUNT(*) FROM T_PEDIDO_SOBEL 
                WHERE CAST(DATAGRAVACAOACACIA AS DATE) = CAST(GETDATE() AS DATE)
            """)
            stats['pedidos_hoje'] = self.cursor.fetchone()[0]
            
            # Valor total hoje
            self.cursor.execute("""
                SELECT ISNULL(SUM(VALORBRUTO), 0) FROM T_PEDIDO_SOBEL 
                WHERE CAST(DATAGRAVACAOACACIA AS DATE) = CAST(GETDATE() AS DATE)
            """)
            stats['valor_hoje'] = float(self.cursor.fetchone()[0])
            
            return stats
            
        except Exception as e:
            print(f"⚠️ Erro ao obter estatísticas: {e}")
            return {'total_pedidos': 0, 'pedidos_hoje': 0, 'valor_hoje': 0.0}

    def close(self):
        """Fecha conexões com tratamento de erro"""
        try:
            if self.cursor:
                self.cursor.close()
                self.cursor = None
            if self.conn:
                self.conn.close()
                self.conn = None
        except Exception as e:
            print(f"⚠️ Erro ao fechar conexão: {e}")

    def __enter__(self):
        """Context manager - entrada"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager - saída"""
        self.close()
        
        # Se houve exceção, log do erro
        if exc_type is not None:
            print(f"❌ Erro no contexto do repository: {exc_type.__name__}: {exc_val}")
        
        return False  # Não suprimir exceções