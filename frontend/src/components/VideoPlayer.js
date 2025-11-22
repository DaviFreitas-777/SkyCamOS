/**
 * SkyCamOS - Componente VideoPlayer
 * Player de video com suporte a HLS e WebRTC
 */

import { VIDEO_CONFIG } from '../utils/constants.js';

/**
 * Web Component do VideoPlayer
 */
class SkycamVideoPlayer extends HTMLElement {
    constructor() {
        super();
        this.src = '';
        this.cameraId = '';
        this.autoplay = false;
        this.muted = true;
        this.isPlaying = false;
        this.isLoading = false;
        this.hasError = false;
        this.hls = null;
        this.peerConnection = null;
        this.retryCount = 0;
        this.maxRetries = 3;
    }

    /**
     * Atributos observados
     */
    static get observedAttributes() {
        return ['src', 'camera-id', 'autoplay', 'muted'];
    }

    /**
     * Atributo alterado
     */
    attributeChangedCallback(name, oldValue, newValue) {
        if (oldValue === newValue) return;

        switch (name) {
            case 'src':
                this.src = newValue;
                if (this.isConnected) {
                    this.loadVideo();
                }
                break;
            case 'camera-id':
                this.cameraId = newValue;
                break;
            case 'autoplay':
                this.autoplay = newValue !== null;
                break;
            case 'muted':
                this.muted = newValue !== null;
                break;
        }
    }

    /**
     * Conectado ao DOM
     */
    connectedCallback() {
        this.render();
        this.attachEventListeners();

        if (this.src && this.autoplay) {
            this.loadVideo();
        }
    }

    /**
     * Desconectado do DOM
     */
    disconnectedCallback() {
        this.cleanup();
    }

    /**
     * Renderizar componente
     */
    render() {
        this.innerHTML = `
            <div class="video-player-wrapper">
                <video class="video-player"
                       playsinline
                       ${this.muted ? 'muted' : ''}
                       ${this.autoplay ? 'autoplay' : ''}>
                </video>

                <div class="video-loading ${this.isLoading ? 'active' : ''}">
                    <div class="loading-spinner"></div>
                </div>

                <div class="video-error ${this.hasError ? 'active' : ''}">
                    <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="12" cy="12" r="10"/>
                        <path d="M15 9l-6 6M9 9l6 6"/>
                    </svg>
                    <span>Erro ao carregar video</span>
                    <button class="btn btn-sm btn-secondary" id="retry-btn">Tentar novamente</button>
                </div>

                <div class="video-controls">
                    <button class="btn btn-icon-sm btn-ghost video-btn-play" id="play-btn">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                            ${this.isPlaying ?
                                '<rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/>' :
                                '<polygon points="5 3 19 12 5 21 5 3"/>'
                            }
                        </svg>
                    </button>

                    <button class="btn btn-icon-sm btn-ghost video-btn-mute" id="mute-btn">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            ${this.muted ?
                                '<path d="M11 5L6 9H2v6h4l5 4V5zM23 9l-6 6M17 9l6 6"/>' :
                                '<path d="M11 5L6 9H2v6h4l5 4V5zM19.07 4.93a10 10 0 010 14.14M15.54 8.46a5 5 0 010 7.07"/>'
                            }
                        </svg>
                    </button>

                    <div class="video-quality-selector">
                        <select class="input" id="quality-select">
                            ${VIDEO_CONFIG.QUALITIES.map(q =>
                                `<option value="${q.id}">${q.label}</option>`
                            ).join('')}
                        </select>
                    </div>

                    <button class="btn btn-icon-sm btn-ghost video-btn-fullscreen" id="fullscreen-btn">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M8 3H5a2 2 0 00-2 2v3m18 0V5a2 2 0 00-2-2h-3m0 18h3a2 2 0 002-2v-3M3 16v3a2 2 0 002 2h3"/>
                        </svg>
                    </button>
                </div>
            </div>
        `;

        this.addStyles();
    }

