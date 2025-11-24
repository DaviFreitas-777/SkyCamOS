/**
 * SkyCamOS - Pagina Settings
 * Pagina de configuracoes do sistema
 */

import { apiService } from '../services/api.js';
import { useAuth } from '../hooks/useAuth.js';
import { useNotifications } from '../hooks/useNotifications.js';
import { storageService } from '../services/storage.js';

class SettingsPage extends HTMLElement {
    constructor() {
        super();
        this.auth = useAuth();
        this.notifications = useNotifications();
        this.activeTab = 'general';
        this.settings = {};
        this.cameras = [];
        this.loading = false;
    }

    async connectedCallback() {
        this.render();
        await this.loadSettings();
    }

    async loadSettings() {
        this.loading = true;
        try {
            const [settings, camerasResponse] = await Promise.all([
                apiService.getSettings(),
                apiService.getCameras()
            ]);
            this.settings = settings;
            // API retorna {items: [...]} ou array direto
            this.cameras = Array.isArray(camerasResponse) ? camerasResponse : (camerasResponse?.items || []);
            this.renderTabContent();
        } catch (error) {
            console.error('[Settings] Erro ao carregar:', error);
            this.notifications.error('Erro ao carregar configuracoes');
        }
        this.loading = false;
    }

    render() {
        this.innerHTML = `
            <div class="settings-page">
                <div class="page-header">
                    <h1 class="page-title">Configuracoes</h1>
                </div>

                <div class="settings-container">
                    <nav class="settings-nav">
                        <button class="settings-nav-item ${this.activeTab === 'general' ? 'active' : ''}" data-tab="general">
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-2 2 2 2 0 01-2-2v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83 0 2 2 0 010-2.83l.06-.06a1.65 1.65 0 00.33-1.82 1.65 1.65 0 00-1.51-1H3a2 2 0 01-2-2 2 2 0 012-2h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 010-2.83 2 2 0 012.83 0l.06.06a1.65 1.65 0 001.82.33H9a1.65 1.65 0 001-1.51V3a2 2 0 012-2 2 2 0 012 2v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 0 2 2 0 010 2.83l-.06.06a1.65 1.65 0 00-.33 1.82V9a1.65 1.65 0 001.51 1H21a2 2 0 012 2 2 2 0 01-2 2h-.09a1.65 1.65 0 00-1.51 1z"/>
                            </svg>
                            Geral
                        </button>
                        <button class="settings-nav-item ${this.activeTab === 'cameras' ? 'active' : ''}" data-tab="cameras">
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <rect x="2" y="6" width="14" height="12" rx="2"/><path d="M22 8l-4 4 4 4V8z"/>
                            </svg>
                            Cameras
                        </button>
                        <button class="settings-nav-item ${this.activeTab === 'notifications' ? 'active' : ''}" data-tab="notifications">
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M18 8A6 6 0 006 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 01-3.46 0"/>
                            </svg>
                            Notificacoes
                        </button>
                        <button class="settings-nav-item ${this.activeTab === 'storage' ? 'active' : ''}" data-tab="storage">
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/>
                            </svg>
                            Armazenamento
                        </button>
                        <button class="settings-nav-item ${this.activeTab === 'profile' ? 'active' : ''}" data-tab="profile">
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/><circle cx="12" cy="7" r="4"/>
                            </svg>
                            Perfil
                        </button>
                    </nav>

                    <div class="settings-content" id="settings-content">
                        <div class="loading-spinner"></div>
                    </div>
                </div>
            </div>
        `;

        this.addStyles();
        this.attachEventListeners();
    }

    renderTabContent() {
        const container = this.querySelector('#settings-content');
        if (!container) return;

        switch (this.activeTab) {
            case 'general': container.innerHTML = this.renderGeneralTab(); break;
            case 'cameras': container.innerHTML = this.renderCamerasTab(); break;
            case 'notifications': container.innerHTML = this.renderNotificationsTab(); break;
            case 'storage': container.innerHTML = this.renderStorageTab(); break;
            case 'profile': container.innerHTML = this.renderProfileTab(); break;
        }

        this.attachFormListeners();
    }

