/**
 * SkyCamOS - Hook useNotifications
 * Gerenciamento de notificacoes push e toasts
 */

import { notificationService } from '../services/notifications.js';
import { NOTIFICATION_SETTINGS } from '../utils/constants.js';
import { generateId } from '../utils/helpers.js';

/**
 * Classe para gerenciar notificacoes e toasts
 */
class NotificationManager {
    constructor() {
        this.toasts = [];
        this.listeners = new Set();

        // Configuracoes
        this.maxToasts = NOTIFICATION_SETTINGS.MAX_TOASTS;
        this.defaultDuration = NOTIFICATION_SETTINGS.TOAST_DURATION;
    }

    // ==========================================
    // Push Notifications
    // ==========================================

    /**
     * Verificar se notificacoes push estao disponiveis
     * @returns {boolean}
     */
    isSupported() {
        return notificationService.isSupported;
    }

    /**
     * Obter permissao atual
     * @returns {string}
     */
    getPermission() {
        return notificationService.permission;
    }

    /**
     * Solicitar permissao para notificacoes
     * @returns {Promise<boolean>}
     */
    async requestPermission() {
        return notificationService.requestPermission();
    }

    /**
     * Subscrever para push notifications
     * @returns {Promise<boolean>}
     */
    async subscribePush() {
        return notificationService.subscribe();
    }

    /**
     * Cancelar subscricao de push
     * @returns {Promise<boolean>}
     */
    async unsubscribePush() {
        return notificationService.unsubscribe();
    }

    /**
     * Verificar se push esta habilitado
     * @returns {boolean}
     */
    isPushEnabled() {
        return notificationService.isEnabled();
    }

    /**
     * Obter status das notificacoes push
     * @returns {Object}
     */
    getPushStatus() {
        return notificationService.getStatus();
    }

    // ==========================================
    // Toast Notifications
    // ==========================================

    /**
     * Adicionar toast
     * @param {Object} options - Opcoes do toast
     * @returns {string} - ID do toast
     */
    addToast(options) {
        const toast = {
            id: generateId(),
            type: options.type || 'info',
            title: options.title || '',
            message: options.message || '',
            duration: options.duration ?? this.defaultDuration,
            dismissible: options.dismissible !== false,
            action: options.action || null,
            createdAt: Date.now()
        };

        // Limitar numero de toasts
        while (this.toasts.length >= this.maxToasts) {
            this.toasts.shift();
        }

        this.toasts.push(toast);
        this.notify();
        this.renderToast(toast);

        // Auto-dismiss
        if (toast.duration > 0) {
            setTimeout(() => {
                this.removeToast(toast.id);
            }, toast.duration);
        }

        return toast.id;
    }

    /**
     * Remover toast por ID
     * @param {string} id - ID do toast
     */
    removeToast(id) {
        const index = this.toasts.findIndex(t => t.id === id);

        if (index !== -1) {
            this.toasts.splice(index, 1);
            this.notify();

            // Remover do DOM
            const element = document.getElementById(`toast-${id}`);
            if (element) {
                element.classList.add('toast-exit');
                setTimeout(() => {
                    element.remove();
                }, 300);
            }
        }
    }

    /**
     * Limpar todos os toasts
     */
    clearToasts() {
        this.toasts = [];
        this.notify();

        const container = document.getElementById('toast-container');
        if (container) {
            container.innerHTML = '';
        }
    }

    /**
     * Renderizar toast no DOM
     * @param {Object} toast - Dados do toast
     */
    renderToast(toast) {
        const container = document.getElementById('toast-container');
        if (!container) return;

        const element = document.createElement('div');
        element.id = `toast-${toast.id}`;
        element.className = `toast toast-${toast.type}`;
        element.innerHTML = `
            <div class="toast-icon">
                ${this.getToastIcon(toast.type)}
            </div>
            <div class="toast-content">
                ${toast.title ? `<div class="toast-title">${toast.title}</div>` : ''}
                ${toast.message ? `<div class="toast-message">${toast.message}</div>` : ''}
                ${toast.action ? `<button class="toast-action btn btn-sm btn-ghost">${toast.action.label}</button>` : ''}
            </div>
            ${toast.dismissible ? `
                <button class="toast-close btn-icon-sm" aria-label="Fechar">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M18 6L6 18M6 6l12 12"/>
                    </svg>
                </button>
            ` : ''}
        `;

        // Event listeners
        if (toast.dismissible) {
            element.querySelector('.toast-close')?.addEventListener('click', () => {
                this.removeToast(toast.id);
            });
        }

        if (toast.action) {
            element.querySelector('.toast-action')?.addEventListener('click', () => {
                toast.action.callback?.();
                this.removeToast(toast.id);
            });
        }

        container.appendChild(element);
    }

