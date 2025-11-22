# SkyCamOS - Especificacao Tecnica Completa

Sistema de monitoramento de cameras IP com interface desktop e web PWA.

---

## Sumario

1. [Visao Geral do Projeto](#visao-geral-do-projeto)
2. [Arquitetura do Sistema](#arquitetura-do-sistema)
3. [Stack Tecnologico](#stack-tecnologico)
4. [Modulos do Sistema](#modulos-do-sistema)
5. [Fluxos Detalhados](#fluxos-detalhados)
6. [Deteccao de Movimento](#deteccao-de-movimento)
7. [PWA - Progressive Web App](#pwa---progressive-web-app)
8. [Modelo de Dados](#modelo-de-dados)
9. [Decisoes Tecnicas](#decisoes-tecnicas)
10. [Estrutura de Arquivos](#estrutura-de-arquivos)
11. [Melhorias Futuras](#melhorias-futuras)

---

## Visao Geral do Projeto

### Objetivo

Criar um sistema de monitoramento **desktop + web PWA** que oferece:

1. Descoberta automatica de cameras IP via ONVIF/SSDP
2. Suporte para ate **10 cameras**
3. Visualizacao com mosaicos (1, 2, 4, 9 cameras)
4. Gravacao local com sobrescrita automatica
5. Interface web acessivel de qualquer lugar
6. PWA instalavel com notificacoes push
7. Visualizar ao vivo, ver gravacoes e rever eventos
8. Deteccao de movimento nas cameras e alertas

### Diagrama de Contexto

```
                              ┌─────────────────────────────────────┐
                              │           SKYCAMOS                   │
                              │    Sistema de Monitoramento          │
                              └───────────────┬─────────────────────┘
                                              │
          ┌───────────────────────────────────┼───────────────────────────────────┐
          │                                   │                                   │
          ▼                                   ▼                                   ▼
┌─────────────────────┐            ┌─────────────────────┐            ┌─────────────────────┐
│                     │            │                     │            │                     │
│    ADMINISTRADOR    │            │     USUARIO         │            │   CAMERAS IP        │
│                     │            │     REMOTO          │            │                     │
│  - Configura        │            │  - Visualiza        │            │  - ONVIF            │
│    cameras          │            │    ao vivo          │            │  - RTSP             │
│  - Gerencia disco   │            │  - Acessa           │            │  - SSDP             │
│  - Define regras    │            │    gravacoes        │            │                     │
│                     │            │  - Recebe alertas   │            │                     │
└─────────────────────┘            └─────────────────────┘            └─────────────────────┘
```

---

## Arquitetura do Sistema

### Visao Macro

```
┌──────────────────────────────────────────────────────────────────────────────────────┐
│                                    SKYCAMOS                                           │
├──────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                       │
│   ┌───────────────────┐                                    ┌───────────────────┐     │
│   │                   │         HTTP/WebSocket             │                   │     │
│   │  DESKTOP MANAGER  │◄──────────────────────────────────►│   WEB/PWA         │     │
│   │                   │                                    │   FRONTEND        │     │
│   │  - PyQt6/Electron │                                    │   - Vue.js/React  │     │
│   │  - System Tray    │                                    │   - HLS.js        │     │
│   │  - Configuracao   │                                    │   - Service Worker│     │
│   │                   │                                    │                   │     │
│   └─────────┬─────────┘                                    └─────────┬─────────┘     │
│             │                                                        │               │
│             │              ┌───────────────────────┐                 │               │
│             │              │                       │                 │               │
│             └─────────────►│     BACKEND / API     │◄────────────────┘               │
│                            │                       │                                 │
│                            │  - FastAPI            │                                 │
│                            │  - REST + WebSocket   │                                 │
│                            │  - Autenticacao JWT   │                                 │
│                            │                       │                                 │
│                            └───────────┬───────────┘                                 │
│                                        │                                             │
│             ┌──────────────────────────┼──────────────────────────┐                  │
│             │                          │                          │                  │
│             ▼                          ▼                          ▼                  │
│   ┌─────────────────┐        ┌─────────────────┐        ┌─────────────────┐         │
│   │                 │        │                 │        │                 │         │
│   │  CAMERA         │        │  RECORDING      │        │  MOTION         │         │
│   │  SERVICE        │        │  SERVICE        │        │  DETECTION      │         │
│   │                 │        │                 │        │  SERVICE        │         │
│   │  - ONVIF        │        │  - FFmpeg       │        │                 │         │
│   │  - RTSP         │        │  - HLS/MP4      │        │  - OpenCV       │         │
│   │  - SSDP         │        │  - FIFO         │        │  - Frame Diff   │         │
│   │                 │        │                 │        │  - ONVIF Events │         │
│   └────────┬────────┘        └────────┬────────┘        └────────┬────────┘         │
│            │                          │                          │                  │
│            │                          │                          │                  │
│            ▼                          ▼                          ▼                  │
│   ┌─────────────────────────────────────────────────────────────────────────┐       │
│   │                                                                         │       │
│   │                          CAMADA DE DADOS                                │       │
│   │                                                                         │       │
│   │   ┌───────────────┐    ┌───────────────┐    ┌───────────────┐          │       │
│   │   │               │    │               │    │               │          │       │
│   │   │   SQLite      │    │  File System  │    │   HLS Cache   │          │       │
│   │   │   Database    │    │  (Recordings) │    │   (.m3u8/.ts) │          │       │
│   │   │               │    │               │    │               │          │       │
│   │   └───────────────┘    └───────────────┘    └───────────────┘          │       │
│   │                                                                         │       │
│   └─────────────────────────────────────────────────────────────────────────┘       │
│                                                                                      │
└──────────────────────────────────────────────────────────────────────────────────────┘
                                         │
                                         │ RTSP / ONVIF
                                         ▼
                    ┌─────────────────────────────────────────────┐
                    │                 CAMERAS IP                   │
                    │                                              │
                    │   ┌───────┐  ┌───────┐  ┌───────┐  ┌──────┐ │
                    │   │Cam 1  │  │Cam 2  │  │Cam 3  │  │Cam N │ │
                    │   └───────┘  └───────┘  └───────┘  └──────┘ │
                    │                                              │
                    └─────────────────────────────────────────────┘
```

### Arquitetura em Camadas

```
┌─────────────────────────────────────────────────────────────────┐
│                    CAMADA DE APRESENTACAO                        │
│                                                                  │
│    Desktop Manager          │           Web PWA                  │
│    ┌──────────────────┐     │     ┌──────────────────────┐      │
│    │ UI de Configuracao│     │     │ Dashboard            │      │
│    │ System Tray       │     │     │ Live View (Mosaico)  │      │
│    │ Discovery Panel   │     │     │ Timeline Playback    │      │
│    └──────────────────┘     │     │ Settings             │      │
│                             │     └──────────────────────┘      │
├─────────────────────────────┴───────────────────────────────────┤
│                    CAMADA DE API                                 │
│                                                                  │
│    ┌────────────┐  ┌────────────┐  ┌────────────┐               │
│    │ REST API   │  │ WebSocket  │  │ Static     │               │
│    │ /api/v1/*  │  │ /ws/*      │  │ Files      │               │
│    └────────────┘  └────────────┘  └────────────┘               │
│                                                                  │
├──────────────────────────────────────────────────────────────────┤
│                    CAMADA DE SERVICOS                            │
│                                                                  │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐             │
│  │ Camera       │ │ Recording    │ │ Motion       │             │
│  │ Service      │ │ Service      │ │ Detection    │             │
│  ├──────────────┤ ├──────────────┤ ├──────────────┤             │
│  │ - Discovery  │ │ - Continuous │ │ - Software   │             │
│  │ - Connection │ │ - On-demand  │ │ - ONVIF      │             │
│  │ - PTZ Control│ │ - Cleanup    │ │ - ROI        │             │
│  └──────────────┘ └──────────────┘ └──────────────┘             │
│                                                                  │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐             │
│  │ Stream       │ │ Notification │ │ Auth         │             │
│  │ Service      │ │ Service      │ │ Service      │             │
│  ├──────────────┤ ├──────────────┤ ├──────────────┤             │
│  │ - RTSP→HLS   │ │ - Web Push   │ │ - JWT        │             │
│  │ - RTSP→WebRTC│ │ - Email      │ │ - Sessions   │             │
│  │ - Transcoding│ │ - Webhooks   │ │ - RBAC       │             │
│  └──────────────┘ └──────────────┘ └──────────────┘             │
│                                                                  │
├──────────────────────────────────────────────────────────────────┤
│                    CAMADA DE DADOS                               │
│                                                                  │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐             │
│  │ SQLite       │ │ File System  │ │ Cache        │             │
│  ├──────────────┤ ├──────────────┤ ├──────────────┤             │
│  │ - Cameras    │ │ - Videos MP4 │ │ - HLS        │             │
│  │ - Users      │ │ - Thumbnails │ │ - Snapshots  │             │
│  │ - Events     │ │ - Logs       │ │              │             │
│  │ - Settings   │ │              │ │              │             │
│  └──────────────┘ └──────────────┘ └──────────────┘             │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## Stack Tecnologico

### Backend

| Tecnologia | Versao | Proposito |
|------------|--------|-----------|
| **Python** | 3.10+ | Linguagem principal |
| **FastAPI** | 0.100+ | Framework web assincrono |
| **Uvicorn** | 0.23+ | Servidor ASGI |
| **SQLAlchemy** | 2.0+ | ORM para banco de dados |
| **SQLite** | 3.35+ | Banco de dados embarcado |
| **FFmpeg** | 4.4+ | Transcoding de video |
| **OpenCV** | 4.8+ | Processamento de imagem |
| **python-onvif** | 0.2+ | Protocolo ONVIF |
| **aiortc** | 1.5+ | WebRTC server-side |
| **Pydantic** | 2.0+ | Validacao de dados |
| **PyJWT** | 2.8+ | Autenticacao JWT |

### Frontend (PWA)

| Tecnologia | Versao | Proposito |
|------------|--------|-----------|
| **Vue.js** | 3.3+ | Framework reativo |
| **TypeScript** | 5.0+ | Tipagem estatica |
| **Vite** | 4.0+ | Build tool |
| **HLS.js** | 1.4+ | Player HLS |
| **Workbox** | 7.0+ | Service Worker |
| **Tailwind CSS** | 3.3+ | Estilizacao |

### Desktop Manager (Opcional)

| Tecnologia | Proposito |
|------------|-----------|
| **PyQt6** | Interface nativa Python |
| **Electron** | Alternativa multiplataforma |

### Infraestrutura

| Tecnologia | Proposito |
|------------|-----------|
| **Docker** | Containerizacao |
| **Nginx** | Proxy reverso |
| **Let's Encrypt** | Certificados SSL |

---

## Modulos do Sistema

### 1. Desktop Manager

```
┌─────────────────────────────────────────────────────────────────┐
│                      DESKTOP MANAGER                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ┌─────────────────┐    ┌──────────────────────────────────┐   │
│   │   System Tray   │    │         Main Window              │   │
│   │                 │    │                                  │   │
│   │  ┌───────────┐  │    │  ┌────────────────────────────┐ │   │
│   │  │ O SkyCam  │  │    │  │    Camera Discovery        │ │   │
│   │  ├───────────┤  │    │  │                            │ │   │
│   │  │ Abrir     │  │    │  │  ┌──────┐ ┌──────┐ ┌────┐ │ │   │
│   │  │ Status    │  │    │  │  │ ONVIF│ │ SSDP │ │Add │ │ │   │
│   │  │ ────────  │  │    │  │  └──────┘ └──────┘ └────┘ │ │   │
│   │  │ Sair      │  │    │  │                            │ │   │
│   │  └───────────┘  │    │  │  ┌────────────────────┐   │ │   │
│   │                 │    │  │  │ Camera 192.168.1.x │   │ │   │
│   └─────────────────┘    │  │  │ Camera 192.168.1.y │   │ │   │
│                          │  │  └────────────────────┘   │ │   │
│                          │  └────────────────────────────┘ │   │
│                          │                                  │   │
│                          │  ┌────────────────────────────┐ │   │
│                          │  │    Storage Manager         │ │   │
│                          │  │                            │ │   │
│                          │  │  Disco: C:\Recordings      │ │   │
│                          │  │  Usado: 45.2 GB / 500 GB   │ │   │
│                          │  │  Retencao: 30 dias         │ │   │
│                          │  │  [Alterar] [Limpar]        │ │   │
│                          │  └────────────────────────────┘ │   │
│                          │                                  │   │
│                          └──────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Responsabilidades:**
- Descoberta automatica de cameras (ONVIF, SSDP)
- Configuracao inicial de cameras
- Gerenciamento de disco e politicas de retencao
- Iniciar/parar servidor backend
- Monitoramento de status do sistema

---

### 2. Backend/API

```
┌─────────────────────────────────────────────────────────────────┐
│                        BACKEND / API                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   FastAPI Application                                            │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │                                                         │   │
│   │   Routers                                               │   │
│   │   ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐      │   │
│   │   │ /auth   │ │/cameras │ │/record  │ │/events  │      │   │
│   │   │         │ │         │ │         │ │         │      │   │
│   │   │ login   │ │ list    │ │ list    │ │ list    │      │   │
│   │   │ refresh │ │ create  │ │ get     │ │ get     │      │   │
│   │   │ logout  │ │ update  │ │ stream  │ │ clip    │      │   │
│   │   │         │ │ delete  │ │ timeline│ │         │      │   │
│   │   └─────────┘ └─────────┘ └─────────┘ └─────────┘      │   │
│   │                                                         │   │
│   │   ┌─────────┐ ┌─────────┐ ┌─────────┐                  │   │
│   │   │/stream  │ │/settings│ │ /ws     │                  │   │
│   │   │         │ │         │ │         │                  │   │
│   │   │ live    │ │ get     │ │ events  │                  │   │
│   │   │ snapshot│ │ update  │ │ stream  │                  │   │
│   │   │ webrtc  │ │ storage │ │         │                  │   │
│   │   └─────────┘ └─────────┘ └─────────┘                  │   │
│   │                                                         │   │
│   └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│   Background Workers                                             │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │                                                         │   │
│   │   ┌───────────────┐  ┌───────────────┐                 │   │
│   │   │ FFmpeg        │  │ Motion        │                 │   │
│   │   │ Workers       │  │ Analyzer      │                 │   │
│   │   │               │  │               │                 │   │
│   │   │ Cam1 ─► HLS   │  │ Frame ─► Diff │                 │   │
│   │   │ Cam2 ─► HLS   │  │       ─► Event│                 │   │
│   │   │ ...           │  │               │                 │   │
│   │   └───────────────┘  └───────────────┘                 │   │
│   │                                                         │   │
│   │   ┌───────────────┐  ┌───────────────┐                 │   │
│   │   │ Storage       │  │ Health        │                 │   │
│   │   │ Cleanup       │  │ Monitor       │                 │   │
│   │   │               │  │               │                 │   │
│   │   │ FIFO delete   │  │ Camera status │                 │   │
│   │   │ old files     │  │ Disk space    │                 │   │
│   │   └───────────────┘  └───────────────┘                 │   │
│   │                                                         │   │
│   └─────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

### 3. Web/PWA Frontend

```
┌─────────────────────────────────────────────────────────────────┐
│                          WEB / PWA                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   App Shell                                                      │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │  ┌─────────────────────────────────────────────────┐    │   │
│   │  │ SkyCamOS                    [User ▼] [Notif] [⚙] │    │   │
│   │  └─────────────────────────────────────────────────┘    │   │
│   │                                                         │   │
│   │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐           │   │
│   │  │Dashboard│ │ Live  │ │Timeline│ │Settings│           │   │
│   │  └────────┘ └────────┘ └────────┘ └────────┘           │   │
│   │                                                         │   │
│   └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│   Pages                                                          │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │                                                         │   │
│   │   Dashboard                                             │   │
│   │   ┌─────────────┐ ┌─────────────┐ ┌─────────────┐      │   │
│   │   │ Cameras: 5  │ │ Online: 5   │ │ Events: 12  │      │   │
│   │   │   [█████]   │ │   [█████]   │ │ hoje        │      │   │
│   │   └─────────────┘ └─────────────┘ └─────────────┘      │   │
│   │                                                         │   │
│   │   Live View (Mosaico 2x2)                               │   │
│   │   ┌─────────────────┬─────────────────┐                │   │
│   │   │                 │                 │                │   │
│   │   │    Camera 1     │    Camera 2     │                │   │
│   │   │    [  ▶  ]      │    [  ▶  ]      │                │   │
│   │   │                 │                 │                │   │
│   │   ├─────────────────┼─────────────────┤                │   │
│   │   │                 │                 │                │   │
│   │   │    Camera 3     │    Camera 4     │                │   │
│   │   │    [  ▶  ]      │    [  ▶  ]      │                │   │
│   │   │                 │                 │                │   │
│   │   └─────────────────┴─────────────────┘                │   │
│   │                                                         │   │
│   │   Timeline                                              │   │
│   │   ┌─────────────────────────────────────────────────┐  │   │
│   │   │ [Camera 1 ▼]  [< 15/01/2024 >]                  │  │   │
│   │   │                                                 │  │   │
│   │   │  00:00    06:00    12:00    18:00    24:00     │  │   │
│   │   │  ├────────┼────────┼────────┼────────┤         │  │   │
│   │   │  [████████████  ██████████████████████]        │  │   │
│   │   │       ▲ Gaps     ▲ Motion Events               │  │   │
│   │   └─────────────────────────────────────────────────┘  │   │
│   │                                                         │   │
│   └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│   Service Worker                                                 │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │  - Cache de assets estaticos                            │   │
│   │  - Modo offline (interface)                             │   │
│   │  - Recebimento de push notifications                    │   │
│   │  - Background sync                                      │   │
│   └─────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Fluxos Detalhados

### Fluxo 1: Descoberta e Adicao de Cameras

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│ Usuario  │     │ Desktop  │     │  ONVIF   │     │ Backend  │     │ Database │
│          │     │ Manager  │     │ Scanner  │     │   API    │     │          │
└────┬─────┘     └────┬─────┘     └────┬─────┘     └────┬─────┘     └────┬─────┘
     │                │                │                │                │
     │ 1. Clica       │                │                │                │
     │ "Descobrir"    │                │                │                │
     │───────────────>│                │                │                │
     │                │                │                │                │
     │                │ 2. Inicia      │                │                │
     │                │    discovery   │                │                │
     │                │───────────────>│                │                │
     │                │                │                │                │
     │                │                │ 3. WS-Discovery│                │
     │                │                │    Broadcast   │                │
     │                │                │    (UDP 3702)  │                │
     │                │                │ ─ ─ ─ ─ ─ ─ ─>│                │
     │                │                │                │                │
     │                │                │ 4. Cameras     │                │
     │                │                │    respondem   │                │
     │                │                │<─ ─ ─ ─ ─ ─ ─ │                │
     │                │                │                │                │
     │                │ 5. GetDeviceInfo               │                │
     │                │    para cada   │                │                │
     │                │    camera      │                │                │
     │                │───────────────>│                │                │
     │                │                │                │                │
     │                │ 6. Retorna     │                │                │
     │                │    info        │                │                │
     │                │<───────────────│                │                │
     │                │                │                │                │
     │ 7. Lista de    │                │                │                │
     │    cameras     │                │                │                │
     │<───────────────│                │                │                │
     │                │                │                │                │
     │ 8. Seleciona   │                │                │                │
     │    e configura │                │                │                │
     │───────────────>│                │                │                │
     │                │                │                │                │
     │                │ 9. POST /cameras               │                │
     │                │────────────────────────────────>│                │
     │                │                │                │                │
     │                │                │                │ 10. INSERT     │
     │                │                │                │    camera      │
     │                │                │                │───────────────>│
     │                │                │                │                │
     │                │                │                │ 11. OK         │
     │                │                │                │<───────────────│
     │                │                │                │                │
     │                │ 12. Camera     │                │                │
     │                │     adicionada │                │                │
     │                │<────────────────────────────────│                │
     │                │                │                │                │
     │ 13. Sucesso    │                │                │                │
     │<───────────────│                │                │                │
     │                │                │                │                │
```

---

### Fluxo 2: Visualizacao ao Vivo (HLS)

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│   PWA    │     │  HLS.js  │     │ Backend  │     │  FFmpeg  │     │  Camera  │
│ Browser  │     │  Player  │     │   API    │     │  Worker  │     │   RTSP   │
└────┬─────┘     └────┬─────┘     └────┬─────┘     └────┬─────┘     └────┬─────┘
     │                │                │                │                │
     │ 1. Acessa      │                │                │                │
     │    Live View   │                │                │                │
     │───────────────>│                │                │                │
     │                │                │                │                │
     │                │ 2. GET         │                │                │
     │                │ /stream/1/live │                │                │
     │                │───────────────>│                │                │
     │                │                │                │                │
     │                │                │ 3. Inicia      │                │
     │                │                │    transcoding │                │
     │                │                │    (se parado) │                │
     │                │                │───────────────>│                │
     │                │                │                │                │
     │                │                │                │ 4. RTSP        │
     │                │                │                │    DESCRIBE    │
     │                │                │                │───────────────>│
     │                │                │                │                │
     │                │                │                │ 5. RTSP        │
     │                │                │                │    SETUP/PLAY  │
     │                │                │                │<──────────────>│
     │                │                │                │                │
     │                │                │                │ 6. RTP Stream  │
     │                │                │                │<═══════════════│
     │                │                │                │    (continuo)  │
     │                │                │                │                │
     │                │                │ 7. FFmpeg gera │                │
     │                │                │    segmentos   │                │
     │                │                │    HLS         │                │
     │                │                │<───────────────│                │
     │                │                │                │                │
     │                │ 8. Retorna URL │                │                │
     │                │    do playlist │                │                │
     │                │<───────────────│                │                │
     │                │                │                │                │
     │                │ 9. GET         │                │                │
     │                │ playlist.m3u8  │                │                │
     │                │───────────────>│                │                │
     │                │                │                │                │
     │                │ 10. Playlist   │                │                │
     │                │<───────────────│                │                │
     │                │                │                │                │
     │                │ 11. GET        │                │                │
     │                │ segment_001.ts │                │                │
     │                │───────────────>│                │                │
     │                │                │                │                │
     │ 12. Video      │                │                │                │
     │     exibido    │                │                │                │
     │<───────────────│                │                │                │
     │                │                │                │                │
     │    [Loop: busca novos segmentos continuamente]   │                │
     │                │                │                │                │
```

---

### Fluxo 3: Deteccao de Movimento e Notificacao

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│  Camera  │     │  Motion  │     │ Recording│     │   Push   │     │   PWA    │
│   RTSP   │     │ Detector │     │  Service │     │ Service  │     │  Client  │
└────┬─────┘     └────┬─────┘     └────┬─────┘     └────┬─────┘     └────┬─────┘
     │                │                │                │                │
     │ 1. Frame       │                │                │                │
     │    stream      │                │                │                │
     │═══════════════>│                │                │                │
     │   (continuo)   │                │                │                │
     │                │                │                │                │
     │                │ 2. Analisa     │                │                │
     │                │    frame N     │                │                │
     │                │    vs N-1      │                │                │
     │                │ ┌────────────┐ │                │                │
     │                │ │ diff > 25% │ │                │                │
     │                │ │ MOVIMENTO! │ │                │                │
     │                │ └────────────┘ │                │                │
     │                │                │                │                │
     │                │ 3. Evento de   │                │                │
     │                │    movimento   │                │                │
     │                │───────────────>│                │                │
     │                │                │                │                │
     │                │                │ 4. Inicia clip │                │
     │                │                │    (pre-buffer │                │
     │                │                │     5 seg)     │                │
     │                │                │                │                │
     │                │                │    [Grava por  │                │
     │                │                │     30 seg]    │                │
     │                │                │                │                │
     │                │                │ 5. Salva       │                │
     │                │                │    evento no   │                │
     │                │                │    banco       │                │
     │                │                │                │                │
     │                │                │ 6. Solicita    │                │
     │                │                │    push        │                │
     │                │                │───────────────>│                │
     │                │                │                │                │
     │                │                │                │ 7. Web Push    │
     │                │                │                │    (VAPID)     │
     │                │                │                │───────────────>│
     │                │                │                │                │
     │                │                │                │                │ 8. Exibe
     │                │                │                │                │    notif
     │                │                │                │                │ ┌──────┐
     │                │                │                │                │ │! Mov.│
     │                │                │                │                │ │Cam 1 │
     │                │                │                │                │ └──────┘
     │                │                │                │                │
     │                │                │                │ 9. Usuario     │
     │                │                │                │    clica       │
     │                │                │                │<───────────────│
     │                │                │                │                │
     │                │                │ 10. GET /events/123/clip        │
     │                │                │<────────────────────────────────│
     │                │                │                │                │
     │                │                │ 11. Retorna clip                │
     │                │                │─────────────────────────────────>│
     │                │                │                │                │
```

---

### Fluxo 4: Reproducao de Gravacoes na Timeline

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│   PWA    │     │ Backend  │     │ Database │     │   File   │
│ Browser  │     │   API    │     │          │     │  System  │
└────┬─────┘     └────┬─────┘     └────┬─────┘     └────┬─────┘
     │                │                │                │
     │ 1. Acessa      │                │                │
     │    Timeline    │                │                │
     │    (Cam 1,     │                │                │
     │     15/01)     │                │                │
     │───────────────>│                │                │
     │                │                │                │
     │                │ 2. SELECT      │                │
     │                │    recordings  │                │
     │                │    WHERE date  │                │
     │                │───────────────>│                │
     │                │                │                │
     │                │ 3. Lista de    │                │
     │                │    segmentos   │                │
     │                │<───────────────│                │
     │                │                │                │
     │ 4. Timeline    │                │                │
     │    renderizada │                │                │
     │                │                │                │
     │  00:00 ░░░░░░░░░░░░░░░░░░░░ 24:00              │
     │  [████████  ██████████████████]                 │
     │       ▲gap    ▲gravacoes                        │
     │<───────────────│                │                │
     │                │                │                │
     │ 5. Usuario     │                │                │
     │    clica em    │                │                │
     │    14:30       │                │                │
     │───────────────>│                │                │
     │                │                │                │
     │                │ 6. Localiza    │                │
     │                │    arquivo     │                │
     │                │───────────────>│                │
     │                │                │                │
     │                │ 7. Retorna     │                │
     │                │    recording   │                │
     │                │<───────────────│                │
     │                │                │                │
     │                │ 8. Calcula     │                │
     │                │    seek offset │                │
     │                │    no arquivo  │                │
     │                │───────────────────────────────>│
     │                │                │                │
     │ 9. Stream MP4  │                │                │
     │    com byte-   │                │                │
     │    range       │                │                │
     │<───────────────│                │                │
     │                │                │                │
     │ 10. Video      │                │                │
     │     reproduz   │                │                │
     │     a partir   │                │                │
     │     de 14:30   │                │                │
     │                │                │                │
```

---

## Deteccao de Movimento

### Opcao 1: Deteccao por Software

```
┌─────────────────────────────────────────────────────────────────┐
│                   MOTION DETECTION (SOFTWARE)                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   Frame Pipeline                                                 │
│                                                                  │
│   ┌────────┐    ┌────────┐    ┌────────┐    ┌────────┐         │
│   │ Frame  │───>│ Resize │───>│ Gray   │───>│ Blur   │         │
│   │ (RGB)  │    │ 320x240│    │ scale  │    │ (21px) │         │
│   └────────┘    └────────┘    └────────┘    └────────┘         │
│                                                   │              │
│                                                   ▼              │
│   ┌────────┐    ┌────────┐    ┌────────┐    ┌────────┐         │
│   │ Event  │<───│ Filter │<───│ Thresh │<───│ Diff   │         │
│   │ Motion!│    │ min_area│    │ > 25   │    │ vs prev│         │
│   └────────┘    └────────┘    └────────┘    └────────┘         │
│                                                                  │
│   Pseudocodigo:                                                  │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │ def detect_motion(frame, prev_frame, sensitivity):      │   │
│   │     # 1. Converter para grayscale                       │   │
│   │     gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)      │   │
│   │                                                         │   │
│   │     # 2. Aplicar blur para reduzir ruido                │   │
│   │     gray = cv2.GaussianBlur(gray, (21, 21), 0)          │   │
│   │                                                         │   │
│   │     # 3. Calcular diferenca absoluta                    │   │
│   │     delta = cv2.absdiff(prev_gray, gray)                │   │
│   │                                                         │   │
│   │     # 4. Aplicar threshold                              │   │
│   │     thresh = cv2.threshold(delta, 25, 255, BINARY)[1]   │   │
│   │                                                         │   │
│   │     # 5. Dilatar para preencher buracos                 │   │
│   │     thresh = cv2.dilate(thresh, None, iterations=2)     │   │
│   │                                                         │   │
│   │     # 6. Encontrar contornos                            │   │
│   │     contours = cv2.findContours(thresh, ...)            │   │
│   │                                                         │   │
│   │     # 7. Filtrar por area minima                        │   │
│   │     for c in contours:                                  │   │
│   │         if cv2.contourArea(c) > min_area:               │   │
│   │             return True, bounding_box(c)                │   │
│   │                                                         │   │
│   │     return False, None                                  │   │
│   └─────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Opcao 2: Eventos ONVIF Nativos

```
┌─────────────────────────────────────────────────────────────────┐
│                   MOTION DETECTION (ONVIF)                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ┌─────────────┐         ┌─────────────┐         ┌───────────┐ │
│   │   Camera    │  ONVIF  │  SkyCamOS   │  Event  │  Database │ │
│   │  (Built-in  │  Event  │   Backend   │         │           │ │
│   │   Motion)   │         │             │         │           │ │
│   └──────┬──────┘         └──────┬──────┘         └─────┬─────┘ │
│          │                       │                      │       │
│          │ 1. Subscribe to       │                      │       │
│          │    motion events      │                      │       │
│          │<──────────────────────│                      │       │
│          │                       │                      │       │
│          │     [Camera detecta   │                      │       │
│          │      movimento        │                      │       │
│          │      internamente]    │                      │       │
│          │                       │                      │       │
│          │ 2. ONVIF Event:       │                      │       │
│          │    MotionAlarm=true   │                      │       │
│          │──────────────────────>│                      │       │
│          │                       │                      │       │
│          │                       │ 3. INSERT event      │       │
│          │                       │────────────────────────────>│ │
│          │                       │                      │       │
│          │                       │ 4. Trigger recording │       │
│          │                       │    & notification    │       │
│          │                       │                      │       │
│                                                                  │
│   Vantagens:                                                     │
│   - Menos consumo de CPU no servidor                             │
│   - Deteccao mais precisa (feita na camera)                      │
│   - Suporte a ROI configurado na camera                          │
│                                                                  │
│   Desvantagens:                                                  │
│   - Nem todas cameras suportam                                   │
│   - Menos controle sobre parametros                              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## PWA - Progressive Web App

### Arquitetura do PWA

```
┌─────────────────────────────────────────────────────────────────┐
│                         PWA ARCHITECTURE                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   manifest.json                                                  │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │ {                                                       │   │
│   │   "name": "SkyCamOS",                                   │   │
│   │   "short_name": "SkyCam",                               │   │
│   │   "start_url": "/",                                     │   │
│   │   "display": "standalone",                              │   │
│   │   "background_color": "#ffffff",                        │   │
│   │   "theme_color": "#1976D2",                             │   │
│   │   "icons": [                                            │   │
│   │     { "src": "/icon-192.png", "sizes": "192x192" },     │   │
│   │     { "src": "/icon-512.png", "sizes": "512x512" }      │   │
│   │   ]                                                     │   │
│   │ }                                                       │   │
│   └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│   Service Worker                                                 │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │                                                         │   │
│   │   Estrategias de Cache                                  │   │
│   │                                                         │   │
│   │   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │   │
│   │   │ Cache First │  │ Network     │  │ Stale While│    │   │
│   │   │             │  │ First       │  │ Revalidate │    │   │
│   │   │ - Assets    │  │ - API       │  │ - Config   │    │   │
│   │   │ - Icons     │  │ - Stream    │  │            │    │   │
│   │   │ - Fonts     │  │             │  │            │    │   │
│   │   └─────────────┘  └─────────────┘  └─────────────┘    │   │
│   │                                                         │   │
│   │   Push Notifications                                    │   │
│   │   ┌─────────────────────────────────────────────────┐  │   │
│   │   │ self.addEventListener('push', (event) => {      │  │   │
│   │   │   const data = event.data.json();               │  │   │
│   │   │   self.registration.showNotification(           │  │   │
│   │   │     data.title,                                 │  │   │
│   │   │     {                                           │  │   │
│   │   │       body: data.body,                          │  │   │
│   │   │       icon: '/icon-192.png',                    │  │   │
│   │   │       data: { url: data.url }                   │  │   │
│   │   │     }                                           │  │   │
│   │   │   );                                            │  │   │
│   │   │ });                                             │  │   │
│   │   └─────────────────────────────────────────────────┘  │   │
│   │                                                         │   │
│   └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│   Fluxo de Instalacao                                            │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │                                                         │   │
│   │   1. Usuario acessa site                                │   │
│   │         │                                               │   │
│   │         ▼                                               │   │
│   │   2. Service Worker registra                            │   │
│   │         │                                               │   │
│   │         ▼                                               │   │
│   │   3. Assets em cache                                    │   │
│   │         │                                               │   │
│   │         ▼                                               │   │
│   │   4. Browser detecta PWA valido                         │   │
│   │         │                                               │   │
│   │         ▼                                               │   │
│   │   5. Prompt "Adicionar a tela inicial?"                 │   │
│   │         │                                               │   │
│   │         ▼                                               │   │
│   │   6. Icone instalado                                    │   │
│   │         │                                               │   │
│   │         ▼                                               │   │
│   │   7. App abre em standalone (tela cheia)                │   │
│   │                                                         │   │
│   └─────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Modelo de Dados

### Diagrama ER

```
┌─────────────────────────────────────────────────────────────────┐
│                       DATABASE SCHEMA                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ┌──────────────────┐                  ┌──────────────────┐    │
│   │      users       │                  │     cameras      │    │
│   ├──────────────────┤                  ├──────────────────┤    │
│   │ *id         INT  │                  │ *id         INT  │    │
│   │  username   STR  │                  │  name       STR  │    │
│   │  password   STR  │──┐               │  ip_address STR  │    │
│   │  email      STR  │  │               │  rtsp_url   STR  │    │
│   │  role       STR  │  │               │  username   STR  │    │
│   │  push_token STR  │  │               │  password   STR  │    │
│   │  created_at DT   │  │               │  status     STR  │    │
│   └──────────────────┘  │               │  motion_on  BOOL │    │
│                         │               │  recording  BOOL │    │
│                         │               │  created_at DT   │    │
│   ┌──────────────────┐  │               └────────┬─────────┘    │
│   │  user_sessions   │  │                        │              │
│   ├──────────────────┤  │                        │              │
│   │ *id         INT  │  │               ┌────────┴────────┐     │
│   │  user_id    INT  │◄─┘               │                 │     │
│   │  token      STR  │                  ▼                 ▼     │
│   │  expires_at DT   │         ┌──────────────┐  ┌──────────────┐
│   │  ip_address STR  │         │  recordings  │  │motion_events │
│   └──────────────────┘         ├──────────────┤  ├──────────────┤
│                                │ *id      INT │  │ *id      INT │
│                                │  camera_id   │  │  camera_id   │
│                                │  start_time  │  │  recording_id│
│                                │  end_time    │  │  timestamp   │
│                                │  file_path   │  │  confidence  │
│   ┌──────────────────┐         │  file_size   │  │  thumbnail   │
│   │     settings     │         │  has_motion  │  │  notified    │
│   ├──────────────────┤         │  thumbnail   │  └──────────────┘
│   │ *key        STR  │         └──────────────┘                  │
│   │  value      TEXT │                                           │
│   │  type       STR  │                                           │
│   │  updated_at DT   │                                           │
│   └──────────────────┘                                           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Decisoes Tecnicas

### Por que SQLite?

| Criterio | SQLite | PostgreSQL | MySQL |
|----------|--------|------------|-------|
| Instalacao | Zero config | Requer servidor | Requer servidor |
| Backup | Copiar arquivo | pg_dump | mysqldump |
| Performance (10 cameras) | Suficiente | Overkill | Overkill |
| Portabilidade | Excelente | Media | Media |
| **Escolha** | **Sim** | Futuro (cloud) | Nao |

### Por que FastAPI?

| Criterio | FastAPI | Flask | Django |
|----------|---------|-------|--------|
| Performance | Excelente | Boa | Boa |
| Async nativo | Sim | Nao | Parcial |
| WebSocket | Nativo | Extension | Channels |
| Documentacao auto | Swagger/OpenAPI | Manual | Manual |
| **Escolha** | **Sim** | Nao | Nao |

### Por que HLS sobre WebRTC (inicialmente)?

| Criterio | HLS | WebRTC |
|----------|-----|--------|
| Latencia | 2-10 seg | < 1 seg |
| Compatibilidade | Universal | Boa |
| Complexidade | Baixa | Alta |
| CDN-friendly | Sim | Nao |
| **MVP** | **Sim** | Versao 1.1 |

### Por que Vue.js?

| Criterio | Vue.js | React | Angular |
|----------|--------|-------|---------|
| Curva aprendizado | Suave | Media | Ingreme |
| Performance | Excelente | Excelente | Boa |
| Tamanho bundle | Pequeno | Medio | Grande |
| Ecossistema | Bom | Excelente | Completo |
| **Escolha** | **Sim** | Alternativa | Nao |

---

## Estrutura de Arquivos

```
skycamos/
│
├── README.md                    # Documentacao principal
├── LICENSE                      # Licenca MIT
├── CONTRIBUTING.md              # Guia de contribuicao
├── CHANGELOG.md                 # Historico de versoes
│
├── config.example.yaml          # Exemplo de configuracao
├── config.yaml                  # Configuracao (gitignore)
├── requirements.txt             # Dependencias Python
├── requirements-dev.txt         # Dependencias de desenvolvimento
├── pyproject.toml               # Configuracao do projeto
│
├── src/                         # Codigo fonte do backend
│   ├── __init__.py
│   ├── main.py                  # Entry point FastAPI
│   │
│   ├── api/                     # Endpoints da API
│   │   ├── __init__.py
│   │   ├── routes/
│   │   │   ├── auth.py          # /auth/*
│   │   │   ├── cameras.py       # /cameras/*
│   │   │   ├── recordings.py    # /recordings/*
│   │   │   ├── events.py        # /events/*
│   │   │   ├── stream.py        # /stream/*
│   │   │   └── settings.py      # /settings/*
│   │   └── websocket.py         # WebSocket handler
│   │
│   ├── core/                    # Logica central
│   │   ├── __init__.py
│   │   ├── config.py            # Carregamento de config
│   │   ├── security.py          # JWT, hashing
│   │   └── exceptions.py        # Excecoes customizadas
│   │
│   ├── services/                # Servicos de negocios
│   │   ├── __init__.py
│   │   ├── camera_service.py    # Gerenciamento de cameras
│   │   ├── recording_service.py # Gravacao
│   │   ├── motion_service.py    # Deteccao de movimento
│   │   ├── stream_service.py    # Transcoding HLS/WebRTC
│   │   ├── notification_service.py # Push notifications
│   │   └── storage_service.py   # Gerenciamento de disco
│   │
│   ├── models/                  # Modelos SQLAlchemy
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── camera.py
│   │   ├── recording.py
│   │   ├── motion_event.py
│   │   └── setting.py
│   │
│   ├── schemas/                 # Schemas Pydantic
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── camera.py
│   │   ├── recording.py
│   │   └── event.py
│   │
│   └── utils/                   # Utilitarios
│       ├── __init__.py
│       ├── ffmpeg.py            # Wrapper FFmpeg
│       ├── onvif.py             # Cliente ONVIF
│       └── helpers.py
│
├── frontend/                    # Codigo fonte do PWA
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   │
│   ├── public/
│   │   ├── manifest.json
│   │   ├── sw.js                # Service Worker
│   │   ├── icon-192.png
│   │   └── icon-512.png
│   │
│   └── src/
│       ├── main.ts
│       ├── App.vue
│       │
│       ├── components/
│       │   ├── VideoPlayer.vue
│       │   ├── MosaicGrid.vue
│       │   ├── Timeline.vue
│       │   ├── CameraCard.vue
│       │   └── MotionEvent.vue
│       │
│       ├── views/
│       │   ├── Dashboard.vue
│       │   ├── LiveView.vue
│       │   ├── Recordings.vue
│       │   ├── Settings.vue
│       │   └── Login.vue
│       │
│       ├── stores/              # Pinia stores
│       │   ├── auth.ts
│       │   ├── cameras.ts
│       │   └── notifications.ts
│       │
│       └── services/
│           ├── api.ts
│           └── websocket.ts
│
├── desktop/                     # Desktop Manager (opcional)
│   ├── main.py
│   ├── ui/
│   │   ├── main_window.py
│   │   └── tray.py
│   └── services/
│       └── discovery.py
│
├── scripts/                     # Scripts auxiliares
│   ├── setup_database.py
│   ├── migrate.py
│   ├── backup.sh
│   └── test_camera.py
│
├── tests/                       # Testes
│   ├── conftest.py
│   ├── test_api/
│   ├── test_services/
│   └── test_integration/
│
├── docs/                        # Documentacao adicional
│   ├── ARCHITECTURE.md
│   ├── API.md
│   ├── DEPLOYMENT.md
│   └── TROUBLESHOOTING.md
│
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
│
├── data/                        # Dados (gitignore)
│   ├── skycamos.db
│   └── hls/
│
├── recordings/                  # Gravacoes (gitignore)
│
└── logs/                        # Logs (gitignore)
```

---

## Melhorias Futuras

### Versao 1.1
- WebRTC para streaming com baixa latencia
- Backup automatico de gravacoes
- Suporte a RTMP

### Versao 2.0
- Deteccao de pessoas com IA (YOLO/TensorFlow)
- Line crossing detection
- Face recognition
- Compartilhamento de camera por link temporario

### Versao 3.0 (Cloud)
- Modo cloud opcional
- Sincronizacao de eventos
- Armazenamento remoto
- Multi-site management

---

## Referencias

- [ONVIF Specifications](https://www.onvif.org/specs/core/ONVIF-Core-Specification.pdf)
- [HLS Specification](https://datatracker.ietf.org/doc/html/rfc8216)
- [WebRTC API](https://developer.mozilla.org/en-US/docs/Web/API/WebRTC_API)
- [PWA Documentation](https://web.dev/progressive-web-apps/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
