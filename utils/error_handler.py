# utils/error_handler.py
import sys
import os
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum

class ErrorType(Enum):
    CLIENTE_NAO_ENCONTRADO = "CLIENTE_NAO_ENCONTRADO"
    PRODUTO_NAO_ENCONTRADO = "PRODUTO_NAO_ENCONTRADO"
    ERRO_BANCO_DADOS = "ERRO_BANCO_DADOS"
    ERRO_API = "ERRO_API"
    ERRO_VALIDACAO = "ERRO_VALIDACAO"
    ERRO_PROCESSAMENTO = "ERRO_PROCESSAMENTO"
    PEDIDO_DUPLICADO = "PEDIDO_DUPLICADO"

class NeogridError(Exception):
    """Classe base para erros do sistema Neogrid"""
    def __init__(self, message: str, error_type: ErrorType, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.error_type = error_type
        self.details = details or {}
        self.timestamp = datetime.now()
        super().__init__(self.message)

class ClienteNaoEncontradoError(NeogridError):
    """Erro quando cliente não é encontrado"""
    def __init__(self, cnpj: str, num_pedido: Optional[str] = None):
        details = {"cnpj": cnpj}
        if num_pedido:
            details["num_pedido"] = num_pedido
        super().__init__(
            f"Cliente com CNPJ {cnpj} não encontrado",
            ErrorType.CLIENTE_NAO_ENCONTRADO,
            details
        )

class ProdutoNaoEncontradoError(NeogridError):
    """Erro quando produto não é encontrado"""
    def __init__(self, ean13: str, dun14: str, codprod: str, num_pedido: Optional[str] = None):
        details = {"ean13": ean13, "dun14": dun14, "codprod": codprod}
        if num_pedido:
            details["num_pedido"] = num_pedido
        super().__init__(
            f"Produto não encontrado - EAN13: '{ean13}', DUN14: '{dun14}', CodProd: '{codprod}'",
            ErrorType.PRODUTO_NAO_ENCONTRADO,
            details
        )

class BancoDadosError(NeogridError):
    """Erro relacionado ao banco de dados"""
    def __init__(self, message: str, original_error: Exception, operation: str = ""):
        details = {
            "original_error": str(original_error),
            "operation": operation,
            "error_class": original_error.__class__.__name__
        }
        super().__init__(
            f"Erro no banco de dados: {message}",
            ErrorType.ERRO_BANCO_DADOS,
            details
        )

class APIError(NeogridError):
    """Erro relacionado à API Neogrid"""
    def __init__(self, message: str, status_code: Optional[int] = None, response_text: Optional[str] = None):
        details = {}
        if status_code:
            details["status_code"] = status_code
        if response_text:
            details["response_text"] = response_text
        super().__init__(
            f"Erro na API Neogrid: {message}",
            ErrorType.ERRO_API,
            details
        )

class PedidoDuplicadoError(NeogridError):
    """Erro quando pedido já existe"""
    def __init__(self, num_pedido: str):
        super().__init__(
            f"Pedido {num_pedido} já existe no banco de dados",
            ErrorType.PEDIDO_DUPLICADO,
            {"num_pedido": num_pedido}
        )

class ErrorHandler:
    """Classe para tratamento centralizado de erros"""
    
    @staticmethod
    def handle_database_error(e: Exception, operation: str = "") -> BancoDadosError:
        """Trata erros de banco de dados"""
        return BancoDadosError(str(e), e, operation)
    
    @staticmethod
    def handle_api_error(e: Exception, status_code: Optional[int] = None, response_text: Optional[str] = None) -> APIError:
        """Trata erros de API"""
        return APIError(str(e), status_code, response_text)
    
    @staticmethod
    def log_error(error: NeogridError, logger=None):
        """Log estruturado de erros"""
        error_msg = f"[{error.error_type.value}] {error.message}"
        
        if error.details:
            details_str = " | ".join([f"{k}={v}" for k, v in error.details.items()])
            error_msg += f" | {details_str}"
        
        if logger:
            logger.error(error_msg)
        else:
            print(f"ERROR: {error_msg}")
    
    @staticmethod
    def format_error_for_ui(error: NeogridError) -> str:
        """Formata erro para exibição na UI"""
        if error.error_type == ErrorType.CLIENTE_NAO_ENCONTRADO:
            return f"❌ Cliente não encontrado (CNPJ: {error.details.get('cnpj', 'N/A')})"
        elif error.error_type == ErrorType.PRODUTO_NAO_ENCONTRADO:
            return f"❌ Produto não encontrado (Código: {error.details.get('codprod', 'N/A')})"
        elif error.error_type == ErrorType.PEDIDO_DUPLICADO:
            return f"⚠️ Pedido duplicado ({error.details.get('num_pedido', 'N/A')})"
        elif error.error_type == ErrorType.ERRO_BANCO_DADOS:
            return f"🗄️ Erro no banco de dados: {error.message}"
        elif error.error_type == ErrorType.ERRO_API:
            return f"🌐 Erro na API: {error.message}"
        else:
            return f"❌ {error.message}"

def safe_execute(func, *args, **kwargs):
    """
    Wrapper para execução segura de funções com tratamento de erro
    """
    try:
        return func(*args, **kwargs)
    except NeogridError:
        # Re-raise custom errors
        raise
    except Exception as e:
        # Convert generic exceptions to NeogridError
        raise NeogridError(
            f"Erro inesperado: {str(e)}",
            ErrorType.ERRO_PROCESSAMENTO,
            {"original_error": str(e), "function": func.__name__}
        )