/**
 * SkyCamOS - Cliente HTTP/API
 * Servico para comunicacao com o backend
 */

import { API_BASE_URL, API_TIMEOUT } from '../utils/constants.js';
import { authService } from './auth.js';

/**
 * Classe para gerenciar requisicoes HTTP
 */
class ApiService {
    constructor() {
        this.baseUrl = API_BASE_URL;
        this.timeout = API_TIMEOUT;
        this.abortControllers = new Map();
    }

    /**
     * Obter headers padrao para requisicoes
     * @returns {Headers}
     */
    getHeaders() {
        const headers = new Headers({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        });

        const token = authService.getToken();
        if (token) {
            headers.append('Authorization', `Bearer ${token}`);
        }

        return headers;
    }

    /**
     * Criar controller de abort para requisicao
     * @param {string} requestId - ID unico da requisicao
     * @param {boolean} cancelPrevious - Se deve cancelar requisicao anterior
     * @returns {AbortController}
     */
    createAbortController(requestId, cancelPrevious = false) {
        // Cancelar requisicao anterior com mesmo ID apenas se solicitado
        if (cancelPrevious && this.abortControllers.has(requestId)) {
            this.abortControllers.get(requestId).abort();
        }

        const controller = new AbortController();
        this.abortControllers.set(requestId, controller);
        return controller;
    }

    /**
     * Remover controller de abort
     * @param {string} requestId - ID da requisicao
     */
    removeAbortController(requestId) {
        this.abortControllers.delete(requestId);
    }

