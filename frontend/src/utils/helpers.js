/**
 * SkyCamOS - Funcoes Auxiliares
 * Utilitarios gerais para a aplicacao
 */

/**
 * Gerar ID unico
 * @returns {string}
 */
export function generateId() {
    return Date.now().toString(36) + Math.random().toString(36).substr(2);
}

/**
 * Debounce - Atrasar execucao ate parar de chamar
 * @param {Function} func - Funcao a executar
 * @param {number} wait - Tempo de espera em ms
 * @returns {Function}
 */
export function debounce(func, wait = 300) {
    let timeout;

    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func.apply(this, args);
        };

        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Throttle - Limitar frequencia de execucao
 * @param {Function} func - Funcao a executar
 * @param {number} limit - Intervalo minimo em ms
 * @returns {Function}
 */
export function throttle(func, limit = 300) {
    let inThrottle;

    return function executedFunction(...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => {
                inThrottle = false;
            }, limit);
        }
    };
}

/**
 * Deep clone de objeto
 * @param {Object} obj - Objeto a clonar
 * @returns {Object}
 */
export function deepClone(obj) {
    if (obj === null || typeof obj !== 'object') {
        return obj;
    }

    if (obj instanceof Date) {
        return new Date(obj.getTime());
    }

    if (Array.isArray(obj)) {
        return obj.map(item => deepClone(item));
    }

    const cloned = {};
    for (const key in obj) {
        if (Object.prototype.hasOwnProperty.call(obj, key)) {
            cloned[key] = deepClone(obj[key]);
        }
    }

    return cloned;
}

/**
 * Merge profundo de objetos
 * @param {Object} target - Objeto alvo
 * @param {...Object} sources - Objetos fonte
 * @returns {Object}
 */
export function deepMerge(target, ...sources) {
    if (!sources.length) return target;

    const source = sources.shift();

    if (isObject(target) && isObject(source)) {
        for (const key in source) {
            if (isObject(source[key])) {
                if (!target[key]) Object.assign(target, { [key]: {} });
                deepMerge(target[key], source[key]);
            } else {
                Object.assign(target, { [key]: source[key] });
            }
        }
    }

    return deepMerge(target, ...sources);
}

/**
 * Verificar se e objeto
 * @param {any} item - Item a verificar
 * @returns {boolean}
 */
export function isObject(item) {
    return item && typeof item === 'object' && !Array.isArray(item);
}

/**
 * Capitalizar primeira letra
 * @param {string} str - String
 * @returns {string}
 */
export function capitalize(str) {
    if (!str) return '';
    return str.charAt(0).toUpperCase() + str.slice(1).toLowerCase();
}

/**
 * Truncar texto com ellipsis
 * @param {string} str - String
 * @param {number} maxLength - Tamanho maximo
 * @returns {string}
 */
export function truncate(str, maxLength = 50) {
    if (!str || str.length <= maxLength) return str;
    return str.substring(0, maxLength - 3) + '...';
}

/**
 * Formatar bytes para tamanho legivel
 * @param {number} bytes - Tamanho em bytes
 * @param {number} decimals - Casas decimais
 * @returns {string}
 */
export function formatBytes(bytes, decimals = 2) {
    if (bytes === 0) return '0 Bytes';

    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB'];

    const i = Math.floor(Math.log(bytes) / Math.log(k));

    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

/**
 * Formatar duracao em segundos para HH:MM:SS
 * @param {number} seconds - Duracao em segundos
 * @returns {string}
 */
export function formatDuration(seconds) {
    if (!seconds || seconds < 0) return '00:00';

    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);

    if (hours > 0) {
        return `${padZero(hours)}:${padZero(minutes)}:${padZero(secs)}`;
    }

    return `${padZero(minutes)}:${padZero(secs)}`;
}

/**
 * Adicionar zero a esquerda
 * @param {number} num - Numero
 * @param {number} size - Tamanho desejado
 * @returns {string}
 */
export function padZero(num, size = 2) {
    return String(num).padStart(size, '0');
}

/**
 * Verificar se esta no modo mobile
 * @returns {boolean}
 */
export function isMobile() {
    return window.innerWidth < 768;
}

/**
 * Verificar se esta no modo tablet
 * @returns {boolean}
 */
export function isTablet() {
    return window.innerWidth >= 768 && window.innerWidth < 1024;
}

/**
 * Verificar se esta no modo desktop
 * @returns {boolean}
 */
export function isDesktop() {
    return window.innerWidth >= 1024;
}

/**
 * Obter query params da URL
 * @param {string} url - URL (opcional, usa window.location)
 * @returns {Object}
 */
export function getQueryParams(url = window.location.href) {
    const params = {};
    const urlObj = new URL(url);

    urlObj.searchParams.forEach((value, key) => {
        params[key] = value;
    });

    return params;
}

/**
 * Construir URL com query params
 * @param {string} baseUrl - URL base
 * @param {Object} params - Parametros
 * @returns {string}
 */
export function buildUrl(baseUrl, params = {}) {
    const url = new URL(baseUrl, window.location.origin);

    Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') {
            url.searchParams.append(key, value);
        }
    });

    return url.toString();
}

/**
 * Copiar texto para clipboard
 * @param {string} text - Texto a copiar
 * @returns {Promise<boolean>}
 */
