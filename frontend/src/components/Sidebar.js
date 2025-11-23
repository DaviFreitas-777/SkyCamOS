/**
 * SkyCamOS - Componente Sidebar
 * Menu lateral de navegacao
 */

import { useAuth } from '../hooks/useAuth.js';
import { MENU_ITEMS } from '../utils/constants.js';

/**
 * Web Component do Sidebar
 */
class SkycamSidebar extends HTMLElement {
    constructor() {
        super();
        this.auth = useAuth();
        this.collapsed = false;
        this.currentRoute = window.location.hash.slice(1) || '/dashboard';
    }

    /**
     * Conectado ao DOM
     */
    connectedCallback() {
        this.render();
        this.attachEventListeners();

        // Ouvir mudancas de rota
        window.addEventListener('hashchange', () => {
            this.currentRoute = window.location.hash.slice(1) || '/dashboard';
            this.updateActiveItem();
        });

        // Ouvir toggle do sidebar
        document.addEventListener('toggle-sidebar', () => {
            this.toggleCollapse();
        });
    }

    /**
     * Renderizar componente
     */
    render() {
        const menuItems = this.getFilteredMenuItems();

        this.innerHTML = `
            <aside class="sidebar ${this.collapsed ? 'collapsed' : ''}" id="sidebar">
                <nav class="sidebar-nav">
                    <ul class="sidebar-menu">
                        ${menuItems.map(item => this.renderMenuItem(item)).join('')}
                    </ul>
                </nav>

                <div class="sidebar-footer">
                    <button class="btn btn-ghost sidebar-collapse-btn" id="collapse-btn">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M11 17l-5-5 5-5M18 17l-5-5 5-5"/>
                        </svg>
                        <span class="sidebar-label">Recolher</span>
                    </button>

                    <div class="sidebar-version">
                        <span class="sidebar-label">v1.0.0</span>
                    </div>
                </div>
            </aside>

            <!-- Overlay para mobile -->
            <div class="sidebar-overlay" id="sidebar-overlay"></div>
        `;

        this.addStyles();
    }

    /**
     * Renderizar item do menu
     * @param {Object} item - Dados do item
     * @returns {string} - HTML do item
     */
    renderMenuItem(item) {
        const isActive = this.isActiveRoute(item.route);

        return `
            <li class="sidebar-menu-item">
                <a href="#${item.route}"
                   class="sidebar-menu-link ${isActive ? 'active' : ''}"
                   data-route="${item.route}">
                    ${this.getMenuIcon(item.icon)}
                    <span class="sidebar-label">${item.label}</span>
                </a>
            </li>
        `;
    }

