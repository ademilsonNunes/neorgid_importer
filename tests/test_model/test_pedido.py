import sys
import os
# Adiciona o diretório raiz do projeto ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import json
import pytest
from models.pedido import Pedido

@pytest.fixture
def exemplo_json():
    # Constrói o caminho absoluto para o arquivo base.json
    # Vai para a raiz do projeto (2 níveis acima) e depois para data/base.json
    current_dir = os.path.dirname(__file__)
    project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
    json_path = os.path.join(project_root, 'data', 'base.json')
    
    with open(json_path, encoding="utf-8") as f:
        base = json.load(f)
        return base["documents"][0]["content"][0]

def test_pedido_basico(exemplo_json):
    '''
    Testa se o Pedido inicializado com o exemplo JSON tem seus dados principais
    corretamente extraídos. Verifica se o número do pedido, o CNPJ do 
    destinatário, a quantidade de itens e o valor total do pedido são válidos.
    '''
    pedido = Pedido(exemplo_json)
    assert pedido.numero_pedido == "5026397"
    assert pedido.cnpj_destino == "04737552000480"
    assert len(pedido.itens) > 0
    assert pedido.valor_total > 0

def test_item_pedido_valores(exemplo_json):
    pedido = Pedido(exemplo_json)
    item = pedido.itens[0]

    assert isinstance(item.codigo_produto, str)
    assert item.quantidade > 0
    assert item.preco_unitario > 0