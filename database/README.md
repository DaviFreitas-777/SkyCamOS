# SkyCamOS - Banco de Dados

Documentacao do banco de dados SQLite do sistema de monitoramento de cameras IP.

## Estrutura de Diretorios

```
database/
├── skycamos.db              # Banco de dados principal (criado apos init)
├── schema.sql               # Esquema completo do banco
├── README.md                # Esta documentacao
├── migrations/              # Arquivos de migracao SQL
│   ├── 001_initial_schema.sql
│   └── 002_seed_data.sql
├── scripts/                 # Scripts Python de gerenciamento
│   ├── init_db.py          # Inicializacao do banco
│   └── backup_db.py        # Backup e restauracao
└── backups/                 # Diretorio de backups (criado automaticamente)
```

## Inicio Rapido

### Inicializar o Banco de Dados

```bash
# Navegar para o diretorio de scripts
cd database/scripts

# Inicializar o banco (primeira vez)
py init_db.py

# Inicializar com modo detalhado
py init_db.py --verbose

# Resetar banco (CUIDADO: apaga todos os dados!)
py init_db.py --reset
```

### Gerenciar Backups

```bash
# Criar backup
py backup_db.py

# Criar backup comprimido
py backup_db.py --compress

# Listar backups disponiveis
py backup_db.py --list

# Restaurar backup
py backup_db.py --restore skycamos_backup_20251122_150000.db

# Limpar backups antigos
py backup_db.py --cleanup
```

## Esquema do Banco de Dados

### Diagrama Entidade-Relacionamento

```
┌─────────────┐       ┌──────────────────┐       ┌───────────────┐
│  usuarios   │       │     cameras      │       │   gravacoes   │
├─────────────┤       ├──────────────────┤       ├───────────────┤
│ id (PK)     │       │ id (PK)          │◄──────│ camera_id (FK)│
│ nome        │       │ nome             │       │ evento_id (FK)│──┐
│ email       │       │ ip               │       │ arquivo_path  │  │
│ senha_hash  │       │ porta            │       │ inicio        │  │
│ ativo       │       │ protocolo        │       │ fim           │  │
│ admin       │       │ status           │       │ tipo          │  │
└──────┬──────┘       │ deteccao_movimento│       └───────────────┘  │
       │              └────────┬─────────┘                           │
       │                       │                                     │
       │                       │                                     │
       ▼                       ▼                                     │
┌─────────────┐       ┌──────────────────┐                           │
│   sessoes   │       │ eventos_movimento│◄──────────────────────────┘
├─────────────┤       ├──────────────────┤
│ usuario_id  │       │ camera_id (FK)   │
│ token       │       │ timestamp        │
│ expira_em   │       │ confianca        │
└─────────────┘       │ visualizado      │
                      └──────────────────┘

┌─────────────────┐       ┌───────────────┐
│  configuracoes  │       │  logs_sistema │
├─────────────────┤       ├───────────────┤
│ chave           │       │ nivel         │
│ valor           │       │ modulo        │
│ tipo            │       │ mensagem      │
│ descricao       │       │ dados_extra   │
└─────────────────┘       └───────────────┘
```

### Tabelas

#### usuarios
Cadastro de usuarios do sistema.

| Coluna | Tipo | Descricao |
|--------|------|-----------|
| id | INTEGER | Chave primaria |
| nome | TEXT | Nome do usuario |
| email | TEXT | Email (unico) |
| senha_hash | TEXT | Hash da senha (PBKDF2) |
| ativo | INTEGER | Usuario ativo (0/1) |
| admin | INTEGER | Administrador (0/1) |
| push_token | TEXT | Token para push notifications |
| ultimo_acesso | DATETIME | Data/hora do ultimo acesso |
| criado_em | DATETIME | Data de criacao |

#### cameras
Cadastro de cameras IP.

| Coluna | Tipo | Descricao |
|--------|------|-----------|
| id | INTEGER | Chave primaria |
| nome | TEXT | Nome da camera |
| ip | TEXT | Endereco IP |
| porta | INTEGER | Porta RTSP (padrao: 554) |
| usuario | TEXT | Usuario de autenticacao |
| senha_hash | TEXT | Hash da senha |
| protocolo | TEXT | rtsp, http, https, rtmp |
| url_stream | TEXT | URL completa do stream |
| onvif_ativo | INTEGER | ONVIF habilitado (0/1) |
| onvif_porta | INTEGER | Porta ONVIF (padrao: 80) |
| status | TEXT | online, offline, erro, manutencao |
| deteccao_movimento | INTEGER | Deteccao habilitada (0/1) |
| sensibilidade_movimento | INTEGER | Sensibilidade (0-100) |
| roi_movimento | TEXT | JSON com regioes de interesse |
| criado_em | DATETIME | Data de criacao |
| atualizado_em | DATETIME | Data de atualizacao |

