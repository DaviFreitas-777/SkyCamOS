/**
 * SkyCamOS - Formatador de Datas
 * Utilitarios para formatacao e manipulacao de datas
 */

/**
 * Formatar data para exibicao
 * @param {Date|string|number} date - Data
 * @param {Object} options - Opcoes de formatacao
 * @returns {string}
 */
export function formatDate(date, options = {}) {
    const d = toDate(date);
    if (!d) return '';

    const defaultOptions = {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        ...options
    };

    return d.toLocaleDateString('pt-BR', defaultOptions);
}

/**
 * Formatar hora para exibicao
 * @param {Date|string|number} date - Data
 * @param {boolean} showSeconds - Mostrar segundos
 * @returns {string}
 */
export function formatTime(date, showSeconds = false) {
    const d = toDate(date);
    if (!d) return '';

    const options = {
        hour: '2-digit',
        minute: '2-digit',
        ...(showSeconds && { second: '2-digit' })
    };

    return d.toLocaleTimeString('pt-BR', options);
}

/**
 * Formatar data e hora
 * @param {Date|string|number} date - Data
 * @param {boolean} showSeconds - Mostrar segundos
 * @returns {string}
 */
export function formatDateTime(date, showSeconds = false) {
    const d = toDate(date);
    if (!d) return '';

    return `${formatDate(d)} ${formatTime(d, showSeconds)}`;
}

/**
 * Formatar data relativa (ex: "ha 5 minutos")
 * @param {Date|string|number} date - Data
 * @returns {string}
 */
export function formatRelativeTime(date) {
    const d = toDate(date);
    if (!d) return '';

    const now = new Date();
    const diff = now.getTime() - d.getTime();
    const seconds = Math.floor(diff / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);
    const weeks = Math.floor(days / 7);
    const months = Math.floor(days / 30);
    const years = Math.floor(days / 365);

    // Futuro
    if (diff < 0) {
        const absDiff = Math.abs(diff);
        const absMinutes = Math.floor(absDiff / 60000);

        if (absMinutes < 1) return 'em breve';
        if (absMinutes < 60) return `em ${absMinutes} min`;

        const absHours = Math.floor(absMinutes / 60);
        if (absHours < 24) return `em ${absHours}h`;

        return formatDate(d);
    }

    // Passado
    if (seconds < 5) return 'agora';
    if (seconds < 60) return `ha ${seconds}s`;
    if (minutes < 60) return `ha ${minutes} min`;
    if (hours < 24) return `ha ${hours}h`;
    if (days < 7) return `ha ${days} dia${days > 1 ? 's' : ''}`;
    if (weeks < 4) return `ha ${weeks} semana${weeks > 1 ? 's' : ''}`;
    if (months < 12) return `ha ${months} mes${months > 1 ? 'es' : ''}`;

    return `ha ${years} ano${years > 1 ? 's' : ''}`;
}

/**
 * Formatar data para input datetime-local
 * @param {Date|string|number} date - Data
 * @returns {string}
 */
export function formatForInput(date) {
    const d = toDate(date);
    if (!d) return '';

    const year = d.getFullYear();
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    const hours = String(d.getHours()).padStart(2, '0');
    const minutes = String(d.getMinutes()).padStart(2, '0');

    return `${year}-${month}-${day}T${hours}:${minutes}`;
}

/**
 * Formatar data para API (ISO 8601)
 * @param {Date|string|number} date - Data
 * @returns {string}
 */
export function formatForAPI(date) {
    const d = toDate(date);
    if (!d) return '';

    return d.toISOString();
}

/**
 * Converter para objeto Date
 * @param {Date|string|number} date - Data
 * @returns {Date|null}
 */
export function toDate(date) {
    if (!date) return null;

    if (date instanceof Date) {
        return isNaN(date.getTime()) ? null : date;
    }

    const parsed = new Date(date);
    return isNaN(parsed.getTime()) ? null : parsed;
}

/**
 * Verificar se e uma data valida
 * @param {any} date - Data
 * @returns {boolean}
 */
export function isValidDate(date) {
    return toDate(date) !== null;
}

/**
 * Obter inicio do dia
 * @param {Date|string|number} date - Data
 * @returns {Date}
 */
export function startOfDay(date) {
    const d = toDate(date) || new Date();
    return new Date(d.getFullYear(), d.getMonth(), d.getDate(), 0, 0, 0, 0);
}

/**
 * Obter fim do dia
 * @param {Date|string|number} date - Data
 * @returns {Date}
 */
export function endOfDay(date) {
    const d = toDate(date) || new Date();
    return new Date(d.getFullYear(), d.getMonth(), d.getDate(), 23, 59, 59, 999);
}

/**
 * Obter inicio da semana (domingo)
 * @param {Date|string|number} date - Data
 * @returns {Date}
 */
export function startOfWeek(date) {
    const d = toDate(date) || new Date();
    const day = d.getDay();
    const diff = d.getDate() - day;
    return startOfDay(new Date(d.setDate(diff)));
}

/**
 * Obter fim da semana (sabado)
 * @param {Date|string|number} date - Data
 * @returns {Date}
 */
export function endOfWeek(date) {
    const d = toDate(date) || new Date();
    const day = d.getDay();
    const diff = d.getDate() + (6 - day);
    return endOfDay(new Date(d.setDate(diff)));
}

/**
 * Obter inicio do mes
 * @param {Date|string|number} date - Data
 * @returns {Date}
 */
export function startOfMonth(date) {
    const d = toDate(date) || new Date();
    return new Date(d.getFullYear(), d.getMonth(), 1, 0, 0, 0, 0);
}

/**
 * Obter fim do mes
 * @param {Date|string|number} date - Data
 * @returns {Date}
 */
