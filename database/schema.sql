-- ============================================================================
-- SkyCamOS - Esquema Completo do Banco de Dados
-- Sistema de Monitoramento de Cameras IP
-- ============================================================================
-- Versao: 1.0.0
-- Data: 2025-11-22
-- Banco: SQLite 3
-- ============================================================================

-- Habilitar foreign keys (necessario para SQLite)
PRAGMA foreign_keys = ON;

-- Habilitar modo WAL para melhor performance de escrita concorrente
PRAGMA journal_mode = WAL;

-- ============================================================================
-- TABELA: usuarios
-- Descricao: Cadastro de usuarios do sistema
-- ============================================================================
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    senha_hash TEXT NOT NULL,
    ativo INTEGER DEFAULT 1 CHECK (ativo IN (0, 1)),
    admin INTEGER DEFAULT 0 CHECK (admin IN (0, 1)),
    push_token TEXT,
    ultimo_acesso DATETIME,
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,

    -- Restricoes adicionais
    CHECK (length(nome) >= 2),
    CHECK (length(email) >= 5),
    CHECK (email LIKE '%@%.%')
);

-- ============================================================================
-- TABELA: cameras
-- Descricao: Cadastro de cameras IP do sistema
-- ============================================================================
CREATE TABLE IF NOT EXISTS cameras (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    ip TEXT NOT NULL,
    porta INTEGER DEFAULT 554,
    usuario TEXT,
    senha_hash TEXT,
    protocolo TEXT DEFAULT 'rtsp' CHECK (protocolo IN ('rtsp', 'http', 'https', 'rtmp')),
    url_stream TEXT,
    onvif_ativo INTEGER DEFAULT 0 CHECK (onvif_ativo IN (0, 1)),
    onvif_porta INTEGER DEFAULT 80,
    status TEXT DEFAULT 'offline' CHECK (status IN ('online', 'offline', 'erro', 'manutencao')),
    deteccao_movimento INTEGER DEFAULT 1 CHECK (deteccao_movimento IN (0, 1)),
    sensibilidade_movimento INTEGER DEFAULT 50 CHECK (sensibilidade_movimento BETWEEN 0 AND 100),
    roi_movimento TEXT, -- JSON com regioes de interesse para deteccao
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
    atualizado_em DATETIME DEFAULT CURRENT_TIMESTAMP,

    -- Restricoes adicionais
    CHECK (length(nome) >= 1),
    CHECK (porta BETWEEN 1 AND 65535),
    CHECK (onvif_porta BETWEEN 1 AND 65535)
);

-- ============================================================================
-- TABELA: eventos_movimento
-- Descricao: Registro de eventos de deteccao de movimento
-- ============================================================================
CREATE TABLE IF NOT EXISTS eventos_movimento (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    camera_id INTEGER NOT NULL,
    timestamp DATETIME NOT NULL,
    duracao_segundos INTEGER,
    thumbnail_path TEXT,
    confianca REAL CHECK (confianca BETWEEN 0.0 AND 1.0),
    tipo_deteccao TEXT DEFAULT 'software' CHECK (tipo_deteccao IN ('software', 'onvif')),
    visualizado INTEGER DEFAULT 0 CHECK (visualizado IN (0, 1)),
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,

    -- Chave estrangeira
    FOREIGN KEY (camera_id) REFERENCES cameras(id) ON DELETE CASCADE ON UPDATE CASCADE
);

-- ============================================================================
-- TABELA: gravacoes
-- Descricao: Metadados das gravacoes de video
-- ============================================================================
CREATE TABLE IF NOT EXISTS gravacoes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    camera_id INTEGER NOT NULL,
    arquivo_path TEXT NOT NULL,
    inicio DATETIME NOT NULL,
    fim DATETIME,
    duracao_segundos INTEGER,
    tamanho_bytes INTEGER,
    tipo TEXT DEFAULT 'continua' CHECK (tipo IN ('continua', 'evento')),
    evento_id INTEGER,
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,

    -- Chaves estrangeiras
    FOREIGN KEY (camera_id) REFERENCES cameras(id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (evento_id) REFERENCES eventos_movimento(id) ON DELETE SET NULL ON UPDATE CASCADE,

    -- Restricoes adicionais
    CHECK (tamanho_bytes >= 0),
    CHECK (duracao_segundos >= 0)
);

