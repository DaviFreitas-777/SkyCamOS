/**
 * SkyCamOS - Componente NotificationBell
 * Sino de notificacoes com dropdown
 */

import { useNotifications } from '../hooks/useNotifications.js';
import { wsService } from '../services/websocket.js';
import { apiService } from '../services/api.js';
import { formatRelativeTime } from '../utils/dateFormatter.js';

class SkycamNotificationBell extends HTMLElement {
    constructor() {
        super();
        this.notifications = [];
        this.unreadCount = 0;
        this.isOpen = false;
        this.notificationManager = useNotifications();
    }

    connectedCallback() {
        this.render();
        this.attachEventListeners();
        this.loadNotifications();
        this.subscribeToRealtime();
    }

    disconnectedCallback() {
        wsService.off('notification', this.handleNewNotification);
    }

    async loadNotifications() {
        try {
            const data = await apiService.get('/api/notifications', { limit: 10 });
            this.notifications = data.notifications || [];
            this.unreadCount = data.unreadCount || 0;
            this.updateBadge();
            this.renderNotifications();
        } catch (error) {
            console.error('[NotificationBell] Erro ao carregar:', error);
        }
    }

    subscribeToRealtime() {
        wsService.on('notification', (data) => {
            this.notifications.unshift(data);
            this.unreadCount++;
            this.updateBadge();
            this.renderNotifications();
            this.notificationManager.showEventNotification(data);
        });
    }

    render() {
        this.innerHTML = `
            <div class="notification-bell">
                <button class="btn btn-icon notification-bell-btn" id="bell-btn" aria-label="Notificacoes">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M18 8A6 6 0 006 8c0 7-3 9-3 9h18s-3-2-3-9"/>
                        <path d="M13.73 21a2 2 0 01-3.46 0"/>
                    </svg>
                    <span class="notification-badge ${this.unreadCount === 0 ? 'hidden' : ''}" id="notification-badge">
                        ${this.unreadCount > 99 ? '99+' : this.unreadCount}
                    </span>
                </button>
                <div class="notification-dropdown ${this.isOpen ? 'active' : ''}" id="notification-dropdown">
                    <div class="notification-dropdown-header">
                        <span>Notificacoes</span>
                        <button class="btn btn-ghost btn-sm" id="mark-all-read">Marcar todas como lidas</button>
                    </div>
                    <div class="notification-list" id="notification-list"></div>
                    <div class="notification-dropdown-footer">
                        <a href="#/events" class="btn btn-ghost w-full">Ver todas</a>
                    </div>
                </div>
            </div>
        `;
        this.addStyles();
        this.renderNotifications();
    }

    renderNotifications() {
        const container = this.querySelector('#notification-list');
        if (!container) return;

        if (this.notifications.length === 0) {
            container.innerHTML = `
                <div class="notification-empty">
                    <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                        <path d="M18 8A6 6 0 006 8c0 7-3 9-3 9h18s-3-2-3-9"/>
                        <path d="M13.73 21a2 2 0 01-3.46 0"/>
                    </svg>
                    <p>Sem notificacoes</p>
                </div>
            `;
            return;
        }

        container.innerHTML = this.notifications.slice(0, 10).map(n => `
            <div class="notification-item ${n.read ? '' : 'unread'}" data-id="${n.id}">
                <div class="notification-icon">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/>
                    </svg>
                </div>
                <div class="notification-content">
                    <div class="notification-title">${n.title || 'Notificacao'}</div>
                    <div class="notification-body">${n.message || ''}</div>
                    <div class="notification-time">${formatRelativeTime(n.timestamp)}</div>
                </div>
            </div>
        `).join('');

        container.querySelectorAll('.notification-item').forEach(item => {
            item.addEventListener('click', () => {
                const id = item.dataset.id;
                this.markAsRead(id);
                if (this.notifications.find(n => n.id === id)?.url) {
                    window.location.hash = this.notifications.find(n => n.id === id).url;
                }
            });
        });
    }

