/**
 * SkyCamOS - Servico WebSocket
 * Gerenciamento de conexao WebSocket para eventos em tempo real
 */

import { WS_URL, WS_RECONNECT_INTERVAL, WS_MAX_RECONNECT_ATTEMPTS } from '../utils/constants.js';
import { authService } from './auth.js';

/**
 * Classe para gerenciar conexao WebSocket
 */
class WebSocketService {
    constructor() {
        this.ws = null;
        this.url = WS_URL;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = WS_MAX_RECONNECT_ATTEMPTS;
        this.reconnectInterval = WS_RECONNECT_INTERVAL;
        this.reconnectTimer = null;
        this.pingInterval = null;
        this.isConnecting = false;
        this.isManualClose = false;

        // Event handlers registrados
        this.handlers = new Map();

        // Fila de mensagens para enviar quando reconectar
        this.messageQueue = [];

        // Estado da conexao
        this.state = 'disconnected'; // disconnected, connecting, connected, reconnecting
    }

    /**
     * Conectar ao servidor WebSocket
     * @returns {Promise<void>}
     */
    async connect() {
        if (this.isConnecting || this.ws?.readyState === WebSocket.OPEN) {
            return;
        }

        this.isConnecting = true;
        this.isManualClose = false;
        this.updateState('connecting');

        // Adicionar token na URL se disponivel
        const token = authService.getToken();
        const wsUrl = token ? `${this.url}?token=${token}` : this.url;

        try {
            this.ws = new WebSocket(wsUrl);
            this.setupEventHandlers();
        } catch (error) {
            console.error('[WS] Erro ao criar conexao:', error);
            this.isConnecting = false;
            this.scheduleReconnect();
        }
    }

    /**
     * Configurar handlers de eventos do WebSocket
     */
    setupEventHandlers() {
        this.ws.onopen = () => {
            console.log('[WS] Conexao estabelecida');
            this.isConnecting = false;
            this.reconnectAttempts = 0;
            this.updateState('connected');

            // Iniciar ping para manter conexao viva
            this.startPing();

            // Enviar mensagens da fila
            this.flushMessageQueue();

            // Disparar evento de conexao
            this.emit('connected');
        };

        this.ws.onclose = (event) => {
            console.log('[WS] Conexao fechada:', event.code, event.reason);
            this.isConnecting = false;
            this.stopPing();

            if (!this.isManualClose) {
                this.updateState('reconnecting');
                this.scheduleReconnect();
            } else {
                this.updateState('disconnected');
            }

            this.emit('disconnected', { code: event.code, reason: event.reason });
        };

        this.ws.onerror = (error) => {
            console.error('[WS] Erro:', error);
            this.emit('error', error);
        };

        this.ws.onmessage = (event) => {
            this.handleMessage(event.data);
        };
    }

    /**
     * Processar mensagem recebida
     * @param {string} data - Dados da mensagem
     */
    handleMessage(data) {
        try {
            const message = JSON.parse(data);
            const { type, payload } = message;

            // Pong do servidor
            if (type === 'pong') {
                return;
            }

            // Disparar evento para handlers registrados
            this.emit(type, payload);

            // Disparar evento generico para debug
            this.emit('message', message);

        } catch (error) {
            console.error('[WS] Erro ao processar mensagem:', error);
        }
    }

    /**
     * Enviar mensagem pelo WebSocket
     * @param {string} type - Tipo da mensagem
     * @param {Object} payload - Dados da mensagem
     */
    send(type, payload = {}) {
        const message = JSON.stringify({ type, payload });

        if (this.ws?.readyState === WebSocket.OPEN) {
            this.ws.send(message);
        } else {
            // Adicionar a fila para enviar quando reconectar
            this.messageQueue.push(message);
            console.log('[WS] Mensagem adicionada a fila (desconectado)');
        }
    }

    /**
     * Enviar mensagens da fila
     */
    flushMessageQueue() {
        while (this.messageQueue.length > 0) {
            const message = this.messageQueue.shift();
            if (this.ws?.readyState === WebSocket.OPEN) {
                this.ws.send(message);
            }
        }
    }

    /**
     * Iniciar ping periodico
     */
    startPing() {
        this.stopPing();
        this.pingInterval = setInterval(() => {
            if (this.ws?.readyState === WebSocket.OPEN) {
                this.send('ping');
            }
        }, 30000); // 30 segundos
    }

    /**
     * Parar ping periodico
     */
    stopPing() {
        if (this.pingInterval) {
            clearInterval(this.pingInterval);
            this.pingInterval = null;
        }
    }

