/**
 * SkyCamOS - Servico de Notificacoes
 * Gerenciamento de Push Notifications e notificacoes locais
 */

import { API_BASE_URL, STORAGE_KEYS } from '../utils/constants.js';
import { storageService } from './storage.js';
import { authService } from './auth.js';

/**
 * Classe para gerenciar notificacoes
 */
class NotificationService {
    constructor() {
        this.permission = 'default';
        this.subscription = null;
        this.vapidPublicKey = null;
        this.listeners = new Set();

        // Verificar suporte
        this.isSupported = 'Notification' in window && 'serviceWorker' in navigator;

        // Inicializar
        if (this.isSupported) {
            this.init();
        }
    }

    /**
     * Inicializar servico de notificacoes
     */
    async init() {
        // Obter status atual da permissao
        this.permission = Notification.permission;

        // Carregar VAPID key do servidor
        await this.loadVapidKey();

        // Verificar subscricao existente
        await this.checkExistingSubscription();
    }

    /**
     * Carregar chave publica VAPID do servidor
     */
    async loadVapidKey() {
        try {
            const response = await fetch(`${API_BASE_URL}/api/v1/notifications/vapid-key`);
            if (response.ok) {
                const data = await response.json();
                this.vapidPublicKey = data.publicKey;
            }
        } catch (error) {
            console.error('[Notifications] Erro ao carregar VAPID key:', error);
        }
    }

    /**
     * Verificar subscricao existente
     */
    async checkExistingSubscription() {
        try {
            const registration = await navigator.serviceWorker.ready;
            this.subscription = await registration.pushManager.getSubscription();

            if (this.subscription) {
                console.log('[Notifications] Subscricao existente encontrada');
            }
        } catch (error) {
            console.error('[Notifications] Erro ao verificar subscricao:', error);
        }
    }

    /**
     * Solicitar permissao para notificacoes
     * @returns {Promise<boolean>}
     */
    async requestPermission() {
        if (!this.isSupported) {
            console.warn('[Notifications] Notificacoes nao suportadas');
            return false;
        }

        try {
            const permission = await Notification.requestPermission();
            this.permission = permission;

            if (permission === 'granted') {
                console.log('[Notifications] Permissao concedida');
                return true;
            } else {
                console.log('[Notifications] Permissao negada');
                return false;
            }
        } catch (error) {
            console.error('[Notifications] Erro ao solicitar permissao:', error);
            return false;
        }
    }

    /**
     * Subscrever para push notifications
     * @returns {Promise<boolean>}
     */
    async subscribe() {
        if (!this.isSupported || this.permission !== 'granted') {
            return false;
        }

        if (!this.vapidPublicKey) {
            console.error('[Notifications] VAPID key nao disponivel');
            return false;
        }

        try {
            const registration = await navigator.serviceWorker.ready;

            // Cancelar subscricao anterior se existir
            if (this.subscription) {
                await this.subscription.unsubscribe();
            }

            // Criar nova subscricao
            this.subscription = await registration.pushManager.subscribe({
                userVisibleOnly: true,
                applicationServerKey: this.urlBase64ToUint8Array(this.vapidPublicKey)
            });

            // Enviar subscricao para o servidor
            await this.sendSubscriptionToServer(this.subscription);

            console.log('[Notifications] Subscricao criada com sucesso');
            return true;
        } catch (error) {
            console.error('[Notifications] Erro ao criar subscricao:', error);
            return false;
        }
    }

    /**
     * Cancelar subscricao de push notifications
     * @returns {Promise<boolean>}
     */
    async unsubscribe() {
        if (!this.subscription) {
            return true;
        }

        try {
            await this.subscription.unsubscribe();

            // Remover subscricao do servidor
            await this.removeSubscriptionFromServer();

            this.subscription = null;
            console.log('[Notifications] Subscricao cancelada');
            return true;
        } catch (error) {
            console.error('[Notifications] Erro ao cancelar subscricao:', error);
            return false;
        }
    }

