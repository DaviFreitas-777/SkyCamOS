/**
 * SkyCamOS - Componente EventList
 * Lista de eventos do sistema
 */

import { EVENT_TYPE_LABELS } from '../utils/constants.js';
import { formatRelativeTime } from '../utils/dateFormatter.js';
import { apiService } from '../services/api.js';

class SkycamEventList extends HTMLElement {
    constructor() {
        super();
        this.events = [];
        this.loading = false;
        this.filter = 'all';
    }

    static get observedAttributes() {
        return ['filter', 'limit'];
    }

    attributeChangedCallback(name, oldValue, newValue) {
        if (name === 'filter') this.filter = newValue;
        if (this.isConnected) this.loadEvents();
    }

    async connectedCallback() {
        this.render();
        await this.loadEvents();
    }

    async loadEvents() {
        this.loading = true;
        this.renderLoading();

        try {
            const params = {};
            if (this.filter && this.filter !== 'all') params.type = this.filter;
            if (this.hasAttribute('limit')) params.limit = this.getAttribute('limit');

            const response = await apiService.getEvents(params);
            this.events = Array.isArray(response) ? response : (response.events || []);
            this.renderEvents();
        } catch (error) {
            console.error('[EventList] Erro ao carregar eventos:', error);
            this.renderError();
        }

        this.loading = false;
    }

    render() {
        this.innerHTML = `
            <div class="event-list-wrapper">
                <div class="event-list-header">
                    <h3 class="event-list-title">Eventos Recentes</h3>
                    <select class="input event-filter" id="event-filter">
                        <option value="all">Todos</option>
                        <option value="motion">Movimento</option>
                        <option value="person">Pessoa</option>
                        <option value="vehicle">Veiculo</option>
                        <option value="camera_offline">Offline</option>
                    </select>
                </div>
                <div class="event-list" id="event-list-container"></div>
            </div>
        `;

        this.addStyles();
        this.querySelector('#event-filter')?.addEventListener('change', (e) => {
            this.filter = e.target.value;
            this.loadEvents();
        });
    }

    renderEvents() {
        const container = this.querySelector('#event-list-container');
        if (!container) return;

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
            <div class="event-item" data-event-id="${event.id}">
                <div class="event-thumbnail">
                    ${event.thumbnail ?
                        `<img src="${event.thumbnail}" alt="Thumbnail">` :
                        `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <rect x="2" y="6" width="14" height="12" rx="2"/><path d="M22 8l-4 4 4 4V8z"/>
                        </svg>`
                    }
                </div>
                <div class="event-info">
                    <div class="event-title">
                        <span class="badge badge-${this.getEventBadgeType(event.type)}">${EVENT_TYPE_LABELS[event.type] || event.type}</span>
                    </div>
                    <div class="event-meta">
                        <span>${event.cameraName || 'Camera'}</span>
                        <span class="event-time">${formatRelativeTime(event.timestamp)}</span>
                    </div>
                </div>
                <button class="btn btn-icon-sm btn-ghost" data-action="view">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M9 18l6-6-6-6"/>
                    </svg>
                </button>
            </div>
        `).join('');

        container.querySelectorAll('.event-item').forEach(item => {
            item.addEventListener('click', () => {
                const eventId = item.dataset.eventId;
                this.dispatchEvent(new CustomEvent('event-select', { detail: { eventId }, bubbles: true }));
            });
        });
    }

    renderLoading() {
        const container = this.querySelector('#event-list-container');
        if (container) {
            container.innerHTML = Array(5).fill(`
                <div class="event-item skeleton-item">
                    <div class="skeleton" style="width: 80px; height: 48px;"></div>
                    <div class="event-info">
                        <div class="skeleton" style="width: 100px; height: 16px; margin-bottom: 4px;"></div>
                        <div class="skeleton" style="width: 150px; height: 12px;"></div>
                    </div>
                </div>
            `).join('');
        }
    }

    renderError() {
        const container = this.querySelector('#event-list-container');
        if (container) {
            container.innerHTML = `
                <div class="empty-state">
                    <p>Erro ao carregar eventos</p>
                    <button class="btn btn-secondary btn-sm" id="retry-events">Tentar novamente</button>
                </div>
            `;
            container.querySelector('#retry-events')?.addEventListener('click', () => this.loadEvents());
        }
    }

    getEventBadgeType(type) {
        const map = {
            motion: 'warning', person: 'info', vehicle: 'info',
            camera_offline: 'error', camera_online: 'success',
            recording_start: 'success', recording_stop: 'warning'
        };
        return map[type] || 'primary';
    }

    addStyles() {
        if (document.getElementById('event-list-styles')) return;
        const styles = document.createElement('style');
        styles.id = 'event-list-styles';
        styles.textContent = `
            .event-list-wrapper { background: var(--color-bg-card); border-radius: var(--radius-lg); padding: var(--spacing-md); }
            .event-list-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: var(--spacing-md); }
            .event-list-title { font-size: var(--font-size-lg); font-weight: var(--font-weight-semibold); }
            .event-filter { width: 120px; font-size: var(--font-size-sm); padding: var(--spacing-xs) var(--spacing-sm); }
            .event-list { display: flex; flex-direction: column; gap: var(--spacing-sm); max-height: 400px; overflow-y: auto; }
            .event-item { display: flex; align-items: center; gap: var(--spacing-md); padding: var(--spacing-sm); background: var(--color-bg-tertiary); border-radius: var(--radius-md); cursor: pointer; transition: background var(--transition-fast); }
            .event-item:hover { background: var(--color-bg-card-hover); }
            .event-thumbnail { width: 80px; height: 48px; background: var(--color-bg-secondary); border-radius: var(--radius-sm); display: flex; align-items: center; justify-content: center; overflow: hidden; flex-shrink: 0; }
            .event-thumbnail img { width: 100%; height: 100%; object-fit: cover; }
            .event-thumbnail svg { color: var(--color-text-tertiary); }
            .event-info { flex: 1; min-width: 0; }
            .event-title { margin-bottom: var(--spacing-xs); }
            .event-meta { display: flex; gap: var(--spacing-sm); font-size: var(--font-size-xs); color: var(--color-text-tertiary); }
            .skeleton-item { pointer-events: none; }
        `;
        document.head.appendChild(styles);
    }
}

customElements.define('skycam-event-list', SkycamEventList);
export default SkycamEventList;