    renderGeneralTab() {
        return `
            <div class="settings-section">
                <h2 class="settings-section-title">Configuracoes Gerais</h2>
                <form id="general-form" class="settings-form">
                    <div class="input-group">
                        <label class="input-label">Nome do Sistema</label>
                        <input type="text" class="input" name="systemName" value="${this.settings.systemName || 'SkyCamOS'}">
                    </div>
                    <div class="input-group">
                        <label class="input-label">Idioma</label>
                        <select class="input" name="language">
                            <option value="pt-BR" ${this.settings.language === 'pt-BR' ? 'selected' : ''}>Portugues (Brasil)</option>
                            <option value="en" ${this.settings.language === 'en' ? 'selected' : ''}>English</option>
                        </select>
                    </div>
                    <div class="input-group">
                        <label class="input-label">Fuso Horario</label>
                        <select class="input" name="timezone">
                            <option value="America/Sao_Paulo">America/Sao_Paulo (GMT-3)</option>
                            <option value="America/Manaus">America/Manaus (GMT-4)</option>
                            <option value="UTC">UTC</option>
                        </select>
                    </div>
                    <div class="checkbox-group">
                        <input type="checkbox" class="checkbox" name="autoStart" ${this.settings.autoStart ? 'checked' : ''}>
                        <label>Iniciar gravacao automaticamente</label>
                    </div>
                    <button type="submit" class="btn btn-primary">Salvar Alteracoes</button>
                </form>
            </div>
        `;
    }

    renderCamerasTab() {
        return `
            <div class="settings-section">
                <div class="settings-section-header">
                    <h2 class="settings-section-title">Cameras (${this.cameras.length})</h2>
                    <button class="btn btn-primary" id="add-camera-btn">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <circle cx="12" cy="12" r="10"/><path d="M12 8v8M8 12h8"/>
                        </svg>
                        Adicionar Camera
                    </button>
                </div>
                <div class="cameras-list">
                    ${this.cameras.length === 0 ? '<p class="text-center" style="color: var(--color-text-tertiary);">Nenhuma camera configurada</p>' :
                        this.cameras.map(cam => `
                            <div class="camera-item" data-id="${cam.id}">
                                <div class="camera-item-info">
                                    <span class="status-dot ${cam.status === 'online' ? 'online' : 'offline'}"></span>
                                    <span class="camera-name">${cam.name}</span>
                                    <span class="camera-ip">${cam.ip || cam.url || ''}</span>
                                </div>
                                <div class="camera-item-actions">
                                    <button class="btn btn-icon-sm btn-ghost" data-action="edit" title="Editar">
                                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                            <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7"/>
                                            <path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z"/>
                                        </svg>
                                    </button>
                                    <button class="btn btn-icon-sm btn-ghost" data-action="delete" title="Excluir">
                                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                            <path d="M3 6h18M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/>
                                        </svg>
                                    </button>
                                </div>
                            </div>
                        `).join('')
                    }
                </div>
            </div>
        `;
    }

    renderNotificationsTab() {
        const pushStatus = this.notifications.getPushStatus();
        return `
            <div class="settings-section">
                <h2 class="settings-section-title">Notificacoes</h2>
                <form id="notifications-form" class="settings-form">
                    <div class="setting-row">
                        <div class="setting-info">
                            <span class="setting-name">Push Notifications</span>
                            <span class="setting-desc">Receber notificacoes mesmo com o app fechado</span>
                        </div>
                        <div class="toggle ${pushStatus.permission === 'granted' ? 'active' : ''}" id="push-toggle"></div>
                    </div>
                    <div class="setting-row">
                        <div class="setting-info">
                            <span class="setting-name">Eventos de Movimento</span>
                            <span class="setting-desc">Notificar quando detectar movimento</span>
                        </div>
                        <div class="toggle ${this.settings.notifyMotion !== false ? 'active' : ''}" data-setting="notifyMotion"></div>
                    </div>
                    <div class="setting-row">
                        <div class="setting-info">
                            <span class="setting-name">Camera Offline</span>
                            <span class="setting-desc">Notificar quando uma camera ficar offline</span>
                        </div>
                        <div class="toggle ${this.settings.notifyOffline !== false ? 'active' : ''}" data-setting="notifyOffline"></div>
                    </div>
                    <div class="setting-row">
                        <div class="setting-info">
                            <span class="setting-name">Alertas de Armazenamento</span>
                            <span class="setting-desc">Notificar quando armazenamento estiver cheio</span>
                        </div>
                        <div class="toggle ${this.settings.notifyStorage !== false ? 'active' : ''}" data-setting="notifyStorage"></div>
                    </div>
                </form>
            </div>
        `;
    }

