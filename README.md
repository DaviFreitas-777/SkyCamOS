# SkyCamOS

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Version](https://img.shields.io/badge/version-1.0.0--alpha-orange.svg)]()
[![Python](https://img.shields.io/badge/python-3.10+-green.svg)](https://www.python.org/)
[![Status](https://img.shields.io/badge/status-em%20desenvolvimento-yellow.svg)]()

**Sistema open source de monitoramento de cameras IP** com interface desktop e web PWA. Uma alternativa leve e simplificada ao Digiforte e Luxriot EVO.

---

## Screenshots

> Em breve

| Dashboard | Mosaico 2x2 | Timeline |
|-----------|-------------|----------|
| ![Dashboard](docs/assets/screenshot-dashboard.png) | ![Mosaico](docs/assets/screenshot-mosaic.png) | ![Timeline](docs/assets/screenshot-timeline.png) |

---

## Funcionalidades Principais

- **Descoberta Automatica** - Detecta cameras IP via protocolos ONVIF e SSDP
- **Visualizacao ao Vivo** - Stream em tempo real com WebRTC e HLS
- **Layouts Flexiveis** - Mosaicos configuráveis (1x1, 2x2, 3x3) com modo ronda
- **Gravacao Inteligente** - Continua ou por eventos de movimento
- **Deteccao de Movimento** - Via software (diff de frames) ou eventos nativos da camera
- **PWA Completo** - Instalavel como app, funciona offline, notificacoes push
- **Acesso Remoto** - Interface web acessivel de qualquer lugar
- **Armazenamento FIFO** - Sobrescrita automatica de gravacoes antigas
- **Multi-plataforma** - Suporte a Windows, Linux e macOS

---

## Arquitetura do Sistema

```
+-------------------+     +-------------------+     +-------------------+
|                   |     |                   |     |                   |
|  Desktop Manager  |<--->|   Backend/API     |<--->|     Web/PWA       |
|                   |     |                   |     |                   |
+-------------------+     +-------------------+     +-------------------+
         |                         |                         |
         v                         v                         v
+-------------------+     +-------------------+     +-------------------+
|                   |     |                   |     |                   |
|  Cameras IP       |     |  SQLite Database  |     |  Service Worker   |
|  (ONVIF/RTSP)     |     |                   |     |  + Cache          |
|                   |     |                   |     |                   |
+-------------------+     +-------------------+     +-------------------+
```

### Componentes

| Componente | Descricao |
|------------|-----------|
| **Desktop Manager** | Interface de configuracao, descoberta de cameras e gerenciamento de disco |
| **Backend/API** | REST API + WebSockets, conversao RTSP, gravacao e deteccao de movimento |
| **Web/PWA** | Interface responsiva, mosaicos, timeline, notificacoes push |
| **SQLite** | Armazenamento de cameras, configuracoes, eventos e usuarios |

Para detalhes completos, consulte a [Documentacao de Arquitetura](docs/ARCHITECTURE.md).

---

## Requisitos de Sistema

### Minimos

| Recurso | Especificacao |
|---------|---------------|
| **Sistema Operacional** | Windows 10+, Ubuntu 20.04+, macOS 11+ |
| **Processador** | Intel i3 / AMD Ryzen 3 ou superior |
| **Memoria RAM** | 4 GB |
| **Armazenamento** | 50 GB livres (mais espaco = mais dias de gravacao) |
| **Python** | 3.10 ou superior |
| **Rede** | Conexao na mesma rede das cameras |

### Recomendados (para 10 cameras)

| Recurso | Especificacao |
|---------|---------------|
| **Processador** | Intel i5 / AMD Ryzen 5 ou superior |
| **Memoria RAM** | 8 GB ou mais |
| **Armazenamento** | SSD com 500 GB+ |
| **GPU** | Dedicada (para transcoding acelerado) |

---

## Instalacao

### 1. Clonar o Repositorio

```bash
git clone https://github.com/seu-usuario/skycamos.git
cd skycamos
```

### 2. Criar Ambiente Virtual

```bash
# Windows
py -m venv venv
venv\Scripts\activate

# Linux/macOS
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar Dependencias

```bash
pip install -r requirements.txt
```

### 4. Executar o Sistema

```bash
# Terminal 1 - Backend (porta 8000)
cd backend
py -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2 - Frontend (porta 3000)
cd frontend
npx serve public -l 3000

# Opcional - Desktop Manager (CLI)
cd desktop
py run.py
```

> O banco de dados SQLite e criado automaticamente na primeira execucao

### 6. Desktop Manager (Opcional)

O Desktop Manager oferece uma interface CLI para gerenciamento do sistema, descoberta de cameras e monitoramento de disco.

**Instalar dependencias do Desktop:**

```bash
cd desktop
pip install -r requirements.txt
```

**Executar Desktop Manager:**

```bash
# Modo interativo (CLI)
start-desktop.bat

# Ou diretamente via Python
python run.py

# Modo minimizado (apenas tray)
start-desktop-tray.bat

# Ou via Python
pythonw run.py --minimized
```

**Comandos disponiveis no CLI:**

| Comando | Descricao |
|---------|-----------|
| `status` | Mostra status do backend, disco e cameras |
| `cameras` | Lista cameras descobertas |
| `discover` | Executa descoberta de cameras na rede |
| `start` | Inicia o backend |
| `stop` | Para o backend |
| `restart` | Reinicia o backend |
| `disk` | Mostra informacoes de armazenamento |
| `cleanup` | Executa limpeza de gravacoes antigas |
| `config` | Exibe configuracao atual |
| `autostart` | Configura inicio automatico com Windows |
| `help` | Exibe ajuda |
| `quit` | Sai do programa |

**Opcoes de linha de comando:**

```bash
python run.py --help        # Exibe ajuda
python run.py --minimized   # Inicia minimizado (apenas system tray)
python run.py --no-tray     # Desabilita icone na bandeja
python run.py --debug       # Modo de debug (mais logs)
python run.py --service     # Modo servico (sem interface)
python run.py --version     # Exibe versao
```

### 7. Acessar a Interface Web

- **Local:** `http://localhost:3000`
- **Rede Local:** `http://SEU-IP:3000`
- **Credenciais:** `admin / admin123`

---

## Configuracao

### Arquivo config.yaml

```yaml
# Configuracao do servidor
server:
  host: "0.0.0.0"
  port: 8000
  debug: false

# Configuracao de cameras
cameras:
  max_cameras: 10
  discovery_interval: 300  # segundos

# Configuracao de gravacao
recording:
  enabled: true
  path: "./recordings"
  max_storage_gb: 100
  retention_days: 30
  clip_duration: 30  # segundos

# Configuracao de deteccao de movimento
motion_detection:
  enabled: true
  mode: "software"  # "software" ou "onvif"
  sensitivity: 50   # 0-100

# Configuracao PWA
pwa:
  enabled: true
  push_notifications: true
  vapid_public_key: "sua-chave-publica"
  vapid_private_key: "sua-chave-privada"
```

Para mais detalhes, consulte a [Documentacao de Configuracao](docs/DEPLOYMENT.md#configuracao).

---

## Como Usar

### Adicionar uma Camera

1. Acesse o painel de configuracoes
2. Clique em "Adicionar Camera"
3. Use a descoberta automatica ou insira os dados manualmente:
   - Nome da camera
   - Endereco IP / URL RTSP
   - Usuario e senha (se necessario)
4. Teste a conexao e salve

### Visualizar ao Vivo

1. Acesse o Dashboard principal
2. Selecione o layout desejado (1x1, 2x2, 3x3)
3. Clique em uma camera para expandir em tela cheia

### Acessar Gravacoes

1. Va para a secao "Timeline"
2. Selecione a camera e a data
3. Navegue pela linha do tempo
4. Clique para reproduzir

### Instalar o PWA

1. Acesse a interface web pelo celular
2. O navegador oferecera "Adicionar a tela inicial"
3. Aceite para instalar como app

---

## Documentacao da API

A API RESTful do SkyCamOS oferece acesso programatico a todas as funcionalidades.

**Documentacao completa:** [docs/API.md](docs/API.md)

### Endpoints Principais

| Metodo | Endpoint | Descricao |
|--------|----------|-----------|
| GET | `/api/cameras` | Lista todas as cameras |
| POST | `/api/cameras` | Adiciona uma camera |
| GET | `/api/cameras/{id}/stream` | Obtem URL de stream |
| GET | `/api/recordings` | Lista gravacoes |
| GET | `/api/events` | Lista eventos de movimento |
| POST | `/api/auth/login` | Autenticacao |

### Exemplo de Uso

```bash
# Listar cameras
curl -X GET http://localhost:8000/api/cameras \
  -H "Authorization: Bearer seu-token"

# Resposta
{
  "cameras": [
    {
      "id": 1,
      "name": "Camera Entrada",
      "ip": "192.168.1.100",
      "status": "online"
    }
  ]
}
```

---

## Contribuindo

Contribuicoes sao bem-vindas! Por favor, leia nosso [Guia de Contribuicao](CONTRIBUTING.md) antes de enviar pull requests.

### Formas de Contribuir

- Reportar bugs e problemas
- Sugerir novas funcionalidades
- Melhorar a documentacao
- Enviar correcoes de codigo
- Traduzir para outros idiomas

### Inicio Rapido para Desenvolvedores

```bash
# Fork e clone
git clone https://github.com/seu-usuario/skycamos.git
cd skycamos

# Crie uma branch para sua feature
git checkout -b feature/minha-feature

# Faca suas alteracoes e commit
git commit -m "feat: adiciona minha feature"

# Envie o pull request
git push origin feature/minha-feature
```

---

## Roadmap

### Versao 1.0 (MVP) - Concluida

- [x] Estrutura inicial do projeto
- [x] Descoberta de cameras ONVIF/SSDP
- [x] Visualizacao ao vivo (MJPEG/WebSocket)
- [x] Gravacao local
- [x] Interface web basica (Dashboard, Login, Recordings, Events, Settings)
- [x] PWA instalavel (manifest.json, Service Worker)

### Versao 1.1 - Em Progresso

- [ ] WebRTC para baixa latencia
- [x] Deteccao de movimento por software (OpenCV MOG2)
- [x] Notificacoes push (Service Worker + Backend)
- [x] Timeline de gravacoes

### Versao 2.0 - Parcialmente Implementada

- [x] Deteccao de pessoas com IA (MobileNet SSD/HOG)
- [ ] Integracao com assistentes de voz
- [ ] Modo cloud (opcional)
- [x] Line crossing detection

---

## Licenca

Este projeto esta licenciado sob a **MIT License** - veja o arquivo [LICENSE](LICENSE) para detalhes.

```
MIT License

Copyright (c) 2024 SkyCamOS Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
```

---

## Creditos

### Equipe Principal

- Desenvolvido com assistencia de IA (Claude - Anthropic)

### Tecnologias Utilizadas

- [Python](https://www.python.org/) - Linguagem principal do backend
- [FastAPI](https://fastapi.tiangolo.com/) - Framework web assincrono
- [OpenCV](https://opencv.org/) - Processamento de video e deteccao de movimento
- [SQLite](https://www.sqlite.org/) - Banco de dados embarcado (SQLAlchemy async)
- [Vanilla JS](https://developer.mozilla.org/pt-BR/docs/Web/JavaScript) - Frontend PWA (ES Modules)

### Agradecimentos

- Comunidade open source de video vigilancia
- Contribuidores do protocolo ONVIF
- Todos que reportaram bugs e sugeriram melhorias

---

## Suporte

- **Issues:** [GitHub Issues](https://github.com/seu-usuario/skycamos/issues)
- **Discussoes:** [GitHub Discussions](https://github.com/seu-usuario/skycamos/discussions)
- **Documentacao:** [docs/](docs/)

---

<p align="center">
  Feito com dedicacao para a comunidade de seguranca residencial
</p>
