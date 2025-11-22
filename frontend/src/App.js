/**
 * SkyCamOS - App Principal
 * Componente raiz da aplicacao com roteamento
 */

// Importar componentes
import './components/Header.js';
import './components/Sidebar.js';
import './components/NotificationBell.js';

// Importar paginas
import './pages/Dashboard.js';
import './pages/Recordings.js';
import './pages/Events.js';
import './pages/Settings.js';
import './pages/Login.js';

// Importar servicos
import { useAuth } from './hooks/useAuth.js';
import { useWebSocket } from './hooks/useWebSocket.js';
import { useNotifications } from './hooks/useNotifications.js';

/**
 * Classe principal da aplicacao
 */
class SkyCamApp {
    constructor() {
        this.auth = useAuth();
        this.ws = useWebSocket();
        this.notifications = useNotifications();
        this.currentRoute = '';
        this.sidebarCollapsed = false;

        // Rotas protegidas
        this.protectedRoutes = ['/dashboard', '/recordings', '/events', '/settings'];

        // Rotas publicas
        this.publicRoutes = ['/login'];
    }

    /**
     * Inicializar aplicacao
     */
    async init() {
        console.log('[App] Inicializando SkyCamOS...');

        // Verificar autenticacao
        const isAuthenticated = this.auth.isAuthenticated;

        // Configurar roteamento
        this.setupRouter();

        // Renderizar app
        this.render();

        // Ocultar loading inicial
        this.hideLoadingScreen();

        // Se autenticado, conectar WebSocket
        if (isAuthenticated) {
            await this.ws.connect();
        }

        // Subscrever a mudancas de autenticacao
        this.auth.subscribe((state) => {
            this.handleAuthChange(state);
        });

        // Configurar event listeners globais
        this.setupGlobalListeners();

        console.log('[App] SkyCamOS inicializado com sucesso');
    }

    /**
     * Configurar roteador hash-based
     */
    setupRouter() {
        // Navegacao inicial
        this.navigate(window.location.hash.slice(1) || '/dashboard');

        // Ouvir mudancas de hash
        window.addEventListener('hashchange', () => {
            const route = window.location.hash.slice(1) || '/dashboard';
            this.navigate(route);
        });
    }

    /**
     * Navegar para rota
     * @param {string} route - Rota destino
     */
    navigate(route) {
        const path = route.split('?')[0];

        // Verificar autenticacao para rotas protegidas
        if (this.protectedRoutes.some(r => path.startsWith(r)) && !this.auth.isAuthenticated) {
            window.location.hash = '#/login';
            return;
        }

        // Redirecionar se autenticado tentando acessar login
        if (path === '/login' && this.auth.isAuthenticated) {
            window.location.hash = '#/dashboard';
            return;
        }

        this.currentRoute = route;
        this.renderPage();
    }

    /**
     * Renderizar estrutura principal do app
     */
    render() {
        const app = document.getElementById('app');

        // Se na pagina de login, renderizar apenas login
        if (this.currentRoute.startsWith('/login') || !this.auth.isAuthenticated) {
            app.innerHTML = `<page-login></page-login>`;
            return;
        }

        // Renderizar layout completo
        app.innerHTML = `
            <div class="app-layout">
                <skycam-header></skycam-header>
                <skycam-sidebar></skycam-sidebar>
                <main class="app-main ${this.sidebarCollapsed ? 'sidebar-collapsed' : ''}" id="main-content">
                    <div class="app-content" id="page-container">
                        <!-- Conteudo da pagina sera renderizado aqui -->
                    </div>
                </main>
            </div>
        `;

        this.renderPage();
    }

    /**
     * Renderizar pagina atual
     */
    renderPage() {
        const container = document.getElementById('page-container');
        if (!container) {
            // Se nao existe container, provavelmente esta na tela de login
            return;
        }

        const path = this.currentRoute.split('?')[0];

        // Mapear rota para componente de pagina
        let pageComponent = '';

        switch (true) {
            case path === '/dashboard' || path === '/':
                pageComponent = '<page-dashboard></page-dashboard>';
                break;
            case path === '/recordings':
            case path.startsWith('/recordings/'):
                pageComponent = '<page-recordings></page-recordings>';
                break;
            case path === '/events':
            case path.startsWith('/events/'):
                pageComponent = '<page-events></page-events>';
                break;
            case path === '/settings':
            case path.startsWith('/settings/'):
                pageComponent = '<page-settings></page-settings>';
                break;
            default:
                pageComponent = '<page-dashboard></page-dashboard>';
        }

        container.innerHTML = pageComponent;
    }

    /**
     * Handler para mudanca de autenticacao
     * @param {Object} state - Estado de autenticacao
     */
    handleAuthChange(state) {
        if (state.isAuthenticated) {
            // Usuario logou
            this.ws.connect();
            if (this.currentRoute === '/login' || !this.currentRoute) {
                window.location.hash = '#/dashboard';
            } else {
                this.render();
            }
        } else {
            // Usuario deslogou
            this.ws.disconnect();
            window.location.hash = '#/login';
            this.render();
        }
    }

