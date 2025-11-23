/**
 * SkyCamOS - Componente CameraCard
 * Card individual de camera com video player
 */

import { CAMERA_STATUS, CAMERA_STATUS_LABELS } from '../utils/constants.js';
import { formatRelativeTime } from '../utils/dateFormatter.js';
import './VideoPlayer.js';

/**
 * Web Component do CameraCard
 */
class SkycamCameraCard extends HTMLElement {
    constructor() {
        super();
        this.cameraId = '';
        this.cameraName = '';
        this.cameraStatus = CAMERA_STATUS.OFFLINE;
        this.streamUrl = '';
        this.isFullscreen = false;
        this.isRecording = false;
    }

    /**
     * Atributos observados
     */
    static get observedAttributes() {
        return ['camera-id', 'camera-name', 'camera-status', 'camera-stream'];
    }

    /**
     * Atributo alterado
     */
    attributeChangedCallback(name, oldValue, newValue) {
        if (oldValue === newValue) return;

        switch (name) {
            case 'camera-id':
                this.cameraId = newValue;
                break;
            case 'camera-name':
                this.cameraName = newValue;
                break;
            case 'camera-status':
                this.cameraStatus = newValue;
                this.updateStatus();
                break;
            case 'camera-stream':
                this.streamUrl = newValue;
                break;
        }
    }

    /**
     * Conectado ao DOM
     */
    connectedCallback() {
        this.render();
        this.attachEventListeners();
    }

    /**
     * Renderizar componente
     */
    render() {
        const statusClass = this.getStatusClass();
        const statusLabel = CAMERA_STATUS_LABELS[this.cameraStatus] || 'Desconhecido';

        this.innerHTML = `
            <div class="camera-card" data-camera-id="${this.cameraId}">
                <div class="camera-card-header">
                    <div class="camera-card-title">
                        <span class="status-dot ${statusClass}"></span>
                        <span class="camera-name">${this.cameraName || 'Camera'}</span>
                    </div>
                    <div class="camera-card-actions">
                        ${this.cameraStatus === CAMERA_STATUS.RECORDING ? `
                            <span class="badge badge-error">
                                <span class="status-dot recording"></span>
                                REC
                            </span>
                        ` : ''}
                        <div class="dropdown camera-menu">
                            <button class="btn btn-icon-sm btn-ghost camera-menu-btn" aria-label="Menu">
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <circle cx="12" cy="12" r="1"/>
                                    <circle cx="12" cy="5" r="1"/>
                                    <circle cx="12" cy="19" r="1"/>
                                </svg>
                            </button>
                            <div class="dropdown-menu">
                                <button class="dropdown-item" data-action="fullscreen">
                                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                        <path d="M8 3H5a2 2 0 00-2 2v3m18 0V5a2 2 0 00-2-2h-3m0 18h3a2 2 0 002-2v-3M3 16v3a2 2 0 002 2h3"/>
                                    </svg>
                                    Tela Cheia
                                </button>
                                <button class="dropdown-item" data-action="snapshot">
                                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                        <path d="M23 19a2 2 0 01-2 2H3a2 2 0 01-2-2V8a2 2 0 012-2h4l2-3h6l2 3h4a2 2 0 012 2z"/>
                                        <circle cx="12" cy="13" r="4"/>
                                    </svg>
                                    Capturar Imagem
                                </button>
                                <button class="dropdown-item" data-action="settings">
                                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                        <circle cx="12" cy="12" r="3"/>
                                        <path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-2 2 2 2 0 01-2-2v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83 0 2 2 0 010-2.83l.06-.06a1.65 1.65 0 00.33-1.82 1.65 1.65 0 00-1.51-1H3a2 2 0 01-2-2 2 2 0 012-2h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 010-2.83 2 2 0 012.83 0l.06.06a1.65 1.65 0 001.82.33H9a1.65 1.65 0 001-1.51V3a2 2 0 012-2 2 2 0 012 2v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 0 2 2 0 010 2.83l-.06.06a1.65 1.65 0 00-.33 1.82V9a1.65 1.65 0 001.51 1H21a2 2 0 012 2 2 2 0 01-2 2h-.09a1.65 1.65 0 00-1.51 1z"/>
                                    </svg>
                                    Configuracoes
                                </button>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="camera-card-video">
                    ${this.cameraStatus === CAMERA_STATUS.ONLINE || this.cameraStatus === CAMERA_STATUS.RECORDING || this.cameraStatus === CAMERA_STATUS.CONNECTING ?
                        `<skycam-video-player
                            src="${this.streamUrl}"
                            camera-id="${this.cameraId}"
                            autoplay>
                        </skycam-video-player>` :
                        this.renderOfflineState()
                    }
                </div>

                <div class="camera-card-controls">
                    <button class="btn btn-icon-sm btn-ghost" data-action="ptz-left" title="Mover Esquerda">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M15 18l-6-6 6-6"/>
                        </svg>
                    </button>
                    <button class="btn btn-icon-sm btn-ghost" data-action="ptz-up" title="Mover Cima">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M18 15l-6-6-6 6"/>
                        </svg>
                    </button>
                    <button class="btn btn-icon-sm btn-ghost" data-action="ptz-down" title="Mover Baixo">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M6 9l6 6 6-6"/>
                        </svg>
                    </button>
                    <button class="btn btn-icon-sm btn-ghost" data-action="ptz-right" title="Mover Direita">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M9 18l6-6-6-6"/>
                        </svg>
                    </button>
                    <div class="camera-controls-divider"></div>
                    <button class="btn btn-icon-sm btn-ghost" data-action="zoom-in" title="Zoom In">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <circle cx="11" cy="11" r="8"/>
                            <path d="M21 21l-4.35-4.35M11 8v6M8 11h6"/>
                        </svg>
                    </button>
                    <button class="btn btn-icon-sm btn-ghost" data-action="zoom-out" title="Zoom Out">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <circle cx="11" cy="11" r="8"/>
                            <path d="M21 21l-4.35-4.35M8 11h6"/>
                        </svg>
                    </button>
                </div>

                <div class="camera-card-footer">
                    <span class="camera-status-text">${statusLabel}</span>
                    <span class="camera-last-seen" id="last-seen"></span>
                </div>
            </div>
        `;

        this.addStyles();
    }

