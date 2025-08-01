﻿# 🔄 Sistema Importador Neogrid → Protheus

Sistema completo para importação automatizada de pedidos da API Neogrid para o ERP Protheus, desenvolvido em Python com interface Streamlit.

## 📋 Visão Geral

Este sistema processa pedidos recebidos da API Neogrid, valida clientes e produtos, e grava os dados nas tabelas do Protheus de forma automatizada, incluindo logs completos de auditoria.

### ✨ Funcionalidades Principais

- 🔍 **Consulta automatizada** da API Neogrid
- 👤 **Validação de clientes** contra tabela SA1010
- 📦 **Validação de produtos** via base JSON configurável
- 💾 **Gravação automática** nas tabelas T_PEDIDO_SOBEL e T_PEDIDOITEM_SOBEL
- 📊 **Interface web** com monitoramento em tempo real
- 📝 **Sistema de logs** detalhado com diferentes níveis
- 🔧 **Modo debug** para desenvolvimento e troubleshooting
- ⚡ **Tratamento robusto de erros** com retry automático

## 🏗️ Arquitetura do Sistema

```
neogrid-importer/
├── app/
│   ├── main.py                 # Interface Streamlit principal
│   └── assets/css/             # Estilos customizados
├── models/
│   ├── pedido.py              # Modelo para dados da Neogrid
│   ├── cliente.py             # Modelo de cliente
│   ├── produto.py             # Modelo de produto
│   ├── pedido_sobel.py        # Modelo final para Protheus
│   └── pedido_item_sobel.py   # Modelo de item para Protheus
├── services/
│   ├── api_client.py          # Cliente da API Neogrid
│   ├── validador_cliente.py   # Validação de clientes
│   ├── validador_produto.py   # Validação de produtos
│   ├── processador_pedido.py  # Processamento principal
│   ├── processador_pedido_item.py # Processamento de itens
│   └── database.py            # Gerenciamento de conexões
├── repositories/
│   └── pedido_repository.py   # Acesso a dados do banco
├── utils/
│   ├── helpers.py             # Funções auxiliares
│   ├── logger.py              # Sistema de logging
│   └── error_handler.py       # Tratamento de erros
├── data/
│   └── produtos.json          # Base de produtos
├── config/
│   └── settings.py            # Configurações do sistema
└── logs/                      # Arquivos de log
```

## 🚀 Instalação e Configuração

### 1. Implementação Automática (Recomendado)

```bash
# Clone ou baixe o projeto
git clone <url-do-repositorio>
cd neogrid-importer

# Execute o script de implementação completa
python implementar_sistema.py
```

O script automaticamente:
- ✅ Cria estrutura de diretórios
- ✅ Instala dependências
- ✅ Configura arquivos de exemplo
- ✅ Valida banco de dados
- ✅ Executa testes básicos
- ✅ Cria scripts de execução

### 2. Implementação Manual

#### Pré-requisitos
- Python 3.8+
- SQL Server com ODBC Driver 17
- Acesso à API Neogrid
- Acesso ao banco Protheus

#### Dependências
```bash
pip install -r requirements.txt
```

#### Configuração do Ambiente
1. Copie `.env.example` para `.env`
2. Configure as variáveis:

```env
# Banco de Dados
DB_HOST=192.168.0.16
DB_USER=sa
DB_PASSWORD=sua_senha
DB_NAME_PROTHEUS=Protheus_Producao
DB_DRIVER=ODBC Driver 17 for SQL Server

# API Neogrid
NEOGRID_USERNAME=seu_usuario
NEOGRID_PASSWORD=sua_senha
NEOGRID_URL=https://integration-br-prd.neogrid.com/rest/neogrid/ngproxy/Neogrid/restNew/receiverDocsFromNGProxy
```

#### Configuração dos Produtos
Execute uma vez para criar a base de produtos:
```bash
python setup_data.py
```

## 📊 Estrutura das Tabelas