    /**
     * Adicionar estilos especificos
     */
    addStyles() {
        if (document.getElementById('video-player-styles')) return;

        const styles = document.createElement('style');
        styles.id = 'video-player-styles';
        styles.textContent = `
            skycam-video-player {
                display: block;
                width: 100%;
                height: 100%;
            }

            .video-player-wrapper {
                position: relative;
                width: 100%;
                height: 100%;
                background-color: var(--color-bg-tertiary);
                overflow: hidden;
            }

            .video-player {
                width: 100%;
                height: 100%;
                object-fit: cover;
            }

            .video-loading,
            .video-error {
                position: absolute;
                inset: 0;
                display: none;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                gap: var(--spacing-sm);
                background-color: rgba(0, 0, 0, 0.7);
                color: var(--color-text-secondary);
                z-index: 5;
            }

            .video-loading.active,
            .video-error.active {
                display: flex;
            }

            .video-controls {
                position: absolute;
                bottom: 0;
                left: 0;
                right: 0;
                display: flex;
                align-items: center;
                gap: var(--spacing-sm);
                padding: var(--spacing-sm);
                background: linear-gradient(to top, rgba(0, 0, 0, 0.8), transparent);
                opacity: 0;
                transition: opacity var(--transition-fast);
            }

            .video-player-wrapper:hover .video-controls {
                opacity: 1;
            }

            .video-quality-selector {
                margin-left: auto;
            }

            .video-quality-selector select {
                padding: var(--spacing-xs) var(--spacing-sm);
                font-size: var(--font-size-xs);
                background-color: rgba(0, 0, 0, 0.5);
                border-color: transparent;
            }
        `;

        document.head.appendChild(styles);
    }

    /**
     * Anexar event listeners
     */
    attachEventListeners() {
        const video = this.querySelector('.video-player');
        const playBtn = this.querySelector('#play-btn');
        const muteBtn = this.querySelector('#mute-btn');
        const fullscreenBtn = this.querySelector('#fullscreen-btn');
        const retryBtn = this.querySelector('#retry-btn');
        const qualitySelect = this.querySelector('#quality-select');

        // Video events
        video?.addEventListener('play', () => {
            this.isPlaying = true;
            this.updatePlayButton();
        });

        video?.addEventListener('pause', () => {
            this.isPlaying = false;
            this.updatePlayButton();
        });

        video?.addEventListener('waiting', () => {
            this.showLoading();
        });

        video?.addEventListener('playing', () => {
            this.hideLoading();
            this.hideError();
        });

        video?.addEventListener('error', (e) => {
            console.error('[VideoPlayer] Erro:', e);
            this.handleError();
        });

        // Control buttons
        playBtn?.addEventListener('click', () => this.togglePlay());
        muteBtn?.addEventListener('click', () => this.toggleMute());
        fullscreenBtn?.addEventListener('click', () => this.toggleFullscreen());
        retryBtn?.addEventListener('click', () => this.retry());

        // Quality change
        qualitySelect?.addEventListener('change', (e) => {
            this.changeQuality(e.target.value);
        });

        // Double click para fullscreen
        this.addEventListener('dblclick', () => this.toggleFullscreen());
    }

    /**
     * Carregar video
     */
    async loadVideo() {
        if (!this.src) return;

        this.showLoading();
        this.hideError();

        try {
            // Detectar tipo de stream
            if (this.src.includes('.m3u8')) {
                await this.loadHLS();
            } else if (this.src.includes('webrtc')) {
                await this.loadWebRTC();
            } else {
                await this.loadNative();
            }
        } catch (error) {
            console.error('[VideoPlayer] Erro ao carregar video:', error);
            this.handleError();
        }
    }

    /**
     * Carregar video HLS
     */
    async loadHLS() {
        const video = this.querySelector('.video-player');
        if (!video) return;

        // Verificar suporte nativo a HLS (Safari)
        if (video.canPlayType('application/vnd.apple.mpegurl')) {
            video.src = this.src;
            await video.play();
            return;
        }

        // Usar hls.js para outros navegadores
        if (typeof Hls !== 'undefined' && Hls.isSupported()) {
            this.cleanup();

            this.hls = new Hls({
                enableWorker: true,
                lowLatencyMode: true,
                backBufferLength: 90
            });

            this.hls.loadSource(this.src);
            this.hls.attachMedia(video);

            this.hls.on(Hls.Events.MANIFEST_PARSED, () => {
                video.play();
            });

            this.hls.on(Hls.Events.ERROR, (event, data) => {
                if (data.fatal) {
                    console.error('[VideoPlayer] HLS fatal error:', data);
                    this.handleError();
                }
            });
        } else {
            console.error('[VideoPlayer] HLS nao suportado');
            this.handleError();
        }
    }

