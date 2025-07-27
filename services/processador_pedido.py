import sys
import os
# Adiciona o diretório raiz do projeto ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from typing import Any, Dict
from models.pedido_sobel import PedidoSobel
from services.processador_pedido_item import ProcessadorPedidoItem
from services.validador_cliente import ValidadorCliente
from utils.error_handler import ClienteNaoEncontradoError, NeogridError, ErrorType


class ProcessadorPedido:
    def __init__(self, validador_cliente: ValidadorCliente, processador_item: ProcessadorPedidoItem):
        self.validador_cliente = validador_cliente
        self.processador_item = processador_item

    def processar(self, pedido_json: Dict[str, Any]) -> PedidoSobel:
        """
        Processa um pedido completo a partir do JSON recebido da API Neogrid.
        Valida o cliente e os itens, retornando um objeto PedidoSobel pronto para ser gravado.
        """
        num_pedido = pedido_json.get("num_pedido", "N/A")
        cnpj = pedido_json.get("cnpj", "")
        
        # Validar se CNPJ foi fornecido
        if not cnpj or cnpj.strip() == "":
            raise NeogridError(
                f"CNPJ não informado no pedido {num_pedido}", 
                ErrorType.ERRO_VALIDACAO,
                {"num_pedido": num_pedido}
            )
        
        # Validar cliente
        try:
            cliente = self.validador_cliente.validar_cliente(cnpj)
            if not cliente:
                raise ClienteNaoEncontradoError(cnpj, num_pedido)
        except Exception as e:
            if isinstance(e, ClienteNaoEncontradoError):
                raise
            raise NeogridError(
                f"Erro ao validar cliente: {str(e)}", 
                ErrorType.ERRO_VALIDACAO,
                {"cnpj": cnpj, "num_pedido": num_pedido, "original_error": str(e)}
            )

        # Processar itens
        itens_json = pedido_json.get("itens", [])
        if not itens_json:
            raise NeogridError(
                f"Pedido {num_pedido} não possui itens",
                ErrorType.ERRO_VALIDACAO,
                {"num_pedido": num_pedido}
            )
        
        itens_processados = []
        erros_itens = []

        for i, item in enumerate(itens_json):
            try:
                item_processado = self.processador_item.processar_item(item)
                itens_processados.append(item_processado)
            except Exception as e:
                erro_msg = f"Item {i+1}: {str(e)}"
                erros_itens.append(erro_msg)
                
                # Log do erro mas continua processando outros itens
                print(f"Erro no item {i+1} do pedido {num_pedido}: {e}")

        # Se nenhum item foi processado com sucesso, falha
        if not itens_processados:
            raise NeogridError(
                f"Nenhum item válido encontrado no pedido {num_pedido}. Erros: {'; '.join(erros_itens)}",
                ErrorType.ERRO_VALIDACAO,
                {"num_pedido": num_pedido, "erros_itens": erros_itens}
            )

        # Se alguns itens falharam, registra aviso mas continua
        if erros_itens:
            print(f"⚠️ Pedido {num_pedido}: {len(erros_itens)} itens com erro, {len(itens_processados)} itens processados")

        try:
            return PedidoSobel.from_json(pedido_json, cliente, itens_processados)
        except Exception as e:
            raise NeogridError(
                f"Erro ao criar objeto PedidoSobel: {str(e)}",
                ErrorType.ERRO_PROCESSAMENTO,
                {"num_pedido": num_pedido, "original_error": str(e)}
            )

    def validar_dados_basicos(self, pedido_json: Dict[str, Any]) -> bool:
        """
        Valida se o JSON do pedido possui os campos mínimos necessários
        """
        campos_obrigatorios = ["num_pedido", "data_pedido", "cnpj", "itens"]
        
        for campo in campos_obrigatorios:
            if campo not in pedido_json or not pedido_json[campo]:
                raise NeogridError(
                    f"Campo obrigatório '{campo}' não encontrado ou vazio",
                    ErrorType.ERRO_VALIDACAO,
                    {"campo_faltante": campo, "pedido_data": pedido_json}
                )
        
        return True

    def processar_com_validacao(self, pedido_json: Dict[str, Any]) -> PedidoSobel:
        """
        Processa pedido com validação prévia dos dados básicos
        """
        # Validar dados básicos primeiro
        self.validar_dados_basicos(pedido_json)
        
        # Processar normalmente
        return self.processar(pedido_json)