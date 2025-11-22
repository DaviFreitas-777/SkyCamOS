# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Idioma / Language

Sempre responda em **Portugues BR**. Evite usar emojis no codigo para prevenir problemas de encoding.

## Projeto

**SkyCamOS** - Sistema de monitoramento de cameras IP (desktop + web PWA), similar ao Digiforte/Luxriot EVO, porem simplificado.

### Documentacao Principal

O arquivo `SkyCamOS.md` contem os requisitos completos e especificacao arquitetural do projeto.

## Arquitetura

O sistema e composto por 4 modulos principais:

### 1. Desktop Manager
- Descoberta automatica de cameras via ONVIF/SSDP
- Configuracao de gravacoes e gerenciamento de disco
- Gerenciamento do PWA e API

### 2. Backend/API
- REST API + WebSockets para streaming ao vivo
- Servico de gravacao (continua + por eventos)
- Sobrescrita FIFO para gerenciamento de armazenamento
- Deteccao de movimento (software ou ONVIF nativo)
- Notificacoes push
- Conversao RTSP para WebRTC/HLS

### 3. Web/PWA
- Dashboard de cameras (mosaicos 1x1, 2x2, 3x3)
- Timeline de gravacoes e reproducao
- Modo offline com dados em cache
- Notificacoes push
- Instalavel como app nativo

### 4. Banco de Dados (SQLite)
- Cameras, configuracoes, eventos de movimento, gravacoes, usuarios

## Comandos

```bash
# Executar Python (Windows)
py <script.py>

# Executar testes (quando implementado)
py -m pytest

# Executar servidor de desenvolvimento (quando implementado)
py -m uvicorn main:app --reload
```

## Diretrizes de Desenvolvimento

1. **Antes de implementar**: Sempre verificar a arquitetura existente para evitar duplicacao de codigo ou funcionalidades
2. **Cameras suportadas**: Ate 10 cameras IP
3. **Protocolos**: ONVIF, SSDP, RTSP, WebRTC, HLS
4. **Deteccao de movimento**:
   - Opcao 1: Diferenca entre frames (software)
   - Opcao 2: Eventos ONVIF nativos da camera
5. **Gravacoes**: Clips de 10-30 segundos em eventos de movimento
