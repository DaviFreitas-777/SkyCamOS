/**
 * SkyCamOS - Hook useAuth
 * Interface para gerenciamento de autenticacao
 */

import { authService } from '../services/auth.js';

/**
 * Classe para gerenciar estado de autenticacao
 */
class AuthManager {
    constructor() {
        this.listeners = new Set();
        this.initialized = false;

        // Escutar mudancas do authService
        authService.onAuthChange((state) => {
            this.notify(state);
        });
    }

    /**
     * Inicializar verificacao de autenticacao
     * @returns {Promise<boolean>}
     */
    async init() {
        if (this.initialized) {
            return authService.isAuthenticated();
        }

        await authService.loadFromStorage();
        this.initialized = true;
        return authService.isAuthenticated();
    }

    /**
     * Realizar login
     * @param {string} username - Nome de usuario
     * @param {string} password - Senha
     * @returns {Promise<Object>}
     */
    async login(username, password) {
        return authService.login(username, password);
    }

    /**
     * Realizar logout
     */
    async logout() {
        await authService.logout();
    }

    /**
     * Obter token atual
     * @returns {string|null}
     */
    getToken() {
        return authService.getToken();
    }

    /**
     * Obter usuario atual
     * @returns {Object|null}
     */
    getUser() {
        return authService.getUser();
    }

    /**
     * Verificar se esta autenticado
     * @returns {boolean}
     */
    isAuthenticated() {
        return authService.isAuthenticated();
    }

    /**
     * Verificar se usuario tem permissao
     * @param {string} permission - Nome da permissao
     * @returns {boolean}
     */
    hasPermission(permission) {
        return authService.hasPermission(permission);
    }

    /**
     * Verificar se usuario tem role
     * @param {string} role - Nome do role
     * @returns {boolean}
     */
    hasRole(role) {
        return authService.hasRole(role);
    }

    /**
     * Verificar se usuario e admin
     * @returns {boolean}
     */
    isAdmin() {
        return authService.hasRole('admin');
    }

    /**
     * Atualizar perfil do usuario
     * @param {Object} data - Dados do perfil
     * @returns {Promise<Object>}
     */
    async updateProfile(data) {
        const updated = await authService.updateUser(data);
        return updated;
    }

    /**
     * Alterar senha
     * @param {string} currentPassword - Senha atual
     * @param {string} newPassword - Nova senha
     * @returns {Promise<void>}
     */
    async changePassword(currentPassword, newPassword) {
        return authService.changePassword(currentPassword, newPassword);
    }

    /**
     * Recuperar senha
     * @param {string} email - Email
     * @returns {Promise<void>}
     */
    async forgotPassword(email) {
        return authService.forgotPassword(email);
    }

    /**
     * Resetar senha
     * @param {string} token - Token de reset
     * @param {string} password - Nova senha
     * @returns {Promise<void>}
     */
    async resetPassword(token, password) {
        return authService.resetPassword(token, password);
    }

    /**
     * Registrar listener para mudancas
     * @param {Function} callback - Funcao callback
     * @returns {Function} - Funcao para remover listener
     */
    subscribe(callback) {
        this.listeners.add(callback);

        // Chamar imediatamente com estado atual
        callback(this.getState());

        return () => this.listeners.delete(callback);
    }

    /**
     * Notificar listeners sobre mudancas
     * @param {Object} state - Estado atual
     */
    notify(state) {
        this.listeners.forEach(callback => {
            try {
                callback(state || this.getState());
            } catch (error) {
                console.error('[Auth Manager] Erro no listener:', error);
            }
        });
    }

    /**
     * Obter estado atual
     * @returns {Object}
     */
    getState() {
        return {
            isAuthenticated: this.isAuthenticated(),
            user: this.getUser(),
            isAdmin: this.isAdmin()
        };
    }
}

// Instancia singleton
export const authManager = new AuthManager();

/**
 * Hook para usar em componentes
 * @returns {Object} - Estado e metodos do auth manager
 */
export function useAuth() {
    return {
        // Estado
        get isAuthenticated() { return authManager.isAuthenticated(); },
        get user() { return authManager.getUser(); },
        get isAdmin() { return authManager.isAdmin(); },

        // Metodos
        init: authManager.init.bind(authManager),
        login: authManager.login.bind(authManager),
        logout: authManager.logout.bind(authManager),
        getToken: authManager.getToken.bind(authManager),
        getUser: authManager.getUser.bind(authManager),
        hasPermission: authManager.hasPermission.bind(authManager),
        hasRole: authManager.hasRole.bind(authManager),
        updateProfile: authManager.updateProfile.bind(authManager),
        changePassword: authManager.changePassword.bind(authManager),
        forgotPassword: authManager.forgotPassword.bind(authManager),
        resetPassword: authManager.resetPassword.bind(authManager),
        subscribe: authManager.subscribe.bind(authManager),
        getState: authManager.getState.bind(authManager)
    };
}

export default useAuth;
