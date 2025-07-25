import sys
import os
# Adiciona o diretório raiz do projeto ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
from services.api_client import NeogridAPIClient
from services.processador_pedido import ProcessadorPedido
from services.processador_pedido_item import ProcessadorPedidoItem
from services.validador_cliente import ValidadorCliente
from services.validador_produto import ValidadorProduto
from repositories.pedido_repository import PedidoRepository
from models.pedido import Pedido
from datetime import datetime
import json
import os

LOG_FILE = "logs/log_pedidos.txt"

def garantir_diretorio_logs():
    """Cria o diretório de logs se não existir"""
    os.makedirs("logs", exist_ok=True)

def registrar_log(mensagem: str):
    """Registra mensagem no arquivo de log"""
    garantir_diretorio_logs()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {mensagem}\n")

def processar_pedido_neogrid(doc, processador_pedido, repo):
    """Processa um documento de pedido da Neogrid"""
    doc_id = doc.get("docId", "N/A")
    
    try:
        # O JSON já vem parseado da API - pegar o primeiro content
        if not doc.get("content") or len(doc["content"]) == 0:
            raise ValueError("Documento sem conteúdo válido")
            
        pedido_content = doc["content"][0]
        
        # Criar objeto Pedido a partir do JSON da Neogrid
        pedido_neogrid = Pedido(pedido_content)
        
        # Montar estrutura para processamento interno
        pedido_para_processar = {
            "num_pedido": pedido_neogrid.numero_pedido,
            "data_pedido": pedido_neogrid.data_emissao.strftime("%Y-%m-%d") if pedido_neogrid.data_emissao else "",
            "data_entrega": pedido_neogrid.data_entrega.strftime("%Y-%m-%d") if pedido_neogrid.data_entrega else None,
            "hora_inicio": datetime.now().strftime("%H:%M"),
            "hora_fim": None,
            "observacao": pedido_neogrid.condicao_entrega or "",
            "cnpj": pedido_neogrid.cnpj_destino,
            "itens": []
        }
        
        # Processar itens do pedido
        for item in pedido_neogrid.itens:
            item_para_processar = {
                "ean13": "",  # Neogrid não mapeia diretamente EAN13 no código
                "dun14": "",
                "codprod": item.codigo_produto,
                "qtd": float(item.quantidade),
                "valor": float(item.preco_unitario)
            }
            pedido_para_processar["itens"].append(item_para_processar)
        
        # Processar usando as classes de negócio
        pedido_final = processador_pedido.processar(pedido_para_processar)
        
        # Gravar no banco
        sucesso = repo.inserir_pedido(pedido_final)
        
        if sucesso:
            mensagem = f"✅ Pedido {pedido_final.num_pedido} processado e gravado com sucesso"
            registrar_log(mensagem)
            repo.log_processamento("INFO", mensagem, pedido_final.num_pedido)
            return {"status": "sucesso", "mensagem": mensagem, "pedido": pedido_final.num_pedido}
        else:
            mensagem = f"⚠️ Pedido {pedido_final.num_pedido} já existia no banco"
            registrar_log(mensagem)
            return {"status": "duplicado", "mensagem": mensagem, "pedido": pedido_final.num_pedido}
            
    except Exception as e:
        erro_msg = f"❌ Erro ao processar documento {doc_id}: {str(e)}"
        registrar_log(erro_msg)
        repo.log_processamento("ERROR", erro_msg, doc_id)
        return {"status": "erro", "mensagem": erro_msg, "doc_id": doc_id}

# Função para carregar CSS externo
def load_totvs_css():
    """Carrega o CSS customizado da TOTVS a partir de arquivo externo"""
    css_path = os.path.join(os.path.dirname(__file__), "assets", "css", "totvs-style.css")
    
    try:
        with open(css_path, "r", encoding="utf-8") as f:
            css_content = f.read()
        
        st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)
        
    except FileNotFoundError:
        st.error(f"❌ Arquivo CSS não encontrado: {css_path}")
        # Fallback com CSS básico
        st.markdown("""
        <style>
        .main { font-family: 'Inter', sans-serif; }
        .totvs-header { 
            background: linear-gradient(135deg, #1976D2 0%, #42A5F5 100%);
            padding: 1.5rem; color: white; border-radius: 0 0 16px 16px;
            margin: -1rem -1rem 2rem -1rem;
        }
        .totvs-card { 
            background: white; border-radius: 16px; padding: 1.5rem;
            box-shadow: 0 2px 16px rgba(0,0,0,0.08); margin-bottom: 1rem;
        }
        .success-alert { background: rgba(46,125,50,0.1); color: #2E7D32; padding: 1rem; border-radius: 8px; }
        .warning-alert { background: rgba(245,124,0,0.1); color: #F57C00; padding: 1rem; border-radius: 8px; }
        .error-alert { background: rgba(211,47,47,0.1); color: #D32F2F; padding: 1rem; border-radius: 8px; }
        </style>
        """, unsafe_allow_html=True)
        
    except Exception as e:
        st.error(f"❌ Erro ao carregar CSS: {str(e)}")

