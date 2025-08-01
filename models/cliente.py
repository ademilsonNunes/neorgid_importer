# models/cliente.py
import sys
import os
# Adiciona o diretório raiz do projeto ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from dataclasses import dataclass


@dataclass(init=False)
class Cliente:
    codigo: str = ""
    razao_social: str = ""
    cnpj: str = ""
    inscricao_estadual: str = ""
    endereco: str = ""
    codigo_nome_cidade: str = ""
    estado: str = ""
    bairro: str = ""
    telefone: str = ""
    fax: str = ""
    cep: str = ""
    codigo_status: str = ""
    nome_fantasia: str = ""
    data_cadastro: str = ""
    codigo_entrega: str = ""
    codigo_regiao: int = 0
    codigo_tab_preco: str = ""
    codigo_cond_pagto: str = ""
    codigo_cliente_pai: str = ""
    obs_fechamento: str = ""
    email_copia_pedido: str = ""
    flag_envia_copia: str = ""
    flag_entrega_agendada: int = 0
    qtde_dias_min_entrega: str = ""

    def __init__(self, codigo: str = "", nome: str = "", cnpj: str = "", **kwargs):
        self.codigo = codigo
        self.razao_social = kwargs.get("razao_social", nome)
        self.cnpj = cnpj
        self.inscricao_estadual = kwargs.get("inscricao_estadual", "")
        self.endereco = kwargs.get("endereco", "")
        self.codigo_nome_cidade = kwargs.get("codigo_nome_cidade", "")
        self.estado = kwargs.get("estado", "")
        self.bairro = kwargs.get("bairro", "")
        self.telefone = kwargs.get("telefone", "")
        self.fax = kwargs.get("fax", "")
        self.cep = kwargs.get("cep", "")
        self.codigo_status = kwargs.get("codigo_status", "")
        self.nome_fantasia = kwargs.get("nome_fantasia", nome)
        self.data_cadastro = kwargs.get("data_cadastro", "")
        self.codigo_entrega = kwargs.get("codigo_entrega", "")
        self.codigo_regiao = kwargs.get("codigo_regiao", 0)
        self.codigo_tab_preco = kwargs.get("codigo_tab_preco", "")
        self.codigo_cond_pagto = kwargs.get("codigo_cond_pagto", "")
        self.codigo_cliente_pai = kwargs.get("codigo_cliente_pai", "")
        self.obs_fechamento = kwargs.get("obs_fechamento", "")
        self.email_copia_pedido = kwargs.get("email_copia_pedido", "")
        self.flag_envia_copia = kwargs.get("flag_envia_copia", "")
        self.flag_entrega_agendada = kwargs.get("flag_entrega_agendada", 0)
        self.qtde_dias_min_entrega = kwargs.get("qtde_dias_min_entrega", "")

    @property
    def nome(self) -> str:
        """Retorna o nome fantasia ou razão social como nome do cliente"""
        if self.nome_fantasia and self.nome_fantasia.strip():
            return self.nome_fantasia.strip()
        return self.razao_social.strip() if self.razao_social else ""
    
    @property
    def cnpj_formatado(self) -> str:
        """Retorna CNPJ formatado XX.XXX.XXX/XXXX-XX"""
        if not self.cnpj or len(self.cnpj) != 14:
            return self.cnpj
        
        return f"{self.cnpj[:2]}.{self.cnpj[2:5]}.{self.cnpj[5:8]}/{self.cnpj[8:12]}-{self.cnpj[12:14]}"
    
    @property
    def ativo(self) -> bool:
        """Verifica se o cliente está ativo (não bloqueado)"""
        return self.codigo_status != "1"  # No Protheus, 1 = bloqueado

    @staticmethod
    def _safe_int(value, default=0):
        """Converte valor para int de forma segura"""
        if value is None:
            return default
        
        if isinstance(value, str):
            value = value.strip()
            if not value or value == '':
                return default
        
        try:
            return int(value)
        except (ValueError, TypeError):
            return default

    @staticmethod
    def _safe_str(value, default=""):
        """Converte valor para string de forma segura"""
        if value is None:
            return default
        return str(value).strip()

    @staticmethod
    def from_dict(row: dict) -> "Cliente":
        """Cria instância de Cliente a partir de dicionário com tratamento robusto"""
        return Cliente(
            codigo=Cliente._safe_str(row.get("CODIGO", "")),
            razao_social=Cliente._safe_str(row.get("RAZAOSOCIAL", "")),
            cnpj=Cliente._safe_str(row.get("CGCCPF", "")),
            inscricao_estadual=Cliente._safe_str(row.get("INSCR_ESTADUAL", "")),
            endereco=Cliente._safe_str(row.get("ENDERECO", "")),
            codigo_nome_cidade=Cliente._safe_str(row.get("CODIGONOMECIDADE", "")),
            estado=Cliente._safe_str(row.get("ESTADO", "")),
            bairro=Cliente._safe_str(row.get("BAIRRO", "")),
            telefone=Cliente._safe_str(row.get("TELEFONE", "")),
            fax=Cliente._safe_str(row.get("FAX", "")),
            cep=Cliente._safe_str(row.get("CEP", "")),
            codigo_status=Cliente._safe_str(row.get("CODIGOSTATUSCLI", "")),
            nome_fantasia=Cliente._safe_str(row.get("NOMEFANTASIA", "")),
            data_cadastro=Cliente._safe_str(row.get("DATACADASTRO", "")),
            codigo_entrega=Cliente._safe_str(row.get("CODIGOENDENTREGA", "")),
            codigo_regiao=Cliente._safe_int(row.get("CODIGOREGIAO", 0)),
            codigo_tab_preco=Cliente._safe_str(row.get("CODIGOTABPRECO", "")),
            codigo_cond_pagto=Cliente._safe_str(row.get("CODIGOCONDPAGTO", "")),
            codigo_cliente_pai=Cliente._safe_str(row.get("CODIGOCLIENTEPAI", "")),
            obs_fechamento=Cliente._safe_str(row.get("OBSFETCHATURAMENTO", "")),
            email_copia_pedido=Cliente._safe_str(row.get("EMAILCOPIAPEDIDO", "")),
            flag_envia_copia=Cliente._safe_str(row.get("FLAGENVIACOPIAPEDIDO", "")),
            flag_entrega_agendada=Cliente._safe_int(row.get("CESP_FLAGENTREGAAGENDADA", 0)),
            qtde_dias_min_entrega=Cliente._safe_str(row.get("Cesp_QtdeDiasMinEntrega", "0"))
        )

    def __str__(self):
        return f"{self.codigo} - {self.nome}"
    
    def __repr__(self):
        return f"<Cliente {self.codigo}: {self.nome}>"