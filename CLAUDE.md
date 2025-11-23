# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Idioma / Language

Sempre responda em **Portugues BR**. Evite usar emojis no codigo para prevenir problemas de encoding.

## Projeto

**SkyCamOS** - Sistema de monitoramento de cameras IP (desktop + web PWA), alternativa simplificada ao Digiforte/Luxriot EVO.

## Comandos de Desenvolvimento

### Iniciar Servidores (Windows)

```bash
# Backend (Terminal 1) - porta 8000
cd backend && start.bat
# ou: py -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Frontend (Terminal 2) - porta 3000
cd frontend && start.bat
# ou: npx serve public -l 3000
```

### Makefile (Linux/Mac/WSL)

```bash
make install          # Instala dependencias backend + frontend
make backend-dev      # Inicia backend com hot-reload
make frontend-dev     # Inicia frontend com hot-reload
make test             # Executa todos os testes
make lint             # Executa linters (ruff, eslint)
make format           # Formata codigo (black, prettier)
make docker-up        # Sobe containers Docker
```

### Testes

```bash
# Backend
cd backend && py -m pytest tests/ -v

# Frontend
cd frontend && npm test
```

## Arquitetura

```
┌─────────────────────────────────────────────────┐
│                   SKYCAMOS                       │
├─────────────────────────────────────────────────┤
│  ┌────────────┐  ┌────────────┐  ┌───────────┐ │
│  │  DESKTOP   │  │  BACKEND   │  │  WEB/PWA  │ │
│  │  MANAGER   │◄─► API (8000) │◄─► (3000)    │ │
│  └────────────┘  └────────────┘  └───────────┘ │
│                        │                        │
│                   ┌────────────┐                │
│                   │  SQLite    │                │
│                   │  Database  │                │
│                   └────────────┘                │
└─────────────────────────────────────────────────┘
                        │
                   CAMERAS IP
                  (ONVIF/RTSP)
```

### Backend (FastAPI)

- **Localizacao:** `/backend/`
- **Framework:** FastAPI + Uvicorn
- **Database:** SQLite + SQLAlchemy (async)
- **Auth:** JWT (python-jose)

**Estrutura de rotas:**
- `/api/v1/auth/*` - Autenticacao (login, refresh)
- `/api/v1/cameras/*` - CRUD de cameras
- `/api/v1/recordings/*` - Gravacoes
- `/api/v1/events/*` - Eventos de movimento
- `/api/v1/stream/*` - Streaming MJPEG/WebSocket
- `/api/v1/analytics/*` - IA (person detection, line crossing)
- `/api/v1/notifications/*` - Push notifications
- `/api/v1/settings/*` - Configuracoes

**Servicos principais:**
- `motion_detection.py` - Deteccao de movimento (OpenCV)
- `person_detection.py` - Deteccao de pessoas (MobileNet SSD/HOG)
- `line_crossing.py` - Cruzamento de linhas virtuais
- `storage_manager.py` - Gerenciamento de disco FIFO

### Frontend (Vanilla JS PWA)

- **Localizacao:** `/frontend/`
- **Entry point:** `/frontend/public/index.html`
- **Main JS:** `/frontend/src/index.js`

**Estrutura:**
- `/src/pages/` - Paginas (Dashboard, Recordings, Events, Settings, Login)
- `/src/components/` - Componentes reutilizaveis
- `/src/services/` - API client, auth, notifications
- `/src/hooks/` - Custom hooks (useAuth, useCamera, useWebSocket)
- `/public/` - Assets estaticos, sw.js, manifest.json

**PWA:**
- Service Worker em `/public/sw.js`
- Manifest em `/public/manifest.json`
- Configuracao Vercel em `/vercel.json`

## Stack Tecnologico

| Camada | Tecnologia |
|--------|------------|
| Backend | Python 3.11+, FastAPI, SQLAlchemy, OpenCV |
| Frontend | Vanilla JS (ES modules), HLS.js |
| Database | SQLite (aiosqlite) |
| Auth | JWT (python-jose, bcrypt) |
| Streaming | MJPEG, WebSocket, HLS |
| AI | OpenCV (MOG2, HOG), MobileNet SSD |

## Credenciais Padrao

```
Usuario: admin
Senha: admin123
```

## Variaveis de Ambiente

Backend usa `.env` na raiz do backend:
- `SECRET_KEY` - Chave JWT
- `DATABASE_URL` - sqlite+aiosqlite:///./data/skycamos.db
- `DEBUG` - true/false
- `CORS_ORIGINS` - URLs permitidas

Frontend usa `/frontend/public/env.js` para detectar ambiente automaticamente.

## Documentacao Adicional

- `SkyCamOS.md` - Especificacao tecnica completa
- `docs/ARCHITECTURE.md` - Arquitetura detalhada
- `docs/API.md` - Documentacao da API
- `docs/DEPLOYMENT.md` - Guia de deploy