    /**
     * Enviar subscricao para o servidor
     * @param {PushSubscription} subscription - Objeto de subscricao
     */
    async sendSubscriptionToServer(subscription) {
        const token = authService.getToken();
        if (!token) {
            return;
        }

        try {
            await fetch(`${API_BASE_URL}/api/v1/notifications/subscribe`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({
                    subscription: subscription.toJSON()
                })
            });
        } catch (error) {
            console.error('[Notifications] Erro ao enviar subscricao:', error);
        }
    }

    /**
     * Remover subscricao do servidor
     */
    async removeSubscriptionFromServer() {
        const token = authService.getToken();
        if (!token) {
            return;
        }

        try {
            await fetch(`${API_BASE_URL}/api/v1/notifications/unsubscribe`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
        } catch (error) {
            console.error('[Notifications] Erro ao remover subscricao:', error);
        }
    }

    /**
     * Converter base64 URL para Uint8Array (para VAPID key)
     * @param {string} base64String - String base64
     * @returns {Uint8Array}
     */
    urlBase64ToUint8Array(base64String) {
        const padding = '='.repeat((4 - base64String.length % 4) % 4);
        const base64 = (base64String + padding)
            .replace(/-/g, '+')
            .replace(/_/g, '/');

        const rawData = window.atob(base64);
        const outputArray = new Uint8Array(rawData.length);

        for (let i = 0; i < rawData.length; ++i) {
            outputArray[i] = rawData.charCodeAt(i);
        }

        return outputArray;
    }

    /**
     * Exibir notificacao local
     * @param {string} title - Titulo
     * @param {Object} options - Opcoes da notificacao
     * @returns {Notification|null}
     */
    show(title, options = {}) {
        if (!this.isSupported || this.permission !== 'granted') {
            console.warn('[Notifications] Permissao nao concedida');
            return null;
        }

        const defaultOptions = {
            icon: '/icons/icon-192x192.svg',
            badge: '/icons/icon-96x96.svg',
            vibrate: [200, 100, 200],
            requireInteraction: false,
            silent: false
        };

        const notification = new Notification(title, {
            ...defaultOptions,
            ...options
        });

        // Handlers de eventos
        notification.onclick = (event) => {
            event.preventDefault();
            window.focus();
            notification.close();

            if (options.onClick) {
                options.onClick(event);
            }
        };

        notification.onclose = () => {
            if (options.onClose) {
                options.onClose();
            }
        };

        notification.onerror = (error) => {
            console.error('[Notifications] Erro na notificacao:', error);
            if (options.onError) {
                options.onError(error);
            }
        };

        return notification;
    }

    /**
     * Exibir notificacao de camera
     * @param {Object} camera - Dados da camera
     * @param {string} message - Mensagem
     */
    showCameraNotification(camera, message) {
        this.show(`Camera: ${camera.name}`, {
            body: message,
            tag: `camera-${camera.id}`,
            data: { type: 'camera', cameraId: camera.id },
            onClick: () => {
                window.location.hash = `#/dashboard?camera=${camera.id}`;
            }
        });
    }

    /**
     * Exibir notificacao de evento
     * @param {Object} event - Dados do evento
     */
    showEventNotification(event) {
        this.show(`Novo Evento: ${event.type}`, {
            body: event.description || `Evento detectado em ${event.cameraName}`,
            tag: `event-${event.id}`,
            data: { type: 'event', eventId: event.id },
            requireInteraction: event.priority === 'high',
            onClick: () => {
                window.location.hash = `#/events/${event.id}`;
            }
        });
    }

    /**
     * Exibir notificacao de sistema
     * @param {string} title - Titulo
     * @param {string} message - Mensagem
     * @param {string} type - Tipo (info, warning, error)
     */
    showSystemNotification(title, message, type = 'info') {
        this.show(title, {
            body: message,
            tag: `system-${Date.now()}`,
            data: { type: 'system' }
        });
    }

    /**
     * Verificar se notificacoes estao habilitadas
     * @returns {boolean}
     */
    isEnabled() {
        return this.isSupported && this.permission === 'granted' && !!this.subscription;
    }

    /**
     * Obter status das notificacoes
     * @returns {Object}
     */
    getStatus() {
        return {
            isSupported: this.isSupported,
            permission: this.permission,
            isSubscribed: !!this.subscription
        };
    }

    /**
     * Registrar listener para eventos de notificacao
     * @param {Function} callback - Funcao callback
     * @returns {Function} - Funcao para remover listener
     */
    onNotification(callback) {
        this.listeners.add(callback);
        return () => this.listeners.delete(callback);
    }

    /**
     * Disparar evento para listeners
     * @param {Object} notification - Dados da notificacao
     */
    emit(notification) {
        this.listeners.forEach(callback => {
            try {
                callback(notification);
            } catch (error) {
                console.error('[Notifications] Erro no listener:', error);
            }
        });
    }
}

// Instancia singleton
export const notificationService = new NotificationService();

export default notificationService;
