/**
 * SkyCamOS - Servico de Storage
 * Gerenciamento de localStorage e IndexedDB
 */

import { STORAGE_KEYS, DB_NAME, DB_VERSION } from '../utils/constants.js';

/**
 * Classe para gerenciar armazenamento local
 */
class StorageService {
    constructor() {
        this.db = null;
        this.dbReady = false;
        this.dbPromise = this.initIndexedDB();
    }

    /**
     * Inicializar IndexedDB
     * @returns {Promise<IDBDatabase>}
     */
    async initIndexedDB() {
        return new Promise((resolve, reject) => {
            if (!('indexedDB' in window)) {
                console.warn('[Storage] IndexedDB nao suportado, usando localStorage');
                resolve(null);
                return;
            }

            const request = indexedDB.open(DB_NAME, DB_VERSION);

            request.onerror = (event) => {
                console.error('[Storage] Erro ao abrir IndexedDB:', event.target.error);
                // Resolve com null para usar fallback localStorage
                resolve(null);
            };

            request.onsuccess = (event) => {
                this.db = event.target.result;
                this.dbReady = true;
                console.log('[Storage] IndexedDB inicializado');
                resolve(this.db);
            };

            request.onupgradeneeded = (event) => {
                const db = event.target.result;

                // Store para dados gerais
                if (!db.objectStoreNames.contains('keyvalue')) {
                    db.createObjectStore('keyvalue', { keyPath: 'key' });
                }

                // Store para cameras
                if (!db.objectStoreNames.contains('cameras')) {
                    const cameraStore = db.createObjectStore('cameras', { keyPath: 'id' });
                    cameraStore.createIndex('name', 'name', { unique: false });
                    cameraStore.createIndex('status', 'status', { unique: false });
                }

                // Store para eventos
                if (!db.objectStoreNames.contains('events')) {
                    const eventStore = db.createObjectStore('events', { keyPath: 'id' });
                    eventStore.createIndex('cameraId', 'cameraId', { unique: false });
                    eventStore.createIndex('timestamp', 'timestamp', { unique: false });
                    eventStore.createIndex('type', 'type', { unique: false });
                }

                // Store para gravacoes (metadados)
                if (!db.objectStoreNames.contains('recordings')) {
                    const recordingStore = db.createObjectStore('recordings', { keyPath: 'id' });
                    recordingStore.createIndex('cameraId', 'cameraId', { unique: false });
                    recordingStore.createIndex('startTime', 'startTime', { unique: false });
                }

                // Store para configuracoes offline
                if (!db.objectStoreNames.contains('settings')) {
                    db.createObjectStore('settings', { keyPath: 'key' });
                }

                // Store para fila de sincronizacao
                if (!db.objectStoreNames.contains('syncQueue')) {
                    const syncStore = db.createObjectStore('syncQueue', { keyPath: 'id', autoIncrement: true });
                    syncStore.createIndex('timestamp', 'timestamp', { unique: false });
                }

                console.log('[Storage] Estrutura do banco atualizada');
            };
        });
    }

    /**
     * Aguardar DB estar pronto
     * @returns {Promise<IDBDatabase>}
     */
    async waitForDB() {
        if (this.dbReady) {
            return this.db;
        }
        return this.dbPromise;
    }

    // ==========================================
    // Metodos de Key-Value (compativel com localStorage)
    // ==========================================

    /**
     * Salvar valor
     * @param {string} key - Chave
     * @param {any} value - Valor
     * @returns {Promise<void>}
     */
    async set(key, value) {
        // Tentar IndexedDB primeiro
        if (this.db) {
            return this.setIndexedDB(key, value);
        }

        // Fallback para localStorage
        try {
            localStorage.setItem(key, JSON.stringify(value));
        } catch (error) {
            console.error('[Storage] Erro ao salvar no localStorage:', error);
            throw error;
        }
    }

