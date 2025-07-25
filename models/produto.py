# models/produto.py
import sys
import os

# Adiciona o diretório raiz do projeto ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from dataclasses import dataclass

@dataclass
class Produto:
    codigo: str
    descricao: str
    ean13: str
    dun14: str
    peso_bruto: float
    peso_liquido: float
    qtde_embalagem: float
    unidade: str
    perc_acresc_max: float
    flag_uso: int
    flag_verba: int
