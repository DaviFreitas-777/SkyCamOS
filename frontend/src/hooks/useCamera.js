/**
 * SkyCamOS - Hook useCamera
 * Gerenciamento de estado e operacoes de cameras
 */

import { apiService } from '../services/api.js';
import { wsService } from '../services/websocket.js';
import { storageService } from '../services/storage.js';
import { CAMERA_STATUS } from '../utils/constants.js';

/**
 * Classe para gerenciar cameras
 */
class CameraManager {
    constructor() {
        this.cameras = [];
        this.selectedCamera = null;
        this.loading = false;
        this.error = null;
        this.listeners = new Set();

        // Bind de metodos
        this.handleCameraUpdate = this.handleCameraUpdate.bind(this);
        this.handleCameraStatus = this.handleCameraStatus.bind(this);

        // Inicializar listeners de WebSocket
        this.initWebSocketListeners();
    }

    /**
     * Inicializar listeners de WebSocket
     */
    initWebSocketListeners() {
        wsService.on('camera_update', this.handleCameraUpdate);
        wsService.on('camera_status', this.handleCameraStatus);
        wsService.on('connected', () => {
            wsService.subscribeCamerasStatus();
        });
    }

    /**
     * Handler para atualizacao de camera via WebSocket
     * @param {Object} data - Dados da camera
     */
    handleCameraUpdate(data) {
        const index = this.cameras.findIndex(c => c.id === data.id);

        if (index !== -1) {
            this.cameras[index] = { ...this.cameras[index], ...data };
            this.notify();
        }
    }

    /**
     * Handler para status de camera via WebSocket
     * @param {Object} data - Dados de status
     */
    handleCameraStatus(data) {
        const index = this.cameras.findIndex(c => c.id === data.cameraId);

        if (index !== -1) {
            this.cameras[index].status = data.status;
            this.cameras[index].lastSeen = data.timestamp;
            this.notify();
        }
    }

    /**
     * Carregar lista de cameras
     * @param {boolean} forceRefresh - Forcar atualizacao do servidor
     * @returns {Promise<Array>}
     */
    async loadCameras(forceRefresh = false) {
        this.loading = true;
        this.error = null;
        this.notify();

        try {
            // Tentar cache primeiro se nao for refresh forcado
            if (!forceRefresh) {
                const cached = await storageService.getCachedCameras();
                if (cached && cached.length > 0) {
                    this.cameras = cached;
                    this.notify();
                }
            }

            // Buscar do servidor
            const cameras = await apiService.getCameras();
            this.cameras = Array.isArray(cameras) ? cameras : [];

            // Salvar no cache
            await storageService.cacheCameras(this.cameras);

            this.loading = false;
            this.notify();

            return this.cameras;
        } catch (error) {
            console.error('[Camera] Erro ao carregar cameras:', error);
            this.error = error.message;
            this.loading = false;
            this.notify();

            // Usar cache em caso de erro
            const cached = await storageService.getCachedCameras();
            if (cached && cached.length > 0) {
                this.cameras = cached;
                this.notify();
            }

            throw error;
        }
    }

    /**
     * Obter camera por ID
     * @param {string} id - ID da camera
     * @returns {Promise<Object>}
     */
    async getCamera(id) {
        // Verificar cache local primeiro
        let camera = this.cameras.find(c => c.id === id);

        if (!camera) {
            try {
                camera = await apiService.getCamera(id);
            } catch (error) {
                console.error('[Camera] Erro ao obter camera:', error);
                throw error;
            }
        }

        return camera;
    }

    /**
     * Criar nova camera
     * @param {Object} data - Dados da camera
     * @returns {Promise<Object>}
     */
    async createCamera(data) {
        try {
            const camera = await apiService.createCamera(data);
            this.cameras.push(camera);
            await storageService.cacheCameras(this.cameras);
            this.notify();
            return camera;
        } catch (error) {
            console.error('[Camera] Erro ao criar camera:', error);
            throw error;
        }
    }

    /**
     * Atualizar camera
     * @param {string} id - ID da camera
     * @param {Object} data - Dados a atualizar
     * @returns {Promise<Object>}
     */
    async updateCamera(id, data) {
        try {
            const camera = await apiService.updateCamera(id, data);
            const index = this.cameras.findIndex(c => c.id === id);

            if (index !== -1) {
                this.cameras[index] = camera;
                await storageService.cacheCameras(this.cameras);
                this.notify();
            }

            return camera;
        } catch (error) {
            console.error('[Camera] Erro ao atualizar camera:', error);
            throw error;
        }
    }

    /**
     * Remover camera
     * @param {string} id - ID da camera
     * @returns {Promise<void>}
     */
    async deleteCamera(id) {
        try {
            await apiService.deleteCamera(id);
            this.cameras = this.cameras.filter(c => c.id !== id);
            await storageService.cacheCameras(this.cameras);

            if (this.selectedCamera?.id === id) {
                this.selectedCamera = null;
            }

            this.notify();
        } catch (error) {
            console.error('[Camera] Erro ao remover camera:', error);
            throw error;
        }
    }

    /**
     * Selecionar camera
     * @param {string|Object} camera - ID ou objeto da camera
     */
    async selectCamera(camera) {
        if (typeof camera === 'string') {
            this.selectedCamera = await this.getCamera(camera);
        } else {
            this.selectedCamera = camera;
        }

        // Subscrever para atualizacoes desta camera
        if (this.selectedCamera) {
            wsService.subscribeCamera(this.selectedCamera.id);
        }

        this.notify();
    }

