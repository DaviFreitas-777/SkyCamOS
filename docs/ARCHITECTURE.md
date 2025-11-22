# Arquitetura do SkyCamOS

Este documento descreve a arquitetura tecnica completa do sistema SkyCamOS, incluindo componentes, fluxos de dados e decisoes de design.

---

## Sumario

- [Visao Geral](#visao-geral)
- [Diagrama de Arquitetura](#diagrama-de-arquitetura)
- [Componentes Principais](#componentes-principais)
- [Fluxos de Dados](#fluxos-de-dados)
- [Modelo de Dados](#modelo-de-dados)
- [Protocolos e Comunicacao](#protocolos-e-comunicacao)
- [Decisoes Arquiteturais](#decisoes-arquiteturais)

---

## Visao Geral

O SkyCamOS e um sistema de monitoramento de cameras IP composto por quatro modulos principais que trabalham de forma integrada:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              SKYCAMOS                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                  │
│   │              │    │              │    │              │                  │
│   │   DESKTOP    │◄──►│   BACKEND    │◄──►│   WEB/PWA    │                  │
│   │   MANAGER    │    │     API      │    │   FRONTEND   │                  │
│   │              │    │              │    │              │                  │
│   └──────┬───────┘    └──────┬───────┘    └──────┬───────┘                  │
│          │                   │                   │                          │
│          │            ┌──────┴───────┐           │                          │
│          │            │              │           │                          │
│          └───────────►│   SQLITE     │◄──────────┘                          │
│                       │   DATABASE   │                                       │
│                       │              │                                       │
│                       └──────────────┘                                       │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
        ┌─────────────────────────────────────────────────────────┐
        │                    CAMERAS IP                            │
        │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐     │
        │  │ Cam 01  │  │ Cam 02  │  │ Cam 03  │  │ Cam N   │     │
        │  │ ONVIF   │  │ ONVIF   │  │ RTSP    │  │ ...     │     │
        │  └─────────┘  └─────────┘  └─────────┘  └─────────┘     │
        └─────────────────────────────────────────────────────────┘
```

---

## Diagrama de Arquitetura

### Arquitetura em Camadas

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CAMADA DE APRESENTACAO                             │
│  ┌───────────────────────────────┐  ┌───────────────────────────────────┐   │
│  │       Desktop Manager          │  │           Web PWA                  │   │
│  │  ┌─────────────────────────┐  │  │  ┌─────────────────────────────┐  │   │
│  │  │  - Config UI            │  │  │  │  - Dashboard                 │  │   │
│  │  │  - Camera Discovery     │  │  │  │  - Live View (Mosaico)      │  │   │
│  │  │  - Disk Management      │  │  │  │  │  - Timeline               │  │   │
│  │  │  - System Tray          │  │  │  │  - Settings                  │  │   │
│  │  └─────────────────────────┘  │  │  │  - Notificacoes              │  │   │
│  └───────────────────────────────┘  │  └─────────────────────────────────┘   │
│                                      └───────────────────────────────────────┘│
├─────────────────────────────────────────────────────────────────────────────┤
│                             CAMADA DE API                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                         FastAPI Application                          │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌────────────┐  │    │
│  │  │ REST API    │  │ WebSocket   │  │ Auth        │  │ Static     │  │    │
│  │  │ Endpoints   │  │ Handler     │  │ Middleware  │  │ Files      │  │    │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └────────────┘  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
├─────────────────────────────────────────────────────────────────────────────┤
│                           CAMADA DE SERVICOS                                 │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌───────────┐  │
│  │ Camera     │ │ Recording  │ │ Motion     │ │ Push       │ │ Stream    │  │
│  │ Service    │ │ Service    │ │ Detection  │ │ Notif.     │ │ Converter │  │
│  │            │ │            │ │ Service    │ │ Service    │ │ Service   │  │
│  │ - ONVIF    │ │ - FIFO     │ │ - Frame    │ │ - WebPush  │ │ - RTSP    │  │
│  │ - SSDP     │ │ - Clips    │ │   Diff     │ │ - FCM      │ │ - HLS     │  │
│  │ - RTSP     │ │ - Timeline │ │ - ONVIF    │ │            │ │ - WebRTC  │  │
│  └────────────┘ └────────────┘ └────────────┘ └────────────┘ └───────────┘  │
├─────────────────────────────────────────────────────────────────────────────┤
│                            CAMADA DE DADOS                                   │
│  ┌─────────────────────────────┐  ┌─────────────────────────────────────┐   │
│  │        SQLite Database       │  │          File System                 │   │
│  │  ┌──────────┐ ┌──────────┐  │  │  ┌──────────┐ ┌──────────────────┐  │   │
│  │  │ Cameras  │ │ Users    │  │  │  │ Videos   │ │ Thumbnails       │  │   │
│  │  ├──────────┤ ├──────────┤  │  │  │ (.mp4)   │ │ (.jpg)           │  │   │
│  │  │ Events   │ │ Settings │  │  │  ├──────────┤ ├──────────────────┤  │   │
│  │  ├──────────┤ └──────────┘  │  │  │ HLS      │ │ Logs             │  │   │
│  │  │Recordings│               │  │  │ Segments │ │                  │  │   │
│  │  └──────────┘               │  │  └──────────┘ └──────────────────┘  │   │
│  └─────────────────────────────┘  └─────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Componentes Principais

### 1. Desktop Manager

Aplicacao desktop para configuracao e gerenciamento local do sistema.

```
┌────────────────────────────────────────────────────────────┐
│                     DESKTOP MANAGER                         │
├────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────┐    ┌─────────────────────────────┐    │
│  │  System Tray    │    │     Main Window              │    │
│  │  ┌───────────┐  │    │  ┌─────────────────────┐    │    │
│  │  │ Icon      │  │    │  │  Camera Discovery   │    │    │
│  │  │ Menu      │  │    │  │  - ONVIF Scan       │    │    │
│  │  │ Notif.    │  │    │  │  - SSDP Scan        │    │    │
│  │  └───────────┘  │    │  │  - Manual Add       │    │    │
│  └─────────────────┘    │  └─────────────────────┘    │    │
│                         │  ┌─────────────────────┐    │    │
│                         │  │  Storage Manager    │    │    │
│                         │  │  - Disk Selection   │    │    │
│                         │  │  - FIFO Config      │    │    │
│                         │  │  - Retention Days   │    │    │
│                         │  └─────────────────────┘    │    │
│                         │  ┌─────────────────────┐    │    │
│                         │  │  Recording Config   │    │    │
│                         │  │  - Schedule         │    │    │
│                         │  │  - Quality          │    │    │
│                         │  │  - Motion Trigger   │    │    │
│                         │  └─────────────────────┘    │    │
│                         └─────────────────────────────┘    │
└────────────────────────────────────────────────────────────┘
```

**Responsabilidades:**
- Descoberta automatica de cameras na rede local
- Configuracao de cameras (credenciais, stream URL)
- Gerenciamento de espaco em disco
- Configuracao de gravacao e retencao
- Inicializacao do servidor backend

**Tecnologias:**
- Python + PyQt6/PySide6 ou Electron
- python-onvif para descoberta ONVIF
- psutil para monitoramento de disco

---

### 2. Backend/API

Servidor central que processa video, gerencia gravacoes e fornece a API.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              BACKEND / API                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                           FastAPI Server                             │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌────────────┐  │    │
│  │  │  /api/      │  │  /ws/       │  │  /stream/   │  │  /static/  │  │    │
│  │  │  cameras    │  │  live       │  │  {id}/      │  │  pwa/      │  │    │
│  │  │  recordings │  │  events     │  │  hls/       │  │  assets/   │  │    │
│  │  │  events     │  │             │  │  webrtc/    │  │            │  │    │
│  │  │  auth       │  │             │  │             │  │            │  │    │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └────────────┘  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                      │                                       │
│                                      ▼                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                          SERVICE LAYER                               │    │
│  ├─────────────────┬─────────────────┬─────────────────┬───────────────┤    │
│  │                 │                 │                 │               │    │
│  │  CameraService  │ RecordingService│ MotionService   │ StreamService │    │
│  │  ┌───────────┐  │  ┌───────────┐  │  ┌───────────┐  │ ┌───────────┐ │    │
│  │  │ Connect   │  │  │ Start     │  │  │ Detect    │  │ │ RTSP→HLS  │ │    │
│  │  │ Configure │  │  │ Stop      │  │  │ Configure │  │ │ RTSP→RTC  │ │    │
│  │  │ GetStream │  │  │ Clip      │  │  │ Notify    │  │ │ Transcode │ │    │
│  │  │ PTZ       │  │  │ Cleanup   │  │  │ ROI       │  │ │           │ │    │
│  │  └───────────┘  │  └───────────┘  │  └───────────┘  │ └───────────┘ │    │
│  │                 │                 │                 │               │    │
│  └─────────────────┴─────────────────┴─────────────────┴───────────────┘    │
│                                      │                                       │
│                                      ▼                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                         WORKER PROCESSES                             │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │    │
│  │  │ FFmpeg       │  │ Frame        │  │ Cleanup      │               │    │
│  │  │ Workers      │  │ Analyzer     │  │ Worker       │               │    │
│  │  │ (per camera) │  │ (motion)     │  │ (FIFO)       │               │    │
│  │  └──────────────┘  └──────────────┘  └──────────────┘               │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Responsabilidades:**
- API REST para CRUD de cameras e configuracoes
- WebSocket para streaming ao vivo e eventos em tempo real
- Conversao de RTSP para HLS/WebRTC
- Gerenciamento de gravacoes
- Deteccao de movimento
- Autenticacao e autorizacao

**Tecnologias:**
- Python + FastAPI
- FFmpeg para transcoding
- OpenCV para deteccao de movimento
- aiortc para WebRTC

---

### 3. Web/PWA Frontend

Interface web progressiva para acesso remoto e local.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              WEB / PWA                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                         PWA Shell                                    │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────────┐  │    │
│  │  │ manifest    │  │ Service     │  │ App Shell                    │  │    │
│  │  │ .json       │  │ Worker      │  │ (Header, Nav, Footer)       │  │    │
│  │  └─────────────┘  └─────────────┘  └─────────────────────────────┘  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                      │                                       │
│                                      ▼                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                            PAGES                                     │    │
│  ├──────────────┬──────────────┬──────────────┬──────────────┬─────────┤    │
│  │              │              │              │              │         │    │
│  │  Dashboard   │  Live View   │  Timeline    │  Settings    │  Login  │    │
│  │  ┌────────┐  │  ┌────────┐  │  ┌────────┐  │  ┌────────┐  │ ┌─────┐ │    │
│  │  │ Status │  │  │ Mosaic │  │  │ Date   │  │  │ Cameras│  │ │Form │ │    │
│  │  │ Cards  │  │  │ Grid   │  │  │ Picker │  │  │ Users  │  │ │     │ │    │
│  │  │ Alerts │  │  │ Player │  │  │ Seek   │  │  │ System │  │ │     │ │    │
│  │  └────────┘  │  └────────┘  │  └────────┘  │  └────────┘  │ └─────┘ │    │
│  │              │              │              │              │         │    │
│  └──────────────┴──────────────┴──────────────┴──────────────┴─────────┘    │
│                                      │                                       │
│                                      ▼                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                         COMPONENTS                                   │    │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌───────────┐  │    │
│  │  │VideoPlayer│ │ Timeline │ │ Mosaic   │ │ Camera   │ │ Motion    │  │    │
│  │  │ (HLS.js) │ │ Scrubber │ │ Layout   │ │ Card     │ │ Event     │  │    │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └───────────┘  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Responsabilidades:**
- Visualizacao ao vivo com layouts de mosaico
- Reproducao de gravacoes com timeline
- Exibicao de eventos de movimento
- Recebimento de notificacoes push
- Funcionamento offline (cache de interface)

**Tecnologias:**
- Vue.js 3 ou React 18
- TypeScript
- HLS.js para reproducao
- Workbox para PWA/Service Worker

---

### 4. Banco de Dados

Modelo de dados SQLite para armazenamento local.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            DATABASE SCHEMA                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐      │
│  │     users       │      │    cameras      │      │   recordings    │      │
│  ├─────────────────┤      ├─────────────────┤      ├─────────────────┤      │
│  │ id (PK)         │      │ id (PK)         │      │ id (PK)         │      │
│  │ username        │      │ name            │◄─────│ camera_id (FK)  │      │
│  │ password_hash   │      │ ip_address      │      │ start_time      │      │
│  │ email           │      │ rtsp_url        │      │ end_time        │      │
│  │ role            │      │ onvif_port      │      │ file_path       │      │
│  │ created_at      │      │ username        │      │ file_size       │      │
│  │ push_token      │      │ password        │      │ has_motion      │      │
│  └─────────────────┘      │ status          │      │ thumbnail       │      │
│          │                │ created_at      │      └─────────────────┘      │
│          │                └─────────────────┘               │               │
│          │                         │                        │               │
│          │                         │                        │               │
│          ▼                         ▼                        ▼               │
│  ┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐      │
│  │  user_sessions  │      │  motion_events  │      │   settings      │      │
│  ├─────────────────┤      ├─────────────────┤      ├─────────────────┤      │
│  │ id (PK)         │      │ id (PK)         │      │ key (PK)        │      │
│  │ user_id (FK)    │      │ camera_id (FK)  │      │ value           │      │
│  │ token           │      │ recording_id(FK)│      │ type            │      │
│  │ expires_at      │      │ timestamp       │      │ updated_at      │      │
│  │ ip_address      │      │ confidence      │      └─────────────────┘      │
│  │ user_agent      │      │ thumbnail       │                               │
│  └─────────────────┘      │ notified        │                               │
│                           └─────────────────┘                               │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Fluxos de Dados

### Fluxo 1: Descoberta de Cameras

```
┌────────────┐     ┌────────────┐     ┌────────────┐     ┌────────────┐
│   Usuario  │     │  Desktop   │     │   ONVIF    │     │  Cameras   │
│            │     │  Manager   │     │  Scanner   │     │    IP      │
└─────┬──────┘     └─────┬──────┘     └─────┬──────┘     └─────┬──────┘
      │                  │                  │                  │
      │ 1. Clica         │                  │                  │
      │    "Descobrir"   │                  │                  │
      │─────────────────>│                  │                  │
      │                  │                  │                  │
      │                  │ 2. Inicia scan   │                  │
      │                  │─────────────────>│                  │
      │                  │                  │                  │
      │                  │                  │ 3. WS-Discovery  │
      │                  │                  │     broadcast    │
      │                  │                  │─────────────────>│
      │                  │                  │                  │
      │                  │                  │ 4. Resposta      │
      │                  │                  │    com info      │
      │                  │                  │<─────────────────│
      │                  │                  │                  │
      │                  │ 5. Lista de      │                  │
      │                  │    cameras       │                  │
      │                  │<─────────────────│                  │
      │                  │                  │                  │
      │ 6. Exibe cameras │                  │                  │
      │    encontradas   │                  │                  │
      │<─────────────────│                  │                  │
      │                  │                  │                  │
```

---

### Fluxo 2: Streaming ao Vivo

```
┌────────────┐     ┌────────────┐     ┌────────────┐     ┌────────────┐
│   PWA      │     │  Backend   │     │  FFmpeg    │     │  Camera    │
│  Browser   │     │   API      │     │  Worker    │     │    IP      │
└─────┬──────┘     └─────┬──────┘     └─────┬──────┘     └─────┬──────┘
      │                  │                  │                  │
      │ 1. GET           │                  │                  │
      │    /stream/1     │                  │                  │
      │─────────────────>│                  │                  │
      │                  │                  │                  │
      │                  │ 2. Start         │                  │
      │                  │    transcoding   │                  │
      │                  │─────────────────>│                  │
      │                  │                  │                  │
      │                  │                  │ 3. RTSP connect  │
      │                  │                  │─────────────────>│
      │                  │                  │                  │
      │                  │                  │ 4. Video frames  │
      │                  │                  │<─────────────────│
      │                  │                  │                  │
      │                  │ 5. HLS segments  │                  │
      │                  │    (.m3u8 + .ts) │                  │
      │                  │<─────────────────│                  │
      │                  │                  │                  │
      │ 6. Playlist +    │                  │                  │
      │    segments      │                  │                  │
      │<─────────────────│                  │                  │
      │                  │                  │                  │
      │    [loop: request new segments]     │                  │
      │                  │                  │                  │
```

---

### Fluxo 3: Deteccao de Movimento

```
┌────────────┐     ┌────────────┐     ┌────────────┐     ┌────────────┐
│  Camera    │     │  Motion    │     │ Recording  │     │   PWA      │
│    IP      │     │  Detector  │     │  Service   │     │  (Push)    │
└─────┬──────┘     └─────┬──────┘     └─────┬──────┘     └─────┬──────┘
      │                  │                  │                  │
      │ 1. Frame         │                  │                  │
      │    continuo      │                  │                  │
      │─────────────────>│                  │                  │
      │                  │                  │                  │
      │                  │ 2. Analisa       │                  │
      │                  │    frame diff    │                  │
      │                  │    ┌──────────┐  │                  │
      │                  │    │ Motion   │  │                  │
      │                  │    │ Detected!│  │                  │
      │                  │    └──────────┘  │                  │
      │                  │                  │                  │
      │                  │ 3. Trigger       │                  │
      │                  │    recording     │                  │
      │                  │─────────────────>│                  │
      │                  │                  │                  │
      │                  │                  │ 4. Grava clip    │
      │                  │                  │    (30 seg)      │
      │                  │                  │    ┌──────────┐  │
      │                  │                  │    │ .mp4     │  │
      │                  │                  │    └──────────┘  │
      │                  │                  │                  │
      │                  │                  │ 5. Salva evento  │
      │                  │                  │    no banco      │
      │                  │                  │                  │
      │                  │                  │ 6. Push          │
      │                  │                  │    notification  │
      │                  │                  │─────────────────>│
      │                  │                  │                  │
      │                  │                  │                  │ 7. Exibe
      │                  │                  │                  │    alerta
      │                  │                  │                  │
```

---

### Fluxo 4: Reproducao de Gravacoes

```
┌────────────┐     ┌────────────┐     ┌────────────┐     ┌────────────┐
│   PWA      │     │  Backend   │     │   SQLite   │     │ FileSystem │
│  Browser   │     │   API      │     │  Database  │     │  (Videos)  │
└─────┬──────┘     └─────┬──────┘     └─────┬──────┘     └─────┬──────┘
      │                  │                  │                  │
      │ 1. GET           │                  │                  │
      │ /recordings?     │                  │                  │
      │ camera=1&        │                  │                  │
      │ date=2024-01-15  │                  │                  │
      │─────────────────>│                  │                  │
      │                  │                  │                  │
      │                  │ 2. Query         │                  │
      │                  │    recordings    │                  │
      │                  │─────────────────>│                  │
      │                  │                  │                  │
      │                  │ 3. Results       │                  │
      │                  │<─────────────────│                  │
      │                  │                  │                  │
      │ 4. Lista de      │                  │                  │
      │    gravacoes     │                  │                  │
      │<─────────────────│                  │                  │
      │                  │                  │                  │
      │ 5. GET           │                  │                  │
      │ /recordings/     │                  │                  │
      │ 123/stream       │                  │                  │
      │─────────────────>│                  │                  │
      │                  │                  │                  │
      │                  │ 6. Read file     │                  │
      │                  │─────────────────────────────────────>│
      │                  │                  │                  │
      │                  │ 7. Video data    │                  │
      │                  │<─────────────────────────────────────│
      │                  │                  │                  │
      │ 8. Stream MP4    │                  │                  │
      │    (range req)   │                  │                  │
      │<─────────────────│                  │                  │
      │                  │                  │                  │
```

---

## Modelo de Dados

### Diagrama ER Completo

```
                    ┌─────────────────────────────────────┐
                    │               users                  │
                    ├─────────────────────────────────────┤
                    │ * id           INTEGER PK           │
                    │   username     VARCHAR(50) UNIQUE   │
                    │   password_hash VARCHAR(255)        │
                    │   email        VARCHAR(100)         │
                    │   role         VARCHAR(20)          │
                    │   push_token   VARCHAR(255)         │
                    │   created_at   DATETIME             │
                    │   updated_at   DATETIME             │
                    └────────────────┬────────────────────┘
                                     │
                                     │ 1:N
                                     ▼
                    ┌─────────────────────────────────────┐
                    │           user_sessions              │
                    ├─────────────────────────────────────┤
                    │ * id           INTEGER PK           │
                    │   user_id      INTEGER FK           │
                    │   token        VARCHAR(255)         │
                    │   expires_at   DATETIME             │
                    │   ip_address   VARCHAR(45)          │
                    │   user_agent   TEXT                 │
                    │   created_at   DATETIME             │
                    └─────────────────────────────────────┘

┌─────────────────────────────────────┐
│              cameras                 │
├─────────────────────────────────────┤
│ * id           INTEGER PK           │
│   name         VARCHAR(100)         │
│   ip_address   VARCHAR(45)          │
│   rtsp_url     VARCHAR(255)         │
│   rtsp_substream VARCHAR(255)       │
│   onvif_port   INTEGER              │
│   username     VARCHAR(50)          │
│   password     VARCHAR(100)         │
│   manufacturer VARCHAR(50)          │
│   model        VARCHAR(50)          │
│   status       VARCHAR(20)          │
│   motion_enabled BOOLEAN            │
│   motion_sensitivity INTEGER        │
│   recording_enabled BOOLEAN         │
│   created_at   DATETIME             │
│   updated_at   DATETIME             │
└────────────────┬────────────────────┘
                 │
        ┌────────┴────────┐
        │ 1:N             │ 1:N
        ▼                 ▼
┌───────────────────┐   ┌───────────────────────────────────┐
│   recordings      │   │          motion_events             │
├───────────────────┤   ├───────────────────────────────────┤
│ * id        PK    │   │ * id             INTEGER PK       │
│   camera_id FK    │◄──│   camera_id      INTEGER FK       │
│   start_time      │   │   recording_id   INTEGER FK       │
│   end_time        │   │   timestamp      DATETIME         │
│   duration        │   │   confidence     FLOAT            │
│   file_path       │   │   region_x       INTEGER          │
│   file_size       │   │   region_y       INTEGER          │
│   has_motion      │   │   region_w       INTEGER          │
│   thumbnail       │   │   region_h       INTEGER          │
│   created_at      │   │   thumbnail      VARCHAR(255)     │
└───────────────────┘   │   notified       BOOLEAN          │
                        │   created_at     DATETIME         │
                        └───────────────────────────────────┘

┌─────────────────────────────────────┐
│              settings                │
├─────────────────────────────────────┤
│ * key          VARCHAR(50) PK       │
│   value        TEXT                 │
│   type         VARCHAR(20)          │
│   description  TEXT                 │
│   updated_at   DATETIME             │
└─────────────────────────────────────┘
```

---

## Protocolos e Comunicacao

### Matriz de Protocolos

| Componente | Protocolo | Porta | Descricao |
|------------|-----------|-------|-----------|
| API REST | HTTP/HTTPS | 8000 | Endpoints para CRUD |
| WebSocket | WS/WSS | 8000 | Eventos em tempo real |
| Camera RTSP | RTSP | 554 | Stream de video |
| Camera ONVIF | HTTP/SOAP | 80/8080 | Descoberta e controle |
| HLS Streaming | HTTP | 8000 | Segmentos de video |
| WebRTC | UDP | Dinamico | Stream baixa latencia |
| Push Notifications | HTTPS | 443 | Web Push (VAPID) |

### Diagrama de Comunicacao

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         NETWORK COMMUNICATION                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│     REDE LOCAL (LAN)                    │        INTERNET                   │
│                                         │                                    │
│  ┌──────────┐     RTSP (554)           │                                    │
│  │ Camera 1 │◄───────────────────┐     │                                    │
│  └──────────┘                    │     │                                    │
│                                  │     │                                    │
│  ┌──────────┐     RTSP (554)     │     │     HTTPS (443)    ┌────────────┐ │
│  │ Camera 2 │◄─────────────────┐ │     │  ┌────────────────►│ Push       │ │
│  └──────────┘                  │ │     │  │                 │ Service    │ │
│                                │ │     │  │                 └────────────┘ │
│  ┌──────────┐     RTSP (554)   │ │     │  │                                │
│  │ Camera N │◄───────────────┐ │ │     │  │                                │
│  └──────────┘                │ │ │     │  │                                │
│                              ▼ ▼ ▼     │  │                                │
│                         ┌──────────┐   │  │     ┌────────────────────────┐ │
│                         │          │   │  │     │                        │ │
│                         │ BACKEND  │───┼──┴────►│   PWA (Browser/App)    │ │
│                         │ SERVER   │   │        │                        │ │
│                         │          │◄──┼────────│   - HTTP/HTTPS         │ │
│                         │ :8000    │   │        │   - WebSocket          │ │
│                         │          │   │        │   - HLS Stream         │ │
│                         └──────────┘   │        │                        │ │
│                              ▲         │        └────────────────────────┘ │
│                              │         │                                    │
│                         ┌────┴─────┐   │                                    │
│                         │ Desktop  │   │                                    │
│                         │ Manager  │   │                                    │
│                         └──────────┘   │                                    │
│                                        │                                    │
└────────────────────────────────────────┴────────────────────────────────────┘
```

---

## Decisoes Arquiteturais

### ADR 001: Escolha do SQLite como Banco de Dados

**Contexto:** Necessidade de armazenamento persistente para configuracoes e metadados.

**Decisao:** Utilizar SQLite como banco de dados principal.

**Justificativa:**
- Nao requer servidor separado
- Backup simples (copiar arquivo)
- Performance adequada para ate 10 cameras
- Suporte nativo em Python
- Zero configuracao

**Consequencias:**
- (+) Instalacao simplificada
- (+) Portabilidade do sistema
- (-) Limitacao de concorrencia para escrita
- (-) Nao adequado para clusters

---

### ADR 002: FFmpeg para Transcoding

**Contexto:** Necessidade de converter RTSP para formatos web-friendly.

**Decisao:** Utilizar FFmpeg como engine de transcoding.

**Justificativa:**
- Suporte a praticamente todos os codecs
- Ampla documentacao
- Comunidade ativa
- Suporte a HLS e segmentacao
- Aceleracao por hardware (GPU)

**Consequencias:**
- (+) Flexibilidade de formatos
- (+) Qualidade de transcoding
- (-) Dependencia externa
- (-) Consumo de CPU significativo

---

### ADR 003: HLS como Protocolo de Streaming Primario

**Contexto:** Necessidade de streaming compativel com navegadores.

**Decisao:** HLS como protocolo primario, WebRTC como secundario.

**Justificativa:**
- Compatibilidade universal com navegadores
- Suporte nativo em iOS
- Tolerante a variacoes de rede
- Cache eficiente

**Consequencias:**
- (+) Funciona em qualquer navegador
- (+) CDN-friendly
- (-) Latencia de 2-10 segundos
- (-) WebRTC necessario para baixa latencia

---

### ADR 004: Arquitetura Monolitica Inicial

**Contexto:** Projeto em fase inicial com recursos limitados.

**Decisao:** Iniciar com arquitetura monolitica modular.

**Justificativa:**
- Simplicidade de desenvolvimento
- Deploy simplificado
- Menos overhead de comunicacao
- Facilidade de debug

**Consequencias:**
- (+) Time to market rapido
- (+) Menor complexidade operacional
- (-) Escalabilidade limitada
- (-) Refatoracao futura para microservicos

---

## Proximos Passos

Para detalhes de implementacao, consulte:
- [API.md](API.md) - Documentacao completa da API
- [DEPLOYMENT.md](DEPLOYMENT.md) - Guia de deploy
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Resolucao de problemas
