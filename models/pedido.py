# models/pedido.py
import sys
import os
# Adiciona o diretório raiz do projeto ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from typing import List, Optional
from datetime import datetime
from decimal import Decimal
from utils.helpers import (
    converter_valor_neogrid, converter_quantidade_neogrid, 
    converter_data_neogrid, limpar_string_neogrid, 
    converter_percentual_neogrid, extrair_cnpj_limpo
)

class ItemPedido:
    def __init__(self, item_data: dict):
        """
        Inicializa item do pedido a partir dos dados da Neogrid
        """
        # Dados básicos do produto
        self.numero_sequencial = limpar_string_neogrid(item_data.get("numeroSequencialItem", ""))
        self.codigo_produto = limpar_string_neogrid(item_data.get("codigoProduto", ""))
        self.descricao_produto = limpar_string_neogrid(item_data.get("descricaoProduto", ""))
        self.referencia_produto = limpar_string_neogrid(item_data.get("referenciaProduto", ""))
        
        # Quantidades
        self.quantidade = converter_quantidade_neogrid(item_data.get("quantidadePedida", "0"))
        self.quantidade_bonificada = converter_quantidade_neogrid(item_data.get("quantidadeBonificada", "0"))
        self.quantidade_troca = converter_quantidade_neogrid(item_data.get("quantidadeTroca", "0"))
        
        # Valores unitários
        self.preco_bruto_unitario = converter_valor_neogrid(item_data.get("precoBrutoUnitario", "0"))
        self.preco_liquido_unitario = converter_valor_neogrid(item_data.get("precoLiquidoUnitario", "0"))
        
        # Valores totais
        self.valor_bruto_item = converter_valor_neogrid(item_data.get("valorBrutoItem", "0"))
        self.valor_liquido_item = converter_valor_neogrid(item_data.get("valorLiquidoItem", "0"))
        
        # Descontos
        self.valor_desconto_comercial = converter_valor_neogrid(item_data.get("valorUnitarioDescontoComercial", "0"))
        self.percentual_desconto_comercial = converter_percentual_neogrid(item_data.get("percentualDescontoComercial", "0"))
        
        # IPI
        self.valor_ipi_unitario = converter_valor_neogrid(item_data.get("valorUnitarioIPI", "0"))
        self.aliquota_ipi = converter_percentual_neogrid(item_data.get("aliquotaIPI", "0"))
        
        # Embalagem e unidade
        self.tipo_embalagem = limpar_string_neogrid(item_data.get("tipoEmbalagem", ""))
        self.numero_embalagens = int(item_data.get("numeroEmbalagens", "0"))
        self.numero_unidades_embalagem = int(item_data.get("numeroUnidadesEmbalagem", "0"))
        self.unidade_medida = limpar_string_neogrid(item_data.get("unidadeMedida", ""))
        
        # Outros valores
        self.valor_frete_unitario = converter_valor_neogrid(item_data.get("valorUnitarioFrete", "0"))
        self.valor_despesa_acessoria_tributada = converter_valor_neogrid(item_data.get("valorUnitarioDespesaAcessoriaTributada", "0"))
        self.valor_despesa_acessoria_nao_tributada = converter_valor_neogrid(item_data.get("valorUnitarioDespesaAcessoriaNaoTributada", "0"))

    @property
    def valor_total(self) -> Decimal:
        """Retorna o valor total do item (liquido)"""
        return self.valor_liquido_item

    @property
    def preco_unitario(self) -> Decimal:
        """Retorna o preço unitário (liquido)"""
        return self.preco_liquido_unitario

    def __repr__(self):
        return f"<ItemPedido {self.codigo_produto} - {self.quantidade} x {self.preco_unitario}>"


