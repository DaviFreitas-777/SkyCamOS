/**
 * SkyCamOS - Pagina Login
 * Pagina de autenticacao
 */

import '../components/LoginForm.js';

class LoginPage extends HTMLElement {
    connectedCallback() {
        this.render();
    }

    render() {
        this.innerHTML = `
            <div class="login-page">
                <div class="login-background">
                    <div class="login-bg-gradient"></div>
                </div>
                <div class="login-container">
                    <skycam-login-form></skycam-login-form>
                </div>
                <footer class="login-footer">
                    <p>SkyCamOS v1.0.0 - Sistema de Monitoramento de Cameras</p>
                </footer>
            </div>
        `;

        this.addStyles();
    }

    addStyles() {
        if (document.getElementById('login-page-styles')) return;
        const styles = document.createElement('style');
        styles.id = 'login-page-styles';
        styles.textContent = `
            .login-page {
                min-height: 100vh; display: flex; flex-direction: column;
                align-items: center; justify-content: center;
                padding: var(--spacing-lg); position: relative;
            }
            .login-background {
                position: fixed; inset: 0; z-index: -1;
                background: linear-gradient(135deg, var(--color-bg-primary) 0%, var(--color-bg-secondary) 100%);
            }
            .login-bg-gradient {
                position: absolute; inset: 0;
                background: radial-gradient(circle at 30% 20%, rgba(79, 70, 229, 0.15) 0%, transparent 50%),
                            radial-gradient(circle at 70% 80%, rgba(124, 58, 237, 0.1) 0%, transparent 50%);
            }
            .login-container { width: 100%; max-width: 440px; z-index: 1; }
            .login-footer {
                margin-top: var(--spacing-xl); text-align: center;
                font-size: var(--font-size-sm); color: var(--color-text-tertiary);
            }
        `;
        document.head.appendChild(styles);
    }
}

customElements.define('page-login', LoginPage);
export default LoginPage;