    /**
     * Renderizar estado offline
     * @returns {string}
     */
    renderOfflineState() {
        return `
            <div class="camera-offline-state">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                    <rect x="2" y="6" width="14" height="12" rx="2" ry="2"/>
                    <path d="M22 8l-4 4 4 4V8z"/>
                    <path d="M2 2l20 20" stroke-linecap="round"/>
                </svg>
                <span>${this.cameraStatus === CAMERA_STATUS.ERROR ? 'Erro de conexao' : 'Camera offline'}</span>
            </div>
        `;
    }

    /**
     * Obter classe de status
     * @returns {string}
     */
    getStatusClass() {
        switch (this.cameraStatus) {
            case CAMERA_STATUS.ONLINE:
                return 'online';
            case CAMERA_STATUS.RECORDING:
                return 'recording';
            case CAMERA_STATUS.ERROR:
                return 'warning';
            case CAMERA_STATUS.CONNECTING:
                return 'warning';
            default:
                return 'offline';
        }
    }

    /**
     * Adicionar estilos especificos
     */
    addStyles() {
        if (document.getElementById('camera-card-styles')) return;

        const styles = document.createElement('style');
        styles.id = 'camera-card-styles';
        styles.textContent = `
            skycam-camera-card {
                display: block;
                height: 100%;
            }

            .camera-card {
                position: relative;
                background-color: var(--color-bg-card);
                border-radius: var(--radius-lg);
                overflow: hidden;
                display: flex;
                flex-direction: column;
                height: 100%;
            }

            .camera-card-header {
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                display: flex;
                align-items: center;
                justify-content: space-between;
                padding: var(--spacing-sm);
                background: linear-gradient(to bottom, rgba(0, 0, 0, 0.7), transparent);
                z-index: 10;
            }

            .camera-card-title {
                display: flex;
                align-items: center;
                gap: var(--spacing-sm);
                font-size: var(--font-size-sm);
                font-weight: var(--font-weight-medium);
            }

            .camera-card-actions {
                display: flex;
                align-items: center;
                gap: var(--spacing-xs);
            }

            .camera-card-video {
                flex: 1;
                background-color: var(--color-bg-tertiary);
                display: flex;
                align-items: center;
                justify-content: center;
                min-height: 150px;
            }

            .camera-card-video skycam-video-player {
                width: 100%;
                height: 100%;
            }

            .camera-offline-state {
                display: flex;
                flex-direction: column;
                align-items: center;
                gap: var(--spacing-sm);
                color: var(--color-text-tertiary);
            }

            .camera-card-controls {
                position: absolute;
                bottom: 40px;
                left: 0;
                right: 0;
                display: flex;
                align-items: center;
                justify-content: center;
                gap: var(--spacing-xs);
                padding: var(--spacing-sm);
                background: linear-gradient(to top, rgba(0, 0, 0, 0.7), transparent);
                opacity: 0;
                transition: opacity var(--transition-fast);
            }

            .camera-card:hover .camera-card-controls {
                opacity: 1;
            }

            .camera-controls-divider {
                width: 1px;
                height: 20px;
                background-color: var(--color-border-primary);
                margin: 0 var(--spacing-xs);
            }

            .camera-card-footer {
                display: flex;
                align-items: center;
                justify-content: space-between;
                padding: var(--spacing-sm);
                background-color: var(--color-bg-card-hover);
                font-size: var(--font-size-xs);
                color: var(--color-text-tertiary);
            }

            .camera-menu .dropdown-menu {
                right: 0;
                left: auto;
            }

            @media (max-width: 768px) {
                .camera-card-controls {
                    opacity: 1;
                }
            }
        `;

        document.head.appendChild(styles);
    }

