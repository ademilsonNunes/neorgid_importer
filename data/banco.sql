-- Estrutura das Tabelas para o Sistema de Importação Neogrid
-- Database: Protheus_Producao

-- ============================================
-- Tabela Principal de Pedidos
-- ============================================

IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='T_PEDIDO_SOBEL' AND xtype='U')
BEGIN
    CREATE TABLE T_PEDIDO_SOBEL (
        NUM_PEDIDO VARCHAR(50) NOT NULL PRIMARY KEY,
        CODIGO_CLIENTE VARCHAR(20) NOT NULL,
        DATA_PEDIDO DATE NOT NULL,
        DATA_ENTREGA DATE NULL,
        QTDE_ITENS INT NOT NULL DEFAULT 0,
        VALOR_TOTAL DECIMAL(15,2) NOT NULL DEFAULT 0.00,
        OBSERVACAO VARCHAR(500) NULL,
        CREATED_AT DATETIME NOT NULL DEFAULT GETDATE(),
        UPDATED_AT DATETIME NULL,
        STATUS_PEDIDO VARCHAR(20) DEFAULT 'IMPORTADO'
    );
    
    PRINT 'Tabela T_PEDIDO_SOBEL criada com sucesso';
END
ELSE
BEGIN
    PRINT 'Tabela T_PEDIDO_SOBEL já existe';
END

-- ============================================
-- Tabela de Itens dos Pedidos
-- ============================================

IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='T_PEDIDOITEM_SOBEL' AND xtype='U')
BEGIN
    CREATE TABLE T_PEDIDOITEM_SOBEL (
        ID INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
        NUM_PEDIDO VARCHAR(50) NOT NULL,
        COD_PRODUTO VARCHAR(30) NOT NULL,
        DESCRICAO_PRODUTO VARCHAR(100) NOT NULL,
        QUANTIDADE DECIMAL(15,3) NOT NULL DEFAULT 0.000,
        VALOR_UNITARIO DECIMAL(15,2) NOT NULL DEFAULT 0.00,
        VALOR_TOTAL DECIMAL(15,2) NOT NULL DEFAULT 0.00,
        UNIDADE VARCHAR(10) NOT NULL,
        EAN13 VARCHAR(20) NULL,
        DUN14 VARCHAR(20) NULL,
        CREATED_AT DATETIME NOT NULL DEFAULT GETDATE()
    );
    
    PRINT 'Tabela T_PEDIDOITEM_SOBEL criada com sucesso';
END
ELSE
BEGIN
    PRINT 'Tabela T_PEDIDOITEM_SOBEL já existe';
END

-- ============================================
-- Tabela de Log de Processamento
-- ============================================

IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='T_LOG_PROCESSAMENTO' AND xtype='U')
BEGIN
    CREATE TABLE T_LOG_PROCESSAMENTO (
        ID INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
        DATA_HORA DATETIME NOT NULL DEFAULT GETDATE(),
        TIPO VARCHAR(20) NOT NULL, -- INFO, ERROR, WARNING, DEBUG
        MENSAGEM VARCHAR(1000) NOT NULL,
        NUM_PEDIDO VARCHAR(50) NULL,
        DETALHES TEXT NULL,
        USUARIO VARCHAR(50) DEFAULT SYSTEM_USER,
        IP_ADDRESS VARCHAR(50) NULL
    );
    
    PRINT 'Tabela T_LOG_PROCESSAMENTO criada com sucesso';
END
ELSE
BEGIN
    PRINT 'Tabela T_LOG_PROCESSAMENTO já existe';
END

-- ============================================
-- Tabela de Controle de Importação
-- ============================================

IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='T_CONTROLE_IMPORTACAO' AND xtype='U')
BEGIN
    CREATE TABLE T_CONTROLE_IMPORTACAO (
        ID INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
        DATA_IMPORTACAO DATETIME NOT NULL DEFAULT GETDATE(),
        TOTAL_DOCUMENTOS INT NOT NULL DEFAULT 0,
        PEDIDOS_PROCESSADOS INT NOT NULL DEFAULT 0,
        PEDIDOS_DUPLICADOS INT NOT NULL DEFAULT 0,
        PEDIDOS_ERRO INT NOT NULL DEFAULT 0,
        TEMPO_PROCESSAMENTO_SEGUNDOS INT NULL,
        STATUS_IMPORTACAO VARCHAR(20) DEFAULT 'CONCLUIDA', -- INICIADA, CONCLUIDA, ERRO
        OBSERVACOES TEXT NULL
    );
    
    PRINT 'Tabela T_CONTROLE_IMPORTACAO criada com sucesso';
