/**
 * SkyCamOS - Constantes da Aplicacao
 * Valores constantes usados em toda a aplicacao
 */

// ==========================================
// Configuracoes de API
// ==========================================

/**
 * URL base da API
 * Pode ser sobrescrito por variavel de ambiente
 */
export const API_BASE_URL = window.ENV?.API_BASE_URL || 'http://localhost:8000';

/**
 * URL do WebSocket
 */
export const WS_URL = window.ENV?.WS_URL || 'ws://localhost:8000/ws';

/**
 * Timeout padrao para requisicoes HTTP (ms)
 */
export const API_TIMEOUT = 30000;

/**
 * Intervalo de reconexao WebSocket (ms)
 */
export const WS_RECONNECT_INTERVAL = 3000;

/**
 * Maximo de tentativas de reconexao WebSocket
 */
export const WS_MAX_RECONNECT_ATTEMPTS = 10;

// ==========================================
// Configuracoes de Storage
// ==========================================

/**
 * Nome do banco IndexedDB
 */
export const DB_NAME = 'SkyCamOS';

/**
 * Versao do banco IndexedDB
 */
export const DB_VERSION = 1;

/**
 * Chaves de storage
 */
export const STORAGE_KEYS = {
    AUTH_TOKEN: 'skycamos_auth_token',
    USER: 'skycamos_user',
    THEME: 'skycamos_theme',
    LANGUAGE: 'skycamos_language',
    MOSAIC_LAYOUT: 'skycamos_mosaic_layout',
    SELECTED_CAMERAS: 'skycamos_selected_cameras',
    NOTIFICATION_SETTINGS: 'skycamos_notification_settings',
    LAST_SYNC: 'skycamos_last_sync'
};

// ==========================================
// Layouts de Mosaico
// ==========================================

export const MOSAIC_LAYOUTS = {
    '1x1': { rows: 1, cols: 1, max: 1 },
    '2x2': { rows: 2, cols: 2, max: 4 },
    '3x3': { rows: 3, cols: 3, max: 9 },
    '4x4': { rows: 4, cols: 4, max: 16 },
    '1+5': { rows: 2, cols: 3, max: 6, special: true },
    '2+8': { rows: 3, cols: 4, max: 10, special: true }
};

// ==========================================
// Tipos de Eventos
// ==========================================

export const EVENT_TYPES = {
    MOTION: 'motion',
    PERSON: 'person',
    VEHICLE: 'vehicle',
    FACE: 'face',
    LINE_CROSSING: 'line_crossing',
    ZONE_INTRUSION: 'zone_intrusion',
    CAMERA_OFFLINE: 'camera_offline',
    CAMERA_ONLINE: 'camera_online',
    RECORDING_START: 'recording_start',
    RECORDING_STOP: 'recording_stop',
    STORAGE_WARNING: 'storage_warning',
    SYSTEM_ERROR: 'system_error'
};

/**
 * Labels para tipos de eventos
 */
export const EVENT_TYPE_LABELS = {
    [EVENT_TYPES.MOTION]: 'Movimento',
    [EVENT_TYPES.PERSON]: 'Pessoa',
    [EVENT_TYPES.VEHICLE]: 'Veiculo',
    [EVENT_TYPES.FACE]: 'Face',
    [EVENT_TYPES.LINE_CROSSING]: 'Cruzamento de Linha',
    [EVENT_TYPES.ZONE_INTRUSION]: 'Intrusao de Zona',
    [EVENT_TYPES.CAMERA_OFFLINE]: 'Camera Offline',
    [EVENT_TYPES.CAMERA_ONLINE]: 'Camera Online',
    [EVENT_TYPES.RECORDING_START]: 'Gravacao Iniciada',
    [EVENT_TYPES.RECORDING_STOP]: 'Gravacao Parada',
    [EVENT_TYPES.STORAGE_WARNING]: 'Alerta de Armazenamento',
    [EVENT_TYPES.SYSTEM_ERROR]: 'Erro do Sistema'
};

// ==========================================
// Status de Camera
// ==========================================

export const CAMERA_STATUS = {
    ONLINE: 'online',
    OFFLINE: 'offline',
    RECORDING: 'recording',
    ERROR: 'error',
    CONNECTING: 'connecting'
};

/**
 * Labels para status de camera
 */
