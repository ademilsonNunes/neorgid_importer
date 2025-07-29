# utils/logger.py
import os
import logging
from datetime import datetime
from typing import Optional
from enum import Enum

class LogLevel(Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    DEBUG = "DEBUG"

class Logger:
    def __init__(self, log_file: str = "logs/log_pedidos.txt", console_output: bool = True):
        self.log_file = log_file
        self.console_output = console_output
        
        # Criar diretório se não existe
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        # Configurar logging
        self._setup_logging()
    
    def _setup_logging(self):
        """Configura o sistema de logging"""
        self.logger = logging.getLogger('NeogridImporter')
        self.logger.setLevel(logging.DEBUG)
        
        # Limpar handlers existentes
        self.logger.handlers.clear()
        
        # Handler para arquivo
        file_handler = logging.FileHandler(self.log_file, encoding='utf-8')
        file_formatter = logging.Formatter(
            '[%(asctime)s] [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)
        
        # Handler para console (se habilitado)
        if self.console_output:
            console_handler = logging.StreamHandler()
            console_formatter = logging.Formatter('[%(levelname)s] %(message)s')
            console_handler.setFormatter(console_formatter)
            self.logger.addHandler(console_handler)
    
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

    def sql(self, query: str, params=None):
        """Registra a consulta SQL enviada ao banco"""
        if params is not None:
            self.logger.debug("SQL: %s | Params: %s", query.strip(), params)
        else:
            self.logger.debug("SQL: %s", query.strip())
    
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
        except Exception as e:
            self.error(f"Erro ao limpar logs: {e}")
    
    def get_log_stats(self) -> dict:
        """Retorna estatísticas do log atual"""
        try:
            if not os.path.exists(self.log_file):
                return {"total_lines": 0, "info": 0, "warning": 0, "error": 0}
            
            with open(self.log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            stats = {"total_lines": len(lines), "info": 0, "warning": 0, "error": 0}
            
            for line in lines:
                if "[INFO]" in line:
                    stats["info"] += 1
                elif "[WARNING]" in line:
                    stats["warning"] += 1
                elif "[ERROR]" in line:
                    stats["error"] += 1
            
            return stats
            
        except Exception as e:
            self.error(f"Erro ao calcular estatísticas do log: {e}")
            return {"total_lines": 0, "info": 0, "warning": 0, "error": 0}

# Instância global do logger
logger = Logger()
