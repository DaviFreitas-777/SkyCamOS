/**
 * SkyCamOS - Componente Header
 * Cabecalho principal da aplicacao
 */

import { useAuth } from '../hooks/useAuth.js';
import { useNotifications } from '../hooks/useNotifications.js';
import { getInitials, stringToColor } from '../utils/helpers.js';

/**
 * Web Component do Header
 */
class SkycamHeader extends HTMLElement {
    constructor() {
        super();
        this.auth = useAuth();
        this.notifications = useNotifications();
        this.unsubscribeAuth = null;
    }

    /**
     * Conectado ao DOM
     */
    connectedCallback() {
        this.render();
        this.attachEventListeners();

        // Subscrever para mudancas de autenticacao
        this.unsubscribeAuth = this.auth.subscribe((state) => {
            this.updateUserInfo(state.user);
        });
    }

    /**
     * Desconectado do DOM
     */
    disconnectedCallback() {
        if (this.unsubscribeAuth) {
            this.unsubscribeAuth();
        }
    }

    /**
     * Renderizar componente
     */
    render() {
        const user = this.auth.getUser();

        this.innerHTML = `
            <header class="header">
                <div class="header-left">
                    <button class="btn btn-icon header-menu-toggle" id="menu-toggle" aria-label="Menu">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M3 12h18M3 6h18M3 18h18"/>
                        </svg>
                    </button>
                    <a href="#/" class="header-logo">
                        <svg viewBox="0 0 100 100" class="header-logo-icon">
                            <circle cx="50" cy="50" r="45" fill="none" stroke="currentColor" stroke-width="2"/>
                            <circle cx="50" cy="50" r="20" fill="currentColor"/>
                        </svg>
                        <span class="header-logo-text">SkyCamOS</span>
                    </a>
                </div>

                <div class="header-center">
                    <div class="header-search">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <circle cx="11" cy="11" r="8"/>
                            <path d="M21 21l-4.35-4.35"/>
                        </svg>
                        <input type="search"
                               class="header-search-input"
                               placeholder="Buscar cameras, eventos..."
                               id="global-search">
                    </div>
                </div>

                <div class="header-right">
                    <!-- Indicador de conexao -->
                    <div class="header-connection-status" id="connection-status" title="Status da conexao">
                        <span class="status-dot online"></span>
                    </div>

                    <!-- Notificacoes -->
                    <skycam-notification-bell></skycam-notification-bell>

                    <!-- Fullscreen -->
                    <button class="btn btn-icon header-fullscreen" id="fullscreen-toggle" aria-label="Tela cheia">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" id="fullscreen-icon">
                            <path d="M8 3H5a2 2 0 00-2 2v3m18 0V5a2 2 0 00-2-2h-3m0 18h3a2 2 0 002-2v-3M3 16v3a2 2 0 002 2h3"/>
                        </svg>
                    </button>

                    <!-- Menu do usuario -->
                    <div class="dropdown header-user-menu" id="user-menu">
                        <button class="btn header-user-button" aria-label="Menu do usuario">
                            <div class="avatar avatar-sm" id="user-avatar" style="background-color: ${user ? stringToColor(user.name || user.username) : 'var(--color-primary-600)'}">
                                ${user ? getInitials(user.name || user.username) : 'U'}
                            </div>
                            <span class="header-user-name" id="user-name">${user?.name || user?.username || 'Usuario'}</span>
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M6 9l6 6 6-6"/>
                            </svg>
                        </button>
                        <div class="dropdown-menu">
                            <a href="#/settings/profile" class="dropdown-item">
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/>
                                    <circle cx="12" cy="7" r="4"/>
                                </svg>
                                Meu Perfil
                            </a>
                            <a href="#/settings" class="dropdown-item">
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <circle cx="12" cy="12" r="3"/>
                                    <path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-2 2 2 2 0 01-2-2v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83 0 2 2 0 010-2.83l.06-.06a1.65 1.65 0 00.33-1.82 1.65 1.65 0 00-1.51-1H3a2 2 0 01-2-2 2 2 0 012-2h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 010-2.83 2 2 0 012.83 0l.06.06a1.65 1.65 0 001.82.33H9a1.65 1.65 0 001-1.51V3a2 2 0 012-2 2 2 0 012 2v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 0 2 2 0 010 2.83l-.06.06a1.65 1.65 0 00-.33 1.82V9a1.65 1.65 0 001.51 1H21a2 2 0 012 2 2 2 0 01-2 2h-.09a1.65 1.65 0 00-1.51 1z"/>
                                </svg>
                                Configuracoes
                            </a>
                            <div class="dropdown-divider"></div>
                            <button class="dropdown-item" id="logout-btn">
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4"/>
                                    <polyline points="16 17 21 12 16 7"/>
                                    <line x1="21" y1="12" x2="9" y2="12"/>
                                </svg>
                                Sair
                            </button>
                        </div>
                    </div>
                </div>
            </header>
        `;

        this.addStyles();
    }

