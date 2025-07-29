# utils/logger.py
import os
import logging
from datetime import datetime
from typing import Optional, Any, Dict, List
from enum import Enum

class LogLevel(Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    DEBUG = "DEBUG"
    SQL = "SQL"  # Nível específico para queries SQL

class Logger:
    def __init__(self, log_file: str = "logs/log_pedidos.txt", console_output: bool = True, debug_mode: bool = False):
        self.log_file = log_file
        self.console_output = console_output
        self.debug_mode = debug_mode  # Controla se logs de DEBUG/SQL são exibidos
        
        # Criar diretório se não existe
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        # Configurar logging
        self._setup_logging()
        
        # Buffer para queries SQL (para debug)
        self._sql_buffer = []
        self._max_sql_buffer = 100
    
    def _setup_logging(self):
        """Configura o sistema de logging"""
        self.logger = logging.getLogger('NeogridImporter')
        
        # Configurar nível baseado no modo debug
        if self.debug_mode:
            self.logger.setLevel(logging.DEBUG)
        else:
            self.logger.setLevel(logging.INFO)
        
        # Limpar handlers existentes
        self.logger.handlers.clear()
        
        # Handler para arquivo (sempre inclui DEBUG)
        file_handler = logging.FileHandler(self.log_file, encoding='utf-8')
        file_formatter = logging.Formatter(
            '[%(asctime)s] [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        file_handler.setLevel(logging.DEBUG)  # Arquivo sempre recebe todos os logs
        self.logger.addHandler(file_handler)
        
        # Handler para console (respeitando configurações)
        if self.console_output:
            console_handler = logging.StreamHandler()
            console_formatter = logging.Formatter('[%(levelname)s] %(message)s')
            console_handler.setFormatter(console_formatter)
            
            # Console respeita o modo debug
            if self.debug_mode:
                console_handler.setLevel(logging.DEBUG)
            else:
                console_handler.setLevel(logging.INFO)
                
            self.logger.addHandler(console_handler)
    
    def enable_debug_mode(self):
        """Ativa o modo debug"""
        self.debug_mode = True
        self._setup_logging()
        self.info("🔧 Modo debug ativado")
    
    def disable_debug_mode(self):
        """Desativa o modo debug"""
        self.debug_mode = False
        self._setup_logging()
        self.info("🔧 Modo debug desativado")
    
    def log(self, nivel: LogLevel, mensagem: str, num_pedido: Optional[str] = None, **kwargs):
        """Log genérico com nível especificado"""
        if num_pedido:
            mensagem = f"{mensagem} | Pedido: {num_pedido}"
        
        # Adicionar informações extras se fornecidas
        if kwargs:
            extras = " | ".join([f"{k}={v}" for k, v in kwargs.items()])
            mensagem = f"{mensagem} | {extras}"
        
        if nivel == LogLevel.INFO:
            self.logger.info(mensagem)
        elif nivel == LogLevel.WARNING:
            self.logger.warning(mensagem)
        elif nivel == LogLevel.ERROR:
            self.logger.error(mensagem)
        elif nivel == LogLevel.DEBUG:
            self.logger.debug(mensagem)
        elif nivel == LogLevel.SQL:
            # SQL logs sempre vão para arquivo, console só se debug ativo
            self.logger.debug(f"[SQL] {mensagem}")
    
    def info(self, mensagem: str, num_pedido: Optional[str] = None, **kwargs):
        """Log de informação"""
        self.log(LogLevel.INFO, mensagem, num_pedido, **kwargs)
    
    def warning(self, mensagem: str, num_pedido: Optional[str] = None, **kwargs):
        """Log de aviso"""
        self.log(LogLevel.WARNING, mensagem, num_pedido, **kwargs)
    
    def error(self, mensagem: str, num_pedido: Optional[str] = None, **kwargs):
        """Log de erro"""
        self.log(LogLevel.ERROR, mensagem, num_pedido, **kwargs)
    
    def debug(self, mensagem: str, num_pedido: Optional[str] = None, **kwargs):
        """Log de debug"""
        self.log(LogLevel.DEBUG, mensagem, num_pedido, **kwargs)

    def sql(self, query: str, params=None, operation: str = None):
        """
        Registra query SQL com formatação especial e buffer para debug
        """
        # Limpar query para melhor visualização
        clean_query = ' '.join(query.strip().split())
        
        # Construir mensagem detalhada
        sql_msg = f"Query: {clean_query}"
        
        if params is not None:
            # Formatar parâmetros de forma legível
            if isinstance(params, (list, tuple)):
                params_str = ", ".join([f"'{p}'" if isinstance(p, str) else str(p) for p in params])
            else:
                params_str = str(params)
            sql_msg += f" | Params: [{params_str}]"
        
        if operation:
            sql_msg = f"[{operation}] {sql_msg}"
        
        # Log da query
        self.log(LogLevel.SQL, sql_msg)
        
        # Adicionar ao buffer SQL para debug
        sql_entry = {
            'timestamp': datetime.now(),
            'operation': operation or 'UNKNOWN',
            'query': clean_query,
            'params': params
        }
        
        self._sql_buffer.append(sql_entry)
        
        # Manter buffer dentro do limite
        if len(self._sql_buffer) > self._max_sql_buffer:
            self._sql_buffer.pop(0)
    
    def sql_error(self, query: str, params: Any, error: Exception, operation: str = None):
        """
        Log específico para erros SQL com informações detalhadas
        """
        clean_query = ' '.join(query.strip().split())
        
        error_msg = f"❌ ERRO SQL"
        if operation:
            error_msg += f" [{operation}]"
        
        error_msg += f": {str(error)}"
        
        self.error(error_msg)
        self.error(f"Query que falhou: {clean_query}")
        
        if params is not None:
            if isinstance(params, (list, tuple)):
                params_str = ", ".join([f"'{p}'" if isinstance(p, str) else str(p) for p in params])
            else:
                params_str = str(params)
            self.error(f"Parâmetros: [{params_str}]")
        
        # Adicionar erro ao buffer SQL
        sql_entry = {
            'timestamp': datetime.now(),
            'operation': operation or 'UNKNOWN',
            'query': clean_query,
            'params': params,
            'error': str(error),
            'error_type': error.__class__.__name__
        }
        
        self._sql_buffer.append(sql_entry)
        if len(self._sql_buffer) > self._max_sql_buffer:
            self._sql_buffer.pop(0)
    
    def get_recent_sql_queries(self, limit: int = 10) -> List[Dict]:
        """
        Retorna as queries SQL mais recentes do buffer
        """
        return self._sql_buffer[-limit:] if limit <= len(self._sql_buffer) else self._sql_buffer.copy()
    
    def get_failed_sql_queries(self, limit: int = 10) -> List[Dict]:
        """
        Retorna apenas as queries que falharam
        """
        failed_queries = [entry for entry in self._sql_buffer if 'error' in entry]
        return failed_queries[-limit:] if limit <= len(failed_queries) else failed_queries
    
    def clear_sql_buffer(self):
        """Limpa o buffer de queries SQL"""
        self._sql_buffer.clear()
        self.debug("🧹 Buffer de queries SQL limpo")
    
    def export_sql_debug(self, filepath: str = None) -> str:
        """
        Exporta informações de debug SQL para arquivo
        """
        if not filepath:
            filepath = f"logs/sql_debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"=== DEBUG SQL - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n\n")
                f.write(f"Total de queries no buffer: {len(self._sql_buffer)}\n")
                
                failed_queries = [entry for entry in self._sql_buffer if 'error' in entry]
                f.write(f"Queries com erro: {len(failed_queries)}\n\n")
                
                for i, entry in enumerate(self._sql_buffer, 1):
                    f.write(f"--- Query #{i} ---\n")
                    f.write(f"Timestamp: {entry['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"Operação: {entry['operation']}\n")
                    f.write(f"Query: {entry['query']}\n")
                    
                    if entry['params']:
                        f.write(f"Parâmetros: {entry['params']}\n")
                    
                    if 'error' in entry:
                        f.write(f"ERRO: {entry['error']}\n")
                        f.write(f"Tipo do erro: {entry['error_type']}\n")
                    
                    f.write("\n")
            
            self.info(f"📄 Debug SQL exportado para: {filepath}")
            return filepath
            
        except Exception as e:
            self.error(f"Erro ao exportar debug SQL: {e}")
            return None
    
    def log_inicio_processamento(self, total_documentos: int):
        """Log específico para início de processamento"""
        self.info(f"🚀 Iniciando processamento de {total_documentos} documento(s)")
    
    def log_fim_processamento(self, sucessos: int, duplicados: int, erros: int):
        """Log específico para fim de processamento"""
        self.info(
            f"🏁 Processamento concluído",
            sucessos=sucessos,
            duplicados=duplicados,
            erros=erros
        )
    
    def log_pedido_processado(self, num_pedido: str, cliente: str, itens: int, valor: float):
        """Log específico para pedido processado com sucesso"""
        self.info(
            f"✅ Pedido processado com sucesso",
            num_pedido=num_pedido,
            cliente=cliente,
            itens=itens,
            valor=f"R$ {valor:.2f}"
        )
    
    def log_pedido_duplicado(self, num_pedido: str):
        """Log específico para pedido duplicado"""
        self.warning(f"⚠️ Pedido já existe no banco", num_pedido)
    
    def log_erro_api(self, erro: str):
        """Log específico para erro na API"""
        self.error(f"🌐 Erro na API Neogrid: {erro}")
    
    def log_erro_banco(self, erro: str, num_pedido: Optional[str] = None):
        """Log específico para erro no banco"""
        self.error(f"🗄️ Erro no banco de dados: {erro}", num_pedido)
    
    def log_cliente_nao_encontrado(self, cnpj: str, num_pedido: Optional[str] = None):
        """Log específico para cliente não encontrado"""
        self.error(f"👤 Cliente não encontrado", num_pedido, cnpj=cnpj)
    
    def log_produto_nao_encontrado(self, ean13: str, dun14: str, codprod: str, num_pedido: Optional[str] = None):
        """Log específico para produto não encontrado"""
        self.error(
            f"📦 Produto não encontrado",
            num_pedido,
            ean13=ean13,
            dun14=dun14,
            codprod=codprod
        )
    
    def get_log_lines(self, num_lines: int = 50) -> list:
        """Retorna as últimas N linhas do log"""
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                return lines[-num_lines:] if len(lines) > num_lines else lines
        except FileNotFoundError:
            return []
        except Exception as e:
            self.error(f"Erro ao ler arquivo de log: {e}")
            return []
    
    def clear_logs(self):
        """Limpa o arquivo de log"""
        try:
            if os.path.exists(self.log_file):
                os.remove(self.log_file)
                self.info("📝 Arquivo de log limpo")
                # Limpar buffer SQL também
                self.clear_sql_buffer()
        except Exception as e:
            self.error(f"Erro ao limpar logs: {e}")
    
    def get_log_stats(self) -> dict:
        """Retorna estatísticas do log atual"""
        try:
            if not os.path.exists(self.log_file):
                return {
                    "total_lines": 0, 
                    "info": 0, 
                    "warning": 0, 
                    "error": 0, 
                    "debug": 0, 
                    "sql": 0,
                    "sql_errors": len(self.get_failed_sql_queries())
                }
            
            with open(self.log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            stats = {
                "total_lines": len(lines), 
                "info": 0, 
                "warning": 0, 
                "error": 0, 
                "debug": 0, 
                "sql": 0,
                "sql_errors": len(self.get_failed_sql_queries())
            }
            
            for line in lines:
                if "[INFO]" in line:
                    stats["info"] += 1
                elif "[WARNING]" in line:
                    stats["warning"] += 1
                elif "[ERROR]" in line:
                    stats["error"] += 1
                elif "[DEBUG]" in line:
                    if "[SQL]" in line:
                        stats["sql"] += 1
                    else:
                        stats["debug"] += 1
            
            return stats
            
        except Exception as e:
            self.error(f"Erro ao calcular estatísticas do log: {e}")
            return {"total_lines": 0, "info": 0, "warning": 0, "error": 0, "debug": 0, "sql": 0, "sql_errors": 0}

    def log_performance(self, operation: str, duration_seconds: float, details: Dict[str, Any] = None):
        """Log específico para métricas de performance"""
        perf_msg = f"⏱️ Performance [{operation}]: {duration_seconds:.3f}s"
        
        if details:
            detail_items = []
            for key, value in details.items():
                detail_items.append(f"{key}={value}")
            perf_msg += f" | {' | '.join(detail_items)}"
        
        self.info(perf_msg)

# Instância global do logger
logger = Logger()

# Função para ativar/desativar debug mode facilmente
def enable_debug_logging():
    """Ativa logs de debug globalmente"""
    global logger
    logger.enable_debug_mode()

def disable_debug_logging():
    """Desativa logs de debug globalmente"""
    global logger
    logger.disable_debug_mode()

def get_sql_debug_info():
    """Retorna informações de debug SQL"""
    return {
        'recent_queries': logger.get_recent_sql_queries(20),
        'failed_queries': logger.get_failed_sql_queries(10),
        'buffer_size': len(logger._sql_buffer)
    }