    /**
     * Obter icone do menu
     * @param {string} iconName - Nome do icone
     * @returns {string} - SVG do icone
     */
    getMenuIcon(iconName) {
        const icons = {
            grid: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="3" y="3" width="7" height="7"/>
                <rect x="14" y="3" width="7" height="7"/>
                <rect x="14" y="14" width="7" height="7"/>
                <rect x="3" y="14" width="7" height="7"/>
            </svg>`,
            video: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="2" y="6" width="14" height="12" rx="2" ry="2"/>
                <path d="M22 8l-4 4 4 4V8z"/>
            </svg>`,
            bell: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M18 8A6 6 0 006 8c0 7-3 9-3 9h18s-3-2-3-9"/>
                <path d="M13.73 21a2 2 0 01-3.46 0"/>
            </svg>`,
            settings: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="3"/>
                <path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-2 2 2 2 0 01-2-2v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83 0 2 2 0 010-2.83l.06-.06a1.65 1.65 0 00.33-1.82 1.65 1.65 0 00-1.51-1H3a2 2 0 01-2-2 2 2 0 012-2h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 010-2.83 2 2 0 012.83 0l.06.06a1.65 1.65 0 001.82.33H9a1.65 1.65 0 001-1.51V3a2 2 0 012-2 2 2 0 012 2v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 0 2 2 0 010 2.83l-.06.06a1.65 1.65 0 00-.33 1.82V9a1.65 1.65 0 001.51 1H21a2 2 0 012 2 2 2 0 01-2 2h-.09a1.65 1.65 0 00-1.51 1z"/>
            </svg>`,
            download: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/>
                <polyline points="7 10 12 15 17 10"/>
                <line x1="12" y1="15" x2="12" y2="3"/>
            </svg>`
        };

        return icons[iconName] || icons.grid;
    }

    /**
     * Adicionar estilos especificos do componente
     */
    addStyles() {
        if (document.getElementById('sidebar-styles')) return;

        const styles = document.createElement('style');
        styles.id = 'sidebar-styles';
        styles.textContent = `
            .sidebar {
                position: fixed;
                top: var(--header-height);
                left: 0;
                bottom: 0;
                width: var(--sidebar-width);
                background-color: var(--color-bg-tertiary);
                border-right: 1px solid var(--color-border-secondary);
                display: flex;
                flex-direction: column;
                z-index: var(--z-fixed);
                transition: width var(--transition-normal), transform var(--transition-normal);
            }

            .sidebar.collapsed {
                width: var(--sidebar-collapsed-width);
            }

            .sidebar.collapsed .sidebar-label {
                display: none;
            }

            .sidebar.collapsed .sidebar-collapse-btn svg {
                transform: rotate(180deg);
            }

            .sidebar-nav {
                flex: 1;
                overflow-y: auto;
                padding: var(--spacing-md);
            }

            .sidebar-menu {
                display: flex;
                flex-direction: column;
                gap: var(--spacing-xs);
            }

            .sidebar-menu-link {
                display: flex;
                align-items: center;
                gap: var(--spacing-md);
                padding: var(--spacing-sm) var(--spacing-md);
                color: var(--color-text-secondary);
                border-radius: var(--radius-md);
                text-decoration: none;
                transition: all var(--transition-fast);
            }

            .sidebar-menu-link:hover {
                background-color: var(--color-bg-card);
                color: var(--color-text-primary);
            }

            .sidebar-menu-link.active {
                background-color: var(--color-primary-600);
                color: var(--color-text-primary);
            }

            .sidebar-menu-link svg {
                flex-shrink: 0;
            }

            .sidebar-label {
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            }

            .sidebar-footer {
                padding: var(--spacing-md);
                border-top: 1px solid var(--color-border-secondary);
            }

            .sidebar-collapse-btn {
                width: 100%;
                justify-content: flex-start;
            }

            .sidebar-collapse-btn svg {
                transition: transform var(--transition-normal);
            }

            .sidebar-version {
                margin-top: var(--spacing-sm);
                text-align: center;
                font-size: var(--font-size-xs);
                color: var(--color-text-tertiary);
            }

            .sidebar-overlay {
                display: none;
                position: fixed;
                inset: 0;
                background-color: var(--color-bg-overlay);
                z-index: calc(var(--z-fixed) - 1);
            }

            @media (max-width: 768px) {
                .sidebar {
                    transform: translateX(-100%);
                }

                .sidebar.open {
                    transform: translateX(0);
                }

                .sidebar.open ~ .sidebar-overlay,
                #sidebar.open ~ #sidebar-overlay {
                    display: block;
                }

                .sidebar.collapsed {
                    width: var(--sidebar-width);
                }

                .sidebar.collapsed .sidebar-label {
                    display: inline;
                }
            }
        `;

        document.head.appendChild(styles);
    }

    /**
     * Anexar event listeners
     */
    attachEventListeners() {
        // Collapse button
        this.querySelector('#collapse-btn')?.addEventListener('click', () => {
            this.toggleCollapse();
        });

        // Overlay click (mobile)
        this.querySelector('#sidebar-overlay')?.addEventListener('click', () => {
            this.closeMobile();
        });

        // Menu links
        this.querySelectorAll('.sidebar-menu-link').forEach(link => {
            link.addEventListener('click', () => {
                // Fechar sidebar em mobile
                if (window.innerWidth <= 768) {
                    this.closeMobile();
                }
            });
        });
    }

    /**
     * Filtrar itens do menu baseado em permissoes
     * @returns {Array} - Itens filtrados
     */
    getFilteredMenuItems() {
        return MENU_ITEMS.filter(item => {
            if (!item.permission) return true;
            return this.auth.hasPermission(item.permission);
        });
    }

    /**
     * Verificar se rota esta ativa
     * @param {string} route - Rota a verificar
     * @returns {boolean}
     */
    isActiveRoute(route) {
        const current = this.currentRoute || '/dashboard';
        return current === route || current.startsWith(route + '/');
    }

    /**
     * Atualizar item ativo
     */
    updateActiveItem() {
        this.querySelectorAll('.sidebar-menu-link').forEach(link => {
            const route = link.dataset.route;
            link.classList.toggle('active', this.isActiveRoute(route));
        });
    }

    /**
     * Alternar estado colapsado
     */
    toggleCollapse() {
        const sidebar = this.querySelector('#sidebar');

        if (window.innerWidth <= 768) {
            // Mobile: abrir/fechar
            sidebar?.classList.toggle('open');
        } else {
            // Desktop: expandir/recolher
            this.collapsed = !this.collapsed;
            sidebar?.classList.toggle('collapsed', this.collapsed);

            // Disparar evento para ajustar layout
            document.dispatchEvent(new CustomEvent('sidebar-toggled', {
                detail: { collapsed: this.collapsed }
            }));
        }
    }

    /**
     * Fechar sidebar em mobile
     */
    closeMobile() {
        const sidebar = this.querySelector('#sidebar');
        sidebar?.classList.remove('open');
    }

    /**
     * Abrir sidebar em mobile
     */
    openMobile() {
        const sidebar = this.querySelector('#sidebar');
        sidebar?.classList.add('open');
    }
}

// Registrar Web Component
customElements.define('skycam-sidebar', SkycamSidebar);

export default SkycamSidebar;
