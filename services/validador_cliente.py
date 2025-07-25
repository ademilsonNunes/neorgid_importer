# services/validador_cliente.py
import sys
import os
# Adiciona o diretório raiz do projeto ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import re
from typing import Optional
import pyodbc
from models.cliente import Cliente
from services.database import Database
from config.settings import settings

class ValidadorCliente:
    def __init__(self):
        """
        Inicializa o validador de clientes com a conexão
        para o banco de dados Protheus_producao.
        """
        
        self.db = Database(settings.DB_NAME_PROTHEUS)
    
    def validar_cliente(self, cnpj: str) -> Optional[Cliente]:
        """
        Valida cliente consultando a tabela SA1010 do Protheus
        usando o campo A1_CGC como chave de busca
        """
        if not cnpj:
            return None
            
        # Limpar CNPJ removendo caracteres especiais
        cnpj_limpo = re.sub(r'[^\d]', '', cnpj)
        
        if len(cnpj_limpo) not in [11, 14]:  # CPF ou CNPJ
            return None
            
        conn = None
        try:
            conn = self.db.connect()
            cursor = conn.cursor()
            
            # Query na tabela SA1010 (cadastro de clientes do Protheus)
            query = """
                SELECT 
                    A1_COD as CODIGO,
                    A1_NOME as RAZAOSOCIAL,
                    A1_CGC as CGCCPF,
                    A1_INSCR as INSCR_ESTADUAL,
                    A1_END as ENDERECO,
                    A1_COD_MUN as CODIGONOMECIDADE,
                    A1_EST as ESTADO,
                    A1_BAIRRO as BAIRRO,
                    A1_TEL as TELEFONE,
                    A1_FAX as FAX,
                    A1_CEP as CEP,
                    A1_MSBLQL as CODIGOSTATUSCLI,
                    A1_NREDUZ as NOMEFANTASIA,
                    A1_DTCAD as DATACADASTRO,
                    A1_COD as CODIGOENDENTREGA,
                    A1_REGIAO as CODIGOREGIAO,
                    A1_TABELA as CODIGOTABPRECO,
                    A1_COND as CODIGOCONDPAGTO,
                    '' as CODIGOCLIENTEPAI,
                    A1_OBSERV as OBSFETCHATURAMENTO,
                    A1_EMAIL as EMAILCOPIAPEDIDO,
                    'N' as FLAGENVIACOPIAPEDIDO,
                    0 as CESP_FLAGENTREGAAGENDADA,
                    '0' as Cesp_QtdeDiasMinEntrega
                FROM SA1010
                WHERE A1_CGC = ? 
                AND D_E_L_E_T_ = ''
            """
            
            cursor.execute(query, cnpj_limpo)
            row = cursor.fetchone()
            
            if row:
                # Converter row em dicionário
                columns = [column[0] for column in cursor.description]
                cliente_dict = dict(zip(columns, row))
                
                return Cliente.from_dict(cliente_dict)
            
            return None
            
        except Exception as e:
            print(f"Erro ao validar cliente {cnpj}: {e}")
            return None
        finally:
            if conn:
                conn.close()
    
    def buscar_cliente_por_codigo(self, codigo: str) -> Optional[Cliente]:
        """Busca cliente pelo código A1_COD"""
        if not codigo:
            return None
            
        conn = None
        try:
            conn = self.db.connect()
            cursor = conn.cursor()
            
            query = """
                SELECT 
                    A1_COD as CODIGO,
                    A1_NOME as RAZAOSOCIAL,
                    A1_CGC as CGCCPF,
                    A1_INSCR as INSCR_ESTADUAL,
                    A1_END as ENDERECO,
                    A1_COD_MUN as CODIGONOMECIDADE,
                    A1_EST as ESTADO,
                    A1_BAIRRO as BAIRRO,
                    A1_TEL as TELEFONE,
                    A1_FAX as FAX,
                    A1_CEP as CEP,
                    A1_MSBLQL as CODIGOSTATUSCLI,
                    A1_NREDUZ as NOMEFANTASIA,
                    A1_DTCAD as DATACADASTRO,
                    A1_COD as CODIGOENDENTREGA,
                    A1_REGIAO as CODIGOREGIAO,
                    A1_TABELA as CODIGOTABPRECO,
                    A1_COND as CODIGOCONDPAGTO,
                    '' as CODIGOCLIENTEPAI,
                    A1_OBSERV as OBSFETCHATURAMENTO,
                    A1_EMAIL as EMAILCOPIAPEDIDO,
                    'N' as FLAGENVIACOPIAPEDIDO,
                    0 as CESP_FLAGENTREGAAGENDADA,
                    '0' as Cesp_QtdeDiasMinEntrega
                FROM SA1010
                WHERE A1_COD = ? 
                AND D_E_L_E_T_ = ''
            """
            
            cursor.execute(query, codigo.strip())
            row = cursor.fetchone()
            
            if row:
                columns = [column[0] for column in cursor.description]
                cliente_dict = dict(zip(columns, row))
                return Cliente.from_dict(cliente_dict)
            
            return None
            
        except Exception as e:
            print(f"Erro ao buscar cliente por código {codigo}: {e}")
            return None
        finally:
            if conn:
                conn.close()
    
    def listar_clientes_ativos(self, limite: int = 100) -> list:
        """Lista clientes ativos (não bloqueados)"""
        conn = None
        try:
            conn = self.db.connect()
            cursor = conn.cursor()
            
            query = f"""
                SELECT TOP {limite}
                    A1_COD as CODIGO,
                    A1_NOME as RAZAOSOCIAL,
                    A1_CGC as CGCCPF,
                    A1_NREDUZ as NOMEFANTASIA,
                    A1_EST as ESTADO
                FROM SA1010
                WHERE A1_MSBLQL <> '1'
                AND D_E_L_E_T_ = ''
                ORDER BY A1_NOME
            """
            
            cursor.execute(query)
            rows = cursor.fetchall()
            
            clientes = []
            for row in rows:
                columns = [column[0] for column in cursor.description]
                cliente_dict = dict(zip(columns, row))
                # Preencher campos obrigatórios com valores padrão
                cliente_dict.update({
                    'INSCR_ESTADUAL': '',
                    'ENDERECO': '',
                    'CODIGONOMECIDADE': '',
                    'BAIRRO': '',
                    'TELEFONE': '',
                    'FAX': '',
                    'CEP': '',
                    'CODIGOSTATUSCLI': '1',
                    'DATACADASTRO': '',
                    'CODIGOENDENTREGA': cliente_dict['CODIGO'],
                    'CODIGOREGIAO': 0,
                    'CODIGOANALCLIENTE': '',
                    'CODIGOTABPRECO': '',
                    'CODIGOCONDPAGTO': '',
                    'CODIGOCLIENTEPAI': '',
                    'OBSFETCHATURAMENTO': '',
                    'EMAILCOPIAPEDIDO': '',
                    'FLAGENVIACOPIAPEDIDO': 'N',
                    'CESP_FLAGENTREGAAGENDADA': 0,
                    'Cesp_QtdeDiasMinEntrega': '0'
                })
                clientes.append(Cliente.from_dict(cliente_dict))
            
            return clientes
            
        except Exception as e:
            print(f"Erro ao listar clientes: {e}")
            return []
        finally:
            if conn:
                conn.close()