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
            logger.info("🔗 Conexão com banco estabelecida com sucesso")
        except Exception as e:
            logger.error(f"Falha ao conectar no banco: {str(e)}")
            raise BancoDadosError(f"Falha ao conectar no banco: {str(e)}", e, "conexão inicial")

    def _reconnect_if_needed(self):
        """Reconecta se a conexão foi perdida"""
        try:
            if self.conn is None or self.db._is_connection_closed():
                logger.info("🔄 Reconectando ao banco de dados...")
                self._connect()
        except Exception as e:
            logger.error(f"Falha ao reconectar: {str(e)}")
            raise BancoDadosError(f"Falha ao reconectar: {str(e)}", e, "reconexão")

    def _execute_with_logging(self, query: str, params: tuple, operation: str, num_pedido: str = None):
        """
        Executa query com logging detalhado e tratamento de erro robusto
        """
        try:
            # Log da query ANTES da execução
            logger.debug(f"🔍 [{operation}] Query a ser executada:")
            logger.debug(f"SQL: {query.strip()}")
            logger.debug(f"Parâmetros: {params}")
            
            # Executar query
            self.cursor.execute(query, params)
            
            # Log de sucesso
            logger.debug(f"✅ [{operation}] Query executada com sucesso")
            
        except Exception as e:
            # Log detalhado do erro com a query que falhou
            logger.error(f"❌ [{operation}] Erro ao executar query:")
            logger.error(f"SQL: {query.strip()}")
            logger.error(f"Parâmetros: {params}")
            logger.error(f"Erro: {str(e)}")
            if num_pedido:
                logger.error(f"Pedido: {num_pedido}")
            
            # Re-raise o erro
            raise

    def pedido_existe(self, num_pedido: str) -> bool:
        """Verifica se o pedido já existe na base com tratamento robusto"""
        if not num_pedido or num_pedido.strip() == "":
            return False
            
        try:
            self._reconnect_if_needed()
            
            query = "SELECT 1 FROM T_PEDIDO_SOBEL WHERE NUMPEDIDOSOBEL = ?"
            params = (num_pedido.strip(),)
            
            logger.debug(f"🔍 Verificando existência do pedido: {num_pedido}")
            self._execute_with_logging(query, params, "VERIFICAR_EXISTENCIA", num_pedido)
            
            result = self.cursor.fetchone()
            existe = result is not None
            
            if existe:
                logger.info(f"📋 Pedido {num_pedido} já existe no banco")
            else:
                logger.debug(f"📋 Pedido {num_pedido} não existe no banco")
            
            return existe
            
        except pyodbc.Error as e:
            raise BancoDadosError(
                f"Erro ao verificar existência do pedido {num_pedido}: {str(e)}", 
                e, 
                "verificar_existencia"
            )
        except Exception as e:
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
        
        # Log início da operação
        logger.info(f"💾 Iniciando inserção do pedido {pedido.num_pedido}")
        logger.debug(f"Cliente: {pedido.codigo_cliente} | Itens: {len(pedido.itens)} | Valor: R$ {pedido.valor_total:.2f}")
        
        # Verificar se já existe
        if self.pedido_existe(pedido.num_pedido):
            raise PedidoDuplicadoError(pedido.num_pedido)

        try:
            self._reconnect_if_needed()
            
            # Iniciar transação explícita
            self.conn.autocommit = False
            logger.debug(f"🔄 Transação iniciada para pedido {pedido.num_pedido}")
            
            # Inserir cabeçalho do pedido
            self._inserir_cabecalho_pedido(pedido)
            logger.info(f"✅ Cabeçalho do pedido {pedido.num_pedido} inserido com sucesso")
            
            # Inserir itens do pedido
            itens_inseridos = self._inserir_itens_pedido(pedido)
            logger.info(f"✅ {itens_inseridos} itens do pedido {pedido.num_pedido} inseridos com sucesso")
            
            # Confirmar transação
            self.conn.commit()
            logger.info(f"🎉 Pedido {pedido.num_pedido} gravado com sucesso no banco!")
            
            return True
            
        except pyodbc.IntegrityError as e:
            self.conn.rollback()
            logger.error(f"🔄 Rollback executado para pedido {pedido.num_pedido}")
            
            if "duplicate key" in str(e).lower() or "primary key" in str(e).lower():
                raise PedidoDuplicadoError(pedido.num_pedido)
            else:
                raise BancoDadosError(
                    f"Violação de integridade ao gravar pedido {pedido.num_pedido}: {str(e)}", 
                    e, 
                    "inserir_pedido"
                )
        except pyodbc.Error as e:
            self.conn.rollback()
            logger.error(f"🔄 Rollback executado para pedido {pedido.num_pedido}")
            raise BancoDadosError(
                f"Erro de banco ao gravar pedido {pedido.num_pedido}: {str(e)}", 
                e, 
                "inserir_pedido"
            )
        except Exception as e:
            self.conn.rollback()
            logger.error(f"🔄 Rollback executado para pedido {pedido.num_pedido}")
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
        """Insere o cabeçalho do pedido de forma completa"""
        try:
            if not pedido.codigo_cliente:
                raise ValueError(
                    f"Código do cliente não pode ser vazio para pedido {pedido.num_pedido}"
                )

            if not pedido.num_pedido:
                raise ValueError("Número do pedido não pode ser vazio")

            query = """
                INSERT INTO T_PEDIDO_SOBEL (
                    NUMPEDIDO,
                    NUMPEDIDOSOBEL,
                    LOJACLIENTE,
                    NUMPEDIDOAFV,
                    DATAPEDIDO,
                    HORAINICIAL,
                    HORAFINAL,
                    DATAENTREGA,
                    CODIGOCLIENTE,
                    CODIGOTIPOPEDIDO,
                    CODIGOCONDPAGTO,
                    CODIGONOMEENDERECO,
                    CODIGOUNIDFAT,
                    CODIGOTABPRECO,
                    ORDEMCOMPRA,
                    OBSERVACAOI,
                    OBSERVACAOII,
                    VALORLIQUIDO,
                    VALORBRUTO,
                    CODIGOMOTIVOTIPOPED,
                    CODIGOVENDEDORESP,
                    CESP_DATAENTREGAFIM,
                    CESP_NUMPEDIDOASSOC,
                    DATAGRAVACAOACACIA,
                    DATAINTEGRACAOERP,
                    QTDEITENS,
                    MSGIMPORTACAO,
                    VOLUME
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """

            valores = (
                str(pedido.num_pedido).strip(),  # NUMPEDIDO
                str(pedido.num_pedido).strip(),  # NUMPEDIDOSOBEL
                str(pedido.loja_cliente or "01"),  # LOJACLIENTE
                str(pedido.num_pedido_afv or pedido.num_pedido),  # NUMPEDIDOAFV
                pedido.data_pedido,
                pedido.hora_inicio or "",
                pedido.hora_fim or "",
                pedido.data_entrega,
                pedido.codigo_cliente,
                pedido.codigo_tipo_pedido or "N",
                pedido.codigo_cond_pagto or "055",
                pedido.codigo_nome_endereco or "E",
                pedido.codigo_unid_fat or "01",
                pedido.codigo_tab_preco or "038",
                pedido.ordem_compra or "",
                (pedido.observacao or "CIF")[:50],
                pedido.observacao_ii,
                pedido.valor_liquido or pedido.valor_total,
                pedido.valor_bruto or pedido.valor_total,
                pedido.codigo_motivo_tipo_ped,
                pedido.codigo_vendedor_resp or "000559",
                pedido.cesp_data_entrega_fim or pedido.data_entrega,
                pedido.cesp_num_pedido_assoc,
                datetime.now(),
                pedido.data_integracao_erp,
                pedido.qtde_itens,
                pedido.msg_importacao,
                pedido.volume or 0,
            )

            self._execute_with_logging(
                query, valores, "INSERIR_CABECALHO", pedido.num_pedido
            )

        except pyodbc.Error as e:
            raise BancoDadosError(
                f"Erro ao inserir cabeçalho do pedido {pedido.num_pedido}: {str(e)}",
                e,
                "inserir_cabecalho",
            )

    def _inserir_itens_pedido(self, pedido: PedidoSobel) -> int:
        """Insere os itens do pedido com validação individual"""
        if not pedido.itens:
            raise ValueError(f"Pedido {pedido.num_pedido} não possui itens para inserir")
        
        try:
            query = """
                INSERT INTO T_PEDIDOITEM_SOBEL (
                    NUMPEDIDO,
                    NUMITEM,
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
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            itens_inseridos = 0
            total_itens = len(pedido.itens)
            
            logger.debug(f"📦 Iniciando inserção de {total_itens} itens")
            
            for i, item in enumerate(pedido.itens):
                try:
                    # Validar item
                    if not item.cod_produto or item.cod_produto.strip() == "":
                        logger.warning(f"⚠️ Item {i+1} sem código de produto - ignorando")
                        continue
                    
                    valores = (
                        str(pedido.num_pedido).strip(),        # NUMPEDIDO
                        i,                                    # NUMITEM
                        str(pedido.num_pedido).strip(),        # NUMPEDIDOAFV
                        pedido.data_pedido,
                        pedido.hora_inicio or "",
                        pedido.codigo_cliente,
                        item.cod_produto[:20],
                        float(item.quantidade),
                        float(getattr(item, 'qtde_bonificada', 0)),
                        float(item.valor_unitario),
                        float(getattr(item, 'valor_bruto', item.valor_total)),
                        float(getattr(item, 'desconto_i', 0)),
                        float(getattr(item, 'desconto_ii', 0)),
                        float(getattr(item, 'valor_verba', 0)),
                        item.codigo_vendedor_resp or "000559",
                        item.msg_importacao,
                    )

                    # Log detalhado para o primeiro item (debug)
                    if i == 0:
                        logger.debug(f"📝 Exemplo de valores para item:")
                        campos_item = [
                            'NUMPEDIDO', 'NUMITEM', 'NUMPEDIDOAFV', 'DATAPEDIDO', 'HORAINICIAL',
                            'CODIGOCLIENTE', 'CODIGOPRODUTO', 'QTDEVENDA', 'QTDEBONIFICADA',
                            'VALORVENDA', 'VALORBRUTO', 'DESCONTOI', 'DESCONTOII', 'VALORVERBA',
                            'CODIGOVENDEDORESP', 'MSGIMPORTACAO'
                        ]
                        for campo, valor in zip(campos_item, valores):
                            logger.debug(f"  {campo}: '{valor}' ({type(valor).__name__})")

                    # Executar inserção do item
                    self._execute_with_logging(query, valores, f"INSERIR_ITEM_{i+1}", pedido.num_pedido)
                    
                    itens_inseridos += 1
                    logger.debug(f"✅ Item {i+1}/{total_itens} inserido: {item.cod_produto}")
                    
                except Exception as e:
                    logger.error(f"❌ Erro ao inserir item {i+1}/{total_itens} do pedido {pedido.num_pedido}")
                    logger.error(f"Item: {item.cod_produto} | Qtd: {item.quantidade} | Valor: R$ {item.valor_unitario:.2f}")
                    logger.error(f"Erro: {str(e)}")
                    # Continua com próximo item
                    continue
            
            if itens_inseridos == 0:
                raise ValueError(f"Nenhum item válido foi inserido para o pedido {pedido.num_pedido}")
            
            logger.info(f"📦 {itens_inseridos} de {total_itens} itens inseridos com sucesso")
            return itens_inseridos
            
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
            
            params_cabecalho = (num_pedido,)
            self._execute_with_logging(query_cabecalho, params_cabecalho, "BUSCAR_CABECALHO", num_pedido)
            cabecalho = self.cursor.fetchone()
            
            if not cabecalho:
                logger.debug(f"🔍 Pedido {num_pedido} não encontrado")
                return None
            
            # Buscar itens
            query_itens = """
                SELECT CODIGOPRODUTO, QTDEVENDA, VALORVENDA, VALORBRUTO,
                       QTDEBONIFICADA, DESCONTOI, DESCONTOII, VALORVERBA,
                       MSGIMPORTACAO
                FROM T_PEDIDOITEM_SOBEL
                WHERE NUMPEDIDOAFV = ?
            """
            
            params_itens = (num_pedido,)
            self._execute_with_logging(query_itens, params_itens, "BUSCAR_ITENS", num_pedido)
            itens = self.cursor.fetchall()
            
            logger.debug(f"🔍 Pedido {num_pedido} encontrado com {len(itens)} itens")
            
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
            
            params = (data_inicio, data_fim)
            self._execute_with_logging(query, params, "LISTAR_PEDIDOS")
            resultado = self.cursor.fetchall()
            
            logger.debug(f"🔍 Encontrados {len(resultado)} pedidos no período {data_inicio} - {data_fim}")
            return resultado
            
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
            params = ()
            self._execute_with_logging(query, params, "VERIFICAR_COLUNAS_LOG")
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
                    logger.debug(f"📝 Tabela de log não disponível: [{tipo}] {mensagem}")
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
                
                params = tuple(base_values)
                self._execute_with_logging(query, params, "LOG_PROCESSAMENTO")
                self.conn.commit()
                
            except pyodbc.Error as e:
                error_msg = str(e).lower()
                if any(x in error_msg for x in ["invalid object", "table", "não existe", "invalid column"]):
                    logger.debug(f"📝 Tabela de log não disponível: [{tipo}] {mensagem}")
                else:
                    logger.warning(f"⚠️ Erro ao registrar log no banco: {e}")
                    logger.debug(f"📝 Log local: [{tipo}] {mensagem}")
                    
        except Exception as e:
            # Não falhar o processo principal por causa de log
            logger.warning(f"⚠️ Erro no sistema de log: {e}")
            logger.debug(f"📝 Log local: [{tipo}] {mensagem}")

    def get_estatisticas(self) -> dict:
        """Retorna estatísticas básicas dos pedidos"""
        try:
            self._reconnect_if_needed()
            
            stats = {}
            
            # Total de pedidos
            query1 = "SELECT COUNT(*) FROM T_PEDIDO_SOBEL"
            self._execute_with_logging(query1, (), "STATS_TOTAL")
            stats['total_pedidos'] = self.cursor.fetchone()[0]
            
            # Pedidos hoje
            query2 = """
                SELECT COUNT(*) FROM T_PEDIDO_SOBEL 
                WHERE CAST(DATAGRAVACAOACACIA AS DATE) = CAST(GETDATE() AS DATE)
            """
            self._execute_with_logging(query2, (), "STATS_HOJE")
            stats['pedidos_hoje'] = self.cursor.fetchone()[0]
            
            # Valor total hoje
            query3 = """
                SELECT ISNULL(SUM(VALORBRUTO), 0) FROM T_PEDIDO_SOBEL 
                WHERE CAST(DATAGRAVACAOACACIA AS DATE) = CAST(GETDATE() AS DATE)
            """
            self._execute_with_logging(query3, (), "STATS_VALOR")
            stats['valor_hoje'] = float(self.cursor.fetchone()[0])
            
            return stats
            
        except Exception as e:
            logger.error(f"⚠️ Erro ao obter estatísticas: {e}")
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
            logger.debug("🔌 Conexão com banco fechada")
        except Exception as e:
            logger.warning(f"⚠️ Erro ao fechar conexão: {e}")

    def __enter__(self):
        """Context manager - entrada"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager - saída"""
        self.close()
        
        # Se houve exceção, log do erro
        if exc_type is not None:
            logger.error(f"❌ Erro no contexto do repository: {exc_type.__name__}: {exc_val}")
        
        return False  # Não suprimir exceções