    /**
     * Anexar event listeners
     */
    attachEventListeners() {
        // Menu dropdown
        const menuBtn = this.querySelector('.camera-menu-btn');
        const menu = this.querySelector('.camera-menu');

        menuBtn?.addEventListener('click', (e) => {
            e.stopPropagation();
            menu?.classList.toggle('active');
        });

        // Menu actions
        this.querySelectorAll('.dropdown-item').forEach(item => {
            item.addEventListener('click', (e) => {
                const action = item.dataset.action;
                this.handleMenuAction(action);
                menu?.classList.remove('active');
            });
        });

        // PTZ controls
        this.querySelectorAll('[data-action^="ptz-"], [data-action^="zoom-"]').forEach(btn => {
            btn.addEventListener('click', () => {
                const action = btn.dataset.action;
                this.handlePTZAction(action);
            });
        });

        // Fechar menu ao clicar fora
        document.addEventListener('click', () => {
            menu?.classList.remove('active');
        });
    }

    /**
     * Handler para acoes do menu
     * @param {string} action - Nome da acao
     */
    handleMenuAction(action) {
        switch (action) {
            case 'fullscreen':
                this.dispatchEvent(new CustomEvent('camera-fullscreen', {
                    detail: { cameraId: this.cameraId },
                    bubbles: true
                }));
                break;
            case 'snapshot':
                this.captureSnapshot();
                break;
            case 'settings':
                window.location.hash = `#/settings/cameras/${this.cameraId}`;
                break;
        }
    }

    /**
     * Handler para controles PTZ
     * @param {string} action - Nome da acao
     */
    handlePTZAction(action) {
        // Disparar evento para o pai tratar
        this.dispatchEvent(new CustomEvent('ptz-control', {
            detail: {
                cameraId: this.cameraId,
                action: action
            },
            bubbles: true
        }));
    }

    /**
     * Capturar snapshot
     */
    async captureSnapshot() {
        const player = this.querySelector('skycam-video-player');
        if (player) {
            player.captureSnapshot();
        }
    }

    /**
     * Atualizar status visual
     */
    updateStatus() {
        const statusDot = this.querySelector('.status-dot');
        const statusText = this.querySelector('.camera-status-text');

        if (statusDot) {
            statusDot.className = `status-dot ${this.getStatusClass()}`;
        }

        if (statusText) {
            statusText.textContent = CAMERA_STATUS_LABELS[this.cameraStatus] || 'Desconhecido';
        }

        // Re-renderizar video se status mudou para online
        if (this.cameraStatus === CAMERA_STATUS.ONLINE || this.cameraStatus === CAMERA_STATUS.RECORDING) {
            const videoContainer = this.querySelector('.camera-card-video');
            if (videoContainer && !videoContainer.querySelector('skycam-video-player')) {
                videoContainer.innerHTML = `
                    <skycam-video-player
                        src="${this.streamUrl}"
                        camera-id="${this.cameraId}"
                        autoplay>
                    </skycam-video-player>
                `;
            }
        }
    }
}

// Registrar Web Component
customElements.define('skycam-camera-card', SkycamCameraCard);

export default SkycamCameraCard;
