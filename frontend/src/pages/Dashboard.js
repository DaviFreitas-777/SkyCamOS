/**
 * SkyCamOS - Pagina Dashboard
 * Pagina principal com grid de cameras
 */

import '../components/CameraGrid.js';
import '../components/EventList.js';
import '../components/MosaicSelector.js';
import { useCamera } from '../hooks/useCamera.js';
import { useWebSocket } from '../hooks/useWebSocket.js';

class DashboardPage extends HTMLElement {
    constructor() {
        super();
        this.cameraManager = useCamera();
        this.wsManager = useWebSocket();
    }

    connectedCallback() {
        this.render();
        this.init();
    }

    async init() {
        // Conectar WebSocket
        await this.wsManager.connect();

        // Carregar cameras
        await this.cameraManager.loadCameras();
    }

    render() {
        this.innerHTML = `
            <div class="dashboard-page">
                <div class="dashboard-main">
                    <skycam-camera-grid></skycam-camera-grid>
                </div>
                <aside class="dashboard-sidebar">
                    <div class="dashboard-stats" id="stats-panel">
                        <div class="stat-card">
                            <div class="stat-icon online">
                                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <rect x="2" y="6" width="14" height="12" rx="2"/><path d="M22 8l-4 4 4 4V8z"/>
                                </svg>
                            </div>
                            <div class="stat-info">
                                <span class="stat-value" id="online-count">0</span>
                                <span class="stat-label">Online</span>
                            </div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-icon offline">
                                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <rect x="2" y="6" width="14" height="12" rx="2"/><path d="M22 8l-4 4 4 4V8z"/>
                                    <path d="M2 2l20 20"/>
                                </svg>
                            </div>
                            <div class="stat-info">
                                <span class="stat-value" id="offline-count">0</span>
                                <span class="stat-label">Offline</span>
                            </div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-icon recording">
                                <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                                    <circle cx="12" cy="12" r="8"/>
                                </svg>
                            </div>
                            <div class="stat-info">
                                <span class="stat-value" id="recording-count">0</span>
                                <span class="stat-label">Gravando</span>
                            </div>
                        </div>
                    </div>
                    <skycam-event-list limit="5"></skycam-event-list>
                </aside>
            </div>
        `;

        this.addStyles();
        this.subscribeToUpdates();
    }

    subscribeToUpdates() {
        this.cameraManager.subscribe((state) => {
            this.querySelector('#online-count').textContent = state.onlineCount;
            this.querySelector('#offline-count').textContent = state.offlineCount;
            const recording = state.cameras.filter(c => c.status === 'recording').length;
            this.querySelector('#recording-count').textContent = recording;
        });
    }

    addStyles() {
        if (document.getElementById('dashboard-page-styles')) return;
        const styles = document.createElement('style');
        styles.id = 'dashboard-page-styles';
        styles.textContent = `
            .dashboard-page { display: flex; gap: var(--spacing-lg); height: 100%; }
            .dashboard-main { flex: 1; min-width: 0; }
            .dashboard-sidebar { width: 320px; display: flex; flex-direction: column; gap: var(--spacing-md); }
            .dashboard-stats { display: grid; grid-template-columns: repeat(3, 1fr); gap: var(--spacing-sm); }
            .stat-card {
                background: var(--color-bg-card); border-radius: var(--radius-lg);
                padding: var(--spacing-md); display: flex; align-items: center; gap: var(--spacing-sm);
            }
            .stat-icon {
                width: 40px; height: 40px; border-radius: var(--radius-md);
                display: flex; align-items: center; justify-content: center;
            }
            .stat-icon.online { background: rgba(34, 197, 94, 0.2); color: var(--color-success); }
            .stat-icon.offline { background: rgba(239, 68, 68, 0.2); color: var(--color-error); }
            .stat-icon.recording { background: rgba(239, 68, 68, 0.2); color: var(--color-error); }
            .stat-value { font-size: var(--font-size-xl); font-weight: var(--font-weight-bold); display: block; }
            .stat-label { font-size: var(--font-size-xs); color: var(--color-text-tertiary); }
            @media (max-width: 1024px) {
                .dashboard-page { flex-direction: column; }
                .dashboard-sidebar { width: 100%; }
                .dashboard-stats { grid-template-columns: repeat(3, 1fr); }
            }
        `;
        document.head.appendChild(styles);
    }
}

customElements.define('page-dashboard', DashboardPage);
export default DashboardPage;
