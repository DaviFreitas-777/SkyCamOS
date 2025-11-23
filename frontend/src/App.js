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
import './pages/Export.js';

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
        this.protectedRoutes = ['/dashboard', '/recordings', '/events', '/settings', '/export'];

        // Rotas publicas
        this.publicRoutes = ['/login'];
    }

    /**
     * Inicializar aplicacao
     */
    async init() {
        console.log('[App] Inicializando SkyCamOS...');

        // Inicializar e verificar autenticacao
        await this.auth.init();
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
            case path === '/export':
            case path.startsWith('/export/'):
                pageComponent = '<skycam-export-page></skycam-export-page>';
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
                this.currentRoute = '/dashboard';
                window.location.hash = '#/dashboard';
            }
            // Sempre re-renderizar para mostrar o layout completo
            this.render();
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

        // Modal de descoberta automatica
        document.addEventListener('show-discover-cameras-modal', () => {
            this.showDiscoverCamerasModal();
        });
    }

    /**
     * Mostrar modal de descoberta automatica de cameras
     */
    async showDiscoverCamerasModal() {
        const modal = document.getElementById('modal-container');
        if (!modal) return;

        modal.classList.add('active');
        modal.innerHTML = `
            <div class="modal-backdrop" id="modal-backdrop"></div>
            <div class="modal-content" style="width: 650px; padding: var(--spacing-lg); max-height: 80vh; overflow-y: auto;">
                <h2 style="margin-bottom: var(--spacing-md);">Descobrir Cameras na Rede</h2>
                <p style="margin-bottom: var(--spacing-md); color: var(--text-secondary);">
                    Configure como deseja buscar as cameras na rede.
                </p>

                <div id="discover-form">
                    <!-- Modo de busca -->
                    <div class="input-group" style="margin-bottom: var(--spacing-md);">
                        <label class="input-label">Modo de Busca</label>
                        <select class="input" id="discover-mode" style="width: 100%;">
                            <option value="specific">IP Especifico (mais rapido)</option>
                            <option value="range">Faixa de IPs</option>
                            <option value="auto">Descoberta Automatica (ONVIF)</option>
                        </select>
                    </div>

                    <!-- IP Especifico -->
                    <div id="specific-ip-fields" style="margin-bottom: var(--spacing-md);">
                        <div class="input-group" style="margin-bottom: var(--spacing-xs);">
                            <label class="input-label">IP da Camera</label>
                            <input type="text" class="input" id="discover-ip" placeholder="Ex: 192.168.100.50">
                        </div>
                        <p style="font-size: 0.75rem; color: var(--text-secondary); margin-bottom: 0;">
                            Separe multiplos IPs por virgula: 192.168.100.50, 192.168.100.51
                        </p>
                    </div>

                    <!-- Range de IPs -->
                    <div id="range-ip-fields" style="display: none; margin-bottom: var(--spacing-md);">
                        <div style="display: flex; gap: var(--spacing-sm); align-items: flex-end;">
                            <div class="input-group" style="flex: 1;">
                                <label class="input-label">IP Inicial</label>
                                <input type="text" class="input" id="discover-ip-start" placeholder="192.168.100.1">
                            </div>
                            <span style="padding-bottom: 12px;">ate</span>
                            <div class="input-group" style="flex: 1;">
                                <label class="input-label">IP Final</label>
                                <input type="text" class="input" id="discover-ip-end" placeholder="192.168.100.254">
                            </div>
                        </div>
                    </div>

                    <!-- Credenciais -->
                    <div style="display: flex; gap: var(--spacing-md); margin-bottom: var(--spacing-md);">
                        <div class="input-group" style="flex: 1;">
                            <label class="input-label">Usuario</label>
                            <input type="text" class="input" id="discover-username" value="admin" placeholder="admin">
                        </div>
                        <div class="input-group" style="flex: 1;">
                            <label class="input-label">Senha</label>
                            <input type="password" class="input" id="discover-password" placeholder="Senha da camera">
                        </div>
                    </div>

                    <div class="flex gap-sm" style="justify-content: flex-end;">
                        <button type="button" class="btn btn-secondary" id="cancel-discover">Cancelar</button>
                        <button type="button" class="btn btn-primary" id="start-discover">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="margin-right: 8px;">
                                <circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35"/>
                            </svg>
                            Buscar Cameras
                        </button>
                    </div>
                </div>

                <div id="discover-loading" style="display: none; text-align: center; padding: var(--spacing-xl);">
                    <div class="spinner" style="margin: 0 auto var(--spacing-md);"></div>
                    <p>Buscando cameras na rede...</p>
                    <p style="color: var(--text-secondary); font-size: 0.875rem;">Isso pode levar alguns segundos</p>
                </div>

                <div id="discover-results" style="display: none;">
                    <h3 style="margin-bottom: var(--spacing-sm);">Cameras Encontradas</h3>
                    <div id="cameras-list" style="margin-bottom: var(--spacing-md);"></div>
                    <div class="flex gap-sm" style="justify-content: flex-end;">
                        <button type="button" class="btn btn-secondary" id="cancel-results">Cancelar</button>
                        <button type="button" class="btn btn-primary" id="add-selected">Adicionar Selecionadas</button>
                    </div>
                </div>

                <div id="discover-empty" style="display: none; text-align: center; padding: var(--spacing-xl);">
                    <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="var(--text-secondary)" stroke-width="2" style="margin-bottom: var(--spacing-md);">
                        <rect x="2" y="6" width="14" height="12" rx="2"/><path d="M22 8l-4 4 4 4V8z"/><path d="M2 2l20 20"/>
                    </svg>
                    <p>Nenhuma camera encontrada na rede</p>
                    <p style="color: var(--text-secondary); font-size: 0.875rem;">Verifique se as cameras estao ligadas e conectadas</p>
                    <button type="button" class="btn btn-secondary" id="retry-discover" style="margin-top: var(--spacing-md);">Tentar Novamente</button>
                </div>
            </div>
        `;

        const closeModal = () => {
            modal.classList.remove('active');
            modal.innerHTML = '';
        };

        // Event listeners
        modal.querySelector('#modal-backdrop')?.addEventListener('click', closeModal);
        modal.querySelector('#cancel-discover')?.addEventListener('click', closeModal);
        modal.querySelector('#cancel-results')?.addEventListener('click', closeModal);

        // Alternar campos de acordo com o modo de busca
        modal.querySelector('#discover-mode')?.addEventListener('change', (e) => {
            const mode = e.target.value;
            const specificFields = modal.querySelector('#specific-ip-fields');
            const rangeFields = modal.querySelector('#range-ip-fields');

            if (mode === 'specific') {
                specificFields.style.display = 'block';
                rangeFields.style.display = 'none';
            } else if (mode === 'range') {
                specificFields.style.display = 'none';
                rangeFields.style.display = 'block';
            } else {
                specificFields.style.display = 'none';
                rangeFields.style.display = 'none';
            }
        });

        // Buscar cameras
        modal.querySelector('#start-discover')?.addEventListener('click', async () => {
            const mode = modal.querySelector('#discover-mode').value;
            const username = modal.querySelector('#discover-username').value || 'admin';
            const password = modal.querySelector('#discover-password').value || '';

            // Coletar IPs baseado no modo
            let ips = [];
            if (mode === 'specific') {
                const ipInput = modal.querySelector('#discover-ip').value.trim();
                if (!ipInput) {
                    this.notifications.warning('Digite pelo menos um IP');
                    return;
                }
                ips = ipInput.split(',').map(ip => ip.trim()).filter(ip => ip);
            } else if (mode === 'range') {
                const startIp = modal.querySelector('#discover-ip-start').value.trim();
                const endIp = modal.querySelector('#discover-ip-end').value.trim();
                if (!startIp || !endIp) {
                    this.notifications.warning('Digite o IP inicial e final');
                    return;
                }
                // Gerar range de IPs
                const startParts = startIp.split('.').map(Number);
                const endParts = endIp.split('.').map(Number);
                const base = startParts.slice(0, 3).join('.');
                for (let i = startParts[3]; i <= endParts[3]; i++) {
                    ips.push(`${base}.${i}`);
                }
            }

            // Mostra loading
            modal.querySelector('#discover-form').style.display = 'none';
            modal.querySelector('#discover-loading').style.display = 'block';

            try {
                const { apiService } = await import('./services/api.js');
                let cameras;

                if (mode === 'auto') {
                    // Descoberta automatica via ONVIF
                    cameras = await apiService.discoverAndTestCameras(username, password);
                } else {
                    // Testar IPs especificos
                    cameras = await apiService.discoverAndTestCameras(username, password, ips);
                }

                modal.querySelector('#discover-loading').style.display = 'none';

                if (cameras && cameras.length > 0) {
                    // Mostra resultados
                    this.renderDiscoveredCameras(modal, cameras, username, password, closeModal);
                } else {
                    // Nenhuma camera encontrada
                    modal.querySelector('#discover-empty').style.display = 'block';
                    modal.querySelector('#retry-discover')?.addEventListener('click', () => {
                        modal.querySelector('#discover-empty').style.display = 'none';
                        modal.querySelector('#discover-form').style.display = 'block';
                    });
                }
            } catch (error) {
                console.error('[Discover] Erro:', error);
                modal.querySelector('#discover-loading').style.display = 'none';
                modal.querySelector('#discover-form').style.display = 'block';
                this.notifications.error('Erro ao buscar cameras: ' + error.message);
            }
        });
    }

    /**
     * Renderiza lista de cameras descobertas
     */
    renderDiscoveredCameras(modal, cameras, username, password, closeModal) {
        const list = modal.querySelector('#cameras-list');
        list.innerHTML = cameras.map((cam, index) => `
            <div class="discover-camera-item" style="
                display: flex;
                align-items: center;
                padding: var(--spacing-sm);
                border: 1px solid var(--border-color);
                border-radius: var(--radius-sm);
                margin-bottom: var(--spacing-xs);
                background: ${cam.is_accessible ? 'var(--color-success-bg)' : 'var(--color-bg-secondary)'};
            ">
                <input type="checkbox" id="cam-${index}" ${cam.is_accessible ? 'checked' : ''} style="margin-right: var(--spacing-sm);">
                <div style="flex: 1;">
                    <div style="font-weight: 500;">${cam.name || 'Camera ' + cam.ip_address}</div>
                    <div style="font-size: 0.75rem; color: var(--text-secondary);">
                        ${cam.ip_address} | ${cam.manufacturer || 'Fabricante desconhecido'}
                        ${cam.is_accessible ? ' | Conexao OK' : ' | Sem resposta'}
                    </div>
                </div>
                <span style="
                    padding: 2px 8px;
                    border-radius: 4px;
                    font-size: 0.75rem;
                    background: ${cam.is_accessible ? 'var(--color-success)' : 'var(--color-warning)'};
                    color: white;
                ">${cam.is_accessible ? 'Online' : 'Verificar'}</span>
            </div>
        `).join('');

        modal.querySelector('#discover-results').style.display = 'block';

        // Adicionar selecionadas
        modal.querySelector('#add-selected')?.addEventListener('click', async () => {
            const checkboxes = list.querySelectorAll('input[type="checkbox"]:checked');
            const selectedIndexes = Array.from(checkboxes).map(cb => parseInt(cb.id.replace('cam-', '')));

            if (selectedIndexes.length === 0) {
                this.notifications.warning('Selecione pelo menos uma camera');
                return;
            }

            const { apiService } = await import('./services/api.js');
            const { useCamera } = await import('./hooks/useCamera.js');
            const cameraManager = useCamera();

            let added = 0;
            for (const index of selectedIndexes) {
                const cam = cameras[index];
                try {
                    await apiService.addDiscoveredCamera({
                        ip_address: cam.ip_address,
                        name: cam.name || 'Camera ' + cam.ip_address,
                        username: username,
                        password: password,
                        rtsp_url: cam.rtsp_url,
                        manufacturer: cam.manufacturer,
                    });
                    added++;
                } catch (error) {
                    console.error('[Discover] Erro ao adicionar:', cam.ip_address, error);
                }
            }

            if (added > 0) {
                this.notifications.success(added + ' camera(s) adicionada(s) com sucesso!');
                await cameraManager.loadCameras(true);
            }

            closeModal();
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
                        <label class="input-label">Endereco IP</label>
                        <input type="text" class="input" name="ip_address" required placeholder="Ex: 192.168.1.100">
                    </div>
                    <div class="input-group" style="margin-bottom: var(--spacing-md);">
                        <label class="input-label">Porta RTSP</label>
                        <input type="number" class="input" name="port" value="554" placeholder="554">
                    </div>
                    <div class="input-group" style="margin-bottom: var(--spacing-md);">
                        <label class="input-label">Usuario</label>
                        <input type="text" class="input" name="username" placeholder="admin">
                    </div>
                    <div class="input-group" style="margin-bottom: var(--spacing-md);">
                        <label class="input-label">Senha</label>
                        <input type="password" class="input" name="password" placeholder="Senha da camera">
                    </div>
                    <div class="input-group" style="margin-bottom: var(--spacing-md);">
                        <label class="input-label">URL RTSP (opcional)</label>
                        <input type="text" class="input" name="rtsp_url" placeholder="rtsp://ip:porta/stream1">
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

            // Converter porta para numero
            if (data.port) {
                data.port = parseInt(data.port, 10);
            }

            // Remover campos vazios
            Object.keys(data).forEach(key => {
                if (data[key] === '') {
                    delete data[key];
                }
            });

            try {
                const { useCamera } = await import('./hooks/useCamera.js');
                const cameraManager = useCamera();
                await cameraManager.createCamera(data);
                this.notifications.success('Camera adicionada com sucesso');
                closeModal();
                // Recarregar lista de cameras
                await cameraManager.loadCameras(true);
            } catch (error) {
                this.notifications.error(error.message || 'Erro ao adicionar camera');
            }
        });
    }
}

// Exportar classe do app
export default SkyCamApp;
