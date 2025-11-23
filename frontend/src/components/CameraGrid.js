/**
 * SkyCamOS - Componente CameraGrid
 * Grade de mosaico para exibicao de cameras
 */

import { useCamera } from '../hooks/useCamera.js';
import { MOSAIC_LAYOUTS, STORAGE_KEYS } from '../utils/constants.js';
import { storageService } from '../services/storage.js';
import './CameraCard.js';

/**
 * Web Component do CameraGrid
 */
class SkycamCameraGrid extends HTMLElement {
    constructor() {
        super();
        this.cameraManager = useCamera();
        this.layout = '2x2';
        this.selectedCameras = [];
        this.unsubscribe = null;
    }

    /**
     * Atributos observados
     */
    static get observedAttributes() {
        return ['layout'];
    }

    /**
     * Atributo alterado
     */
    attributeChangedCallback(name, oldValue, newValue) {
        if (name === 'layout' && oldValue !== newValue) {
            this.layout = newValue;
            this.render();
        }
    }

    /**
     * Conectado ao DOM
     */
    async connectedCallback() {
        // Carregar layout salvo
        const savedLayout = await storageService.get(STORAGE_KEYS.MOSAIC_LAYOUT);
        if (savedLayout) {
            this.layout = savedLayout;
        }

        // Carregar cameras selecionadas
        const savedCameras = await storageService.get(STORAGE_KEYS.SELECTED_CAMERAS);
        if (savedCameras) {
            this.selectedCameras = savedCameras;
        }

        // Carregar cameras
        await this.cameraManager.loadCameras();

        // Subscrever para atualizacoes
        this.unsubscribe = this.cameraManager.subscribe((state) => {
            this.updateCameras(state.cameras);
        });

        this.render();
        this.attachEventListeners();
    }

    /**
     * Desconectado do DOM
     */
    disconnectedCallback() {
        if (this.unsubscribe) {
            this.unsubscribe();
        }
    }

    /**
     * Renderizar componente
     */
    render() {
        const layoutConfig = MOSAIC_LAYOUTS[this.layout] || MOSAIC_LAYOUTS['2x2'];
        const cameras = this.getCamerasToDisplay();

        this.innerHTML = `
            <div class="camera-grid-wrapper">
                <div class="camera-grid-header">
                    <h2 class="camera-grid-title">Cameras ao Vivo</h2>
                    <div class="camera-grid-controls">
                        <skycam-mosaic-selector layout="${this.layout}"></skycam-mosaic-selector>
                        <button class="btn btn-secondary btn-sm" id="refresh-cameras">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M23 4v6h-6M1 20v-6h6"/>
                                <path d="M3.51 9a9 9 0 0114.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0020.49 15"/>
                            </svg>
                            Atualizar
                        </button>
                    </div>
                </div>

                <div class="camera-grid grid-${this.layout}" id="camera-grid">
                    ${cameras.length > 0 ?
                        cameras.map((camera, index) => `
                            <skycam-camera-card
                                camera-id="${camera.id}"
                                camera-name="${camera.name}"
                                camera-status="${camera.status}"
                                camera-stream="${camera.stream_url || camera.streamUrl || ''}"
                                data-index="${index}">
                            </skycam-camera-card>
                        `).join('') :
                        this.renderEmptyState()
                    }
                </div>

                ${cameras.length === 0 || cameras.length < layoutConfig.max ? `
                    <div class="camera-grid-add" id="add-camera-slot">
                        <button class="btn btn-primary camera-discover-btn" id="discover-cameras-btn">
                            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <circle cx="11" cy="11" r="8"/>
                                <path d="M21 21l-4.35-4.35"/>
                                <path d="M11 8v6M8 11h6"/>
                            </svg>
                            <span>Descobrir Cameras na Rede</span>
                        </button>
                        <button class="btn btn-ghost camera-add-btn">
                            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <circle cx="12" cy="12" r="10"/>
                                <path d="M12 8v8M8 12h8"/>
                            </svg>
                            <span>Adicionar Manualmente</span>
                        </button>
                    </div>
                ` : ''}
            </div>
        `;

        this.addStyles();
    }

    /**
     * Renderizar estado vazio
     * @returns {string}
     */
    renderEmptyState() {
        return `
            <div class="camera-grid-empty">
                <div class="empty-state">
                    <svg class="empty-state-icon" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                        <rect x="2" y="6" width="14" height="12" rx="2" ry="2"/>
                        <path d="M22 8l-4 4 4 4V8z"/>
                    </svg>
                    <h3 class="empty-state-title">Nenhuma camera configurada</h3>
                    <p class="empty-state-description">Adicione cameras para comecar o monitoramento</p>
                    <button class="btn btn-primary" id="add-first-camera">
                        Adicionar Camera
                    </button>
                </div>
            </div>
        `;
    }