END
ELSE
BEGIN
    PRINT 'Tabela T_CONTROLE_IMPORTACAO já existe';
END

-- ============================================
-- Chaves Estrangeiras e Constraints
-- ============================================

-- Foreign Key: T_PEDIDOITEM_SOBEL -> T_PEDIDO_SOBEL
IF NOT EXISTS (SELECT * FROM sys.foreign_keys WHERE name = 'FK_PEDIDOITEM_PEDIDO')
BEGIN
    ALTER TABLE T_PEDIDOITEM_SOBEL 
    ADD CONSTRAINT FK_PEDIDOITEM_PEDIDO 
    FOREIGN KEY (NUM_PEDIDO) REFERENCES T_PEDIDO_SOBEL(NUM_PEDIDO)
    ON DELETE CASCADE;
    
    PRINT 'Foreign Key FK_PEDIDOITEM_PEDIDO criada';
END

-- Check Constraints
IF NOT EXISTS (SELECT * FROM sys.check_constraints WHERE name = 'CK_PEDIDO_QTDE_POSITIVA')
BEGIN
    ALTER TABLE T_PEDIDO_SOBEL 
    ADD CONSTRAINT CK_PEDIDO_QTDE_POSITIVA 
    CHECK (QTDE_ITENS >= 0);
    
    PRINT 'Constraint CK_PEDIDO_QTDE_POSITIVA criada';
END

IF NOT EXISTS (SELECT * FROM sys.check_constraints WHERE name = 'CK_PEDIDO_VALOR_POSITIVO')
BEGIN
    ALTER TABLE T_PEDIDO_SOBEL 
    ADD CONSTRAINT CK_PEDIDO_VALOR_POSITIVO 
    CHECK (VALOR_TOTAL >= 0);
    
    PRINT 'Constraint CK_PEDIDO_VALOR_POSITIVO criada';
END

IF NOT EXISTS (SELECT * FROM sys.check_constraints WHERE name = 'CK_ITEM_QTD_POSITIVA')
BEGIN
    ALTER TABLE T_PEDIDOITEM_SOBEL 
    ADD CONSTRAINT CK_ITEM_QTD_POSITIVA 
    CHECK (QUANTIDADE > 0);
    
    PRINT 'Constraint CK_ITEM_QTD_POSITIVA criada';
END

-- ============================================
-- Índices para Performance
-- ============================================

-- Índice na data do pedido
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_PEDIDO_DATA')
BEGIN
    CREATE INDEX IX_PEDIDO_DATA ON T_PEDIDO_SOBEL (DATA_PEDIDO DESC);
    PRINT 'Índice IX_PEDIDO_DATA criado';
END

-- Índice no código do cliente
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_PEDIDO_CLIENTE')
BEGIN
    CREATE INDEX IX_PEDIDO_CLIENTE ON T_PEDIDO_SOBEL (CODIGO_CLIENTE);
    PRINT 'Índice IX_PEDIDO_CLIENTE criado';
END

-- Índice no código do produto
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_ITEM_PRODUTO')
BEGIN
    CREATE INDEX IX_ITEM_PRODUTO ON T_PEDIDOITEM_SOBEL (COD_PRODUTO);
    PRINT 'Índice IX_ITEM_PRODUTO criado';
END

-- Índice na data/hora do log
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_LOG_DATA')
BEGIN
    CREATE INDEX IX_LOG_DATA ON T_LOG_PROCESSAMENTO (DATA_HORA DESC);
    PRINT 'Índice IX_LOG_DATA criado';
END

-- Índice no tipo de log
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_LOG_TIPO')
BEGIN
    CREATE INDEX IX_LOG_TIPO ON T_LOG_PROCESSAMENTO (TIPO);
    PRINT 'Índice IX_LOG_TIPO criado';
END

-- ============================================
-- Views para Consultas
-- ============================================

-- View para pedidos com informações consolidadas
IF EXISTS (SELECT * FROM sys.views WHERE name = 'V_PEDIDOS_CONSOLIDADO')
    DROP VIEW V_PEDIDOS_CONSOLIDADO;