class Pedido:
    def __init__(self, raw_data: dict):
        """
        Inicializa pedido a partir da estrutura completa da Neogrid
        """
        # Verificar se é a estrutura completa do documento
        if "order" in raw_data:
            order = raw_data["order"]
        else:
            # Assume que já foi passado apenas o order
            order = raw_data
        
        cabecalho = order["cabecalho"]
        pagamento = order["pagamento"]
        sumario = order["sumario"]
        itens_data = order["itens"]["item"]
        desconto = order.get("desconto", {})
        
        # Dados básicos do pedido
        self.numero_pedido = limpar_string_neogrid(cabecalho["numeroPedidoComprador"])
        self.numero_pedido_emissor = limpar_string_neogrid(cabecalho.get("numeroPedidoEmissor", ""))
        self.tipo_pedido = limpar_string_neogrid(cabecalho.get("tipoPedido", ""))
        self.funcao = limpar_string_neogrid(cabecalho.get("funcao", ""))
        
        # Datas
        self.data_emissao = converter_data_neogrid(cabecalho["dataHoraEmissao"])
        self.data_entrega_inicial = converter_data_neogrid(cabecalho["dataHoraInicialEntrega"])
        self.data_entrega_final = converter_data_neogrid(cabecalho["dataHoraFinalEntrega"])
        
        # CNPJs e dados das empresas
        self.cnpj_fornecedor = extrair_cnpj_limpo(cabecalho["cnpjFornecedor"])
        self.cnpj_comprador = extrair_cnpj_limpo(cabecalho["cnpjComprador"])
        self.cnpj_local_faturado = extrair_cnpj_limpo(cabecalho["cnpjLocalFaturado"])
        self.cnpj_local_entrega = extrair_cnpj_limpo(cabecalho["cnpjLocalEntrega"])
        
        # Para compatibilidade com código existente
        self.cnpj_destino = self.cnpj_comprador
        
        # EANs
        self.ean_fornecedor = limpar_string_neogrid(cabecalho.get("eanFornecedor", ""))
        self.ean_comprador = limpar_string_neogrid(cabecalho.get("eanComprador", ""))
        self.ean_local_faturado = limpar_string_neogrid(cabecalho.get("eanLocalFaturado", ""))
        self.ean_local_entrega = limpar_string_neogrid(cabecalho.get("eanLocalEntrega", ""))
        
        # Dados de entrega
        self.condicao_entrega = limpar_string_neogrid(cabecalho.get("condicaoEntrega", ""))
        self.observacao = limpar_string_neogrid(cabecalho.get("observacao", ""))
        
        # Transportadora
        self.codigo_transportadora = limpar_string_neogrid(cabecalho.get("codTransportadora", ""))
        self.nome_transportadora = limpar_string_neogrid(cabecalho.get("nomeTransportadora", ""))
        
        # Outros dados
        self.numero_contrato = limpar_string_neogrid(cabecalho.get("numeroContrato", ""))
        self.lista_precos = limpar_string_neogrid(cabecalho.get("listaPrecos", ""))
        
        # Dados de pagamento
        self.condicao_pagamento = limpar_string_neogrid(pagamento.get("condicaoPagamento", ""))
        self.referencia_data = limpar_string_neogrid(pagamento.get("referenciaData", ""))
        self.referencia_tempo_data = limpar_string_neogrid(pagamento.get("referenciaTempoData", ""))
        self.tipo_periodo = limpar_string_neogrid(pagamento.get("tipoPeriodo", ""))
        self.numero_periodos = limpar_string_neogrid(pagamento.get("numeroPeriodos", ""))
        self.data_vencimento = converter_data_neogrid(pagamento.get("dataVencimento", ""))
        self.valor_pagar = converter_valor_neogrid(pagamento.get("valorPagar", "0"))
        self.percentual_pagar = converter_percentual_neogrid(pagamento.get("percentualPagarValorFaturado", "0"))
        
        # Dados de desconto
        self.percentual_desconto_financeiro = converter_percentual_neogrid(desconto.get("percentualDescontoFinanceiro", "0"))
        self.valor_desconto_financeiro = converter_valor_neogrid(desconto.get("valorDescontoFinanceiro", "0"))
        self.percentual_desconto_comercial = converter_percentual_neogrid(desconto.get("percentualDescontoComercial", "0"))
        self.valor_desconto_comercial = converter_valor_neogrid(desconto.get("valorDescontoComercial", "0"))
        self.percentual_desconto_promocional = converter_percentual_neogrid(desconto.get("percentualDescontoPromocional", "0"))
        self.valor_desconto_promocional = converter_valor_neogrid(desconto.get("valorDescontoPromocional", "0"))
        
        # Encargos
        self.percentual_encargos_financeiros = converter_percentual_neogrid(desconto.get("percentualEncargosFinanceiros", "0"))
        self.valor_encargos_financeiros = converter_valor_neogrid(desconto.get("valorEncargosFinanceiros", "0"))
        self.percentual_encargos_frete = converter_percentual_neogrid(desconto.get("percentualEncargosFrete", "0"))
        self.valor_encargos_frete = converter_valor_neogrid(desconto.get("valorEncargosFrete", "0"))
        self.percentual_encargos_seguro = converter_percentual_neogrid(desconto.get("percentualEncargosSeguro", "0"))
        self.valor_encargos_seguro = converter_valor_neogrid(desconto.get("valorEncargosSeguro", "0"))
        
        # Valores totais do pedido
        self.valor_total_mercadorias = converter_valor_neogrid(sumario.get("valorTotalMercadorias", "0"))
        self.valor_total_ipi = converter_valor_neogrid(sumario.get("valorTotalIPI", "0"))
        self.valor_total_abatimentos = converter_valor_neogrid(sumario.get("valorTotalAbatimentos", "0"))
        self.valor_total_encargos = converter_valor_neogrid(sumario.get("valorTotalEncargos", "0"))
        self.valor_total_despesas_tributadas = converter_valor_neogrid(sumario.get("valorTotalDespesasAcessoriasTributadas", "0"))
        self.valor_total_descontos_comerciais = converter_valor_neogrid(sumario.get("valorTotalDescontosComerciais", "0"))
        self.valor_total_despesas_nao_tributadas = converter_valor_neogrid(sumario.get("valorTotalDespesasAcessoriasNaoTributadas", "0"))
        self.valor_total_pedido = converter_valor_neogrid(sumario.get("valorTotalPedido", "0"))
        
        # Para compatibilidade com código existente
        self.valor_total = self.valor_total_pedido
        self.valor_ipi_total = self.valor_total_ipi
        
        # Processar itens
        self.itens: List[ItemPedido] = []
        if isinstance(itens_data, list):
            self.itens = [ItemPedido(item) for item in itens_data]
        else:
            # Se for um único item, transformar em lista
            self.itens = [ItemPedido(itens_data)]

    @property
    def data_entrega(self) -> Optional[datetime]:
        """Retorna a data de entrega (inicial)"""
        return self.data_entrega_inicial

    @property
    def quantidade_itens(self) -> int:
        """Retorna a quantidade de itens no pedido"""
        return len(self.itens)

    def to_dict_for_processing(self) -> dict:
        """
        Converte o pedido para o formato esperado pelo processador
        """
        return {
            "num_pedido": self.numero_pedido,
            "data_pedido": self.data_emissao.strftime("%Y-%m-%d") if self.data_emissao else "",
            "data_entrega": self.data_entrega.strftime("%Y-%m-%d") if self.data_entrega else None,
            "hora_inicio": datetime.now().strftime("%H:%M"),
            "hora_fim": None,
            "observacao": self.observacao or self.condicao_entrega or "",
            "cnpj": self.cnpj_destino,
            "itens": [
                {
                    "ean13": "",  # Será interpretado pela função interpretar_codigo_produto
                    "dun14": "",  # Será interpretado pela função interpretar_codigo_produto
                    "codprod": item.codigo_produto,
                    "qtd": float(item.quantidade),
                    "valor": float(item.preco_unitario)
                }
                for item in self.itens
            ]
        }

    def __repr__(self):
        return f"<Pedido {self.numero_pedido} - {len(self.itens)} itens - R$ {self.valor_total:.2f}>"