export async function copyToClipboard(text) {
    try {
        if (navigator.clipboard && window.isSecureContext) {
            await navigator.clipboard.writeText(text);
            return true;
        }

        // Fallback para navegadores antigos
        const textArea = document.createElement('textarea');
        textArea.value = text;
        textArea.style.position = 'fixed';
        textArea.style.left = '-999999px';
        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand('copy');
        textArea.remove();
        return true;
    } catch (error) {
        console.error('Erro ao copiar para clipboard:', error);
        return false;
    }
}

/**
 * Aguardar tempo especificado
 * @param {number} ms - Tempo em milissegundos
 * @returns {Promise<void>}
 */
export function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Retry de funcao assincrona
 * @param {Function} fn - Funcao a executar
 * @param {number} retries - Numero de tentativas
 * @param {number} delay - Atraso entre tentativas
 * @returns {Promise<any>}
 */
export async function retry(fn, retries = 3, delay = 1000) {
    let lastError;

    for (let i = 0; i < retries; i++) {
        try {
            return await fn();
        } catch (error) {
            lastError = error;
            if (i < retries - 1) {
                await sleep(delay * (i + 1)); // Backoff exponencial
            }
        }
    }

    throw lastError;
}

/**
 * Criar elemento DOM a partir de string HTML
 * @param {string} html - String HTML
 * @returns {Element}
 */
export function createElementFromHTML(html) {
    const template = document.createElement('template');
    template.innerHTML = html.trim();
    return template.content.firstChild;
}

/**
 * Escapar HTML para prevenir XSS
 * @param {string} str - String a escapar
 * @returns {string}
 */
export function escapeHTML(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

/**
 * Verificar se elemento esta visivel na viewport
 * @param {Element} element - Elemento DOM
 * @returns {boolean}
 */
export function isElementInViewport(element) {
    const rect = element.getBoundingClientRect();

    return (
        rect.top >= 0 &&
        rect.left >= 0 &&
        rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
        rect.right <= (window.innerWidth || document.documentElement.clientWidth)
    );
}

/**
 * Obter posicao do scroll
 * @returns {Object}
 */
export function getScrollPosition() {
    return {
        x: window.pageXOffset || document.documentElement.scrollLeft,
        y: window.pageYOffset || document.documentElement.scrollTop
    };
}

/**
 * Rolar para topo suavemente
 */
export function scrollToTop() {
    window.scrollTo({
        top: 0,
        behavior: 'smooth'
    });
}

/**
 * Detectar suporte a WebRTC
 * @returns {boolean}
 */
export function supportsWebRTC() {
    return !!(
        window.RTCPeerConnection ||
        window.webkitRTCPeerConnection ||
        window.mozRTCPeerConnection
    );
}

/**
 * Detectar suporte a fullscreen
 * @returns {boolean}
 */
export function supportsFullscreen() {
    return !!(
        document.fullscreenEnabled ||
        document.webkitFullscreenEnabled ||
        document.mozFullScreenEnabled ||
        document.msFullscreenEnabled
    );
}

/**
 * Entrar em fullscreen
 * @param {Element} element - Elemento (opcional, usa document.documentElement)
 */
export function enterFullscreen(element = document.documentElement) {
    if (element.requestFullscreen) {
        element.requestFullscreen();
    } else if (element.webkitRequestFullscreen) {
        element.webkitRequestFullscreen();
    } else if (element.mozRequestFullScreen) {
        element.mozRequestFullScreen();
    } else if (element.msRequestFullscreen) {
        element.msRequestFullscreen();
    }
}

/**
 * Sair do fullscreen
 */
export function exitFullscreen() {
    if (document.exitFullscreen) {
        document.exitFullscreen();
    } else if (document.webkitExitFullscreen) {
        document.webkitExitFullscreen();
    } else if (document.mozCancelFullScreen) {
        document.mozCancelFullScreen();
    } else if (document.msExitFullscreen) {
        document.msExitFullscreen();
    }
}

/**
 * Verificar se esta em fullscreen
 * @returns {boolean}
 */
export function isFullscreen() {
    return !!(
        document.fullscreenElement ||
        document.webkitFullscreenElement ||
        document.mozFullScreenElement ||
        document.msFullscreenElement
    );
}

/**
 * Validar email
 * @param {string} email - Email
 * @returns {boolean}
 */
export function isValidEmail(email) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

/**
 * Validar IP
 * @param {string} ip - Endereco IP
 * @returns {boolean}
 */
export function isValidIP(ip) {
    return /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/.test(ip);
}

/**
 * Gerar cor baseada em string (para avatars)
 * @param {string} str - String base
 * @returns {string} - Cor em formato hex
 */
export function stringToColor(str) {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
        hash = str.charCodeAt(i) + ((hash << 5) - hash);
    }

    const hue = hash % 360;
    return `hsl(${hue}, 70%, 50%)`;
}

/**
 * Obter iniciais de nome
 * @param {string} name - Nome completo
 * @returns {string}
 */
export function getInitials(name) {
    if (!name) return '';

    return name
        .split(' ')
        .map(word => word.charAt(0))
        .slice(0, 2)
        .join('')
        .toUpperCase();
}
