# Documentacao da API

API RESTful do SkyCamOS para integracao e acesso programatico.

---

## Sumario

- [Visao Geral](#visao-geral)
- [Autenticacao](#autenticacao)
- [Endpoints](#endpoints)
  - [Autenticacao](#autenticacao-endpoints)
  - [Cameras](#cameras)
  - [Gravacoes](#gravacoes)
  - [Eventos de Movimento](#eventos-de-movimento)
  - [Streaming](#streaming)
  - [Configuracoes](#configuracoes)
- [WebSocket](#websocket)
- [Codigos de Erro](#codigos-de-erro)
- [Rate Limiting](#rate-limiting)
- [Exemplos](#exemplos)

---

## Visao Geral

### Base URL

```
http://localhost:8000/api/v1
```

### Formato de Resposta

Todas as respostas sao em JSON:

```json
{
  "success": true,
  "data": { },
  "message": "Operacao realizada com sucesso",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Respostas de Erro

```json
{
  "success": false,
  "error": {
    "code": "CAMERA_NOT_FOUND",
    "message": "Camera com ID 99 nao encontrada",
    "details": null
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

---

## Autenticacao

### Metodo: Bearer Token (JWT)

Todas as requisicoes (exceto login) requerem o header de autorizacao:

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Estrutura do Token

```json
{
  "sub": "user_id",
  "username": "admin",
  "role": "admin",
  "exp": 1705312200,
  "iat": 1705225800
}
```

### Duracao do Token

- Access Token: 24 horas
- Refresh Token: 7 dias

---

## Endpoints

### Autenticacao {#autenticacao-endpoints}

#### POST /auth/login

Autentica o usuario e retorna tokens.

**Request:**

```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "senha123"
}
```

**Response (200):**

```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "bearer",
    "expires_in": 86400
  }
}
```

**Erros:**
- 401: Credenciais invalidas
- 429: Muitas tentativas

---

#### POST /auth/refresh

Renova o access token usando o refresh token.

**Request:**

```http
POST /api/v1/auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Response (200):**

```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "expires_in": 86400
  }
}
```

---

#### POST /auth/logout

Invalida o token atual.

**Request:**

```http
POST /api/v1/auth/logout
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

**Response (200):**

```json
{
  "success": true,
  "message": "Logout realizado com sucesso"
}
```

---

### Cameras

#### GET /cameras

Lista todas as cameras cadastradas.

**Request:**

```http
GET /api/v1/cameras
Authorization: Bearer {token}
```

**Query Parameters:**

| Parametro | Tipo | Descricao |
|-----------|------|-----------|
| status | string | Filtrar por status (online, offline, error) |
| page | integer | Numero da pagina (default: 1) |
| limit | integer | Itens por pagina (default: 10, max: 50) |

**Response (200):**

```json
{
  "success": true,
  "data": {
    "cameras": [
      {
        "id": 1,
        "name": "Camera Entrada",
        "ip_address": "192.168.1.100",
        "rtsp_url": "rtsp://192.168.1.100:554/stream1",
        "status": "online",
        "manufacturer": "Intelbras",
        "model": "VIP 1230",
        "motion_enabled": true,
        "recording_enabled": true,
        "created_at": "2024-01-10T08:00:00Z",
        "last_seen": "2024-01-15T10:30:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 10,
      "total": 5,
      "pages": 1
    }
  }
}
```

---

#### GET /cameras/{id}

Retorna detalhes de uma camera especifica.

**Request:**

```http
GET /api/v1/cameras/1
Authorization: Bearer {token}
```

**Response (200):**

```json
{
  "success": true,
  "data": {
    "id": 1,
    "name": "Camera Entrada",
    "ip_address": "192.168.1.100",
    "rtsp_url": "rtsp://192.168.1.100:554/stream1",
    "rtsp_substream": "rtsp://192.168.1.100:554/stream2",
    "onvif_port": 80,
    "username": "admin",
    "status": "online",
    "manufacturer": "Intelbras",
    "model": "VIP 1230",
    "firmware": "2.800.0000.1.R",
    "motion_enabled": true,
    "motion_sensitivity": 50,
    "motion_regions": [
      {"x": 0, "y": 0, "width": 100, "height": 100}
    ],
    "recording_enabled": true,
    "recording_mode": "continuous",
    "created_at": "2024-01-10T08:00:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  }
}
```

---

#### POST /cameras

Adiciona uma nova camera.

**Request:**

```http
POST /api/v1/cameras
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "Camera Garagem",
  "ip_address": "192.168.1.101",
  "rtsp_url": "rtsp://192.168.1.101:554/stream1",
  "username": "admin",
  "password": "camera123",
  "onvif_port": 80,
  "motion_enabled": true,
  "motion_sensitivity": 50,
  "recording_enabled": true
}
```

**Response (201):**

```json
{
  "success": true,
  "data": {
    "id": 2,
    "name": "Camera Garagem",
    "status": "connecting"
  },
  "message": "Camera adicionada com sucesso"
}
```

**Erros:**
- 400: Dados invalidos
- 409: Camera ja cadastrada (mesmo IP)
- 422: Limite de cameras atingido (max 10)

---

#### PUT /cameras/{id}

Atualiza uma camera existente.

**Request:**

```http
PUT /api/v1/cameras/2
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "Camera Garagem Principal",
  "motion_sensitivity": 70
}
```

**Response (200):**

```json
{
  "success": true,
  "data": {
    "id": 2,
    "name": "Camera Garagem Principal",
    "motion_sensitivity": 70
  },
  "message": "Camera atualizada com sucesso"
}
```

---

#### DELETE /cameras/{id}

Remove uma camera e opcionalmente suas gravacoes.

**Request:**

```http
DELETE /api/v1/cameras/2?delete_recordings=false
Authorization: Bearer {token}
```

**Query Parameters:**

| Parametro | Tipo | Descricao |
|-----------|------|-----------|
| delete_recordings | boolean | Remover gravacoes associadas (default: false) |

**Response (200):**

```json
{
  "success": true,
  "message": "Camera removida com sucesso"
}
```

---

#### POST /cameras/discover

Inicia descoberta automatica de cameras na rede.

**Request:**

```http
POST /api/v1/cameras/discover
Authorization: Bearer {token}
Content-Type: application/json

{
  "timeout": 10,
  "protocols": ["onvif", "ssdp"]
}
```

**Response (200):**

```json
{
  "success": true,
  "data": {
    "discovered": [
      {
        "ip_address": "192.168.1.102",
        "manufacturer": "Hikvision",
        "model": "DS-2CD2143G0-I",
        "onvif_url": "http://192.168.1.102:80/onvif/device_service",
        "rtsp_url": "rtsp://192.168.1.102:554/Streaming/Channels/101"
      }
    ],
    "scan_duration": 8.5
  }
}
```

---

#### POST /cameras/{id}/test

Testa conexao com uma camera.

**Request:**

```http
POST /api/v1/cameras/1/test
Authorization: Bearer {token}
```

**Response (200):**

```json
{
  "success": true,
  "data": {
    "connection": "ok",
    "rtsp_stream": "ok",
    "onvif": "ok",
    "latency_ms": 45,
    "resolution": "1920x1080",
    "fps": 25
  }
}
```

---

### Gravacoes

#### GET /recordings

Lista gravacoes com filtros.

**Request:**

```http
GET /api/v1/recordings?camera_id=1&date=2024-01-15&has_motion=true
Authorization: Bearer {token}
```

**Query Parameters:**

| Parametro | Tipo | Descricao |
|-----------|------|-----------|
| camera_id | integer | ID da camera |
| date | string | Data (YYYY-MM-DD) |
| start_date | string | Data inicial |
| end_date | string | Data final |
| has_motion | boolean | Apenas com movimento |
| page | integer | Numero da pagina |
| limit | integer | Itens por pagina |

**Response (200):**

```json
{
  "success": true,
  "data": {
    "recordings": [
      {
        "id": 123,
        "camera_id": 1,
        "camera_name": "Camera Entrada",
        "start_time": "2024-01-15T10:00:00Z",
        "end_time": "2024-01-15T10:30:00Z",
        "duration": 1800,
        "file_size": 157286400,
        "has_motion": true,
        "motion_events_count": 3,
        "thumbnail": "/api/v1/recordings/123/thumbnail"
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 48,
      "pages": 3
    },
    "summary": {
      "total_duration": 86400,
      "total_size": 5368709120,
      "motion_events": 45
    }
  }
}
```

---

#### GET /recordings/{id}

Detalhes de uma gravacao.

**Request:**

```http
GET /api/v1/recordings/123
Authorization: Bearer {token}
```

**Response (200):**

```json
{
  "success": true,
  "data": {
    "id": 123,
    "camera_id": 1,
    "camera_name": "Camera Entrada",
    "start_time": "2024-01-15T10:00:00Z",
    "end_time": "2024-01-15T10:30:00Z",
    "duration": 1800,
    "file_path": "/recordings/camera_1/2024-01-15/10-00-00.mp4",
    "file_size": 157286400,
    "has_motion": true,
    "motion_events": [
      {
        "id": 456,
        "timestamp": "2024-01-15T10:05:23Z",
        "confidence": 0.87,
        "thumbnail": "/api/v1/events/456/thumbnail"
      }
    ],
    "thumbnail": "/api/v1/recordings/123/thumbnail",
    "stream_url": "/api/v1/recordings/123/stream"
  }
}
```

---

#### GET /recordings/{id}/stream

Stream de uma gravacao (suporta range requests).

**Request:**

```http
GET /api/v1/recordings/123/stream
Authorization: Bearer {token}
Range: bytes=0-1048575
```

**Response (206 Partial Content):**

```http
HTTP/1.1 206 Partial Content
Content-Type: video/mp4
Content-Range: bytes 0-1048575/157286400
Content-Length: 1048576

[binary video data]
```

---

#### GET /recordings/{id}/thumbnail

Thumbnail de uma gravacao.

**Request:**

```http
GET /api/v1/recordings/123/thumbnail
Authorization: Bearer {token}
```

**Response (200):**

```http
HTTP/1.1 200 OK
Content-Type: image/jpeg

[binary image data]
```

---

#### DELETE /recordings/{id}

Remove uma gravacao.

**Request:**

```http
DELETE /api/v1/recordings/123
Authorization: Bearer {token}
```

**Response (200):**

```json
{
  "success": true,
  "message": "Gravacao removida com sucesso"
}
```

---

#### GET /recordings/timeline

Retorna timeline de gravacoes para visualizacao.

**Request:**

```http
GET /api/v1/recordings/timeline?camera_id=1&date=2024-01-15
Authorization: Bearer {token}
```

**Response (200):**

```json
{
  "success": true,
  "data": {
    "date": "2024-01-15",
    "camera_id": 1,
    "segments": [
      {
        "start": "2024-01-15T00:00:00Z",
        "end": "2024-01-15T02:30:00Z",
        "has_motion": false
      },
      {
        "start": "2024-01-15T02:30:00Z",
        "end": "2024-01-15T02:35:00Z",
        "has_motion": true,
        "motion_events": 2
      },
      {
        "start": "2024-01-15T02:35:00Z",
        "end": "2024-01-15T08:00:00Z",
        "has_motion": false
      }
    ],
    "gaps": [
      {
        "start": "2024-01-15T08:00:00Z",
        "end": "2024-01-15T08:15:00Z",
        "reason": "camera_offline"
      }
    ]
  }
}
```

---

### Eventos de Movimento

#### GET /events

Lista eventos de movimento.

**Request:**

```http
GET /api/v1/events?camera_id=1&date=2024-01-15
Authorization: Bearer {token}
```

**Query Parameters:**

| Parametro | Tipo | Descricao |
|-----------|------|-----------|
| camera_id | integer | ID da camera |
| date | string | Data (YYYY-MM-DD) |
| start_date | string | Data inicial |
| end_date | string | Data final |
| min_confidence | float | Confianca minima (0-1) |
| page | integer | Numero da pagina |
| limit | integer | Itens por pagina |

**Response (200):**

```json
{
  "success": true,
  "data": {
    "events": [
      {
        "id": 456,
        "camera_id": 1,
        "camera_name": "Camera Entrada",
        "timestamp": "2024-01-15T10:05:23Z",
        "confidence": 0.87,
        "recording_id": 123,
        "recording_offset": 323,
        "region": {
          "x": 120,
          "y": 80,
          "width": 200,
          "height": 300
        },
        "thumbnail": "/api/v1/events/456/thumbnail",
        "notified": true
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 45,
      "pages": 3
    }
  }
}
```

---

#### GET /events/{id}

Detalhes de um evento.

**Request:**

```http
GET /api/v1/events/456
Authorization: Bearer {token}
```

**Response (200):**

```json
{
  "success": true,
  "data": {
    "id": 456,
    "camera_id": 1,
    "camera_name": "Camera Entrada",
    "timestamp": "2024-01-15T10:05:23Z",
    "confidence": 0.87,
    "recording_id": 123,
    "recording_offset": 323,
    "region": {
      "x": 120,
      "y": 80,
      "width": 200,
      "height": 300
    },
    "thumbnail": "/api/v1/events/456/thumbnail",
    "clip_url": "/api/v1/events/456/clip",
    "notified": true,
    "notified_at": "2024-01-15T10:05:25Z"
  }
}
```

---

#### GET /events/{id}/clip

Clip de video do evento (10-30 segundos).

**Request:**

```http
GET /api/v1/events/456/clip
Authorization: Bearer {token}
```

**Response (200):**

```http
HTTP/1.1 200 OK
Content-Type: video/mp4
Content-Length: 5242880

[binary video data]
```

---

### Streaming

#### GET /stream/{camera_id}/live

URL para stream ao vivo HLS.

**Request:**

```http
GET /api/v1/stream/1/live
Authorization: Bearer {token}
```

**Response (200):**

```json
{
  "success": true,
  "data": {
    "hls_url": "/stream/1/live/playlist.m3u8",
    "webrtc_url": "wss://localhost:8000/stream/1/webrtc",
    "thumbnail": "/api/v1/stream/1/snapshot",
    "resolution": "1920x1080",
    "fps": 25
  }
}
```

---

#### GET /stream/{camera_id}/snapshot

Captura frame atual da camera.

**Request:**

```http
GET /api/v1/stream/1/snapshot
Authorization: Bearer {token}
```

**Response (200):**

```http
HTTP/1.1 200 OK
Content-Type: image/jpeg

[binary image data]
```

---

### Configuracoes

#### GET /settings

Lista todas as configuracoes.

**Request:**

```http
GET /api/v1/settings
Authorization: Bearer {token}
```

**Response (200):**

```json
{
  "success": true,
  "data": {
    "server": {
      "port": 8000,
      "debug": false
    },
    "recording": {
      "enabled": true,
      "path": "/recordings",
      "max_storage_gb": 100,
      "retention_days": 30,
      "clip_duration": 30
    },
    "motion_detection": {
      "enabled": true,
      "mode": "software",
      "default_sensitivity": 50
    },
    "notifications": {
      "push_enabled": true,
      "email_enabled": false
    },
    "storage": {
      "used_gb": 45.2,
      "total_gb": 100,
      "free_gb": 54.8,
      "oldest_recording": "2024-01-01T00:00:00Z"
    }
  }
}
```

---

#### PUT /settings

Atualiza configuracoes.

**Request:**

```http
PUT /api/v1/settings
Authorization: Bearer {token}
Content-Type: application/json

{
  "recording": {
    "retention_days": 45
  },
  "motion_detection": {
    "default_sensitivity": 60
  }
}
```

**Response (200):**

```json
{
  "success": true,
  "message": "Configuracoes atualizadas com sucesso"
}
```

---

#### GET /settings/storage

Informacoes de armazenamento.

**Request:**

```http
GET /api/v1/settings/storage
Authorization: Bearer {token}
```

**Response (200):**

```json
{
  "success": true,
  "data": {
    "disks": [
      {
        "path": "/recordings",
        "total_gb": 500,
        "used_gb": 245.8,
        "free_gb": 254.2,
        "percent_used": 49.16
      }
    ],
    "recordings_summary": {
      "total_count": 1250,
      "total_size_gb": 245.8,
      "oldest": "2024-01-01T00:00:00Z",
      "newest": "2024-01-15T10:30:00Z",
      "by_camera": [
        {"camera_id": 1, "size_gb": 50.2},
        {"camera_id": 2, "size_gb": 48.7}
      ]
    }
  }
}
```

---

## WebSocket

### Conexao

```javascript
const ws = new WebSocket('wss://localhost:8000/ws?token=eyJhbGciOiJIUzI1NiIs...');
```

### Eventos Recebidos

#### camera.status

```json
{
  "event": "camera.status",
  "data": {
    "camera_id": 1,
    "status": "online",
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

#### motion.detected

```json
{
  "event": "motion.detected",
  "data": {
    "camera_id": 1,
    "camera_name": "Camera Entrada",
    "event_id": 456,
    "confidence": 0.87,
    "thumbnail": "/api/v1/events/456/thumbnail",
    "timestamp": "2024-01-15T10:05:23Z"
  }
}
```

#### recording.started

```json
{
  "event": "recording.started",
  "data": {
    "camera_id": 1,
    "recording_id": 124,
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

#### recording.stopped

```json
{
  "event": "recording.stopped",
  "data": {
    "camera_id": 1,
    "recording_id": 123,
    "duration": 1800,
    "file_size": 157286400,
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

#### storage.warning

```json
{
  "event": "storage.warning",
  "data": {
    "percent_used": 90,
    "free_gb": 10,
    "message": "Armazenamento quase cheio"
  }
}
```

### Comandos Enviados

#### subscribe

```json
{
  "command": "subscribe",
  "channels": ["camera.1", "motion", "storage"]
}
```

#### unsubscribe

```json
{
  "command": "unsubscribe",
  "channels": ["camera.1"]
}
```

---

## Codigos de Erro

| Codigo HTTP | Codigo Erro | Descricao |
|-------------|-------------|-----------|
| 400 | INVALID_REQUEST | Requisicao mal formada |
| 401 | UNAUTHORIZED | Token ausente ou invalido |
| 401 | TOKEN_EXPIRED | Token expirado |
| 403 | FORBIDDEN | Sem permissao para o recurso |
| 404 | NOT_FOUND | Recurso nao encontrado |
| 404 | CAMERA_NOT_FOUND | Camera nao encontrada |
| 404 | RECORDING_NOT_FOUND | Gravacao nao encontrada |
| 409 | CONFLICT | Conflito (ex: camera ja existe) |
| 422 | VALIDATION_ERROR | Erro de validacao de dados |
| 422 | MAX_CAMERAS_REACHED | Limite de cameras atingido |
| 429 | RATE_LIMITED | Muitas requisicoes |
| 500 | INTERNAL_ERROR | Erro interno do servidor |
| 503 | SERVICE_UNAVAILABLE | Servico indisponivel |

---

## Rate Limiting

| Endpoint | Limite |
|----------|--------|
| /auth/login | 5 req/min |
| /cameras/discover | 1 req/min |
| /stream/* | 100 req/min |
| Outros | 60 req/min |

Headers de resposta:

```http
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1705312260
```

---

## Exemplos

### Python

```python
import requests

BASE_URL = "http://localhost:8000/api/v1"

# Login
response = requests.post(f"{BASE_URL}/auth/login", json={
    "username": "admin",
    "password": "senha123"
})
token = response.json()["data"]["access_token"]

headers = {"Authorization": f"Bearer {token}"}

# Listar cameras
cameras = requests.get(f"{BASE_URL}/cameras", headers=headers)
print(cameras.json())

# Adicionar camera
new_camera = requests.post(f"{BASE_URL}/cameras", headers=headers, json={
    "name": "Camera Teste",
    "ip_address": "192.168.1.100",
    "rtsp_url": "rtsp://192.168.1.100:554/stream1",
    "username": "admin",
    "password": "camera123"
})
print(new_camera.json())
```

### JavaScript/TypeScript

```typescript
const BASE_URL = 'http://localhost:8000/api/v1';

async function login(username: string, password: string): Promise<string> {
  const response = await fetch(`${BASE_URL}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password })
  });
  const data = await response.json();
  return data.data.access_token;
}

async function getCameras(token: string) {
  const response = await fetch(`${BASE_URL}/cameras`, {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  return response.json();
}

// WebSocket
function connectWebSocket(token: string) {
  const ws = new WebSocket(`ws://localhost:8000/ws?token=${token}`);

  ws.onopen = () => {
    ws.send(JSON.stringify({
      command: 'subscribe',
      channels: ['motion', 'camera.1']
    }));
  };

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.event === 'motion.detected') {
      console.log('Movimento detectado!', data.data);
    }
  };

  return ws;
}
```

### cURL

```bash
# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"senha123"}'

# Listar cameras (substitua TOKEN)
curl http://localhost:8000/api/v1/cameras \
  -H "Authorization: Bearer TOKEN"

# Descobrir cameras
curl -X POST http://localhost:8000/api/v1/cameras/discover \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"timeout":10}'

# Snapshot de camera
curl http://localhost:8000/api/v1/stream/1/snapshot \
  -H "Authorization: Bearer TOKEN" \
  --output snapshot.jpg
```
