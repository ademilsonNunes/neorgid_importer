import re

def interpretar_codigo_produto(codigo: str):
    """Interpreta o valor informado em codigoProduto e devolve
    ean13, dun14 ou codigo interno conforme o formato."""
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