    renderStorageTab() {
        return `
            <div class="settings-section">
                <h2 class="settings-section-title">Armazenamento</h2>
                <div class="storage-stats">
                    <div class="storage-bar">
                        <div class="storage-used" style="width: ${this.settings.storageUsedPercent || 0}%"></div>
                    </div>
                    <p class="storage-info">${this.settings.storageUsed || '0 GB'} de ${this.settings.storageTotal || '0 GB'} utilizados</p>
                </div>
                <form id="storage-form" class="settings-form">
                    <div class="input-group">
                        <label class="input-label">Retencao de Gravacoes (dias)</label>
                        <input type="number" class="input" name="retentionDays" value="${this.settings.retentionDays || 30}" min="1" max="365">
                    </div>
                    <div class="input-group">
                        <label class="input-label">Qualidade de Gravacao</label>
                        <select class="input" name="recordingQuality">
                            <option value="high" ${this.settings.recordingQuality === 'high' ? 'selected' : ''}>Alta (1080p)</option>
                            <option value="medium" ${this.settings.recordingQuality === 'medium' ? 'selected' : ''}>Media (720p)</option>
                            <option value="low" ${this.settings.recordingQuality === 'low' ? 'selected' : ''}>Baixa (480p)</option>
                        </select>
                    </div>
                    <button type="submit" class="btn btn-primary">Salvar</button>
                    <button type="button" class="btn btn-danger" id="clear-cache">Limpar Cache Local</button>
                </form>
            </div>
        `;
    }

    renderProfileTab() {
        const user = this.auth.getUser() || {};
        return `
            <div class="settings-section">
                <h2 class="settings-section-title">Meu Perfil</h2>
                <form id="profile-form" class="settings-form">
                    <div class="input-group">
                        <label class="input-label">Nome</label>
                        <input type="text" class="input" name="name" value="${user.name || ''}">
                    </div>
                    <div class="input-group">
                        <label class="input-label">Email</label>
                        <input type="email" class="input" name="email" value="${user.email || ''}">
                    </div>
                    <button type="submit" class="btn btn-primary">Atualizar Perfil</button>
                </form>
                <hr style="margin: var(--spacing-lg) 0; border-color: var(--color-border-secondary);">
                <h3>Alterar Senha</h3>
                <form id="password-form" class="settings-form">
                    <div class="input-group">
                        <label class="input-label">Senha Atual</label>
                        <input type="password" class="input" name="currentPassword" required>
                    </div>
                    <div class="input-group">
                        <label class="input-label">Nova Senha</label>
                        <input type="password" class="input" name="newPassword" required minlength="6">
                    </div>
                    <div class="input-group">
                        <label class="input-label">Confirmar Nova Senha</label>
                        <input type="password" class="input" name="confirmPassword" required>
                    </div>
                    <button type="submit" class="btn btn-secondary">Alterar Senha</button>
                </form>
            </div>
        `;
    }

    addStyles() {
        if (document.getElementById('settings-page-styles')) return;
        const styles = document.createElement('style');
        styles.id = 'settings-page-styles';
        styles.textContent = `
            .settings-page { display: flex; flex-direction: column; height: 100%; }
            .page-header { margin-bottom: var(--spacing-lg); }
            .settings-container { display: flex; gap: var(--spacing-lg); flex: 1; }
            .settings-nav { width: 200px; display: flex; flex-direction: column; gap: var(--spacing-xs); }
            .settings-nav-item {
                display: flex; align-items: center; gap: var(--spacing-sm);
                padding: var(--spacing-sm) var(--spacing-md); background: none; color: var(--color-text-secondary);
                border-radius: var(--radius-md); text-align: left; transition: all var(--transition-fast);
            }
            .settings-nav-item:hover { background: var(--color-bg-card); color: var(--color-text-primary); }
            .settings-nav-item.active { background: var(--color-primary-600); color: var(--color-text-primary); }
            .settings-content { flex: 1; background: var(--color-bg-card); border-radius: var(--radius-lg); padding: var(--spacing-lg); overflow-y: auto; }
            .settings-section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: var(--spacing-md); }
            .settings-section-title { font-size: var(--font-size-lg); font-weight: var(--font-weight-semibold); margin-bottom: var(--spacing-md); }
            .settings-form { display: flex; flex-direction: column; gap: var(--spacing-md); max-width: 500px; }
            .setting-row { display: flex; justify-content: space-between; align-items: center; padding: var(--spacing-sm) 0; border-bottom: 1px solid var(--color-border-secondary); }
            .setting-name { font-weight: var(--font-weight-medium); display: block; }
            .setting-desc { font-size: var(--font-size-sm); color: var(--color-text-tertiary); }
            .cameras-list { display: flex; flex-direction: column; gap: var(--spacing-sm); }
            .camera-item { display: flex; justify-content: space-between; align-items: center; padding: var(--spacing-sm) var(--spacing-md); background: var(--color-bg-tertiary); border-radius: var(--radius-md); }
            .camera-item-info { display: flex; align-items: center; gap: var(--spacing-sm); }
            .camera-ip { font-size: var(--font-size-sm); color: var(--color-text-tertiary); }
            .camera-item-actions { display: flex; gap: var(--spacing-xs); }
            .storage-stats { margin-bottom: var(--spacing-lg); }
            .storage-bar { height: 8px; background: var(--color-bg-tertiary); border-radius: var(--radius-full); overflow: hidden; margin-bottom: var(--spacing-xs); }
            .storage-used { height: 100%; background: var(--color-primary-500); border-radius: var(--radius-full); }
            .storage-info { font-size: var(--font-size-sm); color: var(--color-text-secondary); }
            @media (max-width: 768px) {
                .settings-container { flex-direction: column; }
                .settings-nav {
                    width: 100%;
                    flex-direction: row;
                    overflow-x: auto;
                    gap: var(--spacing-xs);
                    padding-bottom: var(--spacing-xs);
                    -webkit-overflow-scrolling: touch;
                }
                .settings-nav-item {
                    flex-shrink: 0;
                    white-space: nowrap;
                    padding: var(--spacing-sm) var(--spacing-md);
                    font-size: var(--font-size-sm);
                    min-height: 44px;
                }
                .settings-nav-item svg {
                    display: none;
                }
                .settings-content {
                    padding: var(--spacing-md);
                }
                .settings-section-title {
                    font-size: var(--font-size-base);
                    word-wrap: break-word;
                    overflow-wrap: break-word;
                }
                .settings-section-header {
                    flex-direction: column;
                    align-items: flex-start;
                    gap: var(--spacing-sm);
                }
                .settings-form {
                    max-width: 100%;
                }
                .setting-row {
                    flex-direction: column;
                    align-items: flex-start;
                    gap: var(--spacing-sm);
                }
                .setting-info {
                    width: 100%;
                }
                .input-label {
                    white-space: normal;
                    word-wrap: break-word;
                    overflow-wrap: break-word;
                }
            }
        `;
        document.head.appendChild(styles);
    }

