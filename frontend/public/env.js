/**
 * SkyCamOS - Configuracao de Ambiente
 * Este arquivo configura as variaveis de ambiente para o frontend
 */

// Detectar ambiente
const isDevelopment = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';

// URL do backend
// Em desenvolvimento: localhost:8000
// Em producao: configurar via Vercel Environment Variables
const BACKEND_URL = isDevelopment
    ? 'http://localhost:8000'
    : (window.ENV?.API_BASE_URL || 'https://seu-backend.com');

// WebSocket URL
const WS_URL = isDevelopment
    ? 'ws://localhost:8000/api/v1/stream/ws'
    : (window.ENV?.WS_URL || BACKEND_URL.replace('https://', 'wss://').replace('http://', 'ws://') + '/api/v1/stream/ws');

// Exportar configuracoes
window.ENV = {
    API_BASE_URL: BACKEND_URL,
    WS_URL: WS_URL,
    IS_DEVELOPMENT: isDevelopment,
    APP_VERSION: '1.0.0',
    APP_NAME: 'SkyCamOS'
};

console.log('[ENV] Ambiente:', isDevelopment ? 'Desenvolvimento' : 'Producao');
console.log('[ENV] API:', window.ENV.API_BASE_URL);
