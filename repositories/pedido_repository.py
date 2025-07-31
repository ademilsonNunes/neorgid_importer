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

    def pedido_existe(self, pedido: PedidoSobel) -> bool:
   
        try:
            self._reconnect_if_needed()
    
            if not all([pedido.num_pedido_afv, pedido.data_pedido, pedido.hora_inicio, pedido.codigo_cliente]):
                logger.warning(f"⚠️ Verificação de duplicidade incompleta: campos obrigatórios ausentes")
                return False
    
            query = """
                SELECT 1
                FROM T_PEDIDO_SOBEL
                WHERE NUMPEDIDOAFV = ?
                  AND DATAPEDIDO = ?
                  AND HORAINICIAL = ?
                  AND CODIGOCLIENTE = ?
            """
            params = (
                str(pedido.num_pedido_afv),
                self._tratar_data(pedido.data_pedido),
                pedido.hora_inicio,
                pedido.codigo_cliente,
            )
    
            logger.debug(f"🔍 Verificando existência do pedido único:")
            logger.debug(f"  NUMPEDIDOAFV: {pedido.num_pedido_afv}")
            logger.debug(f"  DATAPEDIDO: {pedido.data_pedido}")
            logger.debug(f"  HORAINICIAL: {pedido.hora_inicio}")
            logger.debug(f"  CODIGOCLIENTE: {pedido.codigo_cliente}")
    
            self._execute_with_logging(query, params, "VERIFICAR_EXISTENCIA", str(pedido.num_pedido_afv))
            result = self.cursor.fetchone()
            existe = result is not None
    
            if existe:
                logger.info(f"📋 Pedido já existe no banco com base na chave única")
            else:
                logger.debug(f"📋 Pedido ainda não existe no banco")
    
            return existe
    
        except pyodbc.Error as e:
            raise BancoDadosError(
                f"Erro ao verificar existência do pedido {pedido.num_pedido_afv}: {str(e)}",
                e,
                "verificar_existencia"
            )
        except Exception as e:
            raise BancoDadosError(
                f"Erro inesperado ao verificar pedido {pedido.num_pedido_afv}: {str(e)}",
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
        
        if not all([pedido.num_pedido_afv, pedido.data_pedido, pedido.hora_inicio, pedido.codigo_cliente]):
            raise BancoDadosError("Pedido inválido para inserção", ValueError("Campos obrigatórios ausentes"), "validação")
        # Log início da operação
        logger.info(f"💾 Iniciando inserção do pedido {pedido.num_pedido}")
        logger.debug(f"Cliente: {pedido.codigo_cliente} | Itens: {len(pedido.itens)} | Valor: R$ {pedido.valor_total:.2f}")
        
        # Verificar se já existe
        #if self.pedido_existe(pedido.num_pedido):
        if self.pedido_existe(pedido):
            logger.warning(f"⚠️ Pedido {pedido.num_pedido} ja existe no banco de dados")
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

     # Correção da indentação e melhorias no método _inserir_cabecalho_pedido
     # Este método deve estar dentro da classe PedidoRepository

    # Correção da indentação e melhorias no método _inserir_cabecalho_pedido
# Este método deve estar dentro da classe PedidoRepository

    def _inserir_cabecalho_pedido(self, pedido: PedidoSobel):
        """
        Insere o cabeçalho do pedido na tabela T_PEDIDO_SOBEL com tratamento completo de tipos.
        Compatível com os valores de exemplo da query fornecida.
        """
        try:
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

            # Preparar valores com tratamento robusto e valores padrão baseados na query fornecida
            qtde_itens_valor = None
            if getattr(pedido, 'quantidade_itens', None) is not None:
                qtde_itens_valor = int(pedido.quantidade_itens)
            elif hasattr(pedido, 'itens'):
                qtde_itens_valor = len(pedido.itens)

            volume_valor = int(pedido.volume) if pedido.volume is not None else None

            valores = (
                int(pedido.num_pedido),                           # NUMPEDIDO
                None,                                                           # NUMPEDIDOSOBEL
                str(pedido.loja_cliente or '01').strip(),                       # LOJACLIENTE (padrão '01')
                str(pedido.num_pedido_afv or pedido.num_pedido or '').strip(),  # NUMPEDIDOAFV
                self._tratar_data(pedido.data_pedido),                          # DATAPEDIDO
                str(pedido.hora_inicio or '00:00').strip(),                     # HORAINICIAL
                str(pedido.hora_fim or '').strip() if pedido.hora_fim else None, # HORAFINAL
                self._tratar_data(pedido.data_entrega),                         # DATAENTREGA
                str(pedido.codigo_cliente or '').strip(),                       # CODIGOCLIENTE
                str(pedido.codigo_tipo_pedido or 'N').strip(),                  # CODIGOTIPOPEDIDO (padrão 'N')
                str(pedido.codigo_cond_pagto or '055').strip(),                 # CODIGOCONDPAGTO (padrão '055')
                str(pedido.codigo_nome_endereco or 'E').strip(),                # CODIGONOMEENDERECO (padrão 'E')
                str(pedido.codigo_unidade_faturamento or '01').strip(),         # CODIGOUNIDFAT (padrão '01')
                str(pedido.codigo_tabela_preco or '038').strip(),               # CODIGOTABPRECO (padrão '038')
                str(pedido.ordem_compra or '').strip(),                         # ORDEMCOMPRA
                str(pedido.observacao_1 or '').strip(),                      # OBSERVACAOI (padrão 'CIF')
                str(pedido.observacao_2 or '').strip() if pedido.observacao_2 else None, # OBSERVACAOII
                self._tratar_valor_decimal(pedido.valor_liquido),               # VALORLIQUIDO
                self._tratar_valor_decimal(pedido.valor_bruto),                 # VALORBRUTO
                str(pedido.codigo_motivo_tipo_pedido or '').strip() if pedido.codigo_motivo_tipo_pedido else None, # CODIGOMOTIVOTIPOPED
                str(pedido.codigo_vendedor_resp or '000559').strip(),           # CODIGOVENDEDORESP (padrão '000559')
                self._tratar_data(pedido.data_entrega_fim or pedido.data_entrega), # CESP_DATAENTREGAFIM
                str(pedido.num_pedido_assoc or '').strip() if pedido.num_pedido_assoc else None, # CESP_NUMPEDIDOASSOC
                self._tratar_data_hora(pedido.data_gravacao_acacia or datetime.now()), # DATAGRAVACAOACACIA
                self._tratar_data_hora(pedido.data_integracao_erp) if pedido.data_integracao_erp else None, # DATAINTEGRACAOERP
                qtde_itens_valor,
                str(pedido.mensagem_importacao or '').strip() if pedido.mensagem_importacao else None,
                volume_valor                                         # VOLUME
            )

            # Log dos valores para debug (similar ao exemplo da query)
            logger.debug(f"💾 Valores do cabeçalho do pedido {pedido.num_pedido}:")
            logger.debug(f"  NUMPEDIDO: {valores[0]}")
            logger.debug(f"  LOJACLIENTE: {valores[2]}")
            logger.debug(f"  NUMPEDIDOAFV: {valores[3]}")
            logger.debug(f"  DATAPEDIDO: {valores[4]}")
            logger.debug(f"  CODIGOCLIENTE: {valores[8]}")
            logger.debug(f"  VALORLIQUIDO: {valores[17]}")
            logger.debug(f"  VALORBRUTO: {valores[18]}")

            # Executar query
            self._execute_with_logging(query, valores, "INSERIR_CABECALHO", str(pedido.num_pedido_afv))

        except pyodbc.Error as e:
            raise BancoDadosError(
                f"Erro ao inserir cabeçalho do pedido {pedido.num_pedido}: {str(e)}",
                e,
                "inserir_cabecalho"
            )
        except Exception as e:
            raise BancoDadosError(
                f"Erro inesperado ao inserir cabeçalho do pedido {pedido.num_pedido}: {str(e)}",
                e,
                "inserir_cabecalho"
            )

    def _get_next_numitem(self) -> int:
        """Obtém o próximo valor de ``NUMITEM`` de forma segura."""
        query = (
            "SELECT ISNULL(MAX(NUMITEM), 0) + 1 "
            "FROM T_PEDIDOITEM_SOBEL WITH (TABLOCKX, HOLDLOCK)"
        )
        self._execute_with_logging(query, (), "NEXT_NUMITEM")
        result = self.cursor.fetchone()
        return int(result[0] or 1)

    def _inserir_itens_pedido(self, pedido: PedidoSobel) -> int:
        """Insere os itens do pedido na tabela ``T_PEDIDOITEM_SOBEL`` evitando duplicidade."""
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

            start_idx = self._get_next_numitem()

            count = 0
            for offset, item in enumerate(pedido.itens):
                valores = (
                    int(pedido.num_pedido),
                    start_idx + offset,
                    str(pedido.num_pedido_afv or pedido.num_pedido or "").strip(),
                    self._tratar_data(pedido.data_pedido),
                    str(pedido.hora_inicio or "00:00").strip(),
                    str(pedido.codigo_cliente or "").strip(),
                    str(item.cod_produto).strip(),
                    float(item.quantidade),
                    float(getattr(item, "qtde_bonificada", 0) or 0),
                    self._tratar_valor_decimal(item.valor_unitario),
                    self._tratar_valor_decimal(getattr(item, "valor_bruto", item.valor_total)),
                    self._tratar_valor_decimal(getattr(item, "desconto_i", 0)),
                    self._tratar_valor_decimal(getattr(item, "desconto_ii", 0)),
                    self._tratar_valor_decimal(getattr(item, "valor_verba", 0)),
                    str(getattr(item, "codigo_vendedor_resp", pedido.codigo_vendedor_resp or "")).strip() or None,
                    str(getattr(item, "msg_importacao", "") or "").strip() or None,
                )

                self._execute_with_logging(query, valores, "INSERIR_ITENS", str(pedido.num_pedido_afv))
                count += 1

            return count

        except pyodbc.Error as e:
            raise BancoDadosError(
                f"Erro ao inserir itens do pedido {pedido.num_pedido}: {str(e)}",
                e,
                "inserir_itens"
            )
        except Exception as e:
            raise BancoDadosError(
                f"Erro inesperado ao inserir itens do pedido {pedido.num_pedido}: {str(e)}",
                e,
                "inserir_itens"
            )

    def _tratar_data(self, data) -> datetime:
        """
        Trata diferentes tipos de data e converte para datetime.
        Compatível com CONVERT(datetime, '2025-05-15', 120) do SQL Server.
        """
        if data is None:
            return None
        
        if isinstance(data, datetime):
            return data
        elif isinstance(data, str):
            try:
                # Tenta diferentes formatos de data
                formatos = ['%Y-%m-%d', '%d/%m/%Y', '%Y-%m-%d %H:%M:%S']
                for formato in formatos:
                    try:
                        return datetime.strptime(data, formato)
                    except ValueError:
                        continue
                raise ValueError(f"Formato de data não reconhecido: {data}")
            except Exception as e:
                logger.warning(f"⚠️ Erro ao converter data '{data}': {e}")
                return None
        else:
            return data

    def _tratar_data_hora(self, data_hora) -> datetime:
        """
        Trata datetime incluindo hora.
        Se não houver hora, usa 00:00:00.
        """
        if data_hora is None:
            return None
        
        if isinstance(data_hora, datetime):
            return data_hora
        elif isinstance(data_hora, str):
            try:
                # Se tem formato completo de data/hora
                if ' ' in data_hora:
                    return datetime.strptime(data_hora, '%Y-%m-%d %H:%M:%S')
                else:
                    # Se é só data, adiciona hora 00:00:00
                    data = datetime.strptime(data_hora, '%Y-%m-%d')
                    return data.replace(hour=0, minute=0, second=0)
            except Exception as e:
                logger.warning(f"⚠️ Erro ao converter data/hora '{data_hora}': {e}")
                return None
        else:
            return data_hora

    def _tratar_valor_decimal(self, valor):
        """
        Trata valores decimais com 2 casas decimais.
        Se nenhum valor for fornecido, retorna ``None`` para que o banco
        receba ``NULL`` em vez de ``0``.
        Compatível com valores como ``11709.54`` da query de exemplo.
        """
        if valor is None:
            return None
        
        try:
            if isinstance(valor, str):
                # Remove espaços e vírgulas se houver
                valor = valor.replace(',', '.').replace(' ', '')
                return round(float(valor), 2)
            else:
                return round(float(valor), 2)
        except (ValueError, TypeError) as e:
            logger.warning(f"⚠️ Erro ao converter valor '{valor}': {e}")
            return None

    def inserir_pedido_exemplo(self) -> bool:
        """
        Método de exemplo para inserir o pedido teste
        """
        try:
            # Criar um objeto PedidoSobel com os valores da query de exemplo
            from models.pedido_sobel import PedidoSobel
            
            pedido_exemplo = PedidoSobel()
            pedido_exemplo.num_pedido = '5026396'
            pedido_exemplo.num_pedido_afv = '5026396'
            pedido_exemplo.loja_cliente = '01'
            pedido_exemplo.data_pedido = datetime(2025, 5, 15)
            pedido_exemplo.hora_inicio = '18:47'
            pedido_exemplo.data_entrega = datetime(2025, 5, 31)
            pedido_exemplo.codigo_cliente = '256292'
            pedido_exemplo.codigo_tipo_pedido = 'N'
            pedido_exemplo.codigo_cond_pagto = '055'
            pedido_exemplo.codigo_nome_endereco = 'E'
            pedido_exemplo.codigo_unidade_faturamento = '01'
            pedido_exemplo.codigo_tabela_preco = '038'
            pedido_exemplo.ordem_compra = ''
            pedido_exemplo.observacao_1 = 'CIF'
            pedido_exemplo.valor_liquido = 11709.54
            pedido_exemplo.valor_bruto = 11709.54
            pedido_exemplo.codigo_vendedor_resp = '000559'
            pedido_exemplo.data_entrega_fim = datetime(2025, 5, 31)
            pedido_exemplo.data_gravacao_acacia = datetime(2025, 7, 29, 18, 51, 44)
            pedido_exemplo.quantidade_itens = 8
            pedido_exemplo.volume = 0
            pedido_exemplo.itens = []  # Lista vazia para este exemplo
            
            logger.info("🧪 Inserindo pedido de exemplo baseado na query fornecida...")
            
            # Usar o método existente de inserção
            return self.inserir_pedido(pedido_exemplo)
            
        except Exception as e:
            logger.error(f"❌ Erro ao inserir pedido de exemplo: {e}")
            raise BancoDadosError(f"Erro ao inserir pedido de exemplo: {str(e)}", e, "inserir_exemplo")

    def _tratar_data(self, data) -> datetime:
        """
        Trata diferentes tipos de data e converte para datetime.
        Compatível com CONVERT(datetime, '2025-05-15', 120) do SQL Server.
        """
        if data is None:
            return None
        
        if isinstance(data, datetime):
            return data
        elif isinstance(data, str):
            try:
                # Tenta diferentes formatos de data
                formatos = ['%Y-%m-%d', '%d/%m/%Y', '%Y-%m-%d %H:%M:%S']
                for formato in formatos:
                    try:
                        return datetime.strptime(data, formato)
                    except ValueError:
                        continue
                raise ValueError(f"Formato de data não reconhecido: {data}")
            except Exception as e:
                logger.warning(f"⚠️ Erro ao converter data '{data}': {e}")
                return None
        else:
            return data

    def _tratar_data_hora(self, data_hora) -> datetime:
        """
        Trata datetime incluindo hora.
        Se não houver hora, usa 00:00:00.
        """
        if data_hora is None:
            return None
        
        if isinstance(data_hora, datetime):
            return data_hora
        elif isinstance(data_hora, str):
            try:
                # Se tem formato completo de data/hora
                if ' ' in data_hora:
                    return datetime.strptime(data_hora, '%Y-%m-%d %H:%M:%S')
                else:
                    # Se é só data, adiciona hora 00:00:00
                    data = datetime.strptime(data_hora, '%Y-%m-%d')
                    return data.replace(hour=0, minute=0, second=0)
            except Exception as e:
                logger.warning(f"⚠️ Erro ao converter data/hora '{data_hora}': {e}")
                return None
        else:
            return data_hora

    def _tratar_valor_decimal(self, valor):
        """
        Trata valores decimais com 2 casas decimais.
        Se ``valor`` for ``None`` ou inválido, retorna ``None`` para que o banco
        receba ``NULL``.
        Compatível com valores como ``11709.54``.
        """
        if valor is None:
            return None
        
        try:
            if isinstance(valor, str):
                # Remove espaços e vírgulas se houver
                valor = valor.replace(',', '.').replace(' ', '')
                return round(float(valor), 2)
            else:
                return round(float(valor), 2)
        except (ValueError, TypeError) as e:
            logger.warning(f"⚠️ Erro ao converter valor '{valor}': {e}")
            return None

    def inserir_pedido_exemplo(self) -> bool:
        """
        Método de exemplo para inserir o pedido específico da query fornecida.
        Útil para testes e validação.
        """
        try:
            # Criar um objeto PedidoSobel com os valores da query de exemplo
            from models.pedido_sobel import PedidoSobel
            
            pedido_exemplo = PedidoSobel()
            pedido_exemplo.num_pedido = '5026396'
            pedido_exemplo.num_pedido_afv = '5026396'
            pedido_exemplo.loja_cliente = '01'
            pedido_exemplo.data_pedido = datetime(2025, 5, 15)
            pedido_exemplo.hora_inicio = '18:47'
            pedido_exemplo.data_entrega = datetime(2025, 5, 31)
            pedido_exemplo.codigo_cliente = '256292'
            pedido_exemplo.codigo_tipo_pedido = 'N'
            pedido_exemplo.codigo_cond_pagto = '055'
            pedido_exemplo.codigo_nome_endereco = 'E'
            pedido_exemplo.codigo_unidade_faturamento = '01'
            pedido_exemplo.codigo_tabela_preco = '038'
            pedido_exemplo.ordem_compra = ''
            pedido_exemplo.observacao_1 = 'CIF'
            pedido_exemplo.valor_liquido = 11709.54
            pedido_exemplo.valor_bruto = 11709.54
            pedido_exemplo.codigo_vendedor_resp = '000559'
            pedido_exemplo.data_entrega_fim = datetime(2025, 5, 31)
            pedido_exemplo.data_gravacao_acacia = datetime(2025, 7, 29, 18, 51, 44)
            pedido_exemplo.quantidade_itens = 8
            pedido_exemplo.volume = 0
            pedido_exemplo.itens = []  # Lista vazia para este exemplo
            
            logger.info("🧪 Inserindo pedido de exemplo baseado na query fornecida...")
            
            # Usar o método existente de inserção
            return self.inserir_pedido(pedido_exemplo)
            
        except Exception as e:
            logger.error(f"❌ Erro ao inserir pedido de exemplo: {e}")
            raise BancoDadosError(f"Erro ao inserir pedido de exemplo: {str(e)}", e, "inserir_exemplo")

    def buscar_pedido(self, num_pedido: str) -> dict:
        """Busca um pedido específico com seus itens"""
        if not num_pedido:
            return None
            
        try:
            self._reconnect_if_needed()
            
            # Buscar cabeçalho
            query_cabecalho = """
                SELECT NUMPEDIDOSOBEL, 
                       CODIGOCLIENTE, 
                       DATAPEDIDO, 
                       DATAENTREGA,
                       QTDEITENS, 
                       VALORBRUTO, 
                       OBSERVACAOI, 
                       DATAGRAVACAOACACIA
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
                SELECT CODIGOPRODUTO, 
                       QTDEVENDA, 
                       VALORVENDA, 
                       VALORBRUTO,
                       QTDEBONIFICADA, 
                       DESCONTOI, 
                       DESCONTOII, 
                       VALORVERBA,
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
                SELECT NUMPEDIDOSOBEL, 
                       CODIGOCLIENTE, 
                       DATAPEDIDO,
                       QTDEITENS, 
                       VALORBRUTO, 
                       DATAGRAVACAOACACIA
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