-- ============================================================================
-- TABELA: configuracoes
-- Descricao: Configuracoes gerais do sistema
-- ============================================================================
CREATE TABLE IF NOT EXISTS configuracoes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chave TEXT UNIQUE NOT NULL,
    valor TEXT,
    tipo TEXT DEFAULT 'string' CHECK (tipo IN ('string', 'integer', 'boolean', 'json', 'float')),
    descricao TEXT,
    atualizado_em DATETIME DEFAULT CURRENT_TIMESTAMP,

    -- Restricoes
    CHECK (length(chave) >= 1)
);

-- ============================================================================
-- TABELA: sessoes
-- Descricao: Sessoes de autenticacao dos usuarios
-- ============================================================================
CREATE TABLE IF NOT EXISTS sessoes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER NOT NULL,
    token TEXT UNIQUE NOT NULL,
    ip_address TEXT,
    user_agent TEXT,
    expira_em DATETIME NOT NULL,
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,

    -- Chave estrangeira
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE ON UPDATE CASCADE
);

-- ============================================================================
-- TABELA: logs_sistema
-- Descricao: Registro de logs e eventos do sistema
-- ============================================================================
CREATE TABLE IF NOT EXISTS logs_sistema (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nivel TEXT DEFAULT 'info' CHECK (nivel IN ('debug', 'info', 'warning', 'error', 'critical')),
    modulo TEXT,
    mensagem TEXT NOT NULL,
    dados_extra TEXT, -- JSON com dados adicionais
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- INDICES
-- Descricao: Indices para otimizacao de queries frequentes
-- ============================================================================

-- Indices para tabela usuarios
CREATE INDEX IF NOT EXISTS idx_usuarios_email ON usuarios(email);
CREATE INDEX IF NOT EXISTS idx_usuarios_ativo ON usuarios(ativo);
CREATE INDEX IF NOT EXISTS idx_usuarios_ultimo_acesso ON usuarios(ultimo_acesso);

-- Indices para tabela cameras
CREATE INDEX IF NOT EXISTS idx_cameras_status ON cameras(status);
CREATE INDEX IF NOT EXISTS idx_cameras_ip ON cameras(ip);
CREATE INDEX IF NOT EXISTS idx_cameras_nome ON cameras(nome);

-- Indices para tabela eventos_movimento
CREATE INDEX IF NOT EXISTS idx_eventos_camera_id ON eventos_movimento(camera_id);
CREATE INDEX IF NOT EXISTS idx_eventos_timestamp ON eventos_movimento(timestamp);
CREATE INDEX IF NOT EXISTS idx_eventos_visualizado ON eventos_movimento(visualizado);
CREATE INDEX IF NOT EXISTS idx_eventos_camera_timestamp ON eventos_movimento(camera_id, timestamp);

-- Indices para tabela gravacoes
CREATE INDEX IF NOT EXISTS idx_gravacoes_camera_id ON gravacoes(camera_id);
CREATE INDEX IF NOT EXISTS idx_gravacoes_inicio ON gravacoes(inicio);
CREATE INDEX IF NOT EXISTS idx_gravacoes_tipo ON gravacoes(tipo);
CREATE INDEX IF NOT EXISTS idx_gravacoes_camera_inicio ON gravacoes(camera_id, inicio);
CREATE INDEX IF NOT EXISTS idx_gravacoes_evento_id ON gravacoes(evento_id);

-- Indices para tabela configuracoes
CREATE INDEX IF NOT EXISTS idx_configuracoes_chave ON configuracoes(chave);

-- Indices para tabela sessoes
CREATE INDEX IF NOT EXISTS idx_sessoes_usuario_id ON sessoes(usuario_id);
CREATE INDEX IF NOT EXISTS idx_sessoes_token ON sessoes(token);
CREATE INDEX IF NOT EXISTS idx_sessoes_expira_em ON sessoes(expira_em);

-- Indices para tabela logs_sistema
CREATE INDEX IF NOT EXISTS idx_logs_nivel ON logs_sistema(nivel);
CREATE INDEX IF NOT EXISTS idx_logs_modulo ON logs_sistema(modulo);
CREATE INDEX IF NOT EXISTS idx_logs_criado_em ON logs_sistema(criado_em);
CREATE INDEX IF NOT EXISTS idx_logs_nivel_criado ON logs_sistema(nivel, criado_em);

-- ============================================================================
-- TRIGGERS
-- Descricao: Triggers para automacao de atualizacoes
-- ============================================================================

-- Trigger: Atualizar timestamp da camera quando modificada
CREATE TRIGGER IF NOT EXISTS trg_cameras_atualizado_em
AFTER UPDATE ON cameras
FOR EACH ROW
BEGIN
    UPDATE cameras SET atualizado_em = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Trigger: Atualizar timestamp da configuracao quando modificada
CREATE TRIGGER IF NOT EXISTS trg_configuracoes_atualizado_em
AFTER UPDATE ON configuracoes
FOR EACH ROW
BEGIN
    UPDATE configuracoes SET atualizado_em = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Trigger: Atualizar ultimo_acesso do usuario quando sessao criada
CREATE TRIGGER IF NOT EXISTS trg_sessoes_ultimo_acesso
AFTER INSERT ON sessoes
FOR EACH ROW
BEGIN
    UPDATE usuarios SET ultimo_acesso = CURRENT_TIMESTAMP WHERE id = NEW.usuario_id;
END;

-- Trigger: Calcular duracao da gravacao quando fim for atualizado
CREATE TRIGGER IF NOT EXISTS trg_gravacoes_duracao
AFTER UPDATE OF fim ON gravacoes
FOR EACH ROW
WHEN NEW.fim IS NOT NULL AND NEW.inicio IS NOT NULL
BEGIN
    UPDATE gravacoes
    SET duracao_segundos = CAST((julianday(NEW.fim) - julianday(NEW.inicio)) * 86400 AS INTEGER)
    WHERE id = NEW.id;
END;

-- Trigger: Log automatico quando camera muda de status
CREATE TRIGGER IF NOT EXISTS trg_cameras_log_status
AFTER UPDATE OF status ON cameras
FOR EACH ROW
WHEN OLD.status != NEW.status
BEGIN
    INSERT INTO logs_sistema (nivel, modulo, mensagem, dados_extra)
    VALUES (
        'info',
        'cameras',
        'Camera ' || NEW.nome || ' mudou status de ' || OLD.status || ' para ' || NEW.status,
        json_object('camera_id', NEW.id, 'status_anterior', OLD.status, 'status_novo', NEW.status)
    );
END;

-- ============================================================================
-- VIEWS
-- Descricao: Views para consultas comuns
-- ============================================================================

-- View: Cameras com estatisticas de eventos
CREATE VIEW IF NOT EXISTS vw_cameras_estatisticas AS
SELECT
    c.id,
    c.nome,
    c.ip,
    c.status,
    c.deteccao_movimento,
    COUNT(DISTINCT e.id) AS total_eventos,
    COUNT(DISTINCT CASE WHEN e.visualizado = 0 THEN e.id END) AS eventos_nao_visualizados,
    COUNT(DISTINCT g.id) AS total_gravacoes,
    COALESCE(SUM(g.tamanho_bytes), 0) AS tamanho_total_bytes,
    MAX(e.timestamp) AS ultimo_evento,
    MAX(g.inicio) AS ultima_gravacao
FROM cameras c
LEFT JOIN eventos_movimento e ON e.camera_id = c.id
LEFT JOIN gravacoes g ON g.camera_id = c.id
GROUP BY c.id;

-- View: Eventos recentes (ultimas 24 horas)
CREATE VIEW IF NOT EXISTS vw_eventos_recentes AS
SELECT
    e.id,
    e.camera_id,
    c.nome AS camera_nome,
    e.timestamp,
    e.duracao_segundos,
    e.thumbnail_path,
    e.confianca,
    e.tipo_deteccao,
    e.visualizado
FROM eventos_movimento e
JOIN cameras c ON c.id = e.camera_id
WHERE e.timestamp >= datetime('now', '-24 hours')
ORDER BY e.timestamp DESC;

-- View: Gravacoes com informacoes da camera
CREATE VIEW IF NOT EXISTS vw_gravacoes_detalhadas AS
SELECT
    g.id,
    g.camera_id,
    c.nome AS camera_nome,
    g.arquivo_path,
    g.inicio,
    g.fim,
    g.duracao_segundos,
    g.tamanho_bytes,
    g.tipo,
    g.evento_id,
    e.confianca AS evento_confianca
FROM gravacoes g
JOIN cameras c ON c.id = g.camera_id
LEFT JOIN eventos_movimento e ON e.id = g.evento_id
ORDER BY g.inicio DESC;

-- View: Usuarios ativos com contagem de sessoes
CREATE VIEW IF NOT EXISTS vw_usuarios_sessoes AS
SELECT
    u.id,
    u.nome,
    u.email,
    u.ativo,
    u.admin,
    u.ultimo_acesso,
    COUNT(s.id) AS sessoes_ativas
FROM usuarios u
LEFT JOIN sessoes s ON s.usuario_id = u.id AND s.expira_em > CURRENT_TIMESTAMP
GROUP BY u.id;

-- View: Resumo do sistema
CREATE VIEW IF NOT EXISTS vw_resumo_sistema AS
SELECT
    (SELECT COUNT(*) FROM cameras) AS total_cameras,
    (SELECT COUNT(*) FROM cameras WHERE status = 'online') AS cameras_online,
    (SELECT COUNT(*) FROM cameras WHERE status = 'offline') AS cameras_offline,
    (SELECT COUNT(*) FROM usuarios WHERE ativo = 1) AS usuarios_ativos,
    (SELECT COUNT(*) FROM eventos_movimento WHERE visualizado = 0) AS eventos_pendentes,
    (SELECT COUNT(*) FROM gravacoes WHERE date(inicio) = date('now')) AS gravacoes_hoje,
    (SELECT COALESCE(SUM(tamanho_bytes), 0) FROM gravacoes) AS espaco_total_bytes,
    (SELECT COUNT(*) FROM sessoes WHERE expira_em > CURRENT_TIMESTAMP) AS sessoes_ativas;

-- View: Logs recentes com filtro de erros
CREATE VIEW IF NOT EXISTS vw_logs_erros AS
SELECT
    id,
    nivel,
    modulo,
    mensagem,
    dados_extra,
    criado_em
FROM logs_sistema
WHERE nivel IN ('error', 'critical')
ORDER BY criado_em DESC
LIMIT 100;

-- View: Configuracoes formatadas
CREATE VIEW IF NOT EXISTS vw_configuracoes AS
SELECT
    chave,
    valor,
    tipo,
    descricao,
    CASE tipo
        WHEN 'boolean' THEN CASE valor WHEN '1' THEN 'Sim' ELSE 'Nao' END
        ELSE valor
    END AS valor_formatado,
    atualizado_em
FROM configuracoes
ORDER BY chave;

-- ============================================================================
-- FIM DO ESQUEMA
-- ============================================================================