    /**
     * Executar requisicao HTTP com tratamento de erros
     * @param {string} endpoint - Endpoint da API
     * @param {Object} options - Opcoes da requisicao
     * @returns {Promise<any>}
     */
    async request(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;
        const requestId = options.requestId || `${options.method || 'GET'}-${endpoint}`;
        const cancelPrevious = options.cancelPrevious || false;
        const controller = this.createAbortController(requestId, cancelPrevious);

        // Timeout
        const timeoutId = setTimeout(() => {
            controller.abort();
        }, options.timeout || this.timeout);

        try {
            const response = await fetch(url, {
                ...options,
                headers: options.headers || this.getHeaders(),
                signal: controller.signal
            });

            clearTimeout(timeoutId);
            this.removeAbortController(requestId);

            // Verificar se resposta nao e ok
            if (!response.ok) {
                const error = await this.handleErrorResponse(response);
                throw error;
            }

            // Verificar se tem conteudo
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                return await response.json();
            }

            return await response.text();
        } catch (error) {
            clearTimeout(timeoutId);
            this.removeAbortController(requestId);

            // Verificar se foi abortado
            if (error.name === 'AbortError') {
                throw new Error('Requisicao cancelada ou timeout');
            }

            // Verificar se e erro de rede
            if (error instanceof TypeError && error.message === 'Failed to fetch') {
                throw new Error('Erro de conexao. Verifique sua internet.');
            }

            throw error;
        }
    }

    /**
     * Tratar resposta de erro da API
     * @param {Response} response - Objeto Response
     * @returns {Error}
     */
    async handleErrorResponse(response) {
        let message = 'Erro desconhecido';
        let data = null;

        try {
            data = await response.json();
            message = data.message || data.error || message;
        } catch {
            message = response.statusText || message;
        }

        // Tratar erros especificos
        switch (response.status) {
            case 401:
                authService.logout();
                message = 'Sessao expirada. Faca login novamente.';
                break;
            case 403:
                message = 'Acesso negado.';
                break;
            case 404:
                message = 'Recurso nao encontrado.';
                break;
            case 422:
                message = data?.errors ? Object.values(data.errors).flat().join(', ') : 'Dados invalidos.';
                break;
            case 429:
                message = 'Muitas requisicoes. Aguarde um momento.';
                break;
            case 500:
                message = 'Erro interno do servidor.';
                break;
        }

        const error = new Error(message);
        error.status = response.status;
        error.data = data;
        return error;
    }

    /**
     * Requisicao GET
     * @param {string} endpoint - Endpoint
     * @param {Object} params - Query params
     * @returns {Promise<any>}
     */
    async get(endpoint, params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const url = queryString ? `${endpoint}?${queryString}` : endpoint;

        return this.request(url, {
            method: 'GET'
        });
    }

    /**
     * Requisicao POST
     * @param {string} endpoint - Endpoint
     * @param {Object} data - Dados a enviar
     * @returns {Promise<any>}
     */
    async post(endpoint, data = {}) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    /**
     * Requisicao PUT
     * @param {string} endpoint - Endpoint
     * @param {Object} data - Dados a enviar
     * @returns {Promise<any>}
     */
    async put(endpoint, data = {}) {
        return this.request(endpoint, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }

    /**
     * Requisicao PATCH
     * @param {string} endpoint - Endpoint
     * @param {Object} data - Dados a enviar
     * @returns {Promise<any>}
     */
    async patch(endpoint, data = {}) {
        return this.request(endpoint, {
            method: 'PATCH',
            body: JSON.stringify(data)
        });
    }

    /**
     * Requisicao DELETE
     * @param {string} endpoint - Endpoint
     * @returns {Promise<any>}
     */
    async delete(endpoint) {
        return this.request(endpoint, {
            method: 'DELETE'
        });
    }

    /**
     * Upload de arquivo
     * @param {string} endpoint - Endpoint
     * @param {FormData} formData - Dados do formulario
     * @param {Function} onProgress - Callback de progresso
     * @returns {Promise<any>}
     */
    async upload(endpoint, formData, onProgress) {
        const url = `${this.baseUrl}${endpoint}`;

        return new Promise((resolve, reject) => {
            const xhr = new XMLHttpRequest();

            xhr.open('POST', url);

            // Headers (sem Content-Type para FormData)
            const token = authService.getToken();
            if (token) {
                xhr.setRequestHeader('Authorization', `Bearer ${token}`);
            }

            // Progresso
            if (onProgress) {
                xhr.upload.addEventListener('progress', (event) => {
                    if (event.lengthComputable) {
                        const percent = Math.round((event.loaded / event.total) * 100);
                        onProgress(percent);
                    }
                });
            }

            // Sucesso
            xhr.addEventListener('load', () => {
                if (xhr.status >= 200 && xhr.status < 300) {
                    try {
                        resolve(JSON.parse(xhr.responseText));
                    } catch {
                        resolve(xhr.responseText);
                    }
                } else {
                    reject(new Error(`Upload falhou: ${xhr.statusText}`));
                }
            });

            // Erro
            xhr.addEventListener('error', () => {
                reject(new Error('Erro de rede no upload'));
            });

            // Timeout
            xhr.timeout = this.timeout * 2;
            xhr.addEventListener('timeout', () => {
                reject(new Error('Upload timeout'));
            });

            xhr.send(formData);
        });
    }

    // ==========================================
    // Endpoints especificos da API
    // ==========================================

    // --- Cameras ---

    /**
     * Listar todas as cameras
     * @returns {Promise<Array>}
     */
    async getCameras() {
        return this.get('/api/v1/cameras');
    }

    /**
     * Obter detalhes de uma camera
     * @param {string} id - ID da camera
     * @returns {Promise<Object>}
     */
    async getCamera(id) {
        return this.get(`/api/v1/cameras/${id}`);
    }

    /**
     * Criar nova camera
     * @param {Object} data - Dados da camera
     * @returns {Promise<Object>}
     */
    async createCamera(data) {
        return this.post('/api/v1/cameras', data);
    }

    /**
     * Atualizar camera
     * @param {string} id - ID da camera
     * @param {Object} data - Dados a atualizar
     * @returns {Promise<Object>}
     */
    async updateCamera(id, data) {
        return this.put(`/api/v1/cameras/${id}`, data);
    }

    /**
     * Remover camera
     * @param {string} id - ID da camera
     * @returns {Promise<void>}
     */
    async deleteCamera(id) {
        return this.delete(`/api/v1/cameras/${id}`);
    }

    /**
     * Obter status das cameras
     * @returns {Promise<Object>}
     */
    async getCamerasStatus() {
        return this.get('/api/v1/cameras/status');
    }

    /**
     * Capturar snapshot de camera
     * @param {string} id - ID da camera
     * @returns {Promise<Blob>}
     */
    async getCameraSnapshot(id) {
        const response = await fetch(`${this.baseUrl}/api/v1/cameras/${id}/snapshot`, {
            headers: this.getHeaders()
        });

        if (!response.ok) {
            throw new Error('Falha ao capturar snapshot');
        }

        return response.blob();
    }

    /**
     * Descobrir cameras ONVIF na rede
     * @returns {Promise<Array>}
     */
    async discoverCameras() {
        return this.post('/api/v1/cameras/discover');
    }

    /**
     * Testar conexao com camera
     * @param {Object} data - Dados de conexao
     * @returns {Promise<Object>}
     */
    async testCameraConnection(data) {
        return this.post('/api/v1/cameras/test', data);
    }

    // --- Gravacoes ---

    /**
     * Listar gravacoes
     * @param {Object} params - Filtros
     * @returns {Promise<Array>}
     */
    async getRecordings(params = {}) {
        return this.get('/api/v1/recordings', params);
    }

    /**
     * Obter gravacao especifica
     * @param {string} id - ID da gravacao
     * @returns {Promise<Object>}
     */
    async getRecording(id) {
        return this.get(`/api/v1/recordings/${id}`);
    }

    /**
     * Deletar gravacao
     * @param {string} id - ID da gravacao
     * @returns {Promise<void>}
     */
    async deleteRecording(id) {
        return this.delete(`/api/v1/recordings/${id}`);
    }

    /**
     * Download de gravacao
     * @param {string} id - ID da gravacao
     * @returns {Promise<string>} - URL de download
     */
    async getRecordingDownloadUrl(id) {
        const token = authService.getToken();
        return `${this.baseUrl}/api/v1/recordings/${id}/download?token=${token}`;
    }

    /**
     * Obter URL de stream de gravacao
     * @param {string} id - ID da gravacao
     * @returns {string} - URL de stream
     */
    getRecordingStreamUrl(id) {
        const token = authService.getToken();
        return `${this.baseUrl}/api/v1/recordings/${id}/stream?token=${token}`;
    }

    // --- Eventos ---

    /**
     * Listar eventos
     * @param {Object} params - Filtros
     * @returns {Promise<Array>}
     */
    async getEvents(params = {}) {
        return this.get('/api/v1/events', params);
    }

    /**
     * Obter evento especifico
     * @param {string} id - ID do evento
     * @returns {Promise<Object>}
     */
    async getEvent(id) {
        return this.get(`/api/v1/events/${id}`);
    }

    /**
     * Marcar evento como lido
     * @param {string} id - ID do evento
     * @returns {Promise<void>}
     */
    async markEventAsRead(id) {
        return this.patch(`/api/v1/events/${id}/read`);
    }

    /**
     * Marcar todos eventos como lidos
     * @returns {Promise<void>}
     */
    async markAllEventsAsRead() {
        return this.post('/api/v1/events/mark-all-read');
    }

    // --- Configuracoes ---

    /**
     * Obter configuracoes do sistema
     * @returns {Promise<Object>}
     */
    async getSettings() {
        return this.get('/api/v1/settings');
    }

    /**
     * Atualizar configuracoes
     * @param {Object} data - Novas configuracoes
     * @returns {Promise<Object>}
     */
    async updateSettings(data) {
        return this.put('/api/v1/settings', data);
    }

    // --- Usuario ---

    /**
     * Obter perfil do usuario
     * @returns {Promise<Object>}
     */
    async getProfile() {
        return this.get('/api/v1/user/profile');
    }

    /**
     * Atualizar perfil do usuario
     * @param {Object} data - Dados do perfil
     * @returns {Promise<Object>}
     */
    async updateProfile(data) {
        return this.put('/api/v1/user/profile', data);
    }

    /**
     * Alterar senha
     * @param {Object} data - Senhas atual e nova
     * @returns {Promise<void>}
     */
    async changePassword(data) {
        return this.post('/api/v1/user/change-password', data);
    }
}

// Instancia singleton
export const apiService = new ApiService();

export default apiService;