### T_PEDIDO_SOBEL (Cabeçalho dos Pedidos)
```sql
CREATE TABLE T_PEDIDO_SOBEL (
    NUMPEDIDOSOBEL NVARCHAR(50) PRIMARY KEY,
    LOJACLIENTE NVARCHAR(10),
    DATAPEDIDO NVARCHAR(10),
    HORAINICIAL NVARCHAR(8),
    HORAFINAL NVARCHAR(8),
    DATAENTREGA NVARCHAR(10),
    CODIGOCLIENTE NVARCHAR(20) NOT NULL,
    QTDEITENS INT,
    VALORBRUTO DECIMAL(15,2),
    OBSERVACAOI NVARCHAR(500),
    DATAGRAVACAOACACIA DATETIME
)
```

### T_PEDIDOITEM_SOBEL (Itens dos Pedidos)
```sql
CREATE TABLE T_PEDIDOITEM_SOBEL (
    NUMPEDIDOAFV NVARCHAR(50) NOT NULL,
    DATAPEDIDO NVARCHAR(10),
    HORAINICIAL NVARCHAR(8),
    CODIGOCLIENTE NVARCHAR(20),
    CODIGOPRODUTO NVARCHAR(30) NOT NULL,
    QTDEVENDA DECIMAL(15,2),
    QTDEBONIFICADA DECIMAL(15,2),
    VALORVENDA DECIMAL(15,2),
    VALORBRUTO DECIMAL(15,2),
    DESCONTOI DECIMAL(15,2),
    DESCONTOII DECIMAL(15,2),
    VALORVERBA DECIMAL(15,2),
    CODIGOVENDEDORESP NVARCHAR(20),
    MSGIMPORTACAO NVARCHAR(100)
)
```

## 🎯 Como Usar

### Execução da Interface Web
```bash
# Método 1: Script automático (Windows)
executar_app.bat

# Método 2: Script automático (Linux/Mac)
./executar_app.sh

# Método 3: Manual
streamlit run app/main.py
```

### Interface Principal
1. **🔄 Buscar e Processar Pedidos** - Importa pedidos da Neogrid
2. **🔧 Configurações de Debug** - Ativa logs detalhados
3. **📊 Monitoramento** - Acompanha execução em tempo real
4. **📜 Histórico de Logs** - Visualiza logs completos

### Modo Debug
- Ative na barra lateral para ver logs SQL detalhados
- Ideal para desenvolvimento e troubleshooting
- Exporta informações de debug para arquivos

## 🔍 Validações e Processamento

### Fluxo de Processamento
1. **📡 Consulta API** - Busca novos pedidos na Neogrid
2. **🔍 Validação de Estrutura** - Verifica formato dos dados
3. **👤 Validação de Cliente** - Consulta tabela SA1010
4. **📦 Validação de Produtos** - Verifica base de produtos
5. **⚙️ Processamento** - Aplica regras de negócio
6. **💾 Gravação** - Insere dados no Protheus
7. **📝 Log de Auditoria** - Registra todas as operações

### Códigos de Produto Suportados
- **EAN13**: 13 dígitos (ex: `7896524726150`)
- **DUN14**: 14 dígitos (ex: `17896524703332`)
- **Código Interno**: Alfanumérico (ex: `1001.01.03X05L`)

### Validações Implementadas
- ✅ CNPJ do cliente deve existir na SA1010
- ✅ Cliente não pode estar bloqueado
- ✅ Produto deve existir na base configurada
- ✅ Produto deve estar ativo (flag_uso = 1)
- ✅ Quantidade deve ser maior que zero
- ✅ Valor unitário deve ser não-negativo
- ✅ Pedido não pode ser duplicado

## 📝 Sistema de Logs

### Níveis de Log
- **INFO**: Operações normais
- **WARNING**: Alertas e avisos
- **ERROR**: Erros que impedem processamento
- **DEBUG**: Informações detalhadas
- **SQL**: Queries executadas (modo debug)

### Arquivos de Log
- `logs/log_pedidos.txt` - Log principal
- `logs/sql_debug_*.txt` - Debug SQL (quando exportado)

### Estatísticas Disponíveis
- Total de pedidos processados
- Taxa de sucesso/erro
- Performance por operação
- Estatísticas de produtos/clientes

