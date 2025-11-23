/**
 * SkyCamOS - Pagina Export
 * Pagina de exportacao de gravacoes
 */

import { apiService } from '../services/api.js';
import { formatDate, formatDuration } from '../utils/dateFormatter.js';
import { formatBytes } from '../utils/helpers.js';
import { useNotifications } from '../hooks/useNotifications.js';

class ExportPage extends HTMLElement {
    constructor() {
        super();
        this.cameras = [];
        this.preview = null;
        this.exports = [];
        this.loading = false;
        this.exporting = false;
        this.notifications = useNotifications();
    }

    async connectedCallback() {
        this.render();
        await this.loadCameras();
        await this.loadExports();
        this.attachEventListeners();
    }

    async loadCameras() {
        try {
            const response = await apiService.getCameras();
            this.cameras = response.items || response || [];
            this.renderCameraSelect();
        } catch (error) {
            console.error('[Export] Erro ao carregar cameras:', error);
        }
    }

    async loadExports() {
        try {
            const response = await apiService.request('/api/v1/export');
            this.exports = response || [];
            this.renderExportsList();
        } catch (error) {
            console.error('[Export] Erro ao carregar exportacoes:', error);
        }
    }

    render() {
        const now = new Date();
        const today = now.toISOString().split('T')[0];
        const oneHourAgo = new Date(now.getTime() - 3600000);

        this.innerHTML = `
            <div class="export-page">
                <div class="page-header">
                    <h1 class="page-title">Exportar Gravacoes</h1>
                </div>

                <div class="export-content">
                    <!-- Formulario de Exportacao -->
                    <div class="export-form card">
                        <h3 class="card-title">Selecionar Periodo</h3>

                        <div class="form-grid">
                            <div class="input-group">
                                <label class="input-label">Camera</label>
                                <select class="input" id="export-camera">
                                    <option value="">Selecione uma camera</option>
                                </select>
                            </div>

                            <div class="input-group">
                                <label class="input-label">Data Inicio</label>
                                <input type="date" class="input" id="export-start-date" value="${today}">
                            </div>

                            <div class="input-group">
                                <label class="input-label">Hora Inicio</label>
                                <input type="time" class="input" id="export-start-time" value="${oneHourAgo.toTimeString().slice(0,5)}">
                            </div>

                            <div class="input-group">
                                <label class="input-label">Data Fim</label>
                                <input type="date" class="input" id="export-end-date" value="${today}">
                            </div>

                            <div class="input-group">
                                <label class="input-label">Hora Fim</label>
                                <input type="time" class="input" id="export-end-time" value="${now.toTimeString().slice(0,5)}">
                            </div>

                            <div class="input-group">
                                <label class="input-label">Formato</label>
                                <select class="input" id="export-format">
                                    <option value="mp4">MP4 (Universal)</option>
                                    <option value="mkv">MKV (Qualidade Maxima)</option>
                                    <option value="avi">AVI (Compatibilidade)</option>
                                    <option value="webm">WebM (Web)</option>
                                </select>
                            </div>
                        </div>

                        <div class="form-options">
                            <label class="checkbox-label">
                                <input type="checkbox" id="export-watermark">
                                Adicionar watermark com data/hora
                            </label>
                        </div>

                        <div class="form-actions">
                            <button class="btn btn-secondary" id="btn-preview">
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                                    <circle cx="12" cy="12" r="3"/>
                                </svg>
                                Preview
                            </button>
                            <button class="btn btn-primary" id="btn-export" disabled>
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M7 10l5 5 5-5M12 15V3"/>
                                </svg>
                                Exportar
                            </button>
                        </div>
                    </div>

                    <!-- Preview -->
                    <div class="export-preview card" id="preview-container" style="display: none;">
                        <h3 class="card-title">Preview</h3>
                        <div id="preview-content"></div>
                    </div>

                    <!-- Lista de Exportacoes -->
                    <div class="export-list card">
                        <h3 class="card-title">Exportacoes Recentes</h3>
                        <div id="exports-list">
                            <p class="text-muted">Nenhuma exportacao ainda</p>
                        </div>
                    </div>
                </div>
            </div>

            <style>
                .export-page { padding: var(--spacing-lg); }
                .export-content { display: grid; gap: var(--spacing-lg); }
                .export-form { padding: var(--spacing-lg); }
                .form-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: var(--spacing-md);
                    margin-bottom: var(--spacing-lg);
                }
                .form-options { margin-bottom: var(--spacing-lg); }
                .checkbox-label {
                    display: flex;
                    align-items: center;
                    gap: var(--spacing-sm);
                    cursor: pointer;
                }
                .form-actions {
                    display: flex;
                    gap: var(--spacing-md);
                    justify-content: flex-end;
                }
                .export-preview { padding: var(--spacing-lg); }
                .preview-info {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                    gap: var(--spacing-md);
                    margin-bottom: var(--spacing-lg);
                }
                .preview-stat {
                    background: var(--color-bg-tertiary);
                    padding: var(--spacing-md);
                    border-radius: var(--radius-md);
                    text-align: center;
                }
                .preview-stat-value {
                    font-size: var(--font-size-xl);
                    font-weight: var(--font-weight-bold);
                    color: var(--color-primary-500);
                }
                .preview-stat-label {
                    font-size: var(--font-size-sm);
                    color: var(--color-text-secondary);
                }
                .export-list { padding: var(--spacing-lg); }
                .export-item {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: var(--spacing-md);
                    background: var(--color-bg-tertiary);
                    border-radius: var(--radius-md);
                    margin-bottom: var(--spacing-sm);
                }
                .export-item-info { flex: 1; }
                .export-item-name {
                    font-weight: var(--font-weight-medium);
                    margin-bottom: var(--spacing-xs);
                }
                .export-item-meta {
                    font-size: var(--font-size-sm);
                    color: var(--color-text-secondary);
                }
                .export-item-actions { display: flex; gap: var(--spacing-sm); }
                .loading-spinner {
                    display: inline-block;
                    width: 16px;
                    height: 16px;
                    border: 2px solid currentColor;
                    border-right-color: transparent;
                    border-radius: 50%;
                    animation: spin 0.75s linear infinite;
                }
                @keyframes spin { to { transform: rotate(360deg); } }
            </style>
        `;
    }

