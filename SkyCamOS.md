
**Quero que você atue como um arquiteto de software e me ajude a criar um aplicativo simples de monitoramento de câmeras IP, semelhante ao Digiforte ou Luxriot EVO, porém mais básico. Meu objetivo é criar uma solução que rode no meu computador e também tenha uma interface web para acesso remoto. Não quero código agora — apenas explicações, arquitetura, fluxos, tecnologias, módulos necessários, melhorias e boas práticas.**

---

# **OBJETIVO DO PROJETO**

Criar um sistema de monitoramento **desktop + web PWA**, que oferece:

1. Descoberta automática de câmeras IP via ONVIF/SSDP.
2. Suporte para até **10 câmeras**.
3. Visualização com mozaicos (1, 2, 4, 9 câmeras).
4. Gravação local com sobrescrita automática.
5. Interface web acessível de qualquer lugar.
6. A versão web precisa ser **PWA**:

   * Instalar no celular
   * Receber notificações (se possível)
   * Abrir como app nativo
   * Tela cheia
   * Cache inteligente para carregamento rápido
7. Visualizar ao vivo, ver gravações e rever gravações.
8. Detecção de movimento nas câmeras e alertas.

---

# **FUNCIONALIDADES DO PWA**

Peço que descreva exatamente:

### **1. Instalação como app (PWA completo)**

* Manifest.json configurado
* Service Worker
* Ícone e splashscreen
* Instalável no Android, iOS e Desktop

### **2. Modo offline básico**

Mesmo sem internet:

* Carregar interface
* Carregar configurações salvas
* Mostrar aviso “sem conexão”
* Permitir ver gravações **locais** se estiver na mesma rede

### **3. Acesso remoto**

Quando logado externamente:

* Ver câmeras ao vivo
* Listar gravações
* Reproduzir gravações

### **4. Notificações Push (se possível)**

Descrever como implementar:

* Detecção de movimento aciona backend
* Backend envia push para PWA
* PWA recebe alerta
* Usuário toca e abre timeline da câmera

### **5. Player otimizado**

* HLS ou WebRTC
* PWA deve suportar:

  * Minimizar vídeo
  * Tela cheia
  * Modo mosaico

### **6. Performance**

PWA precisa ser leve, rápido e responsivo.

---

# **DETALHAR A DETECÇÃO DE MOVIMENTO**

Quero que você explique:

### **Opção 1 — Detecção por software (backend)**

* Algoritmo simples de “diferença entre frames”
* ROI (região de interesse opcional)
* Sensibilidade ajustável
* Gatilho salva timestamp e envia notificação

### **Opção 2 — Detecção nativa da câmera (ONVIF Event)**

* Muitas câmeras Intelbras, Hikvision e Dahua suportam
* Backend recebe evento ONVIF
* Marca gravação com flag “Motion”
* Envia push pro PWA

### **O que fazer quando há movimento**

* Gravar clipe de 10–30 segundos
* Registrar evento no banco
* Notificar usuários cadastrados

---

# **MODOS DE VISUALIZAÇÃO DO PWA**

Detalhar no documento:

* Mosaico 1x1
* Mosaico 2x2
* Mosaico 3x3
* Alternância automática (modo ronda)
* Recurso de zoom independente

---

# **FLUXOS DO SISTEMA**

Quero fluxos detalhados para:

### **1. Fluxo de instalação do PWA**

1. Usuário abre o site
2. Service Worker carrega
3. Browser oferece instalar
4. Ícone aparece no celular
5. App abre em tela cheia

### **2. Fluxo do movimento**

1. Backend detecta movimento
2. Marca gravação
3. Gera clipe
4. Notifica usuário
5. PWA abre visão do evento

### **3. Fluxo para ver gravações no PWA**

1. Seleciona câmera
2. Escolhe data
3. Lista gravações
4. Reproduzir em HLS harmonizado

### **4. Fluxo de acesso remoto**

1. Login via web
2. Backend valida
3. Mostra câmeras em tempo real
4. Permite rever gravações

---

# **MÓDULOS DO PROJETO**

Quero descrição detalhada dos módulos:

### **1. Desktop Manager**

* Encontrar câmeras
* Configurar gravações
* Configurar disco(s)
* Gerenciar PWA e API

### **2. Backend/API**

* REST API
* Websockets para câmeras ao vivo
* Serviço de gravação
* Serviço de sobrescrita FIFO
* Serviço de detecção de movimento
* Serviço de notificações push
* Conversão RTSP → WebRTC/HLS

### **3. Web/PWA**

* Painel de câmeras
* Timeline de gravação
* Reprodução de eventos de movimento
* Tela cheia
* Mosaicos
* PWA offline
* Notificações

### **4. Banco de dados SQLite**

* Cameras
* Configurações
* Eventos de movimento
* Gravações
* Usuários

---

# **MELHORIAS SUGERIDAS**

Peço para incluir:

* WebRTC para reduzir latência ao vivo
* Suporte a RTMP opcional
* Backup automático das gravações
* Modo Cloud (futuro)
* Inteligência artificial para detectar pessoas
* Detector de intrusão (line crossing)
* Compartilhamento de câmera por link temporário

---

# **ENTREGÁVEL**

Quero que você retorne:

* Documento completo e organizado
* Arquitetura detalhada
* Diagrama textual dos fluxos
* Descrição de todos os módulos
* Estratégias para detectar movimento
* Plano do PWA
* Lista de tecnologias recomendadas
* Estrutura dos arquivos