## 🧪 Testes e Validação

### Executar Testes Completos
```bash
# Método 1: Script automático (Windows)
testar_sistema.bat

# Método 2: Script automático (Linux/Mac)
./testar_sistema.sh

# Método 3: Manual
python verificar_sistema.py
```

### Testes Específicos
```bash
# Testar processamento
python teste_processamento.py

# Validar estrutura do banco
python validar_estrutura_banco.py

# Testes unitários
pytest tests/ -v
```

### Validação Manual
1. **Conectividade**: API + Banco
2. **Configurações**: Arquivo .env
3. **Dependências**: Pacotes Python
4. **Dados**: Base de produtos
5. **Processamento**: JSON → Banco

## 🔧 Manutenção e Monitoramento

### Monitoramento Regular
- 📊 Interface web mostra status em tempo real
- 📈 Métricas de performance disponíveis
- 🚨 Alertas automáticos para erros

### Manutenção da Base de Produtos
```python
# Atualizar data/produtos.json conforme necessário
{
  "produtos": [
    {
      "codigo": "1001.01.03X05L",
      "descricao": "AGUA SANIT SUPREMA 5L",
      "ean13": "7896524726150",
      "dun14": "27896524726154",
      "peso_bruto": 16.47,
      "peso_liquido": 16.12,
      "qtde_embalagem": 3,
      "unidade": "BX",
      "perc_acresc_max": 10.0,
      "flag_uso": 1,
      "flag_verba": 0
    }
  ]
}
```

### Limpeza de Logs
- Interface permite limpar logs via botão
- Logs são rotacionados automaticamente
- Debug SQL pode ser exportado antes da limpeza

## 🚨 Solução de Problemas

### Problemas Comuns

#### Erro de Conexão com Banco
```
✅ Verificar configurações no .env
✅ Testar conectividade: python validar_estrutura_banco.py
✅ Verificar se ODBC Driver 17 está instalado
```

#### Erro na API Neogrid
```
✅ Verificar credenciais no .env
✅ Testar conectividade na interface
✅ Verificar URLs da API
```

#### Cliente Não Encontrado
```
✅ Verificar se CNPJ existe na SA1010
✅ Verificar se cliente não está bloqueado
✅ Conferir formato do CNPJ (apenas números)
```

#### Produto Não Encontrado
```
✅ Atualizar data/produtos.json
✅ Verificar códigos EAN13/DUN14/Interno
✅ Confirmar flag_uso = 1
```

### Debug Avançado
1. Ativar modo debug na interface
2. Executar processo problemático
3. Exportar debug SQL
4. Analisar logs detalhados

## 📄 Documentação Adicional

- `README_ESTRUTURA_NEOGRID.md` - Estrutura detalhada dos dados
- `RELATORIO_IMPLEMENTACAO.md` - Relatório da implementação
- `ROADMAP.md` - Planejamento do projeto

## 🔐 Segurança

### Boas Práticas
- ✅ Credenciais apenas no arquivo .env
- ✅ .env incluído no .gitignore
- ✅ Conexões com timeout configurado
- ✅ Validação de entrada de dados
- ✅ Logs não expõem dados sensíveis

### Backup e Recuperação
- Fazer backup regular da base de produtos
- Manter histórico de logs importantes
- Documentar configurações específicas

## 📞 Suporte

### Estrutura de Suporte
1. **Consultar esta documentação**
2. **Executar testes de diagnóstico**
3. **Analisar logs de erro**
4. **Contatar equipe de desenvolvimento**

### Informações para Suporte
- Versão do Python: `python --version`
- Logs de erro: `logs/log_pedidos.txt`
- Configurações: `.env` (sem senhas)
- Resultado dos testes: `python verificar_sistema.py`

---

## 📊 Status do Projeto

**Versão Atual**: 1.2.0  
**Status**: ✅ Produção  
**Última Atualização**: Julho 2025  
**Python**: 3.8+  
**Dependências**: Atualizadas  

---

**Desenvolvido com ❤️ para integração TOTVS Protheus + Neogrid**
