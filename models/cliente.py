# models/cliente.py
import sys
import os
# Adiciona o diretório raiz do projeto ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from dataclasses import dataclass

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
    codigo_anal_cliente: str
    codigo_tab_preco: str
    codigo_cond_pagto: str
    codigo_cliente_pai: str
    obs_fechamento: str
    email_copia_pedido: str
    flag_envia_copia: str
    flag_entrega_agendada: int
    qtde_dias_min_entrega: str

    @staticmethod
    def from_dict(row: dict) -> "Cliente":
        return Cliente(
            codigo=row.get("CODIGO"),
            razao_social=row.get("RAZAOSOCIAL"),
            cnpj=row.get("CGCCPF"),
            inscricao_estadual=row.get("INSCR_ESTADUAL"),
            endereco=row.get("ENDERECO"),
            codigo_nome_cidade=row.get("CODIGONOMECIDADE"),
            estado=row.get("ESTADO"),
            bairro=row.get("BAIRRO"),
            telefone=row.get("TELEFONE"),
            fax=row.get("FAX"),
            cep=row.get("CEP"),
            codigo_status=row.get("CODIGOSTATUSCLI"),
            nome_fantasia=row.get("NOMEFANTASIA"),
            data_cadastro=row.get("DATACADASTRO"),
            codigo_entrega=row.get("CODIGOENDENTREGA"),
            codigo_regiao=row.get("CODIGOREGIAO"),
            codigo_anal_cliente=row.get("CODIGOANALCLIENTE"),
            codigo_tab_preco=row.get("CODIGOTABPRECO"),
            codigo_cond_pagto=row.get("CODIGOCONDPAGTO"),
            codigo_cliente_pai=row.get("CODIGOCLIENTEPAI"),
            obs_fechamento=row.get("OBSFETCHATURAMENTO"),
            email_copia_pedido=row.get("EMAILCOPIAPEDIDO"),
            flag_envia_copia=row.get("FLAGENVIACOPIAPEDIDO"),
            flag_entrega_agendada=row.get("CESP_FLAGENTREGAAGENDADA"),
            qtde_dias_min_entrega=row.get("Cesp_QtdeDiasMinEntrega")
        )
