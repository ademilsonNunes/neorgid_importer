# services/validador_produto.py
import sys
import os
# Adiciona o diretório raiz do projeto ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import json
import re
from typing import Optional, Dict, List
from models.produto import Produto
from utils.logger import logger

class ValidadorProduto:
    def __init__(self):
        self.produtos = self._caregar_produtos()
        self._cache_busca = {}  # Cache para otimizar buscas repetidas
    
    def _caregar_produtos(self) -> Dict[str, Produto]:
        """Carrega os produtos do arquivo JSON e cria índices para busca rápida"""
        try:
            # Caminho para o arquivo de produtos
            current_dir = os.path.dirname(__file__)
            project_root = os.path.abspath(os.path.join(current_dir, '..'))
            produtos_file = os.path.join(project_root, 'data', 'produtos.json')
            
            logger.debug(f"🔍 Carregando produtos do arquivo: {produtos_file}")
            
            with open(produtos_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if "produtos" not in data:
                logger.error("❌ Estrutura inválida no arquivo produtos.json - chave 'produtos' não encontrada")
                return {}
                
            # Criar índices para busca rápida
            produtos_dict = {}
            produtos_raw = data['produtos']
            
            logger.debug(f"📦 Processando {len(produtos_raw)} produtos para indexação")
            
            for produto_data in produtos_raw:
                try:
                    # Criar objeto Produto
                    produto = self._criar_produto(produto_data)
                    
                    # Índice por EAN13
                    if produto.ean13 and produto.ean13.strip():
                        chave_ean13 = f"ean13_{produto.ean13}"
                        produtos_dict[chave_ean13] = produto
                        logger.debug(f"  📋 Índice EAN13: {produto.ean13} -> {produto.codigo}")
                    
                    # Índice por DUN14
                    if produto.dun14 and produto.dun14.strip():
                        chave_dun14 = f"dun14_{produto.dun14}"
                        produtos_dict[chave_dun14] = produto
                        logger.debug(f"  📋 Índice DUN14: {produto.dun14} -> {produto.codigo}")
                    
                    # Índice por código exato
                    chave_codigo = f"codigo_{produto.codigo}"
                    produtos_dict[chave_codigo] = produto
                    
                    # Índice por código base (sem sufixo)
                    codigo_base = re.sub(r'\.\w+$', '', produto.codigo)
                    if codigo_base != produto.codigo:
                        chave_codigo_base = f"codigo_base_{codigo_base}"
                        produtos_dict[chave_codigo_base] = produto
                        logger.debug(f"  📋 Índice Código Base: {codigo_base} -> {produto.codigo}")
                
                except Exception as e:
                    logger.warning(f"⚠️ Erro ao processar produto {produto_data.get('codigo', 'DESCONHECIDO')}: {e}")
                    continue
            
            logger.info(f"✅ {len(produtos_raw)} produtos carregados, {len(produtos_dict)} índices criados")
            return produtos_dict
            
        except FileNotFoundError:
            logger.error(f"❌ Arquivo produtos.json não encontrado: {produtos_file}")
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"❌ Erro ao fazer parse do JSON de produtos: {e}")
            return {}
        except Exception as e:
            logger.error(f"❌ Erro inesperado ao carregar produtos: {e}")
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
        
        # Criar chave de cache
        cache_key = f"{ean13}|{dun14}|{codprod}"
        
        # Verificar cache primeiro
        if cache_key in self._cache_busca:
            logger.debug(f"🎯 Cache hit para busca: {cache_key}")
            return self._cache_busca[cache_key]
        
        logger.debug(f"🔍 Buscando produto - EAN13: '{ean13}', DUN14: '{dun14}', CodProd: '{codprod}'")
        
        produto_encontrado = None
        
        # 1ª tentativa: Buscar por EAN13
        if ean13:
            chave_ean13 = f"ean13_{ean13}"
            produto_encontrado = self.produtos.get(chave_ean13)
            if produto_encontrado:
                logger.debug(f"✅ Produto encontrado por EAN13: {ean13} -> {produto_encontrado.codigo}")
                self._cache_busca[cache_key] = produto_encontrado
                return produto_encontrado
        
        # 2ª tentativa: Buscar por DUN14
        if dun14:
            chave_dun14 = f"dun14_{dun14}"
            produto_encontrado = self.produtos.get(chave_dun14)
            if produto_encontrado:
                logger.debug(f"✅ Produto encontrado por DUN14: {dun14} -> {produto_encontrado.codigo}")
                self._cache_busca[cache_key] = produto_encontrado
                return produto_encontrado
        
        # 3ª tentativa: Buscar por código exato
        if codprod:
            chave_codigo = f"codigo_{codprod}"
            produto_encontrado = self.produtos.get(chave_codigo)
            if produto_encontrado:
                logger.debug(f"✅ Produto encontrado por código exato: {codprod} -> {produto_encontrado.codigo}")
                self._cache_busca[cache_key] = produto_encontrado
                return produto_encontrado
        
        # 4ª tentativa: Buscar por código base (remove sufixo como .01, .02, etc)
        if codprod:
            codigo_base = re.sub(r'\.\w+$', '', codprod)
            if codigo_base != codprod:  # Só tenta se realmente removeu algo
                chave_codigo_base = f"codigo_base_{codigo_base}"
                produto_encontrado = self.produtos.get(chave_codigo_base)
                if produto_encontrado:
                    logger.debug(f"✅ Produto encontrado por código base: {codigo_base} -> {produto_encontrado.codigo}")
                    self._cache_busca[cache_key] = produto_encontrado
                    return produto_encontrado
        
        # Se não encontrou nada, registra no cache também (para evitar buscas repetidas)
        logger.debug(f"❌ Produto não encontrado - EAN13: '{ean13}', DUN14: '{dun14}', CodProd: '{codprod}'")
        self._cache_busca[cache_key] = None
        return None
    
    def _criar_produto(self, produto_data: dict) -> Produto:
        """Converte os dados do JSON em um objeto Produto com validação"""
        try:
            return Produto(
                codigo=str(produto_data.get('codigo', '')).strip(),
                descricao=str(produto_data.get('descricao', '')).strip(),
                ean13=str(produto_data.get('ean13', '')).strip(),
                dun14=str(produto_data.get('dun14', '')).strip(),
                peso_bruto=float(produto_data.get('peso_bruto', 0.0)),
                peso_liquido=float(produto_data.get('peso_liquido', 0.0)),
                qtde_embalagem=float(produto_data.get('qtde_embalagem', 0.0)),
                unidade=str(produto_data.get('unidade', '')).strip(),
                perc_acresc_max=float(produto_data.get('perc_acresc_max', 0.0)),
                flag_uso=int(produto_data.get('flag_uso', 1)),
                flag_verba=int(produto_data.get('flag_verba', 0))
            )
        except (ValueError, TypeError) as e:
            raise ValueError(f"Dados inválidos para produto {produto_data.get('codigo', 'DESCONHECIDO')}: {e}")
    
    def listar_todos_produtos(self) -> List[Produto]:
        """Retorna lista de todos os produtos disponíveis"""
        produtos = []
        codigos_processados = set()
        
        for chave, produto in self.produtos.items():
            if chave.startswith('codigo_') and not chave.startswith('codigo_base_'):
                if produto.codigo not in codigos_processados:
                    produtos.append(produto)
                    codigos_processados.add(produto.codigo)
        
        logger.debug(f"📋 Listagem de produtos: {len(produtos)} produtos únicos")
        return produtos
    
    def buscar_por_descricao(self, termo: str) -> List[Produto]:
        """Busca produtos por termo na descrição"""
        if not termo or termo.strip() == "":
            return []
        
        termo = termo.upper().strip()
        produtos_encontrados = []
        codigos_processados = set()
        
        for chave, produto in self.produtos.items():
            if chave.startswith('codigo_') and not chave.startswith('codigo_base_'):
                if produto.codigo not in codigos_processados and termo in produto.descricao.upper():
                    produtos_encontrados.append(produto)
                    codigos_processados.add(produto.codigo)
        
        logger.debug(f"🔍 Busca por descrição '{termo}': {len(produtos_encontrados)} produtos encontrados")
        return produtos_encontrados
    
    def buscar_por_codigo_parcial(self, codigo_parcial: str) -> List[Produto]:
        """Busca produtos por código parcial"""
        if not codigo_parcial or codigo_parcial.strip() == "":
            return []
        
        codigo_parcial = codigo_parcial.upper().strip()
        produtos_encontrados = []
        codigos_processados = set()
        
        for chave, produto in self.produtos.items():
            if chave.startswith('codigo_') and not chave.startswith('codigo_base_'):
                if produto.codigo not in codigos_processados and codigo_parcial in produto.codigo.upper():
                    produtos_encontrados.append(produto)
                    codigos_processados.add(produto.codigo)
        
        logger.debug(f"🔍 Busca por código parcial '{codigo_parcial}': {len(produtos_encontrados)} produtos encontrados")
        return produtos_encontrados
    
    def obter_estatisticas(self) -> Dict[str, int]:
        """Retorna estatísticas dos produtos carregados"""
        produtos_unicos = set()
        total_indices = len(self.produtos)
        
        # Contar produtos únicos
        for chave, produto in self.produtos.items():
            if chave.startswith('codigo_') and not chave.startswith('codigo_base_'):
                produtos_unicos.add(produto.codigo)
        
        # Contar por tipo de índice
        indices_ean13 = len([k for k in self.produtos.keys() if k.startswith('ean13_')])
        indices_dun14 = len([k for k in self.produtos.keys() if k.startswith('dun14_')])
        indices_codigo = len([k for k in self.produtos.keys() if k.startswith('codigo_') and not k.startswith('codigo_base_')])
        indices_codigo_base = len([k for k in self.produtos.keys() if k.startswith('codigo_base_')])
        
        return {
            'produtos_unicos': len(produtos_unicos),
            'total_indices': total_indices,
            'indices_ean13': indices_ean13,
            'indices_dun14': indices_dun14,
            'indices_codigo': indices_codigo,
            'indices_codigo_base': indices_codigo_base,
            'cache_size': len(self._cache_busca)
        }
    
    def limpar_cache(self):
        """Limpa o cache de buscas"""
        cache_size_anterior = len(self._cache_busca)
        self._cache_busca.clear()
        logger.debug(f"🧹 Cache de produtos limpo: {cache_size_anterior} entradas removidas")
    
    def recarregar_produtos(self):
        """Recarrega os produtos do arquivo e limpa o cache"""
        logger.info("🔄 Recarregando produtos do arquivo...")
        self.limpar_cache()
        self.produtos = self._carregar_produtos()
        
        stats = self.obter_estatisticas()
        logger.info(f"✅ Produtos recarregados: {stats['produtos_unicos']} produtos, {stats['total_indices']} índices")
    
    def validar_disponibilidade_produto(self, produto: Produto) -> bool:
        """Valida se o produto está disponível para venda"""
        if not produto:
            return False
        
        # Verificar flag de uso (1 = ativo)
        if produto.flag_uso != 1:
            logger.debug(f"⚠️ Produto {produto.codigo} inativo (flag_uso = {produto.flag_uso})")
            return False
        
        # Verificar se tem código válido
        if not produto.codigo or produto.codigo.strip() == "":
            logger.debug(f"⚠️ Produto sem código válido")
            return False
        
        # Verificar se tem descrição
        if not produto.descricao or produto.descricao.strip() == "":
            logger.debug(f"⚠️ Produto {produto.codigo} sem descrição")
            return False
        
        return True