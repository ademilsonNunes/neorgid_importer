import re
from datetime import datetime
from decimal import Decimal
from typing import Tuple, Optional

def interpretar_codigo_produto(codigo: str) -> Tuple[str, str, str]:
    """Interpreta o valor informado em codigoProduto e devolve
    ean13, dun14 ou codigo interno conforme o formato."""
    if not codigo:
        return "", "", ""
    
    codigo = codigo.strip()
    ean13 = ""
    dun14 = ""
    codprod = ""

    if codigo.isdigit():
        if len(codigo) == 13:
            ean13 = codigo
        elif len(codigo) == 14:
            dun14 = codigo
        else:
            codprod = codigo
    else:
        codprod = codigo

    return ean13, dun14, codprod

def converter_valor_neogrid(valor_str: str) -> Decimal:
    """
    Converte valores do formato Neogrid (ex: "0000000010410.40") para Decimal.
    Remove zeros à esquerda e converte para decimal com 2 casas.
    """
    if not valor_str or valor_str.strip() == "":
        return Decimal("0.00")
    
    # Remove zeros à esquerda e converte
    valor_limpo = valor_str.lstrip("0")
    if not valor_limpo or valor_limpo == ".":
        return Decimal("0.00")
    
    try:
        # Se não tem ponto decimal, considera como centavos
        if "." not in valor_limpo:
            if len(valor_limpo) >= 3:
                # Assume que os últimos 2 dígitos são centavos
                valor_limpo = valor_limpo[:-2] + "." + valor_limpo[-2:]
            else:
                valor_limpo = "0." + valor_limpo.zfill(2)
        
        return Decimal(valor_limpo)
    except:
        return Decimal("0.00")

def converter_quantidade_neogrid(qtd_str: str) -> Decimal:
    """
    Converte quantidades do formato Neogrid (ex: "0000000000560.00") para Decimal.
    """
    if not qtd_str or qtd_str.strip() == "":
        return Decimal("0.00")
    
    # Remove zeros à esquerda
    qtd_limpa = qtd_str.lstrip("0")
    if not qtd_limpa or qtd_limpa == ".":
        return Decimal("0.00")
    
    try:
        return Decimal(qtd_limpa)
    except:
        return Decimal("0.00")

def converter_data_neogrid(data_str: str) -> Optional[datetime]:
    """
    Converte data do formato Neogrid (ex: "150520250000") para datetime.
    Formato: DDMMYYYYHHMM
    """
    if not data_str or len(data_str) < 8:
        return None
    
    try:
        # Extrair componentes da data
        dia = int(data_str[:2])
        mes = int(data_str[2:4])
        ano = int(data_str[4:8])
        
        # Se há informação de hora (12 dígitos)
        if len(data_str) >= 12:
            hora = int(data_str[8:10])
            minuto = int(data_str[10:12])
            return datetime(ano, mes, dia, hora, minuto)
        else:
            return datetime(ano, mes, dia)
    except:
        return None

def limpar_string_neogrid(texto: str) -> str:
    """
    Limpa strings vindas da Neogrid removendo espaços extras.
    """
    if not texto:
        return ""
    return texto.strip()

def converter_percentual_neogrid(perc_str: str) -> Decimal:
    """
    Converte percentuais do formato Neogrid (ex: "003.25") para Decimal.
    """
    if not perc_str or perc_str.strip() == "":
        return Decimal("0.00")
    
    try:
        perc_limpo = perc_str.lstrip("0")
        if not perc_limpo or perc_limpo == ".":
            return Decimal("0.00")
        return Decimal(perc_limpo)
    except:
        return Decimal("0.00")

def mapear_condicao_pagamento(condicao_neogrid: str) -> str:
    """
    Mapeia condição de pagamento da Neogrid para códigos internos.
    """
    mapeamento = {
        "1": "001",  # À vista
        "2": "030",  # 30 dias
        "3": "060",  # 60 dias
        # Adicionar mais mapeamentos conforme necessário
    }
    return mapeamento.get(condicao_neogrid, condicao_neogrid)

def extrair_cnpj_limpo(cnpj: str) -> str:
    """
    Extrai CNPJ removendo formatação e mantendo apenas números.
    """
    if not cnpj:
        return ""
    return re.sub(r'[^\d]', '', cnpj)

def validar_estrutura_pedido_neogrid(doc: dict) -> bool:
    """
    Valida se a estrutura do documento da Neogrid está correta.
    """
    try:
        # Verificar estrutura básica
        if not doc.get("content") or len(doc["content"]) == 0:
            return False
        
        content = doc["content"][0]
        if "order" not in content:
            return False
        
        order = content["order"]
        
        # Verificar seções obrigatórias
        required_sections = ["cabecalho", "itens", "sumario"]
        for section in required_sections:
            if section not in order:
                return False
        
        # Verificar se tem itens
        if "item" not in order["itens"] or not order["itens"]["item"]:
            return False
        
        return True
    except:
        return False