    attachEventListeners() {
        this.querySelectorAll('.settings-nav-item').forEach(btn => {
            btn.addEventListener('click', () => {
                this.activeTab = btn.dataset.tab;
                this.querySelectorAll('.settings-nav-item').forEach(b => b.classList.toggle('active', b === btn));
                this.renderTabContent();
            });
        });
    }

    attachFormListeners() {
        // Toggle switches
        this.querySelectorAll('.toggle').forEach(toggle => {
            toggle.addEventListener('click', async () => {
                toggle.classList.toggle('active');
                if (toggle.id === 'push-toggle') {
                    if (toggle.classList.contains('active')) {
                        await this.notifications.requestPermission();
                        await this.notifications.subscribePush();
                    } else {
                        await this.notifications.unsubscribePush();
                    }
                } else if (toggle.dataset.setting) {
                    this.settings[toggle.dataset.setting] = toggle.classList.contains('active');
                    await apiService.updateSettings({ [toggle.dataset.setting]: this.settings[toggle.dataset.setting] });
                }
            });
        });

        // Forms
        this.querySelector('#general-form')?.addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(e.target);
            await this.saveSettings(Object.fromEntries(formData));
        });

        this.querySelector('#storage-form')?.addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(e.target);
            await this.saveSettings(Object.fromEntries(formData));
        });

        this.querySelector('#profile-form')?.addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(e.target);
            await this.auth.updateProfile(Object.fromEntries(formData));
            this.notifications.success('Perfil atualizado');
        });

        this.querySelector('#password-form')?.addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(e.target);
            const data = Object.fromEntries(formData);
            if (data.newPassword !== data.confirmPassword) {
                this.notifications.error('Senhas nao conferem');
                return;
            }
            try {
                await this.auth.changePassword(data.currentPassword, data.newPassword);
                this.notifications.success('Senha alterada');
                e.target.reset();
            } catch (error) {
                this.notifications.error(error.message);
            }
        });

        this.querySelector('#clear-cache')?.addEventListener('click', async () => {
            if (confirm('Limpar todo o cache local?')) {
                await storageService.clear();
                this.notifications.success('Cache limpo');
            }
        });

        this.querySelector('#add-camera-btn')?.addEventListener('click', () => {
            // Disparar evento para abrir modal de camera
            document.dispatchEvent(new CustomEvent('show-add-camera-modal'));
        });
    }

    async saveSettings(data) {
        try {
            await apiService.updateSettings(data);
            Object.assign(this.settings, data);
            this.notifications.success('Configuracoes salvas');
        } catch (error) {
            this.notifications.error('Erro ao salvar configuracoes');
        }
    }
}

customElements.define('page-settings', SettingsPage);
export default SettingsPage;