    /**
     * Ocultar tela de loading inicial
     */
    hideLoadingScreen() {
        const loading = document.getElementById('loading-screen');
        if (loading) {
            loading.classList.add('hidden');
            setTimeout(() => {
                loading.remove();
            }, 350);
        }
    }

    /**
     * Configurar event listeners globais
     */
    setupGlobalListeners() {
        // Toggle sidebar
        document.addEventListener('sidebar-toggled', (e) => {
            this.sidebarCollapsed = e.detail.collapsed;
            const main = document.getElementById('main-content');
            main?.classList.toggle('sidebar-collapsed', this.sidebarCollapsed);
        });

        // Logout event
        window.addEventListener('auth:logout', () => {
            window.location.hash = '#/login';
            this.render();
        });

        // PWA install prompt
        window.addEventListener('pwa-installable', (e) => {
            this.showInstallPrompt(e.detail);
        });

        // Notificacao click do service worker
        navigator.serviceWorker?.addEventListener('message', (event) => {
            if (event.data.type === 'NOTIFICATION_CLICK') {
                const url = event.data.url;
                if (url) {
                    window.location.hash = url;
                }
            }
        });

        // Online/Offline status
        window.addEventListener('online', () => {
            this.notifications.success('Conexao restaurada');
            this.ws.connect();
        });

        window.addEventListener('offline', () => {
            this.notifications.warning('Voce esta offline');
        });

        // Busca global
        document.addEventListener('global-search', (e) => {
            console.log('[App] Busca global:', e.detail);
            // Implementar logica de busca
        });

        // Modal de adicionar camera
        document.addEventListener('show-add-camera-modal', () => {
            this.showAddCameraModal();
        });
    }

    /**
     * Mostrar prompt de instalacao PWA
     * @param {BeforeInstallPromptEvent} deferredPrompt
     */
    showInstallPrompt(deferredPrompt) {
        // Mostrar botao de instalacao ou toast
        this.notifications.addToast({
            type: 'info',
            title: 'Instalar App',
            message: 'Instale o SkyCamOS para acesso rapido',
            duration: 0,
            action: {
                label: 'Instalar',
                callback: async () => {
                    deferredPrompt.prompt();
                    const { outcome } = await deferredPrompt.userChoice;
                    console.log('[PWA] Instalacao:', outcome);
                }
            }
        });
    }

    /**
     * Mostrar modal de adicionar camera
     */
    showAddCameraModal() {
        const modal = document.getElementById('modal-container');
        if (!modal) return;

        modal.classList.add('active');
        modal.innerHTML = `
            <div class="modal-backdrop" id="modal-backdrop"></div>
            <div class="modal-content" style="width: 500px; padding: var(--spacing-lg);">
                <h2 style="margin-bottom: var(--spacing-md);">Adicionar Camera</h2>
                <form id="add-camera-form">
                    <div class="input-group" style="margin-bottom: var(--spacing-md);">
                        <label class="input-label">Nome da Camera</label>
                        <input type="text" class="input" name="name" required placeholder="Ex: Entrada Principal">
                    </div>
                    <div class="input-group" style="margin-bottom: var(--spacing-md);">
                        <label class="input-label">URL RTSP</label>
                        <input type="text" class="input" name="url" required placeholder="rtsp://usuario:senha@ip:porta/stream">
                    </div>
                    <div class="input-group" style="margin-bottom: var(--spacing-md);">
                        <label class="input-label">Grupo (opcional)</label>
                        <input type="text" class="input" name="group" placeholder="Ex: Externo">
                    </div>
                    <div class="flex gap-sm" style="justify-content: flex-end;">
                        <button type="button" class="btn btn-secondary" id="cancel-modal">Cancelar</button>
                        <button type="submit" class="btn btn-primary">Adicionar</button>
                    </div>
                </form>
            </div>
        `;

        // Fechar modal
        const closeModal = () => {
            modal.classList.remove('active');
            modal.innerHTML = '';
        };

        modal.querySelector('#modal-backdrop')?.addEventListener('click', closeModal);
        modal.querySelector('#cancel-modal')?.addEventListener('click', closeModal);

        // Submit form
        modal.querySelector('#add-camera-form')?.addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(e.target);
            const data = Object.fromEntries(formData);

            try {
                const { useCamera } = await import('./hooks/useCamera.js');
                const cameraManager = useCamera();
                await cameraManager.createCamera(data);
                this.notifications.success('Camera adicionada com sucesso');
                closeModal();
            } catch (error) {
                this.notifications.error(error.message || 'Erro ao adicionar camera');
            }
        });
    }
}

// Exportar classe do app
export default SkyCamApp;
