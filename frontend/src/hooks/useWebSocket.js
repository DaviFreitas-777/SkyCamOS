/**
 * SkyCamOS - Hook useWebSocket
 * Interface simplificada para WebSocket
 */

import { wsService } from '../services/websocket.js';

/**
 * Classe para gerenciar estado do WebSocket
 */
class WebSocketManager {
    constructor() {
        this.connectionState = 'disconnected';
        this.listeners = new Set();
        this.eventHandlers = new Map();

        // Inicializar listeners internos
        this.initListeners();
    }

    /**
     * Inicializar listeners do servico WebSocket
     */
    initListeners() {
        wsService.on('state_change', (state) => {
            this.connectionState = state;
            this.notify();
        });

        wsService.on('connected', () => {
            this.notify();
        });

        wsService.on('disconnected', () => {
            this.notify();
        });

        wsService.on('error', (error) => {
            console.error('[WS Manager] Erro:', error);
        });
    }

    /**
     * Conectar ao servidor
     * @returns {Promise<void>}
     */
    async connect() {
        return wsService.connect();
    }

    /**
     * Desconectar do servidor
     */
    disconnect() {
        wsService.disconnect();
    }

    /**
     * Verificar se esta conectado
     * @returns {boolean}
     */
    isConnected() {
        return wsService.isConnected();
    }

    /**
     * Obter estado da conexao
     * @returns {string}
     */
    getConnectionState() {
        return wsService.getState();
    }

    /**
     * Enviar mensagem
     * @param {string} type - Tipo da mensagem
     * @param {Object} payload - Dados
     */
    send(type, payload = {}) {
        wsService.send(type, payload);
    }

    /**
     * Registrar handler para evento especifico
     * @param {string} event - Nome do evento
     * @param {Function} handler - Funcao callback
     * @returns {Function} - Funcao para remover handler
     */
    on(event, handler) {
        const unsubscribe = wsService.on(event, handler);

        // Manter registro para limpeza
        if (!this.eventHandlers.has(event)) {
            this.eventHandlers.set(event, new Set());
        }
        this.eventHandlers.get(event).add({ handler, unsubscribe });

        return unsubscribe;
    }

    /**
     * Remover handler de evento
     * @param {string} event - Nome do evento
     * @param {Function} handler - Funcao callback
     */
    off(event, handler) {
        wsService.off(event, handler);

        // Atualizar registro
        if (this.eventHandlers.has(event)) {
            const handlers = this.eventHandlers.get(event);
            handlers.forEach(item => {
                if (item.handler === handler) {
                    handlers.delete(item);
                }
            });
        }
    }

    /**
     * Remover todos os handlers de um evento
     * @param {string} event - Nome do evento
     */
    offAll(event) {
        if (this.eventHandlers.has(event)) {
            this.eventHandlers.get(event).forEach(item => {
                item.unsubscribe();
            });
            this.eventHandlers.delete(event);
        }
    }

    /**
     * Limpar todos os handlers registrados
     */
    cleanup() {
        this.eventHandlers.forEach((handlers, event) => {
            handlers.forEach(item => {
                item.unsubscribe();
            });
        });
        this.eventHandlers.clear();
    }

    /**
     * Subscrever a canal especifico
     * @param {string} channel - Nome do canal
     * @param {Object} options - Opcoes adicionais
     */
    subscribe(channel, options = {}) {
        wsService.send('subscribe', { channel, ...options });
    }

    /**
     * Cancelar subscricao de canal
     * @param {string} channel - Nome do canal
     */
    unsubscribe(channel) {
        wsService.send('unsubscribe', { channel });
    }

    /**
     * Registrar listener para mudancas de estado
     * @param {Function} callback - Funcao callback
     * @returns {Function} - Funcao para remover listener
     */
    onStateChange(callback) {
        this.listeners.add(callback);
        return () => this.listeners.delete(callback);
    }

    /**
     * Notificar listeners sobre mudancas
     */
    notify() {
        const state = this.getState();
        this.listeners.forEach(callback => {
            try {
                callback(state);
            } catch (error) {
                console.error('[WS Manager] Erro no listener:', error);
            }
        });
    }

    /**
     * Obter estado atual
     * @returns {Object}
     */
    getState() {
        return {
            isConnected: this.isConnected(),
            connectionState: this.getConnectionState()
        };
    }
}

// Instancia singleton
export const wsManager = new WebSocketManager();

/**
 * Hook para usar em componentes
 * @returns {Object} - Estado e metodos do WebSocket manager
 */
export function useWebSocket() {
    return {
        // Estado
        get isConnected() { return wsManager.isConnected(); },
        get connectionState() { return wsManager.getConnectionState(); },

        // Metodos
        connect: wsManager.connect.bind(wsManager),
        disconnect: wsManager.disconnect.bind(wsManager),
        send: wsManager.send.bind(wsManager),
        on: wsManager.on.bind(wsManager),
        off: wsManager.off.bind(wsManager),
        offAll: wsManager.offAll.bind(wsManager),
        cleanup: wsManager.cleanup.bind(wsManager),
        subscribe: wsManager.subscribe.bind(wsManager),
        unsubscribe: wsManager.unsubscribe.bind(wsManager),
        onStateChange: wsManager.onStateChange.bind(wsManager),
        getState: wsManager.getState.bind(wsManager)
    };
}

export default useWebSocket;
