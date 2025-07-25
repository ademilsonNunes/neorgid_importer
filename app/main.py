import sys
import os
# Adiciona o diretório raiz do projeto ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import streamlit as st
from services.api_client import NeogridAPIClient
from services.processador_pedido import ProcessadorPedido
from services.processador_pedido_item import ProcessadorPedidoItem
from services.validador_cliente import ValidadorCliente
from services.validador_produto import ValidadorProduto
from repository.pedido_repository import PedidoRepository
from models.pedido import Pedido
from datetime import datetime
import json
import os

LOG_FILE = "logs/log_pedidos.txt"

def registrar_log(mensagem: str):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{datetime.now()} - {mensagem}\n")

st.title("📦 Importador de Pedidos - Neogrid")

if st.button("🔄 Buscar e Processar Pedidos"):
    st.info("Consultando API da Neogrid...")
    try:
        api = NeogridAPIClient()
        resposta = api.buscar_pedidos()

        if "documents" not in resposta or not resposta["documents"]:
            st.warning("Nenhum pedido encontrado.")
            registrar_log("Nenhum pedido retornado pela API.")
        else:
            st.success(f"{len(resposta['documents'])} pedido(s) recebido(s).")
            validador_cliente = ValidadorCliente()
            validador_produto = ValidadorProduto()
            processador_item = ProcessadorPedidoItem(validador_produto)
            processador_pedido = ProcessadorPedido(validador_cliente, processador_item)
            repo = PedidoRepository()

            for doc in resposta["documents"]:
                try:
                    pedido_raw = json.loads(doc["data"])
                    pedido_neogrid = Pedido(pedido_raw)
                    pedido_final = processador_pedido.processar({
                        "num_pedido": pedido_neogrid.numero_pedido,
                        "data_pedido": pedido_neogrid.data_emissao.strftime("%Y-%m-%d"),
                        "data_entrega": pedido_neogrid.data_entrega.strftime("%Y-%m-%d"),
                        "observacao": pedido_neogrid.condicao_entrega,
                        "cnpj": pedido_neogrid.cnpj_destino,
                        "itens": [
                            {
                                "ean13": item.ean13,
                                "dun14": "",  # Suporte futuro
                                "codprod": item.codigo_produto,
                                "qtd": float(item.quantidade),
                                "valor": float(item.preco_unitario)
                            } for item in pedido_neogrid.itens
                        ]
                    })

                    repo.inserir_pedido(pedido_final)
                    registrar_log(f"Pedido {pedido_final.num_pedido} processado e gravado com sucesso.")

                except Exception as e:
                    erro_msg = f"Erro ao processar pedido: {str(e)}"
                    registrar_log(erro_msg)
                    st.error(erro_msg)

            repo.close()
            st.success("Todos os pedidos foram processados.")
    except Exception as e:
        erro_msg = f"Erro geral: {str(e)}"
        registrar_log(erro_msg)
        st.error(erro_msg)
