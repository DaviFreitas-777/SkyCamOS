-- ============================================================================
-- Migration 002: Dados Iniciais (Seed)
-- SkyCamOS - Sistema de Monitoramento de Cameras IP
-- ============================================================================
-- Versao: 1.0.0
-- Data: 2025-11-22
-- Descricao: Insercao de dados iniciais para funcionamento do sistema
-- ============================================================================

-- Habilitar foreign keys
PRAGMA foreign_keys = ON;

-- ============================================================================
-- USUARIO ADMINISTRADOR PADRAO
-- ============================================================================
-- Senha padrao: admin123 (hash SHA-256 com salt)
-- IMPORTANTE: Alterar a senha apos primeiro acesso!
INSERT OR IGNORE INTO usuarios (nome, email, senha_hash, ativo, admin)
VALUES (
    'Administrador',
    'admin@skycamos.local',
    'pbkdf2:sha256:600000$skycamos$a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6',
    1,
    1
);

-- ============================================================================
-- CONFIGURACOES DO SISTEMA
-- ============================================================================

-- Configuracoes Gerais
INSERT OR IGNORE INTO configuracoes (chave, valor, tipo, descricao) VALUES
('app_nome', 'SkyCamOS', 'string', 'Nome do aplicativo'),
('app_versao', '1.0.0', 'string', 'Versao atual do sistema'),
('app_idioma', 'pt-BR', 'string', 'Idioma padrao do sistema');

-- Configuracoes de Gravacao
INSERT OR IGNORE INTO configuracoes (chave, valor, tipo, descricao) VALUES
('gravacao_diretorio', '/var/lib/skycamos/recordings', 'string', 'Diretorio padrao para gravacoes'),
('gravacao_formato', 'mp4', 'string', 'Formato de video para gravacoes (mp4, mkv, avi)'),
('gravacao_qualidade', 'high', 'string', 'Qualidade de gravacao (low, medium, high)'),
('gravacao_segmento_minutos', '15', 'integer', 'Duracao de cada segmento de gravacao em minutos'),
('gravacao_retencao_dias', '30', 'integer', 'Dias para manter gravacoes antes de excluir automaticamente'),
('gravacao_continua_ativa', '0', 'boolean', 'Gravacao continua habilitada por padrao'),
('gravacao_espaco_minimo_gb', '10', 'integer', 'Espaco minimo em disco para permitir gravacoes (GB)');

-- Configuracoes de Deteccao de Movimento
INSERT OR IGNORE INTO configuracoes (chave, valor, tipo, descricao) VALUES
('movimento_sensibilidade_padrao', '50', 'integer', 'Sensibilidade padrao para deteccao (0-100)'),
('movimento_pre_gravacao_seg', '5', 'integer', 'Segundos para gravar antes do evento'),
('movimento_pos_gravacao_seg', '10', 'integer', 'Segundos para gravar apos o evento'),
('movimento_intervalo_minimo_seg', '3', 'integer', 'Intervalo minimo entre eventos (segundos)'),
('movimento_notificar_push', '1', 'boolean', 'Enviar notificacao push em eventos de movimento'),
('movimento_salvar_thumbnail', '1', 'boolean', 'Salvar thumbnail do evento de movimento');

-- Configuracoes de Servidor/Rede
INSERT OR IGNORE INTO configuracoes (chave, valor, tipo, descricao) VALUES
('servidor_porta', '8080', 'integer', 'Porta do servidor web'),
('servidor_ssl_ativo', '0', 'boolean', 'Habilitar HTTPS'),
('servidor_ssl_porta', '8443', 'integer', 'Porta HTTPS'),
('servidor_timeout_conexao', '30', 'integer', 'Timeout de conexao em segundos'),
('servidor_max_conexoes', '100', 'integer', 'Numero maximo de conexoes simultaneas');

-- Configuracoes de Autenticacao
INSERT OR IGNORE INTO configuracoes (chave, valor, tipo, descricao) VALUES
('auth_sessao_duracao_horas', '24', 'integer', 'Duracao da sessao em horas'),
('auth_tentativas_max', '5', 'integer', 'Tentativas maximas de login antes de bloqueio'),
('auth_bloqueio_minutos', '15', 'integer', 'Duracao do bloqueio apos tentativas excedidas'),
('auth_2fa_ativo', '0', 'boolean', 'Autenticacao de dois fatores habilitada');

