# Troubleshooting - Resolucao de Problemas

Guia para diagnosticar e resolver problemas comuns do SkyCamOS.

---

## Sumario

- [Problemas de Instalacao](#problemas-de-instalacao)
- [Problemas de Cameras](#problemas-de-cameras)
- [Problemas de Streaming](#problemas-de-streaming)
- [Problemas de Gravacao](#problemas-de-gravacao)
- [Problemas de Deteccao de Movimento](#problemas-de-deteccao-de-movimento)
- [Problemas de Performance](#problemas-de-performance)
- [Problemas de PWA](#problemas-de-pwa)
- [Problemas de Rede](#problemas-de-rede)
- [Logs e Diagnostico](#logs-e-diagnostico)
- [FAQ](#faq)

---

## Problemas de Instalacao

### Erro: "FFmpeg nao encontrado"

**Sintoma:**
```
FileNotFoundError: [Errno 2] No such file or directory: 'ffmpeg'
```

**Solucao:**

Windows:
```powershell
# Baixar FFmpeg de https://ffmpeg.org/download.html
# Extrair para C:\ffmpeg
# Adicionar ao PATH:
# Sistema > Variaveis de Ambiente > Path > Editar > Novo > C:\ffmpeg\bin

# Verificar instalacao
ffmpeg -version
```

Linux:
```bash
sudo apt update
sudo apt install ffmpeg

# Verificar
ffmpeg -version
```

macOS:
```bash
brew install ffmpeg
```

---

### Erro: "ModuleNotFoundError: No module named 'xxx'"

**Sintoma:**
```
ModuleNotFoundError: No module named 'fastapi'
```

**Solucao:**

```bash
# Verificar se o ambiente virtual esta ativo
# Windows
.\venv\Scripts\Activate

# Linux/macOS
source venv/bin/activate

# Reinstalar dependencias
pip install -r requirements.txt

# Se o problema persistir, recriar ambiente
deactivate
rm -rf venv
py -m venv venv
source venv/bin/activate  # ou .\venv\Scripts\Activate no Windows
pip install -r requirements.txt
```

---

### Erro: "Permission denied" ao instalar

**Sintoma:**
```
PermissionError: [Errno 13] Permission denied: '/opt/skycamos'
```

**Solucao:**

```bash
# Linux - ajustar permissoes
sudo chown -R $USER:$USER /opt/skycamos

# Ou usar pip com --user
pip install --user -r requirements.txt
```

---

## Problemas de Cameras

### Camera nao e descoberta automaticamente

**Possiveis causas e solucoes:**

1. **Camera em subnet diferente**
   ```bash
   # Verificar IP da camera e do servidor
   ip addr show  # Linux
   ipconfig      # Windows

   # Camera e servidor devem estar na mesma subnet
   # Ex: 192.168.1.x
   ```

2. **Firewall bloqueando descoberta**
   ```bash
   # Linux - liberar portas ONVIF
   sudo ufw allow 3702/udp  # WS-Discovery
   sudo ufw allow 80/tcp    # ONVIF HTTP

   # Windows - verificar firewall do Windows
   ```

3. **Camera nao suporta ONVIF**
   - Use adicao manual com URL RTSP
   - Consulte manual da camera para obter URL RTSP

---

### Camera mostra "offline" mesmo estando ligada

**Diagnostico:**

```bash
# 1. Verificar conectividade
ping 192.168.1.100  # IP da camera

# 2. Verificar porta RTSP
# Windows
Test-NetConnection -ComputerName 192.168.1.100 -Port 554

# Linux
nc -zv 192.168.1.100 554

# 3. Testar stream RTSP
ffplay rtsp://usuario:senha@192.168.1.100:554/stream1
```

**Solucoes:**

1. **Credenciais incorretas**
   - Verificar usuario/senha na interface da camera
   - Atualizar credenciais no SkyCamOS

2. **URL RTSP incorreta**
   - Cada fabricante usa URLs diferentes
   - Exemplos comuns:
     ```
     # Intelbras
     rtsp://user:pass@ip:554/cam/realmonitor?channel=1&subtype=0

     # Hikvision
     rtsp://user:pass@ip:554/Streaming/Channels/101

     # Dahua
     rtsp://user:pass@ip:554/cam/realmonitor?channel=1&subtype=0
     ```

3. **Camera com muitas conexoes**
   - Cameras baratas suportam poucas conexoes simultaneas
   - Fechar outros softwares que acessam a camera

---

### Erro: "401 Unauthorized" ao conectar camera

**Sintoma:**
```
RTSP Error: 401 Unauthorized
```

**Solucao:**

```python
# Testar autenticacao manualmente
import requests

# ONVIF usa autenticacao Digest
response = requests.get(
    "http://192.168.1.100:80/onvif/device_service",
    auth=requests.auth.HTTPDigestAuth("admin", "senha")
)
print(response.status_code)
```

1. Verificar se o usuario tem permissao para RTSP
2. Algumas cameras exigem ativar autenticacao RTSP
3. Resetar senha da camera se necessario

---

## Problemas de Streaming

### Video nao carrega no navegador

**Diagnostico:**

```javascript
// Console do navegador (F12)
// Verificar erros de rede
```

**Solucoes:**

1. **CORS bloqueando requisicoes**
   ```yaml
   # config.yaml
   server:
     cors:
       enabled: true
       origins:
         - "*"  # Em desenvolvimento
   ```

2. **HLS nao esta sendo gerado**
   ```bash
   # Verificar se segmentos estao sendo criados
   ls -la ./data/hls/camera_1/

   # Deve mostrar arquivos .ts e .m3u8
   ```

3. **FFmpeg falhando silenciosamente**
   ```bash
   # Executar FFmpeg manualmente para ver erros
   ffmpeg -rtsp_transport tcp \
     -i "rtsp://user:pass@192.168.1.100:554/stream" \
     -c:v copy -c:a aac \
     -f hls -hls_time 2 -hls_list_size 5 \
     ./test/playlist.m3u8
   ```

---

### Alta latencia no stream (> 5 segundos)

**Causas e solucoes:**

1. **HLS tem latencia inerente (2-10s)**
   - Use WebRTC para baixa latencia
   - Ou ajuste configuracao HLS:
   ```yaml
   streaming:
     hls:
       segment_duration: 1  # Reduzir de 2 para 1
       playlist_size: 3     # Reduzir de 5 para 3
   ```

2. **Transcoding lento**
   - Ativar aceleracao por hardware:
   ```yaml
   streaming:
     transcoding:
       hardware_acceleration:
         enabled: true
         type: "nvenc"  # NVIDIA
   ```

3. **Rede congestionada**
   - Verificar uso de banda:
   ```bash
   # Linux
   iftop -i eth0

   # Windows
   # Use Resource Monitor
   ```

---

### Stream congela ou apresenta artefatos

**Solucoes:**

1. **Usar TCP em vez de UDP para RTSP**
   ```bash
   # FFmpeg com TCP
   ffmpeg -rtsp_transport tcp -i "rtsp://..."
   ```

   ```yaml
   # config.yaml
   cameras:
     connection:
       rtsp_transport: "tcp"
   ```

2. **Reduzir qualidade do stream**
   - Configurar camera para bitrate menor
   - Usar substream em vez de mainstream

3. **Aumentar buffer**
   ```yaml
   streaming:
     buffer_size: 1048576  # 1MB
   ```

---

## Problemas de Gravacao

### Gravacoes nao estao sendo salvas

**Diagnostico:**

```bash
# Verificar espaco em disco
df -h /path/to/recordings

# Verificar permissoes
ls -la /path/to/recordings

# Verificar logs
tail -f logs/skycamos.log | grep -i recording
```

**Solucoes:**

1. **Disco cheio**
   ```bash
   # Limpar gravacoes antigas manualmente
   find /recordings -mtime +30 -type f -delete
   ```

2. **Permissoes incorretas**
   ```bash
   sudo chown -R skycamos:skycamos /path/to/recordings
   sudo chmod 755 /path/to/recordings
   ```

3. **Gravacao desativada**
   ```yaml
   # config.yaml
   recording:
     enabled: true
   ```

---

### Gravacoes corrompidas

**Sintoma:** Arquivos MP4 nao reproduzem ou param no meio

**Solucoes:**

1. **Sistema desligou durante gravacao**
   ```bash
   # Tentar reparar com FFmpeg
   ffmpeg -i corrupted.mp4 -c copy repaired.mp4
   ```

2. **Usar formato mais resiliente**
   ```yaml
   recording:
     format:
       container: "mkv"  # MKV e mais tolerante a corrupcao
   ```

3. **Gravar em segmentos menores**
   ```yaml
   recording:
     format:
       segment_duration: 60  # 1 minuto por arquivo
   ```

---

### Espaco em disco enchendo rapidamente

**Calculo de espaco necessario:**

```
Bitrate (Mbps) x 3600 (segundos/hora) / 8 = MB/hora
Exemplo: 4 Mbps x 3600 / 8 = 1800 MB/hora = 43.2 GB/dia por camera
```

**Solucoes:**

1. **Ajustar retencao**
   ```yaml
   recording:
     storage:
       retention_days: 7  # Reduzir dias
   ```

2. **Reduzir qualidade**
   - Configurar cameras para menor bitrate
   - Usar 720p em vez de 1080p

3. **Gravar apenas por movimento**
   ```yaml
   recording:
     modes:
       continuous:
         enabled: false
       motion_triggered:
         enabled: true
   ```

---

## Problemas de Deteccao de Movimento

### Muitos falsos positivos

**Causas e solucoes:**

1. **Sensibilidade muito alta**
   ```yaml
   motion_detection:
     software:
       sensitivity: 30  # Reduzir de 50 para 30
       min_area: 1000   # Aumentar area minima
   ```

2. **Mudancas de iluminacao**
   - Evitar cameras apontadas para janelas
   - Usar ROI para excluir areas problematicas

3. **Vegetacao/objetos em movimento**
   - Configurar regioes de interesse (ROI)
   - Excluir areas com arvores/bandeiras

---

### Movimento nao esta sendo detectado

**Solucoes:**

1. **Sensibilidade muito baixa**
   ```yaml
   motion_detection:
     software:
       sensitivity: 70  # Aumentar
       threshold: 15    # Reduzir threshold
   ```

2. **Deteccao desativada**
   ```yaml
   motion_detection:
     enabled: true
   ```

3. **Verificar se camera esta enviando frames**
   ```bash
   # Testar deteccao manualmente
   py scripts/test_motion.py --camera 1
   ```

---

## Problemas de Performance

### Alto uso de CPU

**Diagnostico:**

```bash
# Linux
top -p $(pgrep -f skycamos)
htop

# Windows
# Task Manager > Details
```

**Solucoes:**

1. **Reduzir numero de cameras processadas simultaneamente**
   ```yaml
   streaming:
     max_concurrent_transcodes: 4  # Limitar
   ```

2. **Usar substream para deteccao de movimento**
   - Processar stream de menor resolucao para analise
   - Gravar stream de alta resolucao

3. **Habilitar aceleracao por hardware**
   ```yaml
   streaming:
     transcoding:
       hardware_acceleration:
         enabled: true
         type: "nvenc"  # NVIDIA
   ```

4. **Usar copy em vez de transcoding**
   - Se cameras ja entregam H.264, nao reconverter
   ```bash
   ffmpeg -i input -c:v copy -c:a copy output.mp4
   ```

---

### Alto uso de memoria

**Solucoes:**

1. **Limitar workers**
   ```yaml
   server:
     workers: 2  # Reduzir
   ```

2. **Reduzir buffer de frames**
   ```yaml
   motion_detection:
     buffer_frames: 5  # Reduzir de 10
   ```

3. **Reiniciar periodicamente (paliativo)**
   ```bash
   # Crontab - reiniciar todo dia as 4h
   0 4 * * * systemctl restart skycamos
   ```

---

## Problemas de PWA

### PWA nao oferece instalacao

**Requisitos para instalacao:**

1. HTTPS obrigatorio (ou localhost)
2. manifest.json valido
3. Service Worker registrado
4. Icones configurados

**Verificar:**

```javascript
// Console do navegador
// Chrome: Application > Manifest
// Deve mostrar "Installability" sem erros
```

---

### Notificacoes push nao funcionam

**Solucoes:**

1. **Verificar permissao do navegador**
   - Configuracoes > Notificacoes > Permitir

2. **Verificar chaves VAPID**
   ```bash
   # Gerar novas chaves
   npx web-push generate-vapid-keys
   ```

   ```yaml
   # config.yaml
   notifications:
     push:
       vapid:
         public_key: "nova-chave-publica"
         private_key: "nova-chave-privada"
   ```

3. **Service Worker desatualizado**
   - Limpar cache do navegador
   - Forcar atualizacao: Shift + F5

---

## Problemas de Rede

### Cameras em VLAN/subnet diferente

**Solucao:**

```bash
# Adicionar rota estatica
# Linux
sudo ip route add 192.168.2.0/24 via 192.168.1.1

# Windows
route add 192.168.2.0 mask 255.255.255.0 192.168.1.1
```

Ou configurar roteador para permitir comunicacao entre VLANs.

---

### Acesso externo nao funciona

**Checklist:**

1. **Port forwarding no roteador**
   - Redirecionar porta 8000 (ou 443) para IP do servidor

2. **Firewall liberado**
   ```bash
   # Linux
   sudo ufw allow 8000/tcp

   # Windows
   # Firewall > Regras de Entrada > Nova Regra
   ```

3. **IP publico/DDNS configurado**
   - Use servico como No-IP ou DynDNS

---

## Logs e Diagnostico

### Habilitar logs detalhados

```yaml
# config.yaml
logging:
  level: "debug"

server:
  debug: true
```

### Localizacao dos logs

| Arquivo | Conteudo |
|---------|----------|
| `logs/skycamos.log` | Log principal da aplicacao |
| `logs/access.log` | Requisicoes HTTP |
| `logs/ffmpeg/` | Logs de transcoding por camera |

### Comandos uteis de diagnostico

```bash
# Ver ultimas linhas do log
tail -f logs/skycamos.log

# Filtrar erros
grep -i error logs/skycamos.log

# Ver status do sistema
curl http://localhost:8000/api/v1/health

# Testar camera especifica
py scripts/test_camera.py --id 1

# Verificar processos FFmpeg
ps aux | grep ffmpeg

# Verificar portas em uso
# Linux
netstat -tlnp | grep 8000
# Windows
netstat -an | findstr 8000
```

---

## FAQ

### Quantas cameras posso usar?

O limite padrao e 10 cameras. Este limite pode ser ajustado, mas depende do hardware:

| CPUs | RAM | Cameras (1080p) |
|------|-----|-----------------|
| 2 | 4 GB | 2-4 |
| 4 | 8 GB | 4-6 |
| 8 | 16 GB | 8-10 |

### O sistema funciona com cameras Wi-Fi?

Sim, desde que a camera esteja na mesma rede e suporte RTSP ou ONVIF.

### Posso acessar de fora da minha rede?

Sim, configurando:
1. Port forwarding no roteador
2. DDNS se nao tiver IP fixo
3. SSL/HTTPS para seguranca

### As gravacoes sao criptografadas?

Por padrao, nao. Se necessario, configure o disco com criptografia (LUKS no Linux, BitLocker no Windows).

### Posso integrar com assistentes de voz?

Planejado para versoes futuras. Por enquanto, use a API para integracoes customizadas.

### O sistema funciona offline?

Sim, o servidor funciona localmente. O PWA tambem tem modo offline para a interface, mas precisa de conexao para ver cameras.

---

## Ainda com problemas?

1. Consulte as [Issues do GitHub](https://github.com/seu-usuario/skycamos/issues)
2. Abra uma nova issue com:
   - Descricao detalhada do problema
   - Logs relevantes
   - Configuracao do sistema
   - Passos para reproduzir