    addStyles() {
        if (document.getElementById('notification-bell-styles')) return;
        const styles = document.createElement('style');
        styles.id = 'notification-bell-styles';
        styles.textContent = `
            .notification-bell { position: relative; }
            .notification-bell-btn { position: relative; }
            .notification-badge {
                position: absolute; top: -4px; right: -4px;
                min-width: 18px; height: 18px; padding: 0 4px;
                background: var(--color-error); color: white;
                font-size: 10px; font-weight: var(--font-weight-bold);
                border-radius: var(--radius-full);
                display: flex; align-items: center; justify-content: center;
            }
            .notification-badge.hidden { display: none; }
            .notification-dropdown {
                position: absolute; top: 100%; right: 0;
                width: 320px; max-height: 400px;
                background: var(--color-bg-elevated); border-radius: var(--radius-lg);
                box-shadow: var(--shadow-xl); z-index: var(--z-dropdown);
                opacity: 0; visibility: hidden; transform: translateY(-8px);
                transition: all var(--transition-fast);
            }
            .notification-dropdown.active { opacity: 1; visibility: visible; transform: translateY(var(--spacing-xs)); }
            .notification-dropdown-header {
                display: flex; justify-content: space-between; align-items: center;
                padding: var(--spacing-md); border-bottom: 1px solid var(--color-border-secondary);
                font-weight: var(--font-weight-semibold);
            }
            .notification-list { max-height: 280px; overflow-y: auto; }
            .notification-item {
                display: flex; gap: var(--spacing-sm); padding: var(--spacing-sm) var(--spacing-md);
                cursor: pointer; transition: background var(--transition-fast);
            }
            .notification-item:hover { background: var(--color-bg-card); }
            .notification-item.unread { background: rgba(79, 70, 229, 0.1); }
            .notification-icon { padding: var(--spacing-xs); color: var(--color-primary-400); }
            .notification-content { flex: 1; min-width: 0; }
            .notification-title { font-size: var(--font-size-sm); font-weight: var(--font-weight-medium); }
            .notification-body { font-size: var(--font-size-xs); color: var(--color-text-secondary); margin: var(--spacing-xs) 0; }
            .notification-time { font-size: var(--font-size-xs); color: var(--color-text-tertiary); }
            .notification-dropdown-footer { padding: var(--spacing-sm); border-top: 1px solid var(--color-border-secondary); }
            .notification-empty { padding: var(--spacing-xl); text-align: center; color: var(--color-text-tertiary); }
            .notification-empty svg { margin: 0 auto var(--spacing-sm); }
        `;
        document.head.appendChild(styles);
    }

    attachEventListeners() {
        const bellBtn = this.querySelector('#bell-btn');
        const dropdown = this.querySelector('#notification-dropdown');

        bellBtn?.addEventListener('click', (e) => {
            e.stopPropagation();
            this.isOpen = !this.isOpen;
            dropdown?.classList.toggle('active', this.isOpen);
        });

        this.querySelector('#mark-all-read')?.addEventListener('click', () => this.markAllAsRead());

        document.addEventListener('click', (e) => {
            if (!this.contains(e.target)) {
                this.isOpen = false;
                dropdown?.classList.remove('active');
            }
        });
    }

    updateBadge() {
        const badge = this.querySelector('#notification-badge');
        if (badge) {
            badge.textContent = this.unreadCount > 99 ? '99+' : this.unreadCount;
            badge.classList.toggle('hidden', this.unreadCount === 0);
        }
    }

    async markAsRead(id) {
        try {
            await apiService.patch(`/api/notifications/${id}/read`);
            const notification = this.notifications.find(n => n.id === id);
            if (notification && !notification.read) {
                notification.read = true;
                this.unreadCount = Math.max(0, this.unreadCount - 1);
                this.updateBadge();
                this.renderNotifications();
            }
        } catch (error) {
            console.error('[NotificationBell] Erro ao marcar como lida:', error);
        }
    }

    async markAllAsRead() {
        try {
            await apiService.post('/api/notifications/mark-all-read');
            this.notifications.forEach(n => n.read = true);
            this.unreadCount = 0;
            this.updateBadge();
            this.renderNotifications();
        } catch (error) {
            console.error('[NotificationBell] Erro ao marcar todas como lidas:', error);
        }
    }
}

customElements.define('skycam-notification-bell', SkycamNotificationBell);
export default SkycamNotificationBell;
