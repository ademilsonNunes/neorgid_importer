# models/cliente.py
import sys
import os
# Adiciona o diretório raiz do projeto ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from dataclasses import dataclass
from typing import Optional

@dataclass
class Cliente:
    codigo: str
    razao_social: str
    cnpj: str
    inscricao_estadual: str
    endereco: str
    codigo_nome_cidade: str
    estado: str
    bairro: str
    telefone: str
    fax: str
    cep: str
    codigo_status: str
    nome_fantasia: str
    data_cadastro: str
    codigo_entrega: str
    codigo_regiao: int
    codigo_tab_preco: str
    codigo_cond_pagto: str
    codigo_cliente_pai: str
    obs_fechamento: str
    email_copia_pedido: str
    flag_envia_copia: str
    flag_entrega_agendada: int
    qtde_dias_min_entrega: str

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
    def from_dict(row: dict) -> "Cliente":
        """Cria instância de Cliente a partir de dicionário"""
        return Cliente(
            codigo=str(row.get("CODIGO", "")).strip(),
            razao_social=str(row.get("RAZAOSOCIAL", "")).strip(),
            cnpj=str(row.get("CGCCPF", "")).strip(),
            inscricao_estadual=str(row.get("INSCR_ESTADUAL", "")).strip(),
            endereco=str(row.get("ENDERECO", "")).strip(),
            codigo_nome_cidade=str(row.get("CODIGONOMECIDADE", "")).strip(),
            estado=str(row.get("ESTADO", "")).strip(),
            bairro=str(row.get("BAIRRO", "")).strip(),
            telefone=str(row.get("TELEFONE", "")).strip(),
            fax=str(row.get("FAX", "")).strip(),
            cep=str(row.get("CEP", "")).strip(),
            codigo_status=str(row.get("CODIGOSTATUSCLI", "")).strip(),
            nome_fantasia=str(row.get("NOMEFANTASIA", "")).strip(),
            data_cadastro=str(row.get("DATACADASTRO", "")).strip(),
            codigo_entrega=str(row.get("CODIGOENDENTREGA", "")).strip(),
            codigo_regiao=int(row.get("CODIGOREGIAO", 0)),
            codigo_tab_preco=str(row.get("CODIGOTABPRECO", "")).strip(),
            codigo_cond_pagto=str(row.get("CODIGOCONDPAGTO", "")).strip(),
            codigo_cliente_pai=str(row.get("CODIGOCLIENTEPAI", "")).strip(),
            obs_fechamento=str(row.get("OBSFETCHATURAMENTO", "")).strip(),
            email_copia_pedido=str(row.get("EMAILCOPIAPEDIDO", "")).strip(),
            flag_envia_copia=str(row.get("FLAGENVIACOPIAPEDIDO", "")).strip(),
            flag_entrega_agendada=int(row.get("CESP_FLAGENTREGAAGENDADA", 0)),
            qtde_dias_min_entrega=str(row.get("Cesp_QtdeDiasMinEntrega", "0")).strip()
        )

    def __str__(self):
        return f"{self.codigo} - {self.nome}"
    
    def __repr__(self):
        return f"<Cliente {self.codigo}: {self.nome}>"