    /**
     * Obter valor
     * @param {string} key - Chave
     * @returns {Promise<any>}
     */
    async get(key) {
        // Tentar IndexedDB primeiro
        if (this.db) {
            return this.getIndexedDB(key);
        }

        // Fallback para localStorage
        try {
            const value = localStorage.getItem(key);
            return value ? JSON.parse(value) : null;
        } catch (error) {
            console.error('[Storage] Erro ao ler do localStorage:', error);
            return null;
        }
    }

    /**
     * Remover valor
     * @param {string} key - Chave
     * @returns {Promise<void>}
     */
    async remove(key) {
        // Tentar IndexedDB primeiro
        if (this.db) {
            return this.removeIndexedDB(key);
        }

        // Fallback para localStorage
        localStorage.removeItem(key);
    }

    /**
     * Limpar todos os dados
     * @returns {Promise<void>}
     */
    async clear() {
        // Limpar IndexedDB
        if (this.db) {
            const transaction = this.db.transaction(['keyvalue'], 'readwrite');
            const store = transaction.objectStore('keyvalue');
            store.clear();
        }

        // Limpar localStorage
        localStorage.clear();
    }

    // ==========================================
    // Metodos IndexedDB internos
    // ==========================================

    /**
     * Salvar no IndexedDB
     * @param {string} key - Chave
     * @param {any} value - Valor
     * @returns {Promise<void>}
     */
    async setIndexedDB(key, value) {
        await this.waitForDB();

        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction(['keyvalue'], 'readwrite');
            const store = transaction.objectStore('keyvalue');
            const request = store.put({ key, value, updatedAt: Date.now() });

            request.onsuccess = () => resolve();
            request.onerror = () => reject(request.error);
        });
    }

    /**
     * Obter do IndexedDB
     * @param {string} key - Chave
     * @returns {Promise<any>}
     */
    async getIndexedDB(key) {
        await this.waitForDB();

        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction(['keyvalue'], 'readonly');
            const store = transaction.objectStore('keyvalue');
            const request = store.get(key);

            request.onsuccess = () => {
                resolve(request.result ? request.result.value : null);
            };
            request.onerror = () => reject(request.error);
        });
    }

    /**
     * Remover do IndexedDB
     * @param {string} key - Chave
     * @returns {Promise<void>}
     */
    async removeIndexedDB(key) {
        await this.waitForDB();

        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction(['keyvalue'], 'readwrite');
            const store = transaction.objectStore('keyvalue');
            const request = store.delete(key);

            request.onsuccess = () => resolve();
            request.onerror = () => reject(request.error);
        });
    }

    // ==========================================
    // Metodos especificos para entidades
    // ==========================================

    /**
     * Salvar cameras no cache
     * @param {Array} cameras - Lista de cameras
     * @returns {Promise<void>}
     */
    async cacheCameras(cameras) {
        if (!this.db) return;

        await this.waitForDB();

        const transaction = this.db.transaction(['cameras'], 'readwrite');
        const store = transaction.objectStore('cameras');

        // Limpar store anterior
        store.clear();

        // Adicionar cameras
        cameras.forEach(camera => {
            store.put({ ...camera, cachedAt: Date.now() });
        });
    }

    /**
     * Obter cameras do cache
     * @returns {Promise<Array>}
     */
    async getCachedCameras() {
        if (!this.db) return [];

        await this.waitForDB();

        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction(['cameras'], 'readonly');
            const store = transaction.objectStore('cameras');
            const request = store.getAll();

            request.onsuccess = () => resolve(request.result || []);
            request.onerror = () => reject(request.error);
        });
    }

    /**
     * Salvar eventos no cache
     * @param {Array} events - Lista de eventos
     * @returns {Promise<void>}
     */
    async cacheEvents(events) {
        if (!this.db) return;

        await this.waitForDB();

        const transaction = this.db.transaction(['events'], 'readwrite');
        const store = transaction.objectStore('events');

        events.forEach(event => {
            store.put({ ...event, cachedAt: Date.now() });
        });
    }

    /**
     * Obter eventos do cache
     * @param {Object} filters - Filtros opcionais
     * @returns {Promise<Array>}
     */
    async getCachedEvents(filters = {}) {
        if (!this.db) return [];

        await this.waitForDB();

        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction(['events'], 'readonly');
            const store = transaction.objectStore('events');

            let request;

            if (filters.cameraId) {
                const index = store.index('cameraId');
                request = index.getAll(filters.cameraId);
            } else {
                request = store.getAll();
            }

            request.onsuccess = () => {
                let results = request.result || [];

                // Aplicar filtros adicionais
                if (filters.type) {
                    results = results.filter(e => e.type === filters.type);
                }

                if (filters.limit) {
                    results = results.slice(0, filters.limit);
                }

                resolve(results);
            };
            request.onerror = () => reject(request.error);
        });
    }

    /**
     * Limpar eventos antigos do cache
     * @param {number} maxAge - Idade maxima em milissegundos
     * @returns {Promise<number>} - Numero de eventos removidos
     */
    async cleanOldEvents(maxAge = 7 * 24 * 60 * 60 * 1000) {
        if (!this.db) return 0;

        await this.waitForDB();

        const cutoffTime = Date.now() - maxAge;
        let deletedCount = 0;

        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction(['events'], 'readwrite');
            const store = transaction.objectStore('events');
            const index = store.index('timestamp');
            const range = IDBKeyRange.upperBound(cutoffTime);
            const request = index.openCursor(range);

            request.onsuccess = (event) => {
                const cursor = event.target.result;
                if (cursor) {
                    store.delete(cursor.primaryKey);
                    deletedCount++;
                    cursor.continue();
                }
            };

            transaction.oncomplete = () => resolve(deletedCount);
            transaction.onerror = () => reject(transaction.error);
        });
    }

    // ==========================================
    // Fila de sincronizacao offline
    // ==========================================

    /**
     * Adicionar item a fila de sincronizacao
     * @param {Object} item - Item a sincronizar
     * @returns {Promise<number>} - ID do item
     */
    async addToSyncQueue(item) {
        if (!this.db) return null;

        await this.waitForDB();

        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction(['syncQueue'], 'readwrite');
            const store = transaction.objectStore('syncQueue');
            const request = store.add({
                ...item,
                timestamp: Date.now(),
                retries: 0
            });

            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    /**
     * Obter itens da fila de sincronizacao
     * @returns {Promise<Array>}
     */
    async getSyncQueue() {
        if (!this.db) return [];

        await this.waitForDB();

        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction(['syncQueue'], 'readonly');
            const store = transaction.objectStore('syncQueue');
            const request = store.getAll();

            request.onsuccess = () => resolve(request.result || []);
            request.onerror = () => reject(request.error);
        });
    }

    /**
     * Remover item da fila de sincronizacao
     * @param {number} id - ID do item
     * @returns {Promise<void>}
     */
    async removeFromSyncQueue(id) {
        if (!this.db) return;

        await this.waitForDB();

        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction(['syncQueue'], 'readwrite');
            const store = transaction.objectStore('syncQueue');
            const request = store.delete(id);

            request.onsuccess = () => resolve();
            request.onerror = () => reject(request.error);
        });
    }

    /**
     * Limpar fila de sincronizacao
     * @returns {Promise<void>}
     */
    async clearSyncQueue() {
        if (!this.db) return;

        await this.waitForDB();

        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction(['syncQueue'], 'readwrite');
            const store = transaction.objectStore('syncQueue');
            const request = store.clear();

            request.onsuccess = () => resolve();
            request.onerror = () => reject(request.error);
        });
    }

    /**
     * Obter tamanho estimado do storage
     * @returns {Promise<Object>}
     */
    async getStorageEstimate() {
        if ('storage' in navigator && 'estimate' in navigator.storage) {
            const estimate = await navigator.storage.estimate();
            return {
                usage: estimate.usage,
                quota: estimate.quota,
                usagePercent: ((estimate.usage / estimate.quota) * 100).toFixed(2)
            };
        }

        return { usage: 0, quota: 0, usagePercent: 0 };
    }
}

// Instancia singleton
export const storageService = new StorageService();

export default storageService;
