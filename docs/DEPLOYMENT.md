# Guia de Deployment

Este documento descreve como fazer deploy do SkyCamOS em diferentes ambientes.

---

## Sumario

- [Requisitos](#requisitos)
- [Instalacao Local](#instalacao-local)
- [Deploy em Producao](#deploy-em-producao)
- [Docker](#docker)
- [Configuracao Avancada](#configuracao-avancada)
- [SSL/HTTPS](#sslhttps)
- [Proxy Reverso](#proxy-reverso)
- [Backup e Restauracao](#backup-e-restauracao)
- [Monitoramento](#monitoramento)
- [Atualizacao](#atualizacao)

---

## Requisitos

### Hardware Minimo

| Recurso | Especificacao |
|---------|---------------|
| CPU | 2 cores (4 recomendado) |
| RAM | 4 GB (8 GB recomendado) |
| Disco | 50 GB SSD |
| Rede | 100 Mbps |

### Hardware Recomendado (10 cameras, 1080p)

| Recurso | Especificacao |
|---------|---------------|
| CPU | Intel i5/Ryzen 5 ou superior |
| RAM | 16 GB |
| Disco | 1 TB SSD NVMe |
| Rede | 1 Gbps |
| GPU | NVIDIA (para transcoding acelerado) |

### Software

| Software | Versao |
|----------|--------|
| Python | 3.10+ |
| FFmpeg | 4.4+ |
| Node.js | 18+ (para build do frontend) |
| SQLite | 3.35+ |

---

## Instalacao Local

### Windows

```powershell
# 1. Instalar Python
# Baixe de https://www.python.org/downloads/

# 2. Instalar FFmpeg
# Baixe de https://ffmpeg.org/download.html
# Adicione ao PATH

# 3. Clonar repositorio
git clone https://github.com/seu-usuario/skycamos.git
cd skycamos

# 4. Criar ambiente virtual
py -m venv venv
.\venv\Scripts\Activate

# 5. Instalar dependencias
pip install -r requirements.txt

# 6. Configurar
copy config.example.yaml config.yaml
# Edite config.yaml conforme necessario

# 7. Inicializar banco de dados
py scripts\setup_database.py

# 8. Executar
py -m uvicorn src.main:app --host 0.0.0.0 --port 8000
```

### Linux (Ubuntu/Debian)

```bash
# 1. Instalar dependencias do sistema
sudo apt update
sudo apt install -y python3.10 python3.10-venv python3-pip ffmpeg

# 2. Clonar repositorio
git clone https://github.com/seu-usuario/skycamos.git
cd skycamos

# 3. Criar ambiente virtual
python3 -m venv venv
source venv/bin/activate

# 4. Instalar dependencias Python
pip install -r requirements.txt

# 5. Configurar
cp config.example.yaml config.yaml
nano config.yaml

# 6. Inicializar banco de dados
py scripts/setup_database.py

# 7. Executar
py -m uvicorn src.main:app --host 0.0.0.0 --port 8000
```

### macOS

```bash
# 1. Instalar Homebrew (se nao tiver)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 2. Instalar dependencias
brew install python@3.10 ffmpeg

# 3. Clonar repositorio
git clone https://github.com/seu-usuario/skycamos.git
cd skycamos

# 4. Criar ambiente virtual
python3 -m venv venv
source venv/bin/activate

# 5. Instalar dependencias Python
pip install -r requirements.txt

# 6. Configurar e executar
cp config.example.yaml config.yaml
py scripts/setup_database.py
py -m uvicorn src.main:app --host 0.0.0.0 --port 8000
```

---

## Deploy em Producao

### Usando systemd (Linux)

1. Crie o arquivo de servico:

```bash
sudo nano /etc/systemd/system/skycamos.service
```

```ini
[Unit]
Description=SkyCamOS Camera Monitoring System
After=network.target

[Service]
Type=simple
User=skycamos
Group=skycamos
WorkingDirectory=/opt/skycamos
Environment="PATH=/opt/skycamos/venv/bin"
ExecStart=/opt/skycamos/venv/bin/python -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=10

# Limites de recursos
LimitNOFILE=65536
LimitNPROC=4096

# Seguranca
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/skycamos/data /opt/skycamos/recordings

[Install]
WantedBy=multi-user.target
```

2. Configure o usuario e permissoes:

```bash
# Criar usuario
sudo useradd -r -s /bin/false skycamos

# Criar diretorios
sudo mkdir -p /opt/skycamos
sudo mkdir -p /opt/skycamos/data
sudo mkdir -p /opt/skycamos/recordings

# Copiar arquivos
sudo cp -r . /opt/skycamos/

# Ajustar permissoes
sudo chown -R skycamos:skycamos /opt/skycamos
```

3. Habilite e inicie o servico:

```bash
sudo systemctl daemon-reload
sudo systemctl enable skycamos
sudo systemctl start skycamos

# Verificar status
sudo systemctl status skycamos

# Ver logs
sudo journalctl -u skycamos -f
```

---

## Docker

### Dockerfile

```dockerfile
# Dockerfile
FROM python:3.10-slim

# Instalar FFmpeg
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Criar usuario nao-root
RUN useradd -m -s /bin/bash skycamos

WORKDIR /app

# Copiar requirements primeiro (cache de layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar codigo
COPY --chown=skycamos:skycamos . .

# Criar diretorios de dados
RUN mkdir -p /app/data /app/recordings \
    && chown -R skycamos:skycamos /app

USER skycamos

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  skycamos:
    build: .
    container_name: skycamos
    restart: unless-stopped
    ports:
      - "8000:8000"
    volumes:
      - ./config.yaml:/app/config.yaml:ro
      - skycamos-data:/app/data
      - skycamos-recordings:/app/recordings
    environment:
      - TZ=America/Sao_Paulo
    networks:
      - skycamos-network
    # Para acesso a cameras na rede local
    # network_mode: host

volumes:
  skycamos-data:
  skycamos-recordings:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /mnt/recordings  # Ajuste para seu disco de gravacoes

networks:
  skycamos-network:
    driver: bridge
```

### Comandos Docker

```bash
# Build
docker-compose build

# Iniciar
docker-compose up -d

# Ver logs
docker-compose logs -f

# Parar
docker-compose down

# Atualizar
docker-compose pull
docker-compose up -d --build
```

---

## Configuracao Avancada

### Arquivo config.yaml Completo

```yaml
# =============================================================================
# SKYCAMOS - Arquivo de Configuracao
# =============================================================================

# -----------------------------------------------------------------------------
# Servidor
# -----------------------------------------------------------------------------
server:
  host: "0.0.0.0"
  port: 8000
  workers: 4
  debug: false
  log_level: "info"  # debug, info, warning, error

  # CORS (Cross-Origin Resource Sharing)
  cors:
    enabled: true
    origins:
      - "http://localhost:3000"
      - "https://seu-dominio.com"
    allow_credentials: true

# -----------------------------------------------------------------------------
# Banco de Dados
# -----------------------------------------------------------------------------
database:
  path: "./data/skycamos.db"
  # Para PostgreSQL (opcional, futuro)
  # url: "postgresql://user:pass@localhost/skycamos"

# -----------------------------------------------------------------------------
# Cameras
# -----------------------------------------------------------------------------
cameras:
  max_cameras: 10
  discovery:
    enabled: true
    interval: 300  # segundos
    protocols:
      - "onvif"
      - "ssdp"
    timeout: 10

  # Configuracoes de conexao
  connection:
    timeout: 5
    retry_attempts: 3
    retry_delay: 10
    health_check_interval: 30

# -----------------------------------------------------------------------------
# Streaming
# -----------------------------------------------------------------------------
streaming:
  # HLS (HTTP Live Streaming)
  hls:
    enabled: true
    segment_duration: 2  # segundos
    playlist_size: 5     # numero de segmentos
    path: "./data/hls"

  # WebRTC (baixa latencia)
  webrtc:
    enabled: true
    stun_servers:
      - "stun:stun.l.google.com:19302"

  # Transcoding
  transcoding:
    enabled: true
    # Aceleracao por hardware
    hardware_acceleration:
      enabled: false
      type: "nvenc"  # nvenc, vaapi, videotoolbox

    # Qualidade de stream
    profiles:
      high:
        resolution: "1920x1080"
        bitrate: "4M"
        fps: 25
      medium:
        resolution: "1280x720"
        bitrate: "2M"
        fps: 20
      low:
        resolution: "640x480"
        bitrate: "500K"
        fps: 15

# -----------------------------------------------------------------------------
# Gravacao
# -----------------------------------------------------------------------------
recording:
  enabled: true
  path: "./recordings"

  # Gerenciamento de armazenamento
  storage:
    max_size_gb: 500
    min_free_gb: 10
    retention_days: 30
    cleanup_interval: 3600  # segundos

  # Formato de gravacao
  format:
    container: "mp4"
    video_codec: "h264"
    segment_duration: 300  # 5 minutos por arquivo

  # Modos de gravacao
  modes:
    continuous:
      enabled: true
    motion_triggered:
      enabled: true
      pre_buffer: 5      # segundos antes do evento
      post_buffer: 10    # segundos apos o evento
      min_duration: 10
      max_duration: 60

# -----------------------------------------------------------------------------
# Deteccao de Movimento
# -----------------------------------------------------------------------------
motion_detection:
  enabled: true

  # Modo: "software" ou "onvif"
  mode: "software"

  # Configuracoes do detector por software
  software:
    algorithm: "frame_diff"  # frame_diff, mog2, knn
    sensitivity: 50          # 0-100
    min_area: 500           # pixels minimos para considerar movimento
    blur_size: 21           # suavizacao
    threshold: 25

  # Regioes de interesse (ROI)
  regions:
    enabled: false
    # Definido por camera na interface

  # Cooldown entre deteccoes
  cooldown: 10  # segundos

# -----------------------------------------------------------------------------
# Notificacoes
# -----------------------------------------------------------------------------
notifications:
  # Push notifications (Web Push)
  push:
    enabled: true
    vapid:
      public_key: "sua-chave-publica-base64"
      private_key: "sua-chave-privada-base64"
      subject: "mailto:admin@seudominio.com"

  # Email (opcional)
  email:
    enabled: false
    smtp:
      host: "smtp.gmail.com"
      port: 587
      username: "seu-email@gmail.com"
      password: "sua-senha-de-app"
      use_tls: true
    from: "SkyCamOS <noreply@seudominio.com>"

  # Webhook (opcional)
  webhook:
    enabled: false
    url: "https://seu-servidor.com/webhook"
    secret: "seu-secret"

# -----------------------------------------------------------------------------
# Autenticacao
# -----------------------------------------------------------------------------
auth:
  # JWT
  jwt:
    secret_key: "MUDE-ESTA-CHAVE-EM-PRODUCAO"
    algorithm: "HS256"
    access_token_expire_minutes: 1440  # 24 horas
    refresh_token_expire_days: 7

  # Sessoes
  sessions:
    max_per_user: 5

  # Politica de senha
  password:
    min_length: 8
    require_uppercase: true
    require_lowercase: true
    require_digit: true
    require_special: false

# -----------------------------------------------------------------------------
# PWA
# -----------------------------------------------------------------------------
pwa:
  enabled: true

  # Manifest
  manifest:
    name: "SkyCamOS"
    short_name: "SkyCam"
    theme_color: "#1976D2"
    background_color: "#FFFFFF"

  # Service Worker
  service_worker:
    cache_version: "v1"
    cache_assets: true
    offline_fallback: true

# -----------------------------------------------------------------------------
# Logging
# -----------------------------------------------------------------------------
logging:
  level: "info"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

  # Arquivo de log
  file:
    enabled: true
    path: "./logs/skycamos.log"
    max_size_mb: 10
    backup_count: 5

  # Logs de acesso
  access:
    enabled: true
    path: "./logs/access.log"
```

---

## SSL/HTTPS

### Usando Let's Encrypt com Certbot

```bash
# Instalar Certbot
sudo apt install certbot

# Obter certificado
sudo certbot certonly --standalone -d seu-dominio.com

# Certificados serao salvos em:
# /etc/letsencrypt/live/seu-dominio.com/fullchain.pem
# /etc/letsencrypt/live/seu-dominio.com/privkey.pem
```

### Configuracao do Uvicorn com SSL

```bash
py -m uvicorn src.main:app \
    --host 0.0.0.0 \
    --port 443 \
    --ssl-keyfile /etc/letsencrypt/live/seu-dominio.com/privkey.pem \
    --ssl-certfile /etc/letsencrypt/live/seu-dominio.com/fullchain.pem
```

---

## Proxy Reverso

### Nginx

```nginx
# /etc/nginx/sites-available/skycamos
upstream skycamos {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name seu-dominio.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name seu-dominio.com;

    ssl_certificate /etc/letsencrypt/live/seu-dominio.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/seu-dominio.com/privkey.pem;

    # SSL settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
    ssl_prefer_server_ciphers off;

    # Timeouts para streaming
    proxy_read_timeout 300;
    proxy_connect_timeout 300;
    proxy_send_timeout 300;

    # Tamanho maximo de upload
    client_max_body_size 100M;

    # API e arquivos estaticos
    location / {
        proxy_pass http://skycamos;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket
    location /ws {
        proxy_pass http://skycamos;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 86400;
    }

    # HLS Streaming
    location /stream/ {
        proxy_pass http://skycamos;
        proxy_buffering off;
        proxy_cache off;
    }
}
```

```bash
# Ativar site
sudo ln -s /etc/nginx/sites-available/skycamos /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## Backup e Restauracao

### Script de Backup

```bash
#!/bin/bash
# scripts/backup.sh

BACKUP_DIR="/backup/skycamos"
DATE=$(date +%Y%m%d_%H%M%S)
SKYCAMOS_DIR="/opt/skycamos"

# Criar diretorio de backup
mkdir -p $BACKUP_DIR

# Backup do banco de dados
cp $SKYCAMOS_DIR/data/skycamos.db $BACKUP_DIR/skycamos_$DATE.db

# Backup das configuracoes
cp $SKYCAMOS_DIR/config.yaml $BACKUP_DIR/config_$DATE.yaml

# Opcional: Backup das gravacoes (cuidado com espaco em disco)
# tar -czf $BACKUP_DIR/recordings_$DATE.tar.gz $SKYCAMOS_DIR/recordings

# Limpar backups antigos (manter ultimos 7 dias)
find $BACKUP_DIR -name "*.db" -mtime +7 -delete
find $BACKUP_DIR -name "*.yaml" -mtime +7 -delete

echo "Backup concluido: $DATE"
```

### Agendamento com Cron

```bash
# Editar crontab
crontab -e

# Adicionar linha para backup diario as 3h
0 3 * * * /opt/skycamos/scripts/backup.sh >> /var/log/skycamos-backup.log 2>&1
```

### Restauracao

```bash
# Parar servico
sudo systemctl stop skycamos

# Restaurar banco de dados
cp /backup/skycamos/skycamos_20240115_030000.db /opt/skycamos/data/skycamos.db

# Restaurar configuracao
cp /backup/skycamos/config_20240115_030000.yaml /opt/skycamos/config.yaml

# Ajustar permissoes
sudo chown skycamos:skycamos /opt/skycamos/data/skycamos.db
sudo chown skycamos:skycamos /opt/skycamos/config.yaml

# Reiniciar
sudo systemctl start skycamos
```

---

## Monitoramento

### Health Check Endpoint

```bash
curl http://localhost:8000/api/v1/health
```

Resposta:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "uptime": 86400,
  "cameras": {
    "total": 5,
    "online": 5,
    "offline": 0
  },
  "storage": {
    "used_percent": 45,
    "free_gb": 275
  },
  "workers": {
    "recording": "running",
    "motion_detection": "running",
    "cleanup": "running"
  }
}
```

### Monitoramento com Prometheus (opcional)

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'skycamos'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
```

---

## Atualizacao

### Atualizacao Manual

```bash
# Parar servico
sudo systemctl stop skycamos

# Backup
/opt/skycamos/scripts/backup.sh

# Atualizar codigo
cd /opt/skycamos
git fetch origin
git checkout main
git pull

# Atualizar dependencias
source venv/bin/activate
pip install -r requirements.txt

# Migracoes de banco (se houver)
py scripts/migrate.py

# Reiniciar
sudo systemctl start skycamos
```

### Rollback

```bash
# Ver commits anteriores
git log --oneline -10

# Voltar para versao anterior
git checkout <commit-hash>

# Restaurar banco se necessario
# (ver secao de restauracao)

sudo systemctl restart skycamos
```
