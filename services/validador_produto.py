# services/validador_produto.py
import sys
import os
# Adiciona o diretório raiz do projeto ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import json
import re
from typing import Optional
from models.produto import Produto

class ValidadorProduto:
    def __init__(self):
        self.produtos = self._caregar_produtos()
    
    def _caregar_produtos(self) -> dict:
        """Carrega os produtos do arquivo JSON"""
        try:
            # Caminho para o arquivo de produtos
            current_dir = os.path.dirname(__file__)
            project_root = os.path.abspath(os.path.join(current_dir, '..'))
            produtos_file = os.path.join(project_root, 'data', 'produtos.json')
            
            with open(produtos_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Criar índices para busca rápida
            produtos_dict = {}
            for produto in data['produtos']:
                # Índice por EAN13
                if produto['ean13']:
                    produtos_dict[f"ean13_{produto['ean13']}"] = produto
                
                # Índice por DUN14
                if produto['dun14']:
                    produtos_dict[f"dun14_{produto['dun14']}"] = produto
                
                # Índice por código
                produtos_dict[f"codigo_{produto['codigo']}"] = produto
                
                # Índice por código sem sufixo (para busca flexível)
                codigo_base = re.sub(r'\.\w+$', '', produto['codigo'])
                produtos_dict[f"codigo_base_{codigo_base}"] = produto
                
            return produtos_dict
            
        except Exception as e:
            print(f"Erro ao carregar produtos: {e}")
            return {}
    
    def validar_produto(self, ean13: str, dun14: str, codprod: str) -> Optional[Produto]:
        """
        Valida produto usando múltiplas estratégias de busca:
        1. Por EAN13
        2. Por DUN14  
        3. Por código exato
        4. Por código base (sem sufixo)
        """
        
        # Limpar os códigos de entrada
        ean13 = ean13.strip() if ean13 else ""
        dun14 = dun14.strip() if dun14 else ""
        codprod = codprod.strip() if codprod else ""
        
        produto_data = None
        
        # 1ª tentativa: Buscar por EAN13
        if ean13:
            produto_data = self.produtos.get(f"ean13_{ean13}")
            if produto_data:
                return self._criar_produto(produto_data)
        
        # 2ª tentativa: Buscar por DUN14
        if dun14:
            produto_data = self.produtos.get(f"dun14_{dun14}")
            if produto_data:
                return self._criar_produto(produto_data)
        
        # 3ª tentativa: Buscar por código exato
        if codprod:
            produto_data = self.produtos.get(f"codigo_{codprod}")
            if produto_data:
                return self._criar_produto(produto_data)
        
        # 4ª tentativa: Buscar por código base (remove sufixo como .01, .02, etc)
        if codprod:
            codigo_base = re.sub(r'\.\w+$', '', codprod)
            produto_data = self.produtos.get(f"codigo_base_{codigo_base}")
            if produto_data:
                return self._criar_produto(produto_data)
        
        # Se não encontrou nada, retorna None
        return None
    
    def _criar_produto(self, produto_data: dict) -> Produto:
        """Converte os dados do JSON em um objeto Produto"""
        return Produto(
            codigo=produto_data['codigo'],
            descricao=produto_data['descricao'],
            ean13=produto_data['ean13'],
            dun14=produto_data['dun14'],
            peso_bruto=produto_data['peso_bruto'],
            peso_liquido=produto_data['peso_liquido'],
            qtde_embalagem=produto_data['qtde_embalagem'],
            unidade=produto_data['unidade'],
            perc_acresc_max=produto_data['perc_acresc_max'],
            flag_uso=produto_data['flag_uso'],
            flag_verba=produto_data['flag_verba']
        )
    
    def listar_todos_produtos(self) -> list:
        """Retorna lista de todos os produtos disponíveis"""
        produtos = []
        for key, produto_data in self.produtos.items():
            if key.startswith('codigo_') and not key.startswith('codigo_base_'):
                produtos.append(self._criar_produto(produto_data))
        return produtos
    
    def buscar_por_descricao(self, termo: str) -> list:
        """Busca produtos por termo na descrição"""
        termo = termo.upper().strip()
        produtos_encontrados = []
        
        for key, produto_data in self.produtos.items():
            if key.startswith('codigo_') and not key.startswith('codigo_base_'):
                if termo in produto_data['descricao'].upper():
                    produtos_encontrados.append(self._criar_produto(produto_data))
        
        return produtos_encontrados