export const CAMERA_STATUS_LABELS = {
    [CAMERA_STATUS.ONLINE]: 'Online',
    [CAMERA_STATUS.OFFLINE]: 'Offline',
    [CAMERA_STATUS.RECORDING]: 'Gravando',
    [CAMERA_STATUS.ERROR]: 'Erro',
    [CAMERA_STATUS.CONNECTING]: 'Conectando'
};

// ==========================================
// Rotas da Aplicacao
// ==========================================

export const ROUTES = {
    HOME: '/',
    LOGIN: '/login',
    DASHBOARD: '/dashboard',
    RECORDINGS: '/recordings',
    EVENTS: '/events',
    SETTINGS: '/settings',
    CAMERA: '/camera/:id',
    EVENT_DETAIL: '/events/:id'
};

// ==========================================
// Navegacao do Menu
// ==========================================

export const MENU_ITEMS = [
    {
        id: 'dashboard',
        label: 'Dashboard',
        icon: 'grid',
        route: ROUTES.DASHBOARD,
        permission: null
    },
    {
        id: 'recordings',
        label: 'Gravacoes',
        icon: 'video',
        route: ROUTES.RECORDINGS,
        permission: 'recordings.view'
    },
    {
        id: 'events',
        label: 'Eventos',
        icon: 'bell',
        route: ROUTES.EVENTS,
        permission: 'events.view'
    },
    {
        id: 'settings',
        label: 'Configuracoes',
        icon: 'settings',
        route: ROUTES.SETTINGS,
        permission: 'settings.view'
    }
];

// ==========================================
// Configuracoes de Video
// ==========================================

export const VIDEO_CONFIG = {
    // Qualidades disponiveis
    QUALITIES: [
        { id: 'auto', label: 'Automatico', bitrate: 0 },
        { id: '1080p', label: '1080p', bitrate: 5000000 },
        { id: '720p', label: '720p', bitrate: 2500000 },
        { id: '480p', label: '480p', bitrate: 1000000 },
        { id: '360p', label: '360p', bitrate: 500000 }
    ],

    // Intervalo de keyframes (segundos)
    KEYFRAME_INTERVAL: 2,

    // Buffer de latencia (segundos)
    LIVE_LATENCY: 1,

    // Timeout de conexao de stream (ms)
    STREAM_TIMEOUT: 10000
};

// ==========================================
// Configuracoes de Paginacao
// ==========================================

export const PAGINATION = {
    DEFAULT_PAGE_SIZE: 20,
    PAGE_SIZE_OPTIONS: [10, 20, 50, 100],
    MAX_PAGES_SHOWN: 5
};

// ==========================================
// Breakpoints (para JavaScript)
// ==========================================

export const BREAKPOINTS = {
    SM: 640,
    MD: 768,
    LG: 1024,
    XL: 1280,
    XXL: 1536
};

// ==========================================
// Mensagens de Erro
// ==========================================

export const ERROR_MESSAGES = {
    NETWORK_ERROR: 'Erro de conexao. Verifique sua internet.',
    UNAUTHORIZED: 'Sessao expirada. Faca login novamente.',
    FORBIDDEN: 'Voce nao tem permissao para esta acao.',
    NOT_FOUND: 'Recurso nao encontrado.',
    SERVER_ERROR: 'Erro interno do servidor.',
    VALIDATION_ERROR: 'Dados invalidos.',
    CAMERA_OFFLINE: 'Camera offline. Verifique a conexao.',
    STREAM_ERROR: 'Erro ao carregar stream de video.'
};

// ==========================================
// Configuracoes de Notificacao
// ==========================================

export const NOTIFICATION_SETTINGS = {
    // Duracao padrao do toast (ms)
    TOAST_DURATION: 5000,

    // Maximo de toasts visiveis
    MAX_TOASTS: 5,

    // Tipos de notificacao
    TYPES: {
        SUCCESS: 'success',
        ERROR: 'error',
        WARNING: 'warning',
        INFO: 'info'
    }
};

// ==========================================
// Regex de Validacao
// ==========================================

export const VALIDATION_REGEX = {
    EMAIL: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
    IP_ADDRESS: /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/,
    RTSP_URL: /^rtsp:\/\/.+/,
    PORT: /^([1-9][0-9]{0,3}|[1-5][0-9]{4}|6[0-4][0-9]{3}|65[0-4][0-9]{2}|655[0-2][0-9]|6553[0-5])$/
};

// ==========================================
// Versao da Aplicacao
// ==========================================

export const APP_VERSION = '1.0.0';
export const APP_NAME = 'SkyCamOS';
