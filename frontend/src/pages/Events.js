/**
 * SkyCamOS - Pagina Events
 * Pagina de eventos do sistema
 */

import { apiService } from '../services/api.js';
import { EVENT_TYPE_LABELS, EVENT_TYPES } from '../utils/constants.js';
import { formatDateTime, formatRelativeTime } from '../utils/dateFormatter.js';

class EventsPage extends HTMLElement {
    constructor() {
        super();
        this.events = [];
        this.cameras = [];
        this.filters = { type: '', cameraId: '', startDate: '', endDate: '' };
        this.pagination = { page: 1, limit: 20, total: 0 };
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
            const params = { ...this.filters, page: this.pagination.page, limit: this.pagination.limit };
            const [eventsData, cameras] = await Promise.all([
                apiService.getEvents(params),
                apiService.getCameras()
            ]);

            this.events = eventsData.events || eventsData;
            this.pagination.total = eventsData.total || this.events.length;
            this.cameras = cameras;
            this.renderEvents();
        } catch (error) {
            console.error('[Events] Erro ao carregar:', error);
            this.renderError();
        }

        this.loading = false;
    }

    render() {
        this.innerHTML = `
            <div class="events-page">
                <div class="page-header">
                    <h1 class="page-title">Eventos</h1>
                    <div class="page-actions">
                        <button class="btn btn-secondary" id="mark-all-read">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M22 11.08V12a10 10 0 11-5.93-9.14"/><path d="M22 4L12 14.01l-3-3"/>
                            </svg>
                            Marcar todas como lidas
                        </button>
                    </div>
                </div>

                <div class="events-filters">
                    <select class="input" id="filter-type">
                        <option value="">Todos os tipos</option>
                        ${Object.entries(EVENT_TYPE_LABELS).map(([k, v]) => `<option value="${k}">${v}</option>`).join('')}
                    </select>
                    <select class="input" id="filter-camera">
                        <option value="">Todas as cameras</option>
                    </select>
                    <input type="date" class="input" id="filter-start-date" placeholder="Data inicio">
                    <input type="date" class="input" id="filter-end-date" placeholder="Data fim">
                    <button class="btn btn-primary" id="btn-filter">Filtrar</button>
                </div>

                <div class="events-content">
                    <div class="events-list" id="events-list">
                        <div class="loading-spinner"></div>
                    </div>
                    <div class="events-pagination" id="pagination"></div>
                </div>
            </div>
        `;

        this.addStyles();
        this.attachEventListeners();
    }

    renderEvents() {
        const container = this.querySelector('#events-list');
        if (!container) return;

        // Preencher select de cameras
        const cameraSelect = this.querySelector('#filter-camera');
        if (cameraSelect && cameraSelect.options.length <= 1) {
            cameraSelect.innerHTML += this.cameras.map(c => `<option value="${c.id}">${c.name}</option>`).join('');
        }

        if (this.events.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <svg class="empty-state-icon" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                        <path d="M18 8A6 6 0 006 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 01-3.46 0"/>
                    </svg>
                    <p>Nenhum evento encontrado</p>
                </div>
            `;
            return;
        }

        container.innerHTML = this.events.map(event => `
            <div class="event-card ${event.read ? '' : 'unread'}" data-id="${event.id}">
                <div class="event-card-thumbnail">
                    ${event.thumbnail ?
                        `<img src="${event.thumbnail}" alt="Evento">` :
                        `<div class="event-card-icon">
                            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M18 8A6 6 0 006 8c0 7-3 9-3 9h18s-3-2-3-9"/>
                            </svg>
                        </div>`
                    }
                </div>
                <div class="event-card-content">
                    <div class="event-card-header">
                        <span class="badge badge-${this.getEventBadgeType(event.type)}">${EVENT_TYPE_LABELS[event.type] || event.type}</span>
                        <span class="event-time">${formatRelativeTime(event.timestamp)}</span>
                    </div>
                    <h3 class="event-card-title">${event.title || EVENT_TYPE_LABELS[event.type] || 'Evento'}</h3>
                    <p class="event-card-desc">${event.description || event.cameraName || ''}</p>
                    <div class="event-card-meta">
                        <span>${event.cameraName || 'Camera desconhecida'}</span>
                        <span>${formatDateTime(event.timestamp)}</span>
                    </div>
                </div>
                <div class="event-card-actions">
                    <button class="btn btn-icon-sm btn-ghost" data-action="view" title="Ver detalhes">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>
                        </svg>
                    </button>
                    <button class="btn btn-icon-sm btn-ghost" data-action="goto" title="Ir para gravacao">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <rect x="2" y="6" width="14" height="12" rx="2"/><path d="M22 8l-4 4 4 4V8z"/>
                        </svg>
                    </button>
                </div>
            </div>
        `).join('');

        this.renderPagination();
        this.attachEventCardListeners();
    }

    renderPagination() {
        const container = this.querySelector('#pagination');
        if (!container) return;

        const totalPages = Math.ceil(this.pagination.total / this.pagination.limit);
        if (totalPages <= 1) {
            container.innerHTML = '';
            return;
        }

        container.innerHTML = `
            <button class="btn btn-secondary btn-sm" id="prev-page" ${this.pagination.page <= 1 ? 'disabled' : ''}>Anterior</button>
            <span class="pagination-info">Pagina ${this.pagination.page} de ${totalPages}</span>
            <button class="btn btn-secondary btn-sm" id="next-page" ${this.pagination.page >= totalPages ? 'disabled' : ''}>Proxima</button>
        `;

        container.querySelector('#prev-page')?.addEventListener('click', () => {
            if (this.pagination.page > 1) { this.pagination.page--; this.loadData(); }
        });
        container.querySelector('#next-page')?.addEventListener('click', () => {
            if (this.pagination.page < totalPages) { this.pagination.page++; this.loadData(); }
        });
    }

    renderLoading() {
        const container = this.querySelector('#events-list');
        if (container) container.innerHTML = '<div class="loading-spinner" style="margin: auto;"></div>';
    }

    renderError() {
        const container = this.querySelector('#events-list');
        if (container) {
            container.innerHTML = `<div class="empty-state"><p>Erro ao carregar eventos</p>
                <button class="btn btn-secondary" id="retry-btn">Tentar novamente</button></div>`;
            container.querySelector('#retry-btn')?.addEventListener('click', () => this.loadData());
        }
    }

    getEventBadgeType(type) {
        const map = { motion: 'warning', person: 'info', vehicle: 'info', camera_offline: 'error', camera_online: 'success' };
        return map[type] || 'primary';
    }

    addStyles() {
        if (document.getElementById('events-page-styles')) return;
        const styles = document.createElement('style');
        styles.id = 'events-page-styles';
        styles.textContent = `
            .events-page { display: flex; flex-direction: column; height: 100%; }
            .page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: var(--spacing-md); }
            .page-title { font-size: var(--font-size-2xl); font-weight: var(--font-weight-bold); }
            .events-filters { display: flex; gap: var(--spacing-sm); margin-bottom: var(--spacing-md); flex-wrap: wrap; }
            .events-filters .input { min-width: 150px; }
            .events-content { flex: 1; display: flex; flex-direction: column; min-height: 0; }
            .events-list { flex: 1; display: flex; flex-direction: column; gap: var(--spacing-sm); overflow-y: auto; }
            .event-card {
                display: flex; gap: var(--spacing-md); padding: var(--spacing-md);
                background: var(--color-bg-card); border-radius: var(--radius-lg);
                transition: background var(--transition-fast); cursor: pointer;
            }
            .event-card:hover { background: var(--color-bg-card-hover); }
            .event-card.unread { border-left: 3px solid var(--color-primary-500); }
            .event-card-thumbnail { width: 120px; height: 80px; background: var(--color-bg-tertiary); border-radius: var(--radius-md); overflow: hidden; flex-shrink: 0; display: flex; align-items: center; justify-content: center; }
            .event-card-thumbnail img { width: 100%; height: 100%; object-fit: cover; }
            .event-card-icon { color: var(--color-text-tertiary); }
            .event-card-content { flex: 1; min-width: 0; }
            .event-card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: var(--spacing-xs); }
            .event-time { font-size: var(--font-size-xs); color: var(--color-text-tertiary); }
            .event-card-title { font-size: var(--font-size-base); font-weight: var(--font-weight-medium); margin-bottom: var(--spacing-xs); }
            .event-card-desc { font-size: var(--font-size-sm); color: var(--color-text-secondary); margin-bottom: var(--spacing-xs); }
            .event-card-meta { font-size: var(--font-size-xs); color: var(--color-text-tertiary); display: flex; gap: var(--spacing-md); }
            .event-card-actions { display: flex; flex-direction: column; gap: var(--spacing-xs); }
            .events-pagination { display: flex; justify-content: center; align-items: center; gap: var(--spacing-md); padding: var(--spacing-md); }
            @media (max-width: 768px) {
                .event-card { flex-direction: column; }
                .event-card-thumbnail { width: 100%; height: 150px; }
            }
        `;
        document.head.appendChild(styles);
    }

    attachEventListeners() {
        this.querySelector('#btn-filter')?.addEventListener('click', () => {
            this.filters.type = this.querySelector('#filter-type').value;
            this.filters.cameraId = this.querySelector('#filter-camera').value;
            this.filters.startDate = this.querySelector('#filter-start-date').value;
            this.filters.endDate = this.querySelector('#filter-end-date').value;
            this.pagination.page = 1;
            this.loadData();
        });

        this.querySelector('#mark-all-read')?.addEventListener('click', async () => {
            try {
                await apiService.markAllEventsAsRead();
                this.events.forEach(e => e.read = true);
                this.renderEvents();
            } catch (error) {
                console.error('[Events] Erro ao marcar como lidas:', error);
            }
        });
    }

    attachEventCardListeners() {
        this.querySelectorAll('.event-card').forEach(card => {
            card.addEventListener('click', (e) => {
                if (e.target.closest('button')) return;
                const event = this.events.find(ev => ev.id === card.dataset.id);
                if (event) this.viewEventDetails(event);
            });

            card.querySelectorAll('button').forEach(btn => {
                btn.addEventListener('click', () => {
                    const event = this.events.find(ev => ev.id === card.dataset.id);
                    if (!event) return;
                    if (btn.dataset.action === 'view') this.viewEventDetails(event);
                    if (btn.dataset.action === 'goto') window.location.hash = `#/recordings?event=${event.id}`;
                });
            });
        });
    }

    viewEventDetails(event) {
        // Marcar como lido
        if (!event.read) {
            apiService.markEventAsRead(event.id);
            event.read = true;
            this.renderEvents();
        }
        // Abrir modal ou navegar
        window.location.hash = `#/events/${event.id}`;
    }
}

customElements.define('page-events', EventsPage);
export default EventsPage;
