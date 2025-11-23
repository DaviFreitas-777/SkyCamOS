/**
 * SkyCamOS - Configuracao de Ambiente
 * Este arquivo configura as variaveis de ambiente para o frontend
 */

// Detectar ambiente - localhost, 127.0.0.1 ou IP de rede local
const hostname = window.location.hostname;
const isLocalhost = hostname === 'localhost' || hostname === '127.0.0.1';
const isLocalNetwork = /^(192\.168\.|10\.|172\.(1[6-9]|2[0-9]|3[0-1])\.)/.test(hostname);
const isDevelopment = isLocalhost || isLocalNetwork;

// URL do backend
// Em rede local: usa o mesmo IP do frontend, porta 8000
// Em localhost: localhost:8000
// Em producao: configurar via window.ENV
const BACKEND_URL = isLocalNetwork
    ? `http://${hostname}:8000`
    : isLocalhost
        ? 'http://localhost:8000'
        : (window.ENV?.API_BASE_URL || 'https://seu-backend.com');

// WebSocket URL
const WS_URL = isLocalNetwork
    ? `ws://${hostname}:8000/api/v1/stream/ws`
    : isLocalhost
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