    /**
     * Deselecionar camera
     */
    deselectCamera() {
        if (this.selectedCamera) {
            wsService.unsubscribeCamera(this.selectedCamera.id);
        }
        this.selectedCamera = null;
        this.notify();
    }

    /**
     * Obter URL de stream da camera
     * @param {string} id - ID da camera
     * @param {string} quality - Qualidade do stream
     * @returns {string}
     */
    getStreamUrl(id, quality = 'auto') {
        const camera = this.cameras.find(c => c.id === id);
        if (!camera) return '';

        // Construir URL baseado no tipo de stream
        if (camera.streamType === 'hls') {
            return `${apiService.baseUrl}/api/cameras/${id}/stream/hls/playlist.m3u8?quality=${quality}`;
        }

        if (camera.streamType === 'webrtc') {
            return `${apiService.baseUrl}/api/cameras/${id}/stream/webrtc`;
        }

        // MJPEG fallback
        return `${apiService.baseUrl}/api/cameras/${id}/stream/mjpeg`;
    }

    /**
     * Capturar snapshot
     * @param {string} id - ID da camera
     * @returns {Promise<string>} - URL do blob
     */
    async captureSnapshot(id) {
        try {
            const blob = await apiService.getCameraSnapshot(id);
            return URL.createObjectURL(blob);
        } catch (error) {
            console.error('[Camera] Erro ao capturar snapshot:', error);
            throw error;
        }
    }

    /**
     * Obter cameras online
     * @returns {Array}
     */
    getOnlineCameras() {
        return this.cameras.filter(c =>
            c.status === CAMERA_STATUS.ONLINE ||
            c.status === CAMERA_STATUS.RECORDING
        );
    }

    /**
     * Obter cameras offline
     * @returns {Array}
     */
    getOfflineCameras() {
        return this.cameras.filter(c =>
            c.status === CAMERA_STATUS.OFFLINE ||
            c.status === CAMERA_STATUS.ERROR
        );
    }

    /**
     * Obter cameras por grupo
     * @param {string} group - Nome do grupo
     * @returns {Array}
     */
    getCamerasByGroup(group) {
        return this.cameras.filter(c => c.group === group);
    }

    /**
     * Obter grupos de cameras
     * @returns {Array}
     */
    getGroups() {
        const groups = new Set(this.cameras.map(c => c.group).filter(Boolean));
        return Array.from(groups);
    }

    /**
     * Descobrir cameras ONVIF na rede
     * @returns {Promise<Array>}
     */
    async discoverCameras() {
        try {
            const discovered = await apiService.discoverCameras();
            return discovered || [];
        } catch (error) {
            console.error('[Camera] Erro na descoberta:', error);
            throw error;
        }
    }

    /**
     * Testar conexao com camera
     * @param {Object} data - Dados de conexao
     * @returns {Promise<Object>}
     */
    async testConnection(data) {
        try {
            return await apiService.testCameraConnection(data);
        } catch (error) {
            console.error('[Camera] Erro ao testar conexao:', error);
            throw error;
        }
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
     * Notificar listeners sobre mudancas
     */
    notify() {
        const state = this.getState();
        this.listeners.forEach(callback => {
            try {
                callback(state);
            } catch (error) {
                console.error('[Camera] Erro no listener:', error);
            }
        });
    }

    /**
     * Obter estado atual
     * @returns {Object}
     */
    getState() {
        return {
            cameras: [...this.cameras],
            selectedCamera: this.selectedCamera,
            loading: this.loading,
            error: this.error,
            onlineCount: this.getOnlineCameras().length,
            offlineCount: this.getOfflineCameras().length,
            totalCount: this.cameras.length
        };
    }

    /**
     * Limpar estado
     */
    reset() {
        this.cameras = [];
        this.selectedCamera = null;
        this.loading = false;
        this.error = null;
        this.notify();
    }
}

// Instancia singleton
export const cameraManager = new CameraManager();

/**
 * Hook para usar em componentes
 * @returns {Object} - Estado e metodos do camera manager
 */
export function useCamera() {
    return {
        // Estado
        get cameras() { return cameraManager.cameras; },
        get selectedCamera() { return cameraManager.selectedCamera; },
        get loading() { return cameraManager.loading; },
        get error() { return cameraManager.error; },

        // Metodos
        loadCameras: cameraManager.loadCameras.bind(cameraManager),
        getCamera: cameraManager.getCamera.bind(cameraManager),
        createCamera: cameraManager.createCamera.bind(cameraManager),
        updateCamera: cameraManager.updateCamera.bind(cameraManager),
        deleteCamera: cameraManager.deleteCamera.bind(cameraManager),
        selectCamera: cameraManager.selectCamera.bind(cameraManager),
        deselectCamera: cameraManager.deselectCamera.bind(cameraManager),
        getStreamUrl: cameraManager.getStreamUrl.bind(cameraManager),
        captureSnapshot: cameraManager.captureSnapshot.bind(cameraManager),
        getOnlineCameras: cameraManager.getOnlineCameras.bind(cameraManager),
        getOfflineCameras: cameraManager.getOfflineCameras.bind(cameraManager),
        getCamerasByGroup: cameraManager.getCamerasByGroup.bind(cameraManager),
        getGroups: cameraManager.getGroups.bind(cameraManager),
        discoverCameras: cameraManager.discoverCameras.bind(cameraManager),
        testConnection: cameraManager.testConnection.bind(cameraManager),
        subscribe: cameraManager.subscribe.bind(cameraManager),
        getState: cameraManager.getState.bind(cameraManager),
        reset: cameraManager.reset.bind(cameraManager)
    };
}

export default useCamera;
