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
from utils.helpers import interpretar_codigo_produto
from repositories.pedido_repository import PedidoRepository
from models.pedido import Pedido
from utils.error_handler import (
    NeogridError, ErrorHandler, ClienteNaoEncontradoError, 
    ProdutoNaoEncontradoError, PedidoDuplicadoError, APIError, BancoDadosError
)
from datetime import datetime
import json
import os
import time

# Importar sistema de logging melhorado
from utils.logger import logger, enable_debug_logging, disable_debug_logging, get_sql_debug_info

LOG_FILE = "logs/log_pedidos.txt"

def garantir_diretorio_logs():
    """Cria o diretório de logs se não existir"""
    os.makedirs("logs", exist_ok=True)

def registrar_log(mensagem: str):
    """Registra mensagem no arquivo de log usando o novo sistema"""
    logger.info(mensagem)

def processar_pedido_neogrid(doc, processador_pedido, repo, api_client=None):
    """Processa um documento de pedido da Neogrid com tratamento robusto de erros"""
    doc_id = doc.get("docId", "N/A")
    start_time = time.time()
    
    try:
        logger.debug(f"🔄 Iniciando processamento do documento {doc_id}")
        
        # Validar estrutura do documento
        if not doc.get("content") or len(doc["content"]) == 0:
            raise NeogridError(
                f"Documento {doc_id} sem conteúdo válido",
                "ERRO_VALIDACAO"
            )
            
        pedido_content = doc["content"][0]
        
        # Criar objeto Pedido a partir do JSON da Neogrid
        pedido_neogrid = Pedido(pedido_content)
        logger.debug(f"📋 Pedido Neogrid criado: {pedido_neogrid.numero_pedido}", pedido_neogrid.numero_pedido)
        
        # Montar estrutura para processamento interno
        pedido_para_processar = {
            "num_pedido": pedido_neogrid.numero_pedido,
            # Utiliza o docId como identificador interno (AFV)
            "num_pedido_afv": doc_id,
            "ordem_compra": pedido_neogrid.numero_pedido,
            "data_pedido": pedido_neogrid.data_emissao.strftime("%Y-%m-%d") if pedido_neogrid.data_emissao else "",
            "data_entrega": pedido_neogrid.data_entrega.strftime("%Y-%m-%d") if pedido_neogrid.data_entrega else None,
            "hora_inicio": datetime.now().strftime("%H:%M"),
            "hora_fim": None,
            "observacao": pedido_neogrid.condicao_entrega or "",
            "cnpj": pedido_neogrid.cnpj_destino,
            "itens": []
        }
        
        # Processar itens do pedido
        logger.debug(f"📦 Processando {len(pedido_neogrid.itens)} itens", pedido_neogrid.numero_pedido)
        for i, item in enumerate(pedido_neogrid.itens):
            ean13, dun14, codprod = interpretar_codigo_produto(item.codigo_produto)
            item_para_processar = {
                "ean13": ean13,
                "dun14": dun14,
                "codprod": codprod,
                "qtd": float(item.quantidade),
                "valor": float(item.preco_unitario)
            }
            pedido_para_processar["itens"].append(item_para_processar)
            logger.debug(f"  Item {i+1}: {codprod or ean13 or dun14} | Qtd: {item.quantidade}", pedido_neogrid.numero_pedido)
        
        # Processar usando as classes de negócio
        logger.debug(f"⚙️ Executando processamento de regras de negócio", pedido_neogrid.numero_pedido)
        pedido_final = processador_pedido.processar(pedido_para_processar)
        
        # Calcular tempo de processamento até aqui
        processing_time = time.time() - start_time
        logger.log_performance("PROCESSAR_PEDIDO", processing_time, {
            "pedido": pedido_final.num_pedido,
            "itens": len(pedido_final.itens)
        })
        
        # Gravar no banco
        logger.debug(f"💾 Iniciando gravação no banco", pedido_final.num_pedido)
        db_start_time = time.time()
        
        sucesso = repo.inserir_pedido(pedido_final)
        
        db_time = time.time() - db_start_time
        logger.log_performance("GRAVAR_BANCO", db_time, {
            "pedido": pedido_final.num_pedido,
            "sucesso": sucesso
        })
        
        if sucesso:
            total_time = time.time() - start_time
            mensagem = f"✅ Pedido {pedido_final.num_pedido} processado e gravado com sucesso"
            
            logger.log_pedido_processado(
                pedido_final.num_pedido, 
                pedido_final.codigo_cliente, 
                len(pedido_final.itens), 
                pedido_final.valor_total
            )
            logger.log_performance("TOTAL_PROCESSAMENTO", total_time, {
                "pedido": pedido_final.num_pedido,
                "doc_id": doc_id
            })
            
            repo.log_processamento("INFO", mensagem, pedido_final.num_pedido)

            if api_client:
                try:
                    api_client.atualizar_status([{"docId": doc_id, "status": "true"}])
                    logger.debug(f"✅ Status atualizado na Neogrid para documento {doc_id}")
                except APIError as e:
                    logger.warning(f"Falha ao atualizar status do documento {doc_id}: {e.message}")

            return {"status": "sucesso", "mensagem": mensagem, "pedido": pedido_final.num_pedido}
        else:
            mensagem = f"⚠️ Pedido {pedido_final.num_pedido} já existia no banco"
            logger.log_pedido_duplicado(pedido_final.num_pedido)
            return {"status": "duplicado", "mensagem": mensagem, "pedido": pedido_final.num_pedido}
            
    except ClienteNaoEncontradoError as e:
        erro_msg = ErrorHandler.format_error_for_ui(e)
        logger.log_cliente_nao_encontrado(e.details.get('cnpj', ''), e.details.get('num_pedido', doc_id))
        repo.log_processamento("ERROR", erro_msg, doc_id)
        return {"status": "erro", "mensagem": erro_msg, "doc_id": doc_id, "error_type": "cliente"}
        
    except ProdutoNaoEncontradoError as e:
        erro_msg = ErrorHandler.format_error_for_ui(e)
        logger.log_produto_nao_encontrado(
            e.details.get('ean13', ''),
            e.details.get('dun14', ''),
            e.details.get('codprod', ''),
            e.details.get('num_pedido', doc_id)
        )
        repo.log_processamento("ERROR", erro_msg, doc_id)
        return {"status": "erro", "mensagem": erro_msg, "doc_id": doc_id, "error_type": "produto"}
        
    except PedidoDuplicadoError as e:
        erro_msg = ErrorHandler.format_error_for_ui(e)
        logger.log_pedido_duplicado(e.details.get('num_pedido', doc_id))
        return {"status": "duplicado", "mensagem": erro_msg, "doc_id": doc_id}
        
    except NeogridError as e:
        erro_msg = ErrorHandler.format_error_for_ui(e)
        logger.error(f"Erro de processamento no documento {doc_id}: {e.message}")
        repo.log_processamento("ERROR", erro_msg, doc_id)
        return {"status": "erro", "mensagem": erro_msg, "doc_id": doc_id, "error_type": "processamento"}
        
    except Exception as e:
        erro_msg = f"❌ Erro inesperado ao processar documento {doc_id}: {str(e)}"
        logger.error(f"Erro inesperado no documento {doc_id}: {str(e)}")
        repo.log_processamento("ERROR", erro_msg, doc_id)
        return {"status": "erro", "mensagem": erro_msg, "doc_id": doc_id, "error_type": "inesperado"}

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
    initial_sidebar_state="collapsed"
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
        <p><strong>Versão:</strong> 1.2.0</p>
        <p><strong>Ambiente:</strong> QA</p>
        <p><strong>Última atualização:</strong> Jul 2025</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Controle do modo debug
    st.markdown("""
    <div class="totvs-card">
        <div class="totvs-card-header">
            🔧 Configurações de Debug
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    debug_mode = st.checkbox("🐛 Ativar modo debug", help="Mostra logs SQL detalhados")
    
    if debug_mode:
        enable_debug_logging()
        st.success("✅ Modo debug ativado")
    else:
        disable_debug_logging()
    
    st.markdown("""
    <div class="totvs-card">
        <div class="totvs-card-header">
            🔄 Processo de Importação
        </div>
        <div style="font-size: 0.9rem; line-height: 1.6;">
            <strong>1.</strong> Consulta API Neogrid<br>
            <strong>2.</strong> Valida clientes cadastrados<br>
            <strong>3.</strong> Valida produtos cadastrados<br>
            <strong>4.</strong> Processa regras de negócio<br>
            <strong>5.</strong> Grava pedidos no Protheus<br>
            <strong>6.</strong> Registra logs de auditoria
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Testar conectividade
    if st.button("🔧 Testar Conectividade", help="Testa conexão com API e Banco"):
        with st.spinner("Testando conectividade..."):
            # Testar API
            try:
                api = NeogridAPIClient()
                api_ok = api.test_connection()
                if api_ok:
                    st.success("✅ API Neogrid: OK")
                    logger.info("✅ Teste de conectividade API: OK")
                else:
                    st.error("❌ API Neogrid: Falha")
                    logger.error("❌ Teste de conectividade API: Falha")
            except Exception as e:
                st.error(f"❌ API Neogrid: {str(e)}")
                logger.error(f"❌ Teste de conectividade API: {str(e)}")
            
            # Testar Banco
            try:
                from services.database import Database
                from config.settings import settings
                db = Database(settings.DB_NAME_PROTHEUS)
                banco_ok = db.test_connection()
                if banco_ok:
                    st.success("✅ Banco Protheus: OK")
                    logger.info("✅ Teste de conectividade Banco: OK")
                else:
                    st.error("❌ Banco Protheus: Falha")
                    logger.error("❌ Teste de conectividade Banco: Falha")
            except Exception as e:
                st.error(f"❌ Banco Protheus: {str(e)}")
                logger.error(f"❌ Teste de conectividade Banco: {str(e)}")
    
    # Debug SQL
    if debug_mode:
        st.markdown("""
        <div class="totvs-card">
            <div class="totvs-card-header">
                🔍 Debug SQL
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("📊 Ver Queries Recentes"):
            sql_info = get_sql_debug_info()
            
            st.markdown(f"**Buffer SQL:** {sql_info['buffer_size']} queries")
            st.markdown(f"**Queries com erro:** {len(sql_info['failed_queries'])}")
            
            if sql_info['failed_queries']:
                st.markdown("**🔴 Queries que falharam:**")
                for query_info in sql_info['failed_queries'][-3:]:
                    st.code(f"[{query_info['operation']}] {query_info['query']}", language="sql")
                    st.error(f"Erro: {query_info['error']}")
        
        if st.button("📄 Exportar Debug SQL"):
            filepath = logger.export_sql_debug()
            if filepath:
                st.success(f"✅ Debug exportado: {filepath}")
            else:
                st.error("❌ Erro ao exportar debug")
    
    # Status do sistema
    status_sistema = "🟢 Online"
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
    
    # Estatísticas de log
    try:
        log_stats = logger.get_log_stats()
        st.markdown(f"""
        <div class="totvs-card">
            <div class="totvs-card-header">
                📈 Estatísticas de Log
            </div>
            <div style="font-size: 0.9rem;">
                <strong>Total:</strong> {log_stats['total_lines']}<br>
                <strong>Info:</strong> {log_stats['info']}<br>
                <strong>Warnings:</strong> {log_stats['warning']}<br>
                <strong>Errors:</strong> {log_stats['error']}<br>
                <strong>Debug:</strong> {log_stats['debug']}<br>
                <strong>SQL:</strong> {log_stats['sql']}<br>
                <strong>SQL Errors:</strong> {log_stats['sql_errors']}
            </div>
        </div>
        """, unsafe_allow_html=True)
    except:
        pass
    
    # Botão para limpar logs
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🗑️ Limpar Logs", key="clear_logs", help="Remove todos os arquivos de log"):
        try:
            logger.clear_logs()
            st.success("✅ Logs removidos com sucesso!")
            st.rerun()
        except Exception as e:
            st.error(f"❌ Erro ao limpar logs: {e}")

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
                
                logger.info("🚀 Iniciando processo de importação de pedidos")
                start_total_time = time.time()
                
                # Inicializar serviços
                api = NeogridAPIClient()
                validador_cliente = ValidadorCliente()
                validador_produto = ValidadorProduto()
                processador_item = ProcessadorPedidoItem(validador_produto)
                processador_pedido = ProcessadorPedido(validador_cliente, processador_item)
                
                progress_bar.progress(20)
                logger.debug("🔧 Serviços inicializados com sucesso")
                
                # Etapa 2: Consulta API
                status_placeholder.markdown('<div class="loading-text">🔍 Consultando API da Neogrid...</div>', unsafe_allow_html=True)
                
                try:
                    api_start_time = time.time()
                    resposta = api.buscar_pedidos()
                    api_time = time.time() - api_start_time
                    logger.log_performance("CONSULTA_API", api_time)
                    
                except APIError as e:
                    st.markdown(f'<div class="error-alert">{ErrorHandler.format_error_for_ui(e)}</div>', unsafe_allow_html=True)
                    logger.log_erro_api(e.message)
                    st.stop()
                
                if "documents" not in resposta or not resposta["documents"]:
                    st.markdown('<div class="warning-alert">🔍 Nenhum pedido encontrado na Neogrid no momento.</div>', unsafe_allow_html=True)
                    logger.info("🔍 Nenhum pedido retornado pela API Neogrid")
                else:
                    documentos = resposta["documents"]
                    total_docs = len(documentos)
                    
                    st.markdown(f'<div class="success-alert">📄 {total_docs} documento(s) recebido(s) da Neogrid para processamento.</div>', unsafe_allow_html=True)
                    logger.log_inicio_processamento(total_docs)
                    progress_bar.progress(30)
                    
                    # Etapa 3: Processamento
                    resultados = {"sucesso": 0, "duplicados": 0, "erros": 0}
                    detalhes_processamento = []
                    estatisticas_erro = {"cliente": 0, "produto": 0, "processamento": 0, "inesperado": 0}
                    
                    with PedidoRepository() as repo:
                        for i, doc in enumerate(documentos):
                            status_placeholder.markdown(f'<div class="loading-text">⚙️ Processando documento {i+1} de {total_docs}...</div>', unsafe_allow_html=True)
                            
                            resultado = processar_pedido_neogrid(doc, processador_pedido, repo, api)
                            detalhes_processamento.append(resultado)
                            
                            # Contar resultados
                            if resultado["status"] == "sucesso":
                                resultados["sucesso"] += 1
                            elif resultado["status"] == "duplicado":
                                resultados["duplicados"] += 1
                            else:
                                resultados["erros"] += 1
                                # Contar tipos de erro
                                error_type = resultado.get("error_type", "inesperado")
                                if error_type in estatisticas_erro:
                                    estatisticas_erro[error_type] += 1
                            
                            # Atualizar progress bar
                            progress = 30 + (70 * (i + 1) / total_docs)
                            progress_bar.progress(int(progress))
                    
                    # Etapa 4: Finalização
                    progress_bar.progress(100)
                    status_placeholder.markdown('<div class="success-alert">✅ Processamento concluído com sucesso!</div>', unsafe_allow_html=True)
                    
                    total_time = time.time() - start_total_time
                    logger.log_fim_processamento(resultados["sucesso"], resultados["duplicados"], resultados["erros"])
                    logger.log_performance("PROCESSAMENTO_COMPLETO", total_time, {
                        "total_docs": total_docs,
                        "sucessos": resultados["sucesso"],
                        "erros": resultados["erros"]
                    })
                    
                    # Exibir métricas
                    st.markdown("<br>", unsafe_allow_html=True)
                    metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
                    
                    with metric_col1:
                        st.metric(
                            label="✅ Processados", 
                            value=resultados["sucesso"],
                            delta=f"+{resultados['sucesso']}" if resultados["sucesso"] > 0 else None
                        )
                    with metric_col2:
                        st.metric(
                            label="⚠️ Duplicados", 
                            value=resultados["duplicados"]
                        )
                    with metric_col3:
                        st.metric(
                            label="❌ Erros", 
                            value=resultados["erros"]
                        )
                    with metric_col4:
                        st.metric(
                            label="📊 Total", 
                            value=total_docs
                        )
                    
                    # Estatísticas de erro detalhadas
                    if resultados["erros"] > 0:
                        st.markdown("**📊 Detalhamento dos Erros:**")
                        error_cols = st.columns(4)
                        with error_cols[0]:
                            st.metric("👤 Cliente", estatisticas_erro["cliente"])
                        with error_cols[1]:
                            st.metric("📦 Produto", estatisticas_erro["produto"])
                        with error_cols[2]:
                            st.metric("⚙️ Processamento", estatisticas_erro["processamento"])
                        with error_cols[3]:
                            st.metric("❓ Outros", estatisticas_erro["inesperado"])
                    
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
                        
                        # Agrupar resultados por tipo
                        sucessos = [r for r in detalhes_processamento if r["status"] == "sucesso"]
                        duplicados = [r for r in detalhes_processamento if r["status"] == "duplicado"]
                        erros = [r for r in detalhes_processamento if r["status"] == "erro"]
                        
                        # Mostrar sucessos (limitado)
                        if sucessos:
                            st.markdown("**✅ Pedidos Processados com Sucesso:**")
                            for resultado in sucessos[:5]:  # Mostrar apenas os primeiros 5
                                st.markdown(f'<div class="success-alert">{resultado["mensagem"]}</div>', unsafe_allow_html=True)
                            if len(sucessos) > 5:
                                st.markdown(f"*... e mais {len(sucessos) - 5} pedidos processados com sucesso.*")
                        
                        # Mostrar duplicados (limitado)
                        if duplicados:
                            st.markdown("**⚠️ Pedidos Duplicados:**")
                            for resultado in duplicados[:3]:
                                st.markdown(f'<div class="warning-alert">{resultado["mensagem"]}</div>', unsafe_allow_html=True)
                            if len(duplicados) > 3:
                                st.markdown(f"*... e mais {len(duplicados) - 3} pedidos duplicados.*")
                        
                        # Mostrar erros (limitado)
                        if erros:
                            st.markdown("**❌ Erros de Processamento:**")
                            for resultado in erros[:10]:  # Mostrar mais erros para análise
                                st.markdown(f'<div class="error-alert">{resultado["mensagem"]}</div>', unsafe_allow_html=True)
                            if len(erros) > 10:
                                st.markdown(f"*... e mais {len(erros) - 10} erros. Consulte os logs para detalhes completos.*")
                
            except APIError as e:
                erro_msg = ErrorHandler.format_error_for_ui(e)
                logger.log_erro_api(e.message)
                st.markdown(f'<div class="error-alert">{erro_msg}</div>', unsafe_allow_html=True)
                progress_bar.progress(0)
                status_placeholder.markdown('<div class="error-alert">❌ Falha na consulta da API</div>', unsafe_allow_html=True)
                
            except BancoDadosError as e:
                erro_msg = ErrorHandler.format_error_for_ui(e)
                logger.log_erro_banco(e.message)
                st.markdown(f'<div class="error-alert">{erro_msg}</div>', unsafe_allow_html=True)
                progress_bar.progress(0)
                status_placeholder.markdown('<div class="error-alert">❌ Falha na conexão com o banco</div>', unsafe_allow_html=True)
                
            except Exception as e:
                erro_msg = f"💥 Erro crítico no processamento: {str(e)}"
                logger.error(f"💥 Erro crítico no processamento: {str(e)}")
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
    log_lines = logger.get_log_lines(5)
    if log_lines:
        st.markdown('<div class="success-alert">📝 Sistema de logs ativo</div>', unsafe_allow_html=True)
        
        st.markdown("**Últimas atividades:**")
        for linha in log_lines:
            try:
                # Extrair timestamp e mensagem
                parts = linha.split('] ', 2)
                if len(parts) >= 3:
                    timestamp = parts[0].replace('[', '')
                    level = parts[1].replace('[', '')
                    mensagem = parts[2].strip()
                    
                    if "✅" in mensagem or "INFO" in level:
                        icon = "🟢"
                    elif "⚠️" in mensagem or "WARNING" in level:
                        icon = "🟡"
                    elif "❌" in mensagem or "ERROR" in level:
                        icon = "🔴"
                    elif "DEBUG" in level or "SQL" in mensagem:
                        icon = "🔵"
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
                        {mensagem[:100]}{'...' if len(mensagem) > 100 else ''}
                    </div>
                    """, unsafe_allow_html=True)
            except:
                # Se falhar o parsing, mostrar linha simples
                st.markdown(f"📝 {linha.strip()[:100]}...")
    else:
        st.markdown('<div class="status-indicator status-offline">📝 Aguardando execução</div>', unsafe_allow_html=True)

# Área de logs expandível
with st.expander("📜 Visualizar Histórico Completo de Logs", expanded=False):
    try:
        all_log_lines = logger.get_log_lines(200)  # Últimas 200 linhas
        
        if all_log_lines:
            st.markdown("""
            <div class="totvs-card">
                <div class="totvs-card-header">
                    📋 Logs Completos do Sistema
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            log_content = ''.join(all_log_lines)
            st.text_area(
                "Histórico completo:",
                log_content,
                height=400,
                help="Logs completos de todas as execuções do sistema"
            )
        else:
            st.markdown('<div class="warning-alert">📝 Nenhum histórico disponível. Execute o processo para gerar logs.</div>', unsafe_allow_html=True)
    except Exception as e:
        st.markdown(f'<div class="error-alert">❌ Erro ao carregar histórico: {str(e)}</div>', unsafe_allow_html=True)

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
    <strong>TOTVS</strong> | Importador Neogrid v1.2.0<br>
    Desenvolvido para integração automatizada de pedidos</strong> 
</div>
""", unsafe_allow_html=True)