    /**
     * Carregar video WebRTC
     */
    async loadWebRTC() {
        const video = this.querySelector('.video-player');
        if (!video) return;

        try {
            this.cleanup();

            // Criar peer connection
            this.peerConnection = new RTCPeerConnection({
                iceServers: [{ urls: 'stun:stun.l.google.com:19302' }]
            });

            this.peerConnection.ontrack = (event) => {
                video.srcObject = event.streams[0];
                video.play();
            };

            this.peerConnection.oniceconnectionstatechange = () => {
                if (this.peerConnection.iceConnectionState === 'failed') {
                    this.handleError();
                }
            };

            // Obter offer do servidor
            const response = await fetch(this.src, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });

            const offer = await response.json();

            await this.peerConnection.setRemoteDescription(new RTCSessionDescription(offer));

            const answer = await this.peerConnection.createAnswer();
            await this.peerConnection.setLocalDescription(answer);

            // Enviar answer para o servidor
            await fetch(this.src, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(answer)
            });

        } catch (error) {
            console.error('[VideoPlayer] Erro WebRTC:', error);
            this.handleError();
        }
    }

    /**
     * Carregar video nativo (MJPEG, etc)
     */
    async loadNative() {
        const video = this.querySelector('.video-player');
        if (!video) return;

        video.src = this.src;
        await video.play();
    }

    /**
     * Toggle play/pause
     */
    togglePlay() {
        const video = this.querySelector('.video-player');
        if (!video) return;

        if (video.paused) {
            video.play();
        } else {
            video.pause();
        }
    }

    /**
     * Toggle mute
     */
    toggleMute() {
        const video = this.querySelector('.video-player');
        if (!video) return;

        video.muted = !video.muted;
        this.muted = video.muted;
        this.updateMuteButton();
    }

    /**
     * Toggle fullscreen
     */
    toggleFullscreen() {
        const wrapper = this.querySelector('.video-player-wrapper');
        if (!wrapper) return;

        if (!document.fullscreenElement) {
            wrapper.requestFullscreen();
        } else {
            document.exitFullscreen();
        }
    }

    /**
     * Mudar qualidade
     * @param {string} quality - ID da qualidade
     */
    changeQuality(quality) {
        if (this.hls && this.hls.levels) {
            if (quality === 'auto') {
                this.hls.currentLevel = -1;
            } else {
                const level = this.hls.levels.findIndex(l =>
                    l.height >= parseInt(quality)
                );
                if (level >= 0) {
                    this.hls.currentLevel = level;
                }
            }
        }
    }

    /**
     * Capturar snapshot
     */
    captureSnapshot() {
        const video = this.querySelector('.video-player');
        if (!video) return;

        const canvas = document.createElement('canvas');
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;

        const ctx = canvas.getContext('2d');
        ctx.drawImage(video, 0, 0);

        // Download da imagem
        const link = document.createElement('a');
        link.download = `snapshot_${this.cameraId}_${Date.now()}.png`;
        link.href = canvas.toDataURL('image/png');
        link.click();
    }

    /**
     * Retry ao carregar video
     */
    retry() {
        this.retryCount++;
        if (this.retryCount <= this.maxRetries) {
            this.loadVideo();
        }
    }

    /**
     * Handler de erro
     */
    handleError() {
        this.hideLoading();
        this.showError();

        // Auto retry
        if (this.retryCount < this.maxRetries) {
            setTimeout(() => {
                this.retryCount++;
                this.loadVideo();
            }, 3000);
        }
    }

    /**
     * Mostrar loading
     */
    showLoading() {
        this.isLoading = true;
        this.querySelector('.video-loading')?.classList.add('active');
    }

    /**
     * Esconder loading
     */
    hideLoading() {
        this.isLoading = false;
        this.querySelector('.video-loading')?.classList.remove('active');
    }

    /**
     * Mostrar erro
     */
    showError() {
        this.hasError = true;
        this.querySelector('.video-error')?.classList.add('active');
    }

    /**
     * Esconder erro
     */
    hideError() {
        this.hasError = false;
        this.retryCount = 0;
        this.querySelector('.video-error')?.classList.remove('active');
    }

    /**
     * Atualizar botao de play
     */
    updatePlayButton() {
        const playBtn = this.querySelector('#play-btn svg');
        if (playBtn) {
            playBtn.innerHTML = this.isPlaying ?
                '<rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/>' :
                '<polygon points="5 3 19 12 5 21 5 3"/>';
        }
    }

    /**
     * Atualizar botao de mute
     */
    updateMuteButton() {
        const muteBtn = this.querySelector('#mute-btn svg');
        if (muteBtn) {
            muteBtn.innerHTML = this.muted ?
                '<path d="M11 5L6 9H2v6h4l5 4V5zM23 9l-6 6M17 9l6 6"/>' :
                '<path d="M11 5L6 9H2v6h4l5 4V5zM19.07 4.93a10 10 0 010 14.14M15.54 8.46a5 5 0 010 7.07"/>';
        }
    }

    /**
     * Limpar recursos
     */
    cleanup() {
        if (this.hls) {
            this.hls.destroy();
            this.hls = null;
        }

        if (this.peerConnection) {
            this.peerConnection.close();
            this.peerConnection = null;
        }

        const video = this.querySelector('.video-player');
        if (video) {
            video.srcObject = null;
            video.src = '';
        }
    }
}

// Registrar Web Component
customElements.define('skycam-video-player', SkycamVideoPlayer);

export default SkycamVideoPlayer;