    /**
     * Adicionar estilos especificos do componente
     */
    addStyles() {
        if (document.getElementById('header-styles')) return;

        const styles = document.createElement('style');
        styles.id = 'header-styles';
        styles.textContent = `
            .header {
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                height: var(--header-height);
                background-color: var(--color-bg-secondary);
                border-bottom: 1px solid var(--color-border-secondary);
                display: flex;
                align-items: center;
                justify-content: space-between;
                padding: 0 var(--spacing-md);
                z-index: var(--z-fixed);
            }

            .header-left,
            .header-right {
                display: flex;
                align-items: center;
                gap: var(--spacing-md);
            }

            .header-center {
                flex: 1;
                max-width: 500px;
                margin: 0 var(--spacing-lg);
            }

            .header-menu-toggle {
                display: none;
            }

            .header-logo {
                display: flex;
                align-items: center;
                gap: var(--spacing-sm);
                color: var(--color-text-primary);
                text-decoration: none;
            }

            .header-logo-icon {
                width: 32px;
                height: 32px;
                color: var(--color-primary-500);
            }

            .header-logo-text {
                font-size: var(--font-size-lg);
                font-weight: var(--font-weight-bold);
            }

            .header-search {
                position: relative;
                width: 100%;
            }

            .header-search svg {
                position: absolute;
                left: var(--spacing-sm);
                top: 50%;
                transform: translateY(-50%);
                color: var(--color-text-tertiary);
            }

            .header-search-input {
                width: 100%;
                padding: var(--spacing-sm) var(--spacing-sm) var(--spacing-sm) 40px;
                background-color: var(--color-bg-card);
                border: 1px solid var(--color-border-primary);
                border-radius: var(--radius-full);
                color: var(--color-text-primary);
                transition: all var(--transition-fast);
            }

            .header-search-input:focus {
                border-color: var(--color-primary-500);
                box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.2);
            }

            .header-connection-status {
                display: flex;
                align-items: center;
                padding: var(--spacing-xs);
            }

            .header-user-button {
                display: flex;
                align-items: center;
                gap: var(--spacing-sm);
                padding: var(--spacing-xs) var(--spacing-sm);
                background: none;
            }

            .header-user-name {
                font-size: var(--font-size-sm);
                color: var(--color-text-secondary);
            }

            @media (max-width: 768px) {
                .header-menu-toggle {
                    display: flex;
                }

                .header-center {
                    display: none;
                }

                .header-logo-text,
                .header-user-name {
                    display: none;
                }

                .header-fullscreen {
                    display: none;
                }
            }

            @media (max-width: 480px) {
                .header {
                    padding: 0 var(--spacing-sm);
                }

                .header-left,
                .header-right {
                    gap: var(--spacing-xs);
                }

                .header-logo-icon {
                    width: 24px;
                    height: 24px;
                }

                .header-user-button {
                    padding: var(--spacing-xs);
                }

                .avatar-sm {
                    width: 28px;
                    height: 28px;
                }
            }
        `;

        document.head.appendChild(styles);
    }

    /**
     * Anexar event listeners
     */
    attachEventListeners() {
        // Menu toggle
        this.querySelector('#menu-toggle')?.addEventListener('click', () => {
            document.dispatchEvent(new CustomEvent('toggle-sidebar'));
        });

        // User menu dropdown
        const userMenu = this.querySelector('#user-menu');
        userMenu?.addEventListener('click', (e) => {
            if (e.target.closest('.header-user-button')) {
                userMenu.classList.toggle('active');
            }
        });

        // Fechar dropdown ao clicar fora
        document.addEventListener('click', (e) => {
            if (!userMenu?.contains(e.target)) {
                userMenu?.classList.remove('active');
            }
        });

        // Logout
        this.querySelector('#logout-btn')?.addEventListener('click', async () => {
            await this.auth.logout();
            window.location.hash = '#/login';
        });

        // Fullscreen toggle
        this.querySelector('#fullscreen-toggle')?.addEventListener('click', () => {
            this.toggleFullscreen();
        });

        // Busca global
        this.querySelector('#global-search')?.addEventListener('input', (e) => {
            const query = e.target.value;
            if (query.length >= 3) {
                document.dispatchEvent(new CustomEvent('global-search', { detail: query }));
            }
        });
    }

    /**
     * Alternar modo fullscreen
     */
    toggleFullscreen() {
        const icon = this.querySelector('#fullscreen-icon');

        if (!document.fullscreenElement) {
            document.documentElement.requestFullscreen();
            if (icon) {
                icon.innerHTML = `
                    <path d="M8 3v3a2 2 0 01-2 2H3m18 0h-3a2 2 0 01-2-2V3m0 18v-3a2 2 0 012-2h3M3 16h3a2 2 0 012 2v3"/>
                `;
            }
        } else {
            document.exitFullscreen();
            if (icon) {
                icon.innerHTML = `
                    <path d="M8 3H5a2 2 0 00-2 2v3m18 0V5a2 2 0 00-2-2h-3m0 18h3a2 2 0 002-2v-3M3 16v3a2 2 0 002 2h3"/>
                `;
            }
        }
    }

    /**
     * Atualizar informacoes do usuario
     * @param {Object} user - Dados do usuario
     */
    updateUserInfo(user) {
        const avatar = this.querySelector('#user-avatar');
        const name = this.querySelector('#user-name');

        if (user) {
            if (avatar) {
                avatar.textContent = getInitials(user.name || user.username);
                avatar.style.backgroundColor = stringToColor(user.name || user.username);
            }
            if (name) {
                name.textContent = user.name || user.username;
            }
        }
    }

    /**
     * Atualizar status de conexao
     * @param {boolean} connected - Esta conectado
     */
    updateConnectionStatus(connected) {
        const dot = this.querySelector('#connection-status .status-dot');
        if (dot) {
            dot.classList.toggle('online', connected);
            dot.classList.toggle('offline', !connected);
        }
    }
}

// Registrar Web Component
customElements.define('skycam-header', SkycamHeader);

export default SkycamHeader;