# Interface Streamlit
st.set_page_config(
    page_title="TOTVS | Importador Neogrid",
    page_icon="🔵",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Carregar CSS personalizado
load_totvs_css()

# Header customizado
st.markdown("""
<div class="totvs-header">
    <h1>🔄 Importador de Pedidos</h1>
    <div class="subtitle">Integração Neogrid → Protheus | TOTVS</div>
</div>
""", unsafe_allow_html=True)

# Sidebar com informações
with st.sidebar:
    st.markdown("""
    <div class="totvs-card">
        <div class="totvs-card-header">
            ℹ️ Informações do Sistema
        </div>
        <p><strong>Versão:</strong> 2.1.0</p>
        <p><strong>Ambiente:</strong> Produção</p>
        <p><strong>Última atualização:</strong> Jul 2025</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="totvs-card">
        <div class="totvs-card-header">
            🔄 Processo de Importação
        </div>
        <div style="font-size: 0.9rem; line-height: 1.6;">
            <strong>1.</strong> Consulta API Neogrid<br>
            <strong>2.</strong> Valida clientes cadastrados<br>
            <strong>3.</strong> Valida produtos no estoque<br>
            <strong>4.</strong> Processa regras de negócio<br>
            <strong>5.</strong> Grava pedidos no Protheus<br>
            <strong>6.</strong> Registra logs de auditoria
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Status do sistema
    status_sistema = "🟢 Online" if True else "🔴 Offline"  # Simular status
    st.markdown(f"""
    <div class="totvs-card">
        <div class="totvs-card-header">
            📊 Status do Sistema
        </div>
        <div class="status-indicator status-online">
            {status_sistema}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Botão para limpar logs
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🗑️ Limpar Logs", key="clear_logs", help="Remove todos os arquivos de log"):
        if os.path.exists(LOG_FILE):
            os.remove(LOG_FILE)
            st.success("✅ Logs removidos com sucesso!")
            st.rerun()

# Área principal
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("""
    <div class="totvs-card">
        <div class="totvs-card-header">
            🚀 Execução do Processo
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("🔄 Buscar e Processar Pedidos", type="primary", use_container_width=True):
        
        # Container para progresso
        progress_container = st.container()
        
        with progress_container:
            progress_bar = st.progress(0)
            status_placeholder = st.empty()
            
            try:
                # Etapa 1: Inicialização
                status_placeholder.markdown('<div class="loading-text">🔧 Inicializando serviços...</div>', unsafe_allow_html=True)
                progress_bar.progress(10)
                
                # Inicializar serviços
                api = NeogridAPIClient()
                validador_cliente = ValidadorCliente()
                validador_produto = ValidadorProduto()
                processador_item = ProcessadorPedidoItem(validador_produto)
                processador_pedido = ProcessadorPedido(validador_cliente, processador_item)
                
                progress_bar.progress(20)
                
                # Etapa 2: Consulta API
                status_placeholder.markdown('<div class="loading-text">🔍 Consultando API da Neogrid...</div>', unsafe_allow_html=True)
                resposta = api.buscar_pedidos()
                
                if "documents" not in resposta or not resposta["documents"]:
                    st.markdown('<div class="warning-alert">🔍 Nenhum pedido encontrado na Neogrid no momento.</div>', unsafe_allow_html=True)
                    registrar_log("Nenhum pedido retornado pela API Neogrid")
                else:
                    documentos = resposta["documents"]
                    total_docs = len(documentos)
                    
                    st.markdown(f'<div class="success-alert">📄 {total_docs} documento(s) recebido(s) da Neogrid para processamento.</div>', unsafe_allow_html=True)
                    progress_bar.progress(30)
                    
                    # Etapa 3: Processamento
                    resultados = {"sucesso": 0, "duplicados": 0, "erros": 0}
                    detalhes_processamento = []
                    
                    with PedidoRepository() as repo:
                        for i, doc in enumerate(documentos):
                            status_placeholder.markdown(f'<div class="loading-text">⚙️ Processando documento {i+1} de {total_docs}...</div>', unsafe_allow_html=True)
                            
                            resultado = processar_pedido_neogrid(doc, processador_pedido, repo)
                            detalhes_processamento.append(resultado)
                            
                            # Contar resultados
                            if resultado["status"] == "sucesso":
                                resultados["sucesso"] += 1
                            elif resultado["status"] == "duplicado":
                                resultados["duplicados"] += 1
                            else:
                                resultados["erros"] += 1
                            
                            # Atualizar progress bar
                            progress = 30 + (70 * (i + 1) / total_docs)
                            progress_bar.progress(int(progress))
                    
                    # Etapa 4: Finalização
                    progress_bar.progress(100)
                    status_placeholder.markdown('<div class="success-alert">✅ Processamento concluído com sucesso!</div>', unsafe_allow_html=True)
                    
                    # Exibir métricas
                    st.markdown("<br>", unsafe_allow_html=True)
                    metric_col1, metric_col2, metric_col3 = st.columns(3)
                    
                    with metric_col1:
                        st.metric(
                            label="✅ Pedidos Processados", 
                            value=resultados["sucesso"],
                            delta=f"+{resultados['sucesso']}" if resultados["sucesso"] > 0 else None
                        )
                    with metric_col2:
                        st.metric(
                            label="⚠️ Duplicados", 
                            value=resultados["duplicados"],
                            delta=f"{resultados['duplicados']}" if resultados["duplicados"] > 0 else None
                        )
                    with metric_col3:
                        st.metric(
                            label="❌ Erros", 
                            value=resultados["erros"],
                            delta=f"{resultados['erros']}" if resultados["erros"] > 0 else None
                        )
                    
                    # Detalhes dos processamentos
                    if detalhes_processamento:
                        st.markdown("<br>", unsafe_allow_html=True)
                        st.markdown("""
                        <div class="totvs-card">
                            <div class="totvs-card-header">
                                📋 Relatório Detalhado
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        for resultado in detalhes_processamento:
                            if resultado["status"] == "sucesso":
                                st.markdown(f'<div class="success-alert">{resultado["mensagem"]}</div>', unsafe_allow_html=True)
                            elif resultado["status"] == "duplicado":
                                st.markdown(f'<div class="warning-alert">{resultado["mensagem"]}</div>', unsafe_allow_html=True)
                            else:
                                st.markdown(f'<div class="error-alert">{resultado["mensagem"]}</div>', unsafe_allow_html=True)
                
            except Exception as e:
                erro_msg = f"💥 Erro crítico no processamento: {str(e)}"
                registrar_log(erro_msg)
                st.markdown(f'<div class="error-alert">{erro_msg}</div>', unsafe_allow_html=True)
                progress_bar.progress(0)
                status_placeholder.markdown('<div class="error-alert">❌ Processamento interrompido por erro</div>', unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="totvs-card">
        <div class="totvs-card-header">
            📊 Monitoramento
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Verificar se há logs
    if os.path.exists(LOG_FILE):
        st.markdown('<div class="success-alert">📝 Sistema de logs ativo</div>', unsafe_allow_html=True)
        
        # Mostrar últimas linhas do log
        try:
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                linhas = f.readlines()
                ultimas_linhas = linhas[-5:] if len(linhas) > 5 else linhas
                
            if ultimas_linhas:
                st.markdown("**Últimas atividades:**")
                for i, linha in enumerate(ultimas_linhas):
                    timestamp = linha.split(']')[0].replace('[', '')
                    mensagem = ']'.join(linha.split(']')[1:]).strip()
                    
                    if "✅" in mensagem:
                        icon = "🟢"
                    elif "⚠️" in mensagem:
                        icon = "🟡"
                    elif "❌" in mensagem:
                        icon = "🔴"
                    else:
                        icon = "ℹ️"
                    
                    st.markdown(f"""
                    <div style="
                        font-size: 0.8rem; 
                        padding: 0.5rem; 
                        margin: 0.25rem 0;
                        background: white;
                        border-radius: 8px;
                        border-left: 3px solid var(--totvs-primary);
                        ">
                        {icon} <strong>{timestamp}</strong><br>
                        {mensagem}
                    </div>
                    """, unsafe_allow_html=True)
        except Exception as e:
            st.markdown('<div class="error-alert">❌ Erro ao ler logs</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="status-indicator status-offline">📝 Aguardando execução</div>', unsafe_allow_html=True)

# Área de logs expandível
with st.expander("📜 Visualizar Histórico Completo de Logs", expanded=False):
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                conteudo_log = f.read()
            
            st.markdown("""
            <div class="totvs-card">
                <div class="totvs-card-header">
                    📋 Logs Completos do Sistema
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            st.text_area(
                "Histórico completo:",
                conteudo_log,
                height=400,
                help="Logs completos de todas as execuções do sistema"
            )
        except Exception as e:
            st.markdown(f'<div class="error-alert">❌ Erro ao carregar histórico: {str(e)}</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="warning-alert">📝 Nenhum histórico disponível. Execute o processo para gerar logs.</div>', unsafe_allow_html=True)

# Footer com informações
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("""
<div style="
    text-align: center; 
    padding: 2rem; 
    color: var(--totvs-neutral-500); 
    font-size: 0.9rem;
    border-top: 1px solid rgba(25, 118, 210, 0.1);
    margin-top: 2rem;
">
    <strong>TOTVS</strong> | Importador Neogrid v2.1.0<br>
    Desenvolvido para integração automatizada de pedidos
</div>
""", unsafe_allow_html=True)