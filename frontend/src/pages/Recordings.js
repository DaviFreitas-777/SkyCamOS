/**
 * SkyCamOS - Pagina Recordings
 * Pagina de gravacoes
 */

import '../components/Timeline.js';
import '../components/VideoPlayer.js';
import { apiService } from '../services/api.js';
import { formatDate, formatDuration } from '../utils/dateFormatter.js';
import { formatBytes } from '../utils/helpers.js';

class RecordingsPage extends HTMLElement {
    constructor() {
        super();
        this.recordings = [];
        this.cameras = [];
        this.selectedRecording = null;
        this.filters = { cameraId: '', date: '', type: '' };
        this.loading = false;
    }

    async connectedCallback() {
        this.render();
        await this.loadData();
    }

    async loadData() {
        this.loading = true;
        this.renderLoading();

        try {
            const [recordings, cameras] = await Promise.all([
                apiService.getRecordings(this.filters),
                apiService.getCameras()
            ]);
            this.recordings = recordings;
            this.cameras = cameras;
            this.renderRecordings();
        } catch (error) {
            console.error('[Recordings] Erro ao carregar:', error);
            this.renderError();
        }

        this.loading = false;
    }

    render() {
        this.innerHTML = `
            <div class="recordings-page">
                <div class="page-header">
                    <h1 class="page-title">Gravacoes</h1>
                    <div class="page-actions">
                        <select class="input" id="filter-camera">
                            <option value="">Todas as cameras</option>
                        </select>
                        <input type="date" class="input" id="filter-date" value="${new Date().toISOString().split('T')[0]}">
                        <button class="btn btn-secondary" id="btn-export">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M7 10l5 5 5-5M12 15V3"/>
                            </svg>
                            Exportar
                        </button>
                    </div>
                </div>

                <div class="recordings-content">
                    <div class="recordings-player" id="player-container">
                        <div class="player-placeholder">
                            <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                                <rect x="2" y="6" width="14" height="12" rx="2"/><path d="M22 8l-4 4 4 4V8z"/>
                            </svg>
                            <p>Selecione uma gravacao para reproduzir</p>
                        </div>
                    </div>

                    <div class="recordings-timeline" id="timeline-container">
                        <skycam-timeline></skycam-timeline>
                    </div>

                    <div class="recordings-list" id="recordings-list">
                        <div class="loading-spinner"></div>
                    </div>
                </div>
            </div>
        `;

        this.addStyles();
        this.attachEventListeners();
    }