-- Configuracoes de Notificacoes
INSERT OR IGNORE INTO configuracoes (chave, valor, tipo, descricao) VALUES
('notif_email_ativo', '0', 'boolean', 'Notificacoes por email habilitadas'),
('notif_email_smtp_host', '', 'string', 'Servidor SMTP para emails'),
('notif_email_smtp_porta', '587', 'integer', 'Porta do servidor SMTP'),
('notif_email_smtp_usuario', '', 'string', 'Usuario SMTP'),
('notif_push_ativo', '1', 'boolean', 'Notificacoes push habilitadas'),
('notif_horario_silencioso_inicio', '', 'string', 'Inicio do horario silencioso (HH:MM)'),
('notif_horario_silencioso_fim', '', 'string', 'Fim do horario silencioso (HH:MM)');

-- Configuracoes de Manutencao
INSERT OR IGNORE INTO configuracoes (chave, valor, tipo, descricao) VALUES
('manut_limpeza_auto', '1', 'boolean', 'Limpeza automatica de arquivos antigos'),
('manut_limpeza_hora', '03:00', 'string', 'Horario para executar limpeza automatica'),
('manut_log_retencao_dias', '90', 'integer', 'Dias para manter logs do sistema'),
('manut_backup_auto', '1', 'boolean', 'Backup automatico do banco de dados'),
('manut_backup_hora', '02:00', 'string', 'Horario para backup automatico');

-- Configuracoes de Cameras/ONVIF
INSERT OR IGNORE INTO configuracoes (chave, valor, tipo, descricao) VALUES
('camera_timeout_conexao', '10', 'integer', 'Timeout para conexao com cameras (segundos)'),
('camera_reconexao_tentativas', '3', 'integer', 'Tentativas de reconexao em caso de falha'),
('camera_reconexao_intervalo', '30', 'integer', 'Intervalo entre tentativas de reconexao (segundos)'),
('onvif_discovery_ativo', '1', 'boolean', 'Descoberta automatica de cameras ONVIF'),
('onvif_discovery_intervalo', '300', 'integer', 'Intervalo entre descobertas automaticas (segundos)');

-- Configuracoes de Interface
INSERT OR IGNORE INTO configuracoes (chave, valor, tipo, descricao) VALUES
('ui_tema', 'dark', 'string', 'Tema da interface (light, dark, auto)'),
('ui_grid_colunas', '2', 'integer', 'Colunas no grid de visualizacao'),
('ui_refresh_status_seg', '10', 'integer', 'Intervalo de atualizacao de status (segundos)'),
('ui_mostrar_fps', '1', 'boolean', 'Mostrar FPS no player de video');

-- ============================================================================
-- LOG DE INICIALIZACAO
-- ============================================================================
INSERT INTO logs_sistema (nivel, modulo, mensagem, dados_extra)
VALUES (
    'info',
    'sistema',
    'Sistema inicializado com dados padrao',
    json_object(
        'versao', '1.0.0',
        'migration', '002_seed_data',
        'timestamp', datetime('now')
    )
);

-- ============================================================================
-- CAMERA DE EXEMPLO (OPCIONAL - COMENTADA)
-- ============================================================================
-- Descomente para adicionar uma camera de teste
/*
INSERT INTO cameras (nome, ip, porta, protocolo, url_stream, status)
VALUES (
    'Camera Teste',
    '192.168.1.100',
    554,
    'rtsp',
    'rtsp://192.168.1.100:554/stream1',
    'offline'
);
*/

-- ============================================================================
-- ATUALIZAR VERSAO DO BANCO
-- ============================================================================
UPDATE configuracoes
SET valor = '002', atualizado_em = CURRENT_TIMESTAMP
WHERE chave = 'db_version';

-- Se nao existir, criar
INSERT OR IGNORE INTO configuracoes (chave, valor, tipo, descricao)
VALUES ('db_version', '002', 'string', 'Versao atual do schema do banco de dados');

-- ============================================================================
-- FIM DA MIGRATION 002
-- ============================================================================