    /**
     * Obter icone do toast baseado no tipo
     * @param {string} type - Tipo do toast
     * @returns {string} - SVG do icone
     */
    getToastIcon(type) {
        const icons = {
            success: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M22 11.08V12a10 10 0 11-5.93-9.14"/>
                <path d="M22 4L12 14.01l-3-3"/>
            </svg>`,
            error: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"/>
                <path d="M15 9l-6 6M9 9l6 6"/>
            </svg>`,
            warning: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/>
                <path d="M12 9v4M12 17h.01"/>
            </svg>`,
            info: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"/>
                <path d="M12 16v-4M12 8h.01"/>
            </svg>`
        };

        return icons[type] || icons.info;
    }

    // ==========================================
    // Metodos de conveniencia
    // ==========================================

    /**
     * Toast de sucesso
     * @param {string} message - Mensagem
     * @param {Object} options - Opcoes adicionais
     * @returns {string} - ID do toast
     */
    success(message, options = {}) {
        return this.addToast({
            ...options,
            type: 'success',
            message
        });
    }

    /**
     * Toast de erro
     * @param {string} message - Mensagem
     * @param {Object} options - Opcoes adicionais
     * @returns {string} - ID do toast
     */
    error(message, options = {}) {
        return this.addToast({
            ...options,
            type: 'error',
            message,
            duration: options.duration ?? 8000 // Erros ficam mais tempo
        });
    }

    /**
     * Toast de aviso
     * @param {string} message - Mensagem
     * @param {Object} options - Opcoes adicionais
     * @returns {string} - ID do toast
     */
    warning(message, options = {}) {
        return this.addToast({
            ...options,
            type: 'warning',
            message
        });
    }

    /**
     * Toast informativo
     * @param {string} message - Mensagem
     * @param {Object} options - Opcoes adicionais
     * @returns {string} - ID do toast
     */
    info(message, options = {}) {
        return this.addToast({
            ...options,
            type: 'info',
            message
        });
    }

    /**
     * Registrar listener para mudancas
     * @param {Function} callback - Funcao callback
     * @returns {Function} - Funcao para remover listener
     */
    subscribe(callback) {
        this.listeners.add(callback);
        return () => this.listeners.delete(callback);
    }

    /**
     * Notificar listeners
     */
    notify() {
        const state = this.getState();
        this.listeners.forEach(callback => {
            try {
                callback(state);
            } catch (error) {
                console.error('[Notification Manager] Erro no listener:', error);
            }
        });
    }

    /**
     * Obter estado atual
     * @returns {Object}
     */
    getState() {
        return {
            toasts: [...this.toasts],
            pushStatus: this.getPushStatus()
        };
    }
}

// Instancia singleton
export const notificationManager = new NotificationManager();

/**
 * Hook para usar em componentes
 * @returns {Object} - Estado e metodos do notification manager
 */
export function useNotifications() {
    return {
        // Estado
        get toasts() { return notificationManager.toasts; },

        // Push Notifications
        isSupported: notificationManager.isSupported.bind(notificationManager),
        getPermission: notificationManager.getPermission.bind(notificationManager),
        requestPermission: notificationManager.requestPermission.bind(notificationManager),
        subscribePush: notificationManager.subscribePush.bind(notificationManager),
        unsubscribePush: notificationManager.unsubscribePush.bind(notificationManager),
        isPushEnabled: notificationManager.isPushEnabled.bind(notificationManager),
        getPushStatus: notificationManager.getPushStatus.bind(notificationManager),

        // Toasts
        addToast: notificationManager.addToast.bind(notificationManager),
        removeToast: notificationManager.removeToast.bind(notificationManager),
        clearToasts: notificationManager.clearToasts.bind(notificationManager),
        success: notificationManager.success.bind(notificationManager),
        error: notificationManager.error.bind(notificationManager),
        warning: notificationManager.warning.bind(notificationManager),
        info: notificationManager.info.bind(notificationManager),

        // Subscricao
        subscribe: notificationManager.subscribe.bind(notificationManager),
        getState: notificationManager.getState.bind(notificationManager)
    };
}

export default useNotifications;
