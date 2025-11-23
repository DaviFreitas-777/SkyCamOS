/**
 * SkyCamOS - Servico de Autenticacao
 * Gerenciamento de login, logout e tokens
 */

import { API_BASE_URL, STORAGE_KEYS } from '../utils/constants.js';
import { storageService } from './storage.js';

/**
 * Classe para gerenciar autenticacao
 */
class AuthService {
    constructor() {
        this.token = null;
        this.user = null;
        this.refreshTimer = null;
        this.listeners = new Set();

        // Carregar dados persistidos
        this.loadFromStorage();
    }

    /**
     * Carregar token e usuario do storage
     */
    async loadFromStorage() {
        try {
            this.token = await storageService.get(STORAGE_KEYS.AUTH_TOKEN);
            this.user = await storageService.get(STORAGE_KEYS.USER);

            if (this.token) {
                // Verificar se token ainda e valido
                const isValid = await this.validateToken();
                if (!isValid) {
                    await this.logout();
                } else {
                    // Agendar refresh do token
                    this.scheduleTokenRefresh();
                    this.notifyListeners();
                }
            }
        } catch (error) {
            console.error('[Auth] Erro ao carregar do storage:', error);
        }
    }

    /**
     * Realizar login
     * @param {string} username - Nome de usuario
     * @param {string} password - Senha
     * @returns {Promise<Object>} - Dados do usuario
     */
    async login(username, password) {
        try {
            // OAuth2 usa form-urlencoded
            const formData = new URLSearchParams();
            formData.append('username', username);
            formData.append('password', password);

            const response = await fetch(`${API_BASE_URL}/api/v1/auth/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded'
                },
                body: formData
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Credenciais invalidas');
            }

            const data = await response.json();

            // Salvar token e usuario (backend retorna access_token, nao token)
            this.token = data.access_token;
            this.user = data.user;

            await storageService.set(STORAGE_KEYS.AUTH_TOKEN, this.token);
            await storageService.set(STORAGE_KEYS.USER, this.user);

            // Agendar refresh do token
            this.scheduleTokenRefresh();

            // Notificar listeners
            this.notifyListeners();

            return this.user;
        } catch (error) {
            console.error('[Auth] Erro no login:', error);
            throw error;
        }
    }

    /**
     * Realizar logout
     */
    async logout() {
        // Cancelar refresh timer
        if (this.refreshTimer) {
            clearTimeout(this.refreshTimer);
            this.refreshTimer = null;
        }

        // Tentar invalidar token no servidor
        if (this.token) {
            try {
                await fetch(`${API_BASE_URL}/api/v1/auth/logout`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${this.token}`
                    }
                });
            } catch (error) {
                console.warn('[Auth] Erro ao invalidar token no servidor:', error);
            }
        }

        // Limpar dados locais
        this.token = null;
        this.user = null;

        await storageService.remove(STORAGE_KEYS.AUTH_TOKEN);
        await storageService.remove(STORAGE_KEYS.USER);

        // Notificar listeners
        this.notifyListeners();

        // Redirecionar para login
        window.dispatchEvent(new CustomEvent('auth:logout'));
    }

    /**
     * Renovar token de acesso
     * @returns {Promise<boolean>}
     */
    async refreshToken() {
        if (!this.token) {
            return false;
        }

        try {
            const response = await fetch(`${API_BASE_URL}/api/v1/auth/refresh?refresh_token=${encodeURIComponent(this.token)}`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.token}`
                }
            });

            if (!response.ok) {
                throw new Error('Falha ao renovar token');
            }

            const data = await response.json();
            this.token = data.access_token;

            await storageService.set(STORAGE_KEYS.AUTH_TOKEN, this.token);

            // Reagendar refresh
            this.scheduleTokenRefresh();

            return true;
        } catch (error) {
            console.error('[Auth] Erro ao renovar token:', error);
            await this.logout();
            return false;
        }
    }

    /**
     * Agendar renovacao automatica do token
     */
    scheduleTokenRefresh() {
        if (this.refreshTimer) {
            clearTimeout(this.refreshTimer);
        }

        // Renovar 5 minutos antes de expirar (assumindo token de 1 hora)
        const refreshTime = 55 * 60 * 1000; // 55 minutos

        this.refreshTimer = setTimeout(() => {
            this.refreshToken();
        }, refreshTime);
    }

    /**
     * Validar token atual
     * @returns {Promise<boolean>}
     */
    async validateToken() {
        if (!this.token) {
            return false;
        }

        try {
            // Usar endpoint /me para validar token
            const response = await fetch(`${API_BASE_URL}/api/v1/auth/me`, {
                headers: {
                    'Authorization': `Bearer ${this.token}`
                }
            });

            return response.ok;
        } catch (error) {
            console.error('[Auth] Erro ao validar token:', error);
            return false;
        }
    }

    /**
     * Obter token atual
     * @returns {string|null}
     */
    getToken() {
        return this.token;
    }

    /**
     * Obter usuario atual
     * @returns {Object|null}
     */
    getUser() {
        return this.user;
    }

    /**
     * Verificar se esta autenticado
     * @returns {boolean}
     */
    isAuthenticated() {
        return !!this.token;
    }

    /**
     * Verificar se usuario tem permissao
     * @param {string} permission - Nome da permissao
     * @returns {boolean}
     */
    hasPermission(permission) {
        if (!this.user || !this.user.permissions) {
            return false;
        }

        // Admin tem todas as permissoes
        if (this.user.role === 'admin') {
            return true;
        }

        return this.user.permissions.includes(permission);
    }

    /**
     * Verificar se usuario tem role
     * @param {string} role - Nome do role
     * @returns {boolean}
     */
    hasRole(role) {
        if (!this.user) {
            return false;
        }

        return this.user.role === role;
    }

    /**
     * Registrar listener para mudancas de autenticacao
     * @param {Function} callback - Funcao callback
     * @returns {Function} - Funcao para remover listener
     */
    onAuthChange(callback) {
        this.listeners.add(callback);
        return () => this.listeners.delete(callback);
    }

    /**
     * Notificar listeners sobre mudanca
     */
    notifyListeners() {
        const state = {
            isAuthenticated: this.isAuthenticated(),
            user: this.user
        };

        this.listeners.forEach(callback => {
            try {
                callback(state);
            } catch (error) {
                console.error('[Auth] Erro no listener:', error);
            }
        });
    }

    /**
     * Recuperar senha
     * @param {string} email - Email do usuario
     * @returns {Promise<void>}
     */
    async forgotPassword(email) {
        const response = await fetch(`${API_BASE_URL}/api/v1/auth/forgot-password`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ email })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Erro ao enviar email de recuperacao');
        }
    }

    /**
     * Resetar senha
     * @param {string} token - Token de reset
     * @param {string} password - Nova senha
     * @returns {Promise<void>}
     */
    async resetPassword(token, password) {
        const response = await fetch(`${API_BASE_URL}/api/v1/auth/reset-password`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ token, password })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Erro ao resetar senha');
        }
    }

    /**
     * Alterar senha do usuario logado
     * @param {string} currentPassword - Senha atual
     * @param {string} newPassword - Nova senha
     * @returns {Promise<void>}
     */
    async changePassword(currentPassword, newPassword) {
        const response = await fetch(`${API_BASE_URL}/api/v1/auth/change-password`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${this.token}`
            },
            body: JSON.stringify({
                currentPassword,
                newPassword
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Erro ao alterar senha');
        }
    }

    /**
     * Atualizar dados do usuario em memoria e storage
     * @param {Object} userData - Novos dados do usuario
     */
    async updateUser(userData) {
        this.user = { ...this.user, ...userData };
        await storageService.set(STORAGE_KEYS.USER, this.user);
        this.notifyListeners();
    }
}

// Instancia singleton
export const authService = new AuthService();

export default authService;