    renderRecordings() {
        const container = this.querySelector('#recordings-list');
        if (!container) return;

        // Preencher select de cameras
        const cameraSelect = this.querySelector('#filter-camera');
        if (cameraSelect) {
            cameraSelect.innerHTML = `<option value="">Todas as cameras</option>` +
                this.cameras.map(c => `<option value="${c.id}">${c.name}</option>`).join('');
        }

        if (this.recordings.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <svg class="empty-state-icon" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                        <rect x="2" y="6" width="14" height="12" rx="2"/><path d="M22 8l-4 4 4 4V8z"/>
                    </svg>
                    <p>Nenhuma gravacao encontrada</p>
                </div>
            `;
            return;
        }

        container.innerHTML = `
            <table class="recordings-table">
                <thead>
                    <tr>
                        <th>Camera</th>
                        <th>Inicio</th>
                        <th>Duracao</th>
                        <th>Tamanho</th>
                        <th>Acoes</th>
                    </tr>
                </thead>
                <tbody>
                    ${this.recordings.map(rec => `
                        <tr data-id="${rec.id}" class="${this.selectedRecording?.id === rec.id ? 'selected' : ''}">
                            <td>${rec.cameraName || 'Camera'}</td>
                            <td>${formatDate(rec.startTime)} ${new Date(rec.startTime).toLocaleTimeString('pt-BR')}</td>
                            <td>${formatDuration(rec.duration)}</td>
                            <td>${formatBytes(rec.size || 0)}</td>
                            <td>
                                <button class="btn btn-icon-sm btn-ghost" data-action="play" title="Reproduzir">
                                    <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><polygon points="5 3 19 12 5 21"/></svg>
                                </button>
                                <button class="btn btn-icon-sm btn-ghost" data-action="download" title="Download">
                                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                        <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M7 10l5 5 5-5M12 15V3"/>
                                    </svg>
                                </button>
                                <button class="btn btn-icon-sm btn-ghost" data-action="delete" title="Excluir">
                                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                        <path d="M3 6h18M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/>
                                    </svg>
                                </button>
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;

        this.attachRecordingListeners();
    }

    renderLoading() {
        const container = this.querySelector('#recordings-list');
        if (container) container.innerHTML = '<div class="loading-spinner" style="margin: auto;"></div>';
    }

    renderError() {
        const container = this.querySelector('#recordings-list');
        if (container) {
            container.innerHTML = `<div class="empty-state"><p>Erro ao carregar gravacoes</p>
                <button class="btn btn-secondary" id="retry-btn">Tentar novamente</button></div>`;
            container.querySelector('#retry-btn')?.addEventListener('click', () => this.loadData());
        }
    }

    playRecording(recording) {
        this.selectedRecording = recording;
        const container = this.querySelector('#player-container');
        if (container) {
            container.innerHTML = `
                <skycam-video-player src="${recording.url}" camera-id="${recording.cameraId}" autoplay></skycam-video-player>
                <div class="player-info">
                    <span>${recording.cameraName}</span>
                    <span>${formatDate(recording.startTime)}</span>
                </div>
            `;
        }

        // Atualizar timeline
        const timeline = this.querySelector('skycam-timeline');
        if (timeline) {
            timeline.setAttribute('start-time', recording.startTime);
            timeline.setAttribute('end-time', recording.endTime);
        }

        // Destacar na lista
        this.querySelectorAll('#recordings-list tr').forEach(tr => {
            tr.classList.toggle('selected', tr.dataset.id === recording.id);
        });
    }

    async downloadRecording(recording) {
        try {
            const url = await apiService.getRecordingDownloadUrl(recording.id);
            const link = document.createElement('a');
            link.href = url;
            link.download = `recording_${recording.cameraName}_${recording.startTime}.mp4`;
            link.click();
        } catch (error) {
            console.error('[Recordings] Erro ao baixar:', error);
        }
    }

    async deleteRecording(recording) {
        if (!confirm('Tem certeza que deseja excluir esta gravacao?')) return;
        try {
            await apiService.deleteRecording(recording.id);
            this.recordings = this.recordings.filter(r => r.id !== recording.id);
            this.renderRecordings();
        } catch (error) {
            console.error('[Recordings] Erro ao excluir:', error);
        }
    }

    addStyles() {
        if (document.getElementById('recordings-page-styles')) return;
        const styles = document.createElement('style');
        styles.id = 'recordings-page-styles';
        styles.textContent = `
            .recordings-page { display: flex; flex-direction: column; height: 100%; }
            .page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: var(--spacing-lg); flex-wrap: wrap; gap: var(--spacing-md); }
            .page-title { font-size: var(--font-size-2xl); font-weight: var(--font-weight-bold); }
            .page-actions { display: flex; gap: var(--spacing-sm); align-items: center; }
            .recordings-content { display: grid; grid-template-columns: 1fr 320px; grid-template-rows: auto auto 1fr; gap: var(--spacing-md); flex: 1; min-height: 0; }
            .recordings-player { grid-column: 1; grid-row: 1; background: var(--color-bg-card); border-radius: var(--radius-lg); min-height: 300px; display: flex; align-items: center; justify-content: center; }
            .player-placeholder { text-align: center; color: var(--color-text-tertiary); }
            .player-placeholder svg { margin-bottom: var(--spacing-md); }
            .recordings-timeline { grid-column: 1; grid-row: 2; }
            .recordings-list { grid-column: 1 / -1; grid-row: 3; background: var(--color-bg-card); border-radius: var(--radius-lg); overflow: auto; }
            .recordings-table { width: 100%; border-collapse: collapse; }
            .recordings-table th, .recordings-table td { padding: var(--spacing-sm) var(--spacing-md); text-align: left; border-bottom: 1px solid var(--color-border-secondary); }
            .recordings-table th { background: var(--color-bg-card-hover); font-weight: var(--font-weight-medium); font-size: var(--font-size-sm); color: var(--color-text-secondary); }
            .recordings-table tr { cursor: pointer; transition: background var(--transition-fast); }
            .recordings-table tr:hover { background: var(--color-bg-card-hover); }
            .recordings-table tr.selected { background: rgba(79, 70, 229, 0.1); }
            @media (max-width: 1024px) {
                .recordings-content { grid-template-columns: 1fr; }
                .page-actions { width: 100%; justify-content: flex-start; }
            }
        `;
        document.head.appendChild(styles);
    }

    attachEventListeners() {
        this.querySelector('#filter-camera')?.addEventListener('change', (e) => {
            this.filters.cameraId = e.target.value;
            this.loadData();
        });

        this.querySelector('#filter-date')?.addEventListener('change', (e) => {
            this.filters.date = e.target.value;
            this.loadData();
        });
    }

    attachRecordingListeners() {
        this.querySelectorAll('#recordings-list tr[data-id]').forEach(tr => {
            tr.addEventListener('click', (e) => {
                if (e.target.closest('button')) return;
                const recording = this.recordings.find(r => r.id === tr.dataset.id);
                if (recording) this.playRecording(recording);
            });

            tr.querySelectorAll('button').forEach(btn => {
                btn.addEventListener('click', () => {
                    const recording = this.recordings.find(r => r.id === tr.dataset.id);
                    if (!recording) return;

                    switch (btn.dataset.action) {
                        case 'play': this.playRecording(recording); break;
                        case 'download': this.downloadRecording(recording); break;
                        case 'delete': this.deleteRecording(recording); break;
                    }
                });
            });
        });
    }
}

customElements.define('page-recordings', RecordingsPage);
export default RecordingsPage;
