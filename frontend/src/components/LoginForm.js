/**
 * SkyCamOS - Componente LoginForm
 * Formulario de autenticacao
 */

import { useAuth } from '../hooks/useAuth.js';
import { useNotifications } from '../hooks/useNotifications.js';
import { isValidEmail } from '../utils/helpers.js';

class SkycamLoginForm extends HTMLElement {
    constructor() {
        super();
        this.auth = useAuth();
        this.notifications = useNotifications();
        this.isLoading = false;
        this.mode = 'login'; // login, forgot, reset
    }

    connectedCallback() {
        this.render();
        this.attachEventListeners();
    }

    render() {
        this.innerHTML = `
            <div class="login-form-wrapper">
                <div class="login-header">
                    <svg viewBox="0 0 100 100" class="login-logo">
                        <circle cx="50" cy="50" r="45" fill="none" stroke="currentColor" stroke-width="2"/>
                        <circle cx="50" cy="50" r="20" fill="currentColor"/>
                    </svg>
                    <h1 class="login-title">SkyCamOS</h1>
                    <p class="login-subtitle">${this.mode === 'login' ? 'Faca login para continuar' : 'Recuperar senha'}</p>
                </div>

                <form class="login-form" id="login-form">
                    ${this.mode === 'login' ? this.renderLoginFields() : this.renderForgotFields()}

                    <button type="submit" class="btn btn-primary btn-lg w-full" id="submit-btn" ${this.isLoading ? 'disabled' : ''}>
                        ${this.isLoading ? '<span class="loading-spinner"></span>' : ''}
                        ${this.mode === 'login' ? 'Entrar' : 'Enviar'}
                    </button>
                </form>

                <div class="login-footer">
                    ${this.mode === 'login' ?
                        `<button class="btn btn-ghost" id="forgot-link">Esqueceu a senha?</button>` :
                        `<button class="btn btn-ghost" id="back-link">Voltar para login</button>`
                    }
                </div>
            </div>
        `;
        this.addStyles();
    }

    renderLoginFields() {
        return `
            <div class="input-group">
                <label class="input-label" for="username">Usuario ou Email</label>
                <input type="text" class="input" id="username" name="username" required autocomplete="username" placeholder="Digite seu usuario">
            </div>
            <div class="input-group">
                <label class="input-label" for="password">Senha</label>
                <input type="password" class="input" id="password" name="password" required autocomplete="current-password" placeholder="Digite sua senha">
            </div>
            <div class="checkbox-group">
                <input type="checkbox" class="checkbox" id="remember" name="remember">
                <label for="remember">Lembrar de mim</label>
            </div>
        `;
    }

    renderForgotFields() {
        return `
            <div class="input-group">
                <label class="input-label" for="email">Email</label>
                <input type="email" class="input" id="email" name="email" required placeholder="Digite seu email">
                <span class="input-helper">Enviaremos um link para redefinir sua senha</span>
            </div>
        `;
    }

    addStyles() {
        if (document.getElementById('login-form-styles')) return;
        const styles = document.createElement('style');
        styles.id = 'login-form-styles';
        styles.textContent = `
            .login-form-wrapper {
                max-width: 400px; width: 100%; margin: 0 auto;
                padding: var(--spacing-xl); background: var(--color-bg-secondary);
                border-radius: var(--radius-xl); box-shadow: var(--shadow-xl);
            }
            .login-header { text-align: center; margin-bottom: var(--spacing-xl); }
            .login-logo { width: 64px; height: 64px; margin: 0 auto var(--spacing-md); color: var(--color-primary-500); }
            .login-title { font-size: var(--font-size-2xl); font-weight: var(--font-weight-bold); margin-bottom: var(--spacing-xs); }
            .login-subtitle { color: var(--color-text-secondary); }
            .login-form { display: flex; flex-direction: column; gap: var(--spacing-md); }
            .login-footer { margin-top: var(--spacing-md); text-align: center; }
        `;
        document.head.appendChild(styles);
    }

    attachEventListeners() {
        this.querySelector('#login-form')?.addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleSubmit();
        });

        this.querySelector('#forgot-link')?.addEventListener('click', () => {
            this.mode = 'forgot';
            this.render();
            this.attachEventListeners();
        });

        this.querySelector('#back-link')?.addEventListener('click', () => {
            this.mode = 'login';
            this.render();
            this.attachEventListeners();
        });
    }

    async handleSubmit() {
        // Prevenir submissao dupla
        if (this.isLoading || this._submitting) return;
        this._submitting = true;
        this.isLoading = true;
        this.updateButton();

        try {
            if (this.mode === 'login') {
                const username = this.querySelector('#username').value.trim();
                const password = this.querySelector('#password').value;

                if (!username || !password) {
                    throw new Error('Preencha todos os campos');
                }

                await this.auth.login(username, password);
                this.notifications.success('Login realizado com sucesso!');
                // Força redirect para dashboard (fallback caso handleAuthChange falhe)
                setTimeout(() => {
                    window.location.hash = '#/dashboard';
                }, 100);
                return; // Sair apos login bem sucedido
            } else {
                const email = this.querySelector('#email').value;
                if (!isValidEmail(email)) {
                    throw new Error('Email invalido');
                }
                await this.auth.forgotPassword(email);
                this.notifications.success('Email de recuperacao enviado!');
                this.mode = 'login';
                this.render();
                this.attachEventListeners();
            }
        } catch (error) {
            this.notifications.error(error.message || 'Erro ao processar solicitacao');
            this.isLoading = false;
            this._submitting = false;
            this.updateButton();
        }
    }

    updateButton() {
        const btn = this.querySelector('#submit-btn');
        if (btn) {
            btn.disabled = this.isLoading;
            btn.innerHTML = this.isLoading ?
                '<span class="loading-spinner"></span>' :
                (this.mode === 'login' ? 'Entrar' : 'Enviar');
        }
    }
}

customElements.define('skycam-login-form', SkycamLoginForm);
export default SkycamLoginForm;