    /**
     * Adicionar estilos especificos
     */
    addStyles() {
        if (document.getElementById('camera-grid-styles')) return;

        const styles = document.createElement('style');
        styles.id = 'camera-grid-styles';
        styles.textContent = `
            .camera-grid-wrapper {
                display: flex;
                flex-direction: column;
                height: 100%;
            }

            .camera-grid-header {
                display: flex;
                align-items: center;
                justify-content: space-between;
                margin-bottom: var(--spacing-md);
            }

            .camera-grid-title {
                font-size: var(--font-size-xl);
                font-weight: var(--font-weight-semibold);
            }

            .camera-grid-controls {
                display: flex;
                align-items: center;
                gap: var(--spacing-md);
            }

            .camera-grid {
                flex: 1;
                display: grid;
                gap: var(--spacing-md);
                min-height: 400px;
            }

            .camera-grid.grid-1x1 {
                grid-template-columns: 1fr;
                grid-template-rows: 1fr;
            }

            .camera-grid.grid-2x2 {
                grid-template-columns: repeat(2, 1fr);
                grid-template-rows: repeat(2, 1fr);
            }

            .camera-grid.grid-3x3 {
                grid-template-columns: repeat(3, 1fr);
                grid-template-rows: repeat(3, 1fr);
            }

            .camera-grid.grid-4x4 {
                grid-template-columns: repeat(4, 1fr);
                grid-template-rows: repeat(4, 1fr);
            }

            .camera-grid-empty {
                grid-column: 1 / -1;
                grid-row: 1 / -1;
            }

            .camera-grid-add {
                margin-top: var(--spacing-md);
                text-align: center;
                display: flex;
                justify-content: center;
                gap: var(--spacing-md);
                flex-wrap: wrap;
            }

            .camera-add-btn,
            .camera-discover-btn {
                padding: var(--spacing-md) var(--spacing-lg);
                display: inline-flex;
                align-items: center;
            }

            .camera-add-btn span,
            .camera-discover-btn span {
                margin-left: var(--spacing-sm);
            }

            .camera-discover-btn {
                background: linear-gradient(135deg, var(--primary-color) 0%, #3b7ddd 100%);
            }

            @media (max-width: 1024px) {
                .camera-grid.grid-3x3,
                .camera-grid.grid-4x4 {
                    grid-template-columns: repeat(2, 1fr);
                }
            }

            @media (max-width: 768px) {
                .camera-grid-header {
                    flex-direction: column;
                    align-items: flex-start;
                    gap: var(--spacing-sm);
                }

                .camera-grid {
                    min-height: 200px;
                }

                .camera-grid.grid-2x2,
                .camera-grid.grid-3x3,
                .camera-grid.grid-4x4 {
                    grid-template-columns: 1fr;
                    grid-template-rows: auto;
                }
            }
        `;

        document.head.appendChild(styles);
    }

    /**
     * Anexar event listeners
     */
    attachEventListeners() {
        // Refresh cameras
        this.querySelector('#refresh-cameras')?.addEventListener('click', async () => {
            await this.cameraManager.loadCameras(true);
        });

        // Add camera
        this.querySelector('#add-first-camera')?.addEventListener('click', () => {
            this.showAddCameraModal();
        });

        this.querySelector('.camera-add-btn')?.addEventListener('click', () => {
            this.showAddCameraModal();
        });

        // Discover cameras
        this.querySelector('#discover-cameras-btn')?.addEventListener('click', () => {
            this.showDiscoverCamerasModal();
        });

        // Ouvir mudanca de layout
        this.addEventListener('layout-change', (e) => {
            this.setLayout(e.detail.layout);
        });

        // Ouvir selecao de camera
        this.addEventListener('camera-select', (e) => {
            this.handleCameraSelect(e.detail);
        });

        // Ouvir fullscreen de camera
        this.addEventListener('camera-fullscreen', (e) => {
            this.handleCameraFullscreen(e.detail.cameraId);
        });
    }

    /**
     * Obter cameras a exibir
     * @returns {Array}
     */
    getCamerasToDisplay() {
        const state = this.cameraManager.getState();
        const cameras = state.cameras || [];
        const layoutConfig = MOSAIC_LAYOUTS[this.layout];

        // Se tiver cameras selecionadas, usar elas
        if (this.selectedCameras.length > 0) {
            return this.selectedCameras
                .map(id => cameras.find(c => c.id === id))
                .filter(Boolean)
                .slice(0, layoutConfig.max);
        }

        // Senao, usar as primeiras cameras disponiveis
        return cameras.slice(0, layoutConfig.max);
    }

    /**
     * Definir layout do grid
     * @param {string} layout - Nome do layout
     */
    async setLayout(layout) {
        if (MOSAIC_LAYOUTS[layout]) {
            this.layout = layout;
            await storageService.set(STORAGE_KEYS.MOSAIC_LAYOUT, layout);
            this.render();
            this.attachEventListeners();
        }
    }

    /**
     * Atualizar cameras exibidas
     * @param {Array} cameras - Lista de cameras
     */
    updateCameras(cameras) {
        // Atualizar cards individuais
        cameras.forEach(camera => {
            const card = this.querySelector(`skycam-camera-card[camera-id="${camera.id}"]`);
            if (card) {
                card.setAttribute('camera-status', camera.status);
            }
        });
    }

    /**
     * Handler para selecao de camera
     * @param {Object} detail - Detalhes do evento
     */
    handleCameraSelect(detail) {
        const { cameraId, selected } = detail;

        if (selected) {
            if (!this.selectedCameras.includes(cameraId)) {
                this.selectedCameras.push(cameraId);
            }
        } else {
            this.selectedCameras = this.selectedCameras.filter(id => id !== cameraId);
        }

        storageService.set(STORAGE_KEYS.SELECTED_CAMERAS, this.selectedCameras);
    }

    /**
     * Handler para fullscreen de camera
     * @param {string} cameraId - ID da camera
     */
    handleCameraFullscreen(cameraId) {
        // Alternar para layout 1x1 com essa camera
        this.selectedCameras = [cameraId];
        this.setLayout('1x1');
    }

    /**
     * Mostrar modal de adicionar camera
     */
    showAddCameraModal() {
        document.dispatchEvent(new CustomEvent('show-add-camera-modal'));
    }

    /**
     * Mostrar modal de descoberta de cameras
     */
    showDiscoverCamerasModal() {
        document.dispatchEvent(new CustomEvent('show-discover-cameras-modal'));
    }
}

// Registrar Web Component
customElements.define('skycam-camera-grid', SkycamCameraGrid);

export default SkycamCameraGrid;