CREATE VIEW V_PEDIDOS_CONSOLIDADO AS
SELECT 
    p.NUM_PEDIDO,
    p.CODIGO_CLIENTE,
    c.A1_NOME as NOME_CLIENTE,
    c.A1_NREDUZ as FANTASIA_CLIENTE,
    p.DATA_PEDIDO,
    p.DATA_ENTREGA,
    p.QTDE_ITENS,
    p.VALOR_TOTAL,
    p.STATUS_PEDIDO,
    p.CREATED_AT as DATA_IMPORTACAO,
    DATEDIFF(day, p.DATA_PEDIDO, GETDATE()) as DIAS_DESDE_PEDIDO
FROM T_PEDIDO_SOBEL p
LEFT JOIN SA1010 c ON c.A1_COD = p.CODIGO_CLIENTE AND c.D_E_L_E_T_ = '';

PRINT 'View V_PEDIDOS_CONSOLIDADO criada';

-- View para relatório de importações
IF EXISTS (SELECT * FROM sys.views WHERE name = 'V_RELATORIO_IMPORTACOES')
    DROP VIEW V_RELATORIO_IMPORTACOES;

CREATE VIEW V_RELATORIO_IMPORTACOES AS
SELECT 
    CONVERT(DATE, DATA_IMPORTACAO) as DATA_IMPORTACAO,
    COUNT(*) as TOTAL_IMPORTACOES,
    SUM(PEDIDOS_PROCESSADOS) as TOTAL_PROCESSADOS,
    SUM(PEDIDOS_DUPLICADOS) as TOTAL_DUPLICADOS,
    SUM(PEDIDOS_ERRO) as TOTAL_ERROS,
    AVG(TEMPO_PROCESSAMENTO_SEGUNDOS) as TEMPO_MEDIO_SEG
FROM T_CONTROLE_IMPORTACAO
GROUP BY CONVERT(DATE, DATA_IMPORTACAO);

PRINT 'View V_RELATORIO_IMPORTACOES criada';

-- ============================================
-- Stored Procedures Auxiliares
-- ============================================

-- Procedure para limpeza de logs antigos
IF EXISTS (SELECT * FROM sys.procedures WHERE name = 'SP_LIMPAR_LOGS_ANTIGOS')
    DROP PROCEDURE SP_LIMPAR_LOGS_ANTIGOS;

CREATE PROCEDURE SP_LIMPAR_LOGS_ANTIGOS
    @DiasParaManter INT = 30
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @DataCorte DATETIME = DATEADD(day, -@DiasParaManter, GETDATE());
    
    DELETE FROM T_LOG_PROCESSAMENTO 
    WHERE DATA_HORA < @DataCorte;
    
    PRINT CONCAT('Logs anteriores a ', @DataCorte, ' foram removidos');
END

PRINT 'Procedure SP_LIMPAR_LOGS_ANTIGOS criada';

-- Procedure para estatísticas de pedidos
IF EXISTS (SELECT * FROM sys.procedures WHERE name = 'SP_ESTATISTICAS_PEDIDOS')
    DROP PROCEDURE SP_ESTATISTICAS_PEDIDOS;

CREATE PROCEDURE SP_ESTATISTICAS_PEDIDOS
    @DataInicio DATE = NULL,
    @DataFim DATE = NULL
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Default para últimos 30 dias se não especificado
    IF @DataInicio IS NULL SET @DataInicio = DATEADD(day, -30, GETDATE());
    IF @DataFim IS NULL SET @DataFim = GETDATE();
    
    SELECT 
        'Pedidos no Período' as ESTATISTICA,
        COUNT(*) as TOTAL_PEDIDOS,
        SUM(QTDE_ITENS) as TOTAL_ITENS,
        SUM(VALOR_TOTAL) as VALOR_TOTAL_PERIODO,
        AVG(VALOR_TOTAL) as VALOR_MEDIO_PEDIDO,
        COUNT(DISTINCT CODIGO_CLIENTE) as CLIENTES_DISTINTOS
    FROM T_PEDIDO_SOBEL
    WHERE DATA_PEDIDO BETWEEN @DataInicio AND @DataFim;
    
    -- Top 10 clientes
    SELECT TOP 10
        CODIGO_CLIENTE,
        COUNT(*) as QTD_PEDIDOS,
        SUM(VALOR_TOTAL) as VALOR_TOTAL
    FROM T_PEDIDO_SOBEL
    WHERE DATA_PEDIDO BETWEEN @DataInicio AND @DataFim
    GROUP BY CODIGO_CLIENTE
    ORDER BY SUM(VALOR_TOTAL) DESC;
END

PRINT 'Procedure SP_ESTATISTICAS_PEDIDOS criada';

PRINT '============================================';
PRINT 'Estrutura do banco criada com sucesso!';
PRINT '============================================';