#### eventos_movimento
Eventos de deteccao de movimento.

| Coluna | Tipo | Descricao |
|--------|------|-----------|
| id | INTEGER | Chave primaria |
| camera_id | INTEGER | FK para cameras |
| timestamp | DATETIME | Data/hora do evento |
| duracao_segundos | INTEGER | Duracao do evento |
| thumbnail_path | TEXT | Caminho da thumbnail |
| confianca | REAL | Nivel de confianca (0.0-1.0) |
| tipo_deteccao | TEXT | software ou onvif |
| visualizado | INTEGER | Evento visto (0/1) |
| criado_em | DATETIME | Data de criacao |

#### gravacoes
Metadados das gravacoes de video.

| Coluna | Tipo | Descricao |
|--------|------|-----------|
| id | INTEGER | Chave primaria |
| camera_id | INTEGER | FK para cameras |
| arquivo_path | TEXT | Caminho do arquivo |
| inicio | DATETIME | Inicio da gravacao |
| fim | DATETIME | Fim da gravacao |
| duracao_segundos | INTEGER | Duracao em segundos |
| tamanho_bytes | INTEGER | Tamanho do arquivo |
| tipo | TEXT | continua ou evento |
| evento_id | INTEGER | FK para eventos_movimento |
| criado_em | DATETIME | Data de criacao |

#### configuracoes
Configuracoes do sistema.

| Coluna | Tipo | Descricao |
|--------|------|-----------|
| id | INTEGER | Chave primaria |
| chave | TEXT | Identificador unico |
| valor | TEXT | Valor da configuracao |
| tipo | TEXT | string, integer, boolean, json, float |
| descricao | TEXT | Descricao da configuracao |
| atualizado_em | DATETIME | Data de atualizacao |

#### sessoes
Sessoes de autenticacao.

| Coluna | Tipo | Descricao |
|--------|------|-----------|
| id | INTEGER | Chave primaria |
| usuario_id | INTEGER | FK para usuarios |
| token | TEXT | Token de sessao (unico) |
| ip_address | TEXT | IP do cliente |
| user_agent | TEXT | User agent do navegador |
| expira_em | DATETIME | Data de expiracao |
| criado_em | DATETIME | Data de criacao |

#### logs_sistema
Logs e eventos do sistema.

| Coluna | Tipo | Descricao |
|--------|------|-----------|
| id | INTEGER | Chave primaria |
| nivel | TEXT | debug, info, warning, error, critical |
| modulo | TEXT | Modulo que gerou o log |
| mensagem | TEXT | Mensagem do log |
| dados_extra | TEXT | JSON com dados adicionais |
| criado_em | DATETIME | Data de criacao |

## Views Disponiveis

### vw_cameras_estatisticas
Cameras com estatisticas agregadas de eventos e gravacoes.

```sql
SELECT * FROM vw_cameras_estatisticas;
```

### vw_eventos_recentes
Eventos de movimento das ultimas 24 horas.

```sql
SELECT * FROM vw_eventos_recentes;
```

### vw_gravacoes_detalhadas
Gravacoes com informacoes da camera e evento relacionado.

```sql
SELECT * FROM vw_gravacoes_detalhadas;
```

### vw_usuarios_sessoes
Usuarios com contagem de sessoes ativas.

```sql
SELECT * FROM vw_usuarios_sessoes;
```

### vw_resumo_sistema
Resumo geral do sistema em uma unica linha.

```sql
SELECT * FROM vw_resumo_sistema;
```

### vw_logs_erros
Ultimos 100 logs de erro/critico.

```sql
SELECT * FROM vw_logs_erros;
```

### vw_configuracoes
Configuracoes formatadas para exibicao.

```sql
SELECT * FROM vw_configuracoes;
```

## Triggers

| Trigger | Tabela | Descricao |
|---------|--------|-----------|
| trg_cameras_atualizado_em | cameras | Atualiza timestamp ao modificar |
| trg_configuracoes_atualizado_em | configuracoes | Atualiza timestamp ao modificar |
| trg_sessoes_ultimo_acesso | sessoes | Atualiza ultimo_acesso do usuario |
| trg_gravacoes_duracao | gravacoes | Calcula duracao quando fim e definido |
| trg_cameras_log_status | cameras | Registra log ao mudar status |

## Indices

Os seguintes indices foram criados para otimizar consultas frequentes:

### Usuarios
- `idx_usuarios_email` - Busca por email
- `idx_usuarios_ativo` - Filtro por status
- `idx_usuarios_ultimo_acesso` - Ordenacao por acesso

### Cameras
- `idx_cameras_status` - Filtro por status
- `idx_cameras_ip` - Busca por IP
- `idx_cameras_nome` - Busca por nome

### Eventos de Movimento
- `idx_eventos_camera_id` - Filtro por camera
- `idx_eventos_timestamp` - Ordenacao temporal
- `idx_eventos_visualizado` - Filtro por visualizacao
- `idx_eventos_camera_timestamp` - Busca composta

### Gravacoes
- `idx_gravacoes_camera_id` - Filtro por camera
- `idx_gravacoes_inicio` - Ordenacao temporal
- `idx_gravacoes_tipo` - Filtro por tipo
- `idx_gravacoes_camera_inicio` - Busca composta
- `idx_gravacoes_evento_id` - Relacionamento com eventos

### Logs
- `idx_logs_nivel` - Filtro por nivel
- `idx_logs_modulo` - Filtro por modulo
- `idx_logs_criado_em` - Ordenacao temporal
- `idx_logs_nivel_criado` - Busca composta

## Exemplos de Consultas

### Listar cameras online com eventos nao visualizados

```sql
SELECT
    c.nome,
    c.ip,
    COUNT(e.id) as eventos_pendentes
FROM cameras c
LEFT JOIN eventos_movimento e ON e.camera_id = c.id AND e.visualizado = 0
WHERE c.status = 'online'
GROUP BY c.id
HAVING eventos_pendentes > 0;
```

### Gravacoes de hoje por camera

```sql
SELECT
    c.nome,
    COUNT(g.id) as total_gravacoes,
    SUM(g.duracao_segundos) / 60 as minutos_gravados,
    SUM(g.tamanho_bytes) / 1024 / 1024 as tamanho_mb
FROM cameras c
LEFT JOIN gravacoes g ON g.camera_id = c.id AND date(g.inicio) = date('now')
GROUP BY c.id;
```

### Ultimos eventos com alta confianca

```sql
SELECT
    e.*,
    c.nome as camera_nome
FROM eventos_movimento e
JOIN cameras c ON c.id = e.camera_id
WHERE e.confianca >= 0.8
ORDER BY e.timestamp DESC
LIMIT 20;
```

### Espaco utilizado por camera

```sql
SELECT
    c.nome,
    COUNT(g.id) as arquivos,
    printf("%.2f GB", COALESCE(SUM(g.tamanho_bytes), 0) / 1024.0 / 1024.0 / 1024.0) as espaco
FROM cameras c
LEFT JOIN gravacoes g ON g.camera_id = c.id
GROUP BY c.id
ORDER BY SUM(g.tamanho_bytes) DESC;
```

## Configuracoes Padrao

Apos inicializacao, as seguintes configuracoes estao disponiveis:

| Chave | Valor Padrao | Descricao |
|-------|--------------|-----------|
| app_versao | 1.0.0 | Versao do sistema |
| gravacao_segmento_minutos | 15 | Duracao de cada segmento |
| gravacao_retencao_dias | 30 | Dias para manter gravacoes |
| movimento_sensibilidade_padrao | 50 | Sensibilidade de deteccao |
| servidor_porta | 8080 | Porta do servidor web |
| auth_sessao_duracao_horas | 24 | Duracao da sessao |

## Usuario Padrao

Apos inicializacao, um usuario administrador e criado:

- **Email:** admin@skycamos.local
- **Senha:** (definida via script)

**IMPORTANTE:** Altere a senha apos o primeiro acesso!

```bash
# Definir nova senha para admin
py init_db.py --set-admin-password "sua_nova_senha_segura"
```

## Manutencao

### Verificar Integridade

```bash
py init_db.py --verify
```

### Otimizar Banco

```sql
-- Via SQLite CLI
sqlite3 skycamos.db "VACUUM;"
sqlite3 skycamos.db "ANALYZE;"
```

### Limpar Logs Antigos

```sql
DELETE FROM logs_sistema
WHERE criado_em < datetime('now', '-90 days');
```

### Limpar Sessoes Expiradas

```sql
DELETE FROM sessoes
WHERE expira_em < datetime('now');
```

## Notas Tecnicas

1. **Foreign Keys:** Habilitadas por padrao (PRAGMA foreign_keys = ON)
2. **Journal Mode:** WAL (Write-Ahead Logging) para melhor concorrencia
3. **Encoding:** UTF-8
4. **Booleans:** Armazenados como INTEGER (0 = false, 1 = true)
5. **Timestamps:** Formato ISO 8601 (YYYY-MM-DD HH:MM:SS)

## Suporte

Para problemas ou duvidas sobre o banco de dados, consulte os logs do sistema:

```sql
SELECT * FROM logs_sistema
WHERE nivel = 'error'
ORDER BY criado_em DESC
LIMIT 50;
```