    renderCameraSelect() {
        const select = this.querySelector('#export-camera');
        if (!select) return;

        select.innerHTML = `
            <option value="">Selecione uma camera</option>
            ${this.cameras.map(c => `
                <option value="${c.id}">${c.name}</option>
            `).join('')}
        `;
    }

    renderExportsList() {
        const container = this.querySelector('#exports-list');
        if (!container) return;

        if (!this.exports || this.exports.length === 0) {
            container.innerHTML = '<p class="text-muted">Nenhuma exportacao ainda</p>';
            return;
        }

        container.innerHTML = this.exports.map(exp => `
            <div class="export-item">
                <div class="export-item-info">
                    <div class="export-item-name">${exp.filename}</div>
                    <div class="export-item-meta">
                        ${exp.size_mb} MB - ${formatDate(exp.created_at)}
                    </div>
                </div>
                <div class="export-item-actions">
                    <a href="${window.ENV?.API_BASE_URL || 'http://localhost:8000'}/api/v1/export/download/${exp.filename}"
                       class="btn btn-sm btn-primary" download>
                        Download
                    </a>
                    <button class="btn btn-sm btn-ghost btn-delete" data-filename="${exp.filename}">
                        Excluir
                    </button>
                </div>
            </div>
        `).join('');

        // Attach delete handlers
        container.querySelectorAll('.btn-delete').forEach(btn => {
            btn.addEventListener('click', (e) => this.handleDelete(e.target.dataset.filename));
        });
    }

    attachEventListeners() {
        this.querySelector('#btn-preview')?.addEventListener('click', () => this.handlePreview());
        this.querySelector('#btn-export')?.addEventListener('click', () => this.handleExport());
    }

    getFormData() {
        const cameraId = this.querySelector('#export-camera')?.value;
        const startDate = this.querySelector('#export-start-date')?.value;
        const startTime = this.querySelector('#export-start-time')?.value;
        const endDate = this.querySelector('#export-end-date')?.value;
        const endTime = this.querySelector('#export-end-time')?.value;
        const format = this.querySelector('#export-format')?.value;
        const watermark = this.querySelector('#export-watermark')?.checked;

        if (!cameraId || !startDate || !startTime || !endDate || !endTime) {
            return null;
        }

        return {
            camera_id: parseInt(cameraId),
            start_time: `${startDate}T${startTime}:00`,
            end_time: `${endDate}T${endTime}:00`,
            format,
            add_watermark: watermark,
        };
    }