export function endOfMonth(date) {
    const d = toDate(date) || new Date();
    return new Date(d.getFullYear(), d.getMonth() + 1, 0, 23, 59, 59, 999);
}

/**
 * Adicionar tempo a data
 * @param {Date|string|number} date - Data base
 * @param {number} amount - Quantidade
 * @param {string} unit - Unidade (seconds, minutes, hours, days, weeks, months, years)
 * @returns {Date}
 */
export function addTime(date, amount, unit) {
    const d = toDate(date);
    if (!d) return null;

    const result = new Date(d);

    switch (unit) {
        case 'seconds':
            result.setSeconds(result.getSeconds() + amount);
            break;
        case 'minutes':
            result.setMinutes(result.getMinutes() + amount);
            break;
        case 'hours':
            result.setHours(result.getHours() + amount);
            break;
        case 'days':
            result.setDate(result.getDate() + amount);
            break;
        case 'weeks':
            result.setDate(result.getDate() + (amount * 7));
            break;
        case 'months':
            result.setMonth(result.getMonth() + amount);
            break;
        case 'years':
            result.setFullYear(result.getFullYear() + amount);
            break;
    }

    return result;
}

/**
 * Subtrair tempo da data
 * @param {Date|string|number} date - Data base
 * @param {number} amount - Quantidade
 * @param {string} unit - Unidade
 * @returns {Date}
 */
export function subtractTime(date, amount, unit) {
    return addTime(date, -amount, unit);
}

/**
 * Diferenca entre duas datas em unidade especifica
 * @param {Date|string|number} date1 - Primeira data
 * @param {Date|string|number} date2 - Segunda data
 * @param {string} unit - Unidade
 * @returns {number}
 */
export function diffTime(date1, date2, unit = 'days') {
    const d1 = toDate(date1);
    const d2 = toDate(date2);

    if (!d1 || !d2) return 0;

    const diffMs = d1.getTime() - d2.getTime();

    switch (unit) {
        case 'seconds':
            return Math.floor(diffMs / 1000);
        case 'minutes':
            return Math.floor(diffMs / (1000 * 60));
        case 'hours':
            return Math.floor(diffMs / (1000 * 60 * 60));
        case 'days':
            return Math.floor(diffMs / (1000 * 60 * 60 * 24));
        case 'weeks':
            return Math.floor(diffMs / (1000 * 60 * 60 * 24 * 7));
        case 'months':
            return Math.floor(diffMs / (1000 * 60 * 60 * 24 * 30));
        case 'years':
            return Math.floor(diffMs / (1000 * 60 * 60 * 24 * 365));
        default:
            return diffMs;
    }
}

/**
 * Verificar se data esta entre duas datas
 * @param {Date|string|number} date - Data a verificar
 * @param {Date|string|number} start - Data inicial
 * @param {Date|string|number} end - Data final
 * @returns {boolean}
 */
export function isBetween(date, start, end) {
    const d = toDate(date);
    const s = toDate(start);
    const e = toDate(end);

    if (!d || !s || !e) return false;

    return d >= s && d <= e;
}

/**
 * Verificar se data e hoje
 * @param {Date|string|number} date - Data
 * @returns {boolean}
 */
export function isToday(date) {
    const d = toDate(date);
    if (!d) return false;

    const today = new Date();

    return (
        d.getDate() === today.getDate() &&
        d.getMonth() === today.getMonth() &&
        d.getFullYear() === today.getFullYear()
    );
}

/**
 * Verificar se data e ontem
 * @param {Date|string|number} date - Data
 * @returns {boolean}
 */
export function isYesterday(date) {
    const d = toDate(date);
    if (!d) return false;

    const yesterday = subtractTime(new Date(), 1, 'days');

    return (
        d.getDate() === yesterday.getDate() &&
        d.getMonth() === yesterday.getMonth() &&
        d.getFullYear() === yesterday.getFullYear()
    );
}

/**
 * Obter nome do dia da semana
 * @param {Date|string|number} date - Data
 * @param {string} format - Formato (short, long)
 * @returns {string}
 */
export function getDayName(date, format = 'long') {
    const d = toDate(date);
    if (!d) return '';

    return d.toLocaleDateString('pt-BR', { weekday: format });
}

/**
 * Obter nome do mes
 * @param {Date|string|number} date - Data
 * @param {string} format - Formato (short, long)
 * @returns {string}
 */
export function getMonthName(date, format = 'long') {
    const d = toDate(date);
    if (!d) return '';

    return d.toLocaleDateString('pt-BR', { month: format });
}

/**
 * Gerar array de datas entre duas datas
 * @param {Date|string|number} start - Data inicial
 * @param {Date|string|number} end - Data final
 * @returns {Array<Date>}
 */
export function getDateRange(start, end) {
    const dates = [];
    const current = startOfDay(start);
    const endDate = startOfDay(end);

    while (current <= endDate) {
        dates.push(new Date(current));
        current.setDate(current.getDate() + 1);
    }

    return dates;
}

/**
 * Formatar duracao em formato legivel
 * @param {number} seconds - Duracao em segundos
 * @returns {string}
 */
export function formatDurationLong(seconds) {
    if (!seconds || seconds < 0) return '0 segundos';

    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);

    const parts = [];

    if (hours > 0) {
        parts.push(`${hours} hora${hours > 1 ? 's' : ''}`);
    }

    if (minutes > 0) {
        parts.push(`${minutes} minuto${minutes > 1 ? 's' : ''}`);
    }

    if (secs > 0 || parts.length === 0) {
        parts.push(`${secs} segundo${secs !== 1 ? 's' : ''}`);
    }

    return parts.join(', ');
}