    /**
     * Agendar reconexao
     */
    scheduleReconnect() {
        if (this.reconnectTimer) {
            clearTimeout(this.reconnectTimer);
        }

        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.log('[WS] Numero maximo de tentativas de reconexao atingido');
            this.updateState('disconnected');
            this.emit('max_reconnect_attempts');
            return;
        }

        // Backoff exponencial
        const delay = Math.min(
            this.reconnectInterval * Math.pow(2, this.reconnectAttempts),
            30000 // Max 30 segundos
        );

        console.log(`[WS] Reconectando em ${delay}ms (tentativa ${this.reconnectAttempts + 1})`);

        this.reconnectTimer = setTimeout(() => {
            this.reconnectAttempts++;
            this.connect();
        }, delay);
    }

    /**
     * Desconectar do servidor
     */
    disconnect() {
        this.isManualClose = true;

        if (this.reconnectTimer) {
            clearTimeout(this.reconnectTimer);
            this.reconnectTimer = null;
        }

        this.stopPing();

        if (this.ws) {
            this.ws.close(1000, 'Desconexao manual');
            this.ws = null;
        }

        this.updateState('disconnected');
    }

    /**
     * Atualizar estado da conexao
     * @param {string} state - Novo estado
     */
    updateState(state) {
        this.state = state;
        this.emit('state_change', state);
    }

    /**
     * Registrar handler para evento
     * @param {string} event - Nome do evento
     * @param {Function} handler - Funcao callback
     * @returns {Function} - Funcao para remover handler
     */
    on(event, handler) {
        if (!this.handlers.has(event)) {
            this.handlers.set(event, new Set());
        }
        this.handlers.get(event).add(handler);

        // Retornar funcao para remover handler
        return () => this.off(event, handler);
    }

    /**
     * Remover handler de evento
     * @param {string} event - Nome do evento
     * @param {Function} handler - Funcao callback
     */
    off(event, handler) {
        if (this.handlers.has(event)) {
            this.handlers.get(event).delete(handler);
        }
    }

    /**
     * Remover todos os handlers de um evento
     * @param {string} event - Nome do evento
     */
    offAll(event) {
        this.handlers.delete(event);
    }

    /**
     * Disparar evento para handlers registrados
     * @param {string} event - Nome do evento
     * @param {any} data - Dados do evento
     */
    emit(event, data) {
        if (this.handlers.has(event)) {
            this.handlers.get(event).forEach(handler => {
                try {
                    handler(data);
                } catch (error) {
                    console.error(`[WS] Erro no handler do evento ${event}:`, error);
                }
            });
        }
    }

    /**
     * Verificar se esta conectado
     * @returns {boolean}
     */
    isConnected() {
        return this.ws?.readyState === WebSocket.OPEN;
    }

    /**
     * Obter estado atual
     * @returns {string}
     */
    getState() {
        return this.state;
    }

    // ==========================================
    // Metodos de subscricao especificos
    // ==========================================

    /**
     * Subscrever a atualizacoes de camera
     * @param {string} cameraId - ID da camera
     */
    subscribeCamera(cameraId) {
        this.send('subscribe', { channel: 'camera', id: cameraId });
    }

    /**
     * Cancelar subscricao de camera
     * @param {string} cameraId - ID da camera
     */
    unsubscribeCamera(cameraId) {
        this.send('unsubscribe', { channel: 'camera', id: cameraId });
    }

    /**
     * Subscrever a eventos do sistema
     */
    subscribeEvents() {
        this.send('subscribe', { channel: 'events' });
    }

    /**
     * Cancelar subscricao de eventos
     */
    unsubscribeEvents() {
        this.send('unsubscribe', { channel: 'events' });
    }

    /**
     * Subscrever a notificacoes
     */
    subscribeNotifications() {
        this.send('subscribe', { channel: 'notifications' });
    }

    /**
     * Cancelar subscricao de notificacoes
     */
    unsubscribeNotifications() {
        this.send('unsubscribe', { channel: 'notifications' });
    }

    /**
     * Subscrever a status das cameras
     */
    subscribeCamerasStatus() {
        this.send('subscribe', { channel: 'cameras_status' });
    }

    /**
     * Cancelar subscricao de status das cameras
     */
    unsubscribeCamerasStatus() {
        this.send('unsubscribe', { channel: 'cameras_status' });
    }
}

// Instancia singleton
export const wsService = new WebSocketService();

export default wsService;