    async handlePreview() {
        const data = this.getFormData();
        if (!data) {
            this.notifications.warning('Preencha todos os campos');
            return;
        }

        const btn = this.querySelector('#btn-preview');
        btn.disabled = true;
        btn.innerHTML = '<span class="loading-spinner"></span> Carregando...';

        try {
            const response = await apiService.request('/api/v1/export/preview', {
                method: 'POST',
                body: JSON.stringify({
                    camera_id: data.camera_id,
                    start_time: data.start_time,
                    end_time: data.end_time,
                }),
            });

            this.preview = response;
            this.renderPreview();
            this.querySelector('#btn-export').disabled = false;

        } catch (error) {
            console.error('[Export] Erro no preview:', error);
            this.notifications.error(error.message || 'Erro ao gerar preview');
        } finally {
            btn.disabled = false;
            btn.innerHTML = `
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                    <circle cx="12" cy="12" r="3"/>
                </svg>
                Preview
            `;
        }
    }

    renderPreview() {
        const container = this.querySelector('#preview-container');
        const content = this.querySelector('#preview-content');
        if (!container || !content || !this.preview) return;

        container.style.display = 'block';

        const camera = this.cameras.find(c => c.id === this.preview.camera_id);

        content.innerHTML = `
            <div class="preview-info">
                <div class="preview-stat">
                    <div class="preview-stat-value">${camera?.name || 'Camera ' + this.preview.camera_id}</div>
                    <div class="preview-stat-label">Camera</div>
                </div>
                <div class="preview-stat">
                    <div class="preview-stat-value">${Math.round(this.preview.duration_seconds / 60)} min</div>
                    <div class="preview-stat-label">Duracao</div>
                </div>
                <div class="preview-stat">
                    <div class="preview-stat-value">${this.preview.segment_count}</div>
                    <div class="preview-stat-label">Segmentos</div>
                </div>
                <div class="preview-stat">
                    <div class="preview-stat-value">${this.preview.total_size_mb} MB</div>
                    <div class="preview-stat-label">Tamanho Estimado</div>
                </div>
            </div>
            <div class="preview-period">
                <strong>Periodo:</strong>
                ${formatDate(this.preview.start_time)} - ${formatDate(this.preview.end_time)}
            </div>
            ${this.preview.thumbnail ? `
                <div class="preview-thumbnail">
                    <img src="${this.preview.thumbnail}" alt="Preview" style="max-width: 320px; border-radius: var(--radius-md);">
                </div>
            ` : ''}
        `;
    }

    async handleExport() {
        const data = this.getFormData();
        if (!data) {
            this.notifications.warning('Preencha todos os campos');
            return;
        }

        const btn = this.querySelector('#btn-export');
        btn.disabled = true;
        btn.innerHTML = '<span class="loading-spinner"></span> Exportando...';
        this.exporting = true;

        try {
            const response = await apiService.request('/api/v1/export', {
                method: 'POST',
                body: JSON.stringify(data),
            });

            this.notifications.success('Exportacao concluida!');

            // Recarrega lista de exportacoes
            await this.loadExports();

            // Oferece download automatico
            if (response.filename) {
                const downloadUrl = `${window.ENV?.API_BASE_URL || 'http://localhost:8000'}/api/v1/export/download/${response.filename}`;
                window.open(downloadUrl, '_blank');
            }

        } catch (error) {
            console.error('[Export] Erro na exportacao:', error);
            this.notifications.error(error.message || 'Erro ao exportar');
        } finally {
            btn.disabled = false;
            btn.innerHTML = `
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M7 10l5 5 5-5M12 15V3"/>
                </svg>
                Exportar
            `;
            this.exporting = false;
        }
    }

    async handleDelete(filename) {
        if (!confirm('Remover esta exportacao?')) return;

        try {
            await apiService.request(`/api/v1/export/${filename}`, { method: 'DELETE' });
            this.notifications.success('Exportacao removida');
            await this.loadExports();
        } catch (error) {
            this.notifications.error('Erro ao remover exportacao');
        }
    }
}

customElements.define('skycam-export-page', ExportPage);
export default ExportPage;
