/**
 * SkyCamOS - Entry Point
 * Ponto de entrada da aplicacao
 */

import SkyCamApp from './App.js';

// Configuracoes globais de ambiente
window.ENV = window.ENV || {};

// Verificar variaveis de ambiente (injetadas pelo build ou .env)
if (!window.ENV.API_BASE_URL) {
    // Usar valores padrao para desenvolvimento
    window.ENV.API_BASE_URL = 'http://localhost:8000';
    window.ENV.WS_URL = 'ws://localhost:8000/ws';
}

/**
 * Inicializar aplicacao quando DOM estiver pronto
 */
async function bootstrap() {
    try {
        // Criar instancia do app
        const app = new SkyCamApp();

        // Inicializar
        await app.init();

        // Expor app globalmente para debug (apenas em desenvolvimento)
        if (window.ENV.DEBUG) {
            window.SkyCamApp = app;
        }

        console.log('[SkyCamOS] Aplicacao iniciada com sucesso');

    } catch (error) {
        console.error('[SkyCamOS] Erro ao inicializar:', error);

        // Mostrar mensagem de erro
        const app = document.getElementById('app');
        if (app) {
            app.innerHTML = `
                <div style="
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                    min-height: 100vh;
                    padding: 20px;
                    text-align: center;
                    font-family: system-ui, sans-serif;
                    color: #fff;
                    background: #0f0f23;
                ">
                    <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="#ef4444" stroke-width="2" style="margin-bottom: 20px;">
                        <circle cx="12" cy="12" r="10"/>
                        <path d="M15 9l-6 6M9 9l6 6"/>
                    </svg>
                    <h1 style="margin-bottom: 10px; font-size: 24px;">Erro ao Carregar</h1>
                    <p style="color: #a0a0b0; margin-bottom: 20px;">
                        Ocorreu um erro ao inicializar a aplicacao.<br>
                        Por favor, recarregue a pagina.
                    </p>
                    <button onclick="location.reload()" style="
                        padding: 10px 24px;
                        background: #4f46e5;
                        color: white;
                        border: none;
                        border-radius: 8px;
                        font-size: 16px;
                        cursor: pointer;
                    ">
                        Recarregar Pagina
                    </button>
                </div>
            `;
        }
    }
}

// Aguardar DOM carregar
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', bootstrap);
} else {
    bootstrap();
}

// Tratar erros nao capturados
window.addEventListener('error', (event) => {
    console.error('[SkyCamOS] Erro global:', event.error);
});

window.addEventListener('unhandledrejection', (event) => {
    console.error('[SkyCamOS] Promise rejeitada:', event.reason);
});

// Exportar funcao de bootstrap para testes
export { bootstrap };
