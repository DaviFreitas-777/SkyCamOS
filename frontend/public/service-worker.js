/**
 * SkyCamOS - Service Worker
 * Responsavel pelo cache offline e funcionalidades PWA
 */

const CACHE_NAME = 'skycamos-v1';
const RUNTIME_CACHE = 'skycamos-runtime-v1';

// Arquivos essenciais para cache inicial
const PRECACHE_URLS = [
    '/',
    '/index.html',
    '/manifest.json',
    '/src/styles/variables.css',
    '/src/styles/main.css',
    '/src/styles/components.css',
    '/src/index.js',
    '/src/App.js',
    '/src/services/api.js',
    '/src/services/websocket.js',
    '/src/services/auth.js',
    '/src/services/notifications.js',
    '/src/services/storage.js',
    '/src/utils/constants.js',
    '/src/utils/helpers.js',
    '/src/utils/dateFormatter.js',
    '/src/hooks/useCamera.js',
    '/src/hooks/useWebSocket.js',
    '/src/hooks/useAuth.js',
    '/src/hooks/useNotifications.js',
    '/src/components/Header.js',
    '/src/components/Sidebar.js',
    '/src/components/CameraGrid.js',
    '/src/components/CameraCard.js',
    '/src/components/VideoPlayer.js',
    '/src/components/Timeline.js',
    '/src/components/EventList.js',
    '/src/components/MosaicSelector.js',
    '/src/components/LoginForm.js',
    '/src/components/NotificationBell.js',
    '/src/pages/Dashboard.js',
    '/src/pages/Recordings.js',
    '/src/pages/Events.js',
    '/src/pages/Settings.js',
    '/src/pages/Login.js',
    '/icons/icon-192x192.svg',
    '/icons/icon-512x512.svg'
];

// URLs que devem ser sempre buscadas da rede
const NETWORK_ONLY_URLS = [
    '/api/stream',
    '/api/live',
    '/ws'
];

// URLs que devem usar cache primeiro
const CACHE_FIRST_URLS = [
    '/icons/',
    '/fonts/',
    '.woff',
    '.woff2',
    '.ttf'
];

/**
 * Evento de instalacao - Pre-cachear recursos essenciais
 */
self.addEventListener('install', (event) => {
    console.log('[SW] Instalando Service Worker...');

    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => {
                console.log('[SW] Pre-cacheando recursos...');
                // Adicionar recursos um por um para evitar falha total
                return Promise.allSettled(
                    PRECACHE_URLS.map(url =>
                        cache.add(url).catch(err => {
                            console.warn(`[SW] Falha ao cachear ${url}:`, err.message);
                        })
                    )
                );
            })
            .then(() => {
                console.log('[SW] Pre-cache concluido');
                return self.skipWaiting();
            })
    );
});

/**
 * Evento de ativacao - Limpar caches antigos
 */
self.addEventListener('activate', (event) => {
    console.log('[SW] Ativando Service Worker...');

    event.waitUntil(
        caches.keys()
            .then((cacheNames) => {
                return Promise.all(
                    cacheNames
                        .filter((name) => name !== CACHE_NAME && name !== RUNTIME_CACHE)
                        .map((name) => {
                            console.log('[SW] Removendo cache antigo:', name);
                            return caches.delete(name);
                        })
                );
            })
            .then(() => {
                console.log('[SW] Assumindo controle de todos os clientes');
                return self.clients.claim();
            })
    );
});

/**
 * Estrategia de cache - Stale While Revalidate
 */
async function staleWhileRevalidate(request) {
    const cache = await caches.open(RUNTIME_CACHE);
    const cachedResponse = await cache.match(request);

    const fetchPromise = fetch(request)
        .then((networkResponse) => {
            if (networkResponse.ok) {
                cache.put(request, networkResponse.clone());
            }
            return networkResponse;
        })
        .catch(() => null);

    return cachedResponse || fetchPromise;
}

/**
 * Estrategia de cache - Cache First
 */
async function cacheFirst(request) {
    const cache = await caches.open(CACHE_NAME);
    const cachedResponse = await cache.match(request);

    if (cachedResponse) {
        return cachedResponse;
    }

    try {
        const networkResponse = await fetch(request);
        if (networkResponse.ok) {
            cache.put(request, networkResponse.clone());
        }
        return networkResponse;
    } catch (error) {
        console.error('[SW] Falha ao buscar recurso:', request.url);
        return new Response('Offline', { status: 503 });
    }
}

/**
 * Estrategia de cache - Network First
 */
async function networkFirst(request) {
    try {
        const networkResponse = await fetch(request);

        if (networkResponse.ok) {
            const cache = await caches.open(RUNTIME_CACHE);
            cache.put(request, networkResponse.clone());
        }

        return networkResponse;
    } catch (error) {
        const cache = await caches.open(RUNTIME_CACHE);
        const cachedResponse = await cache.match(request);

        if (cachedResponse) {
            return cachedResponse;
        }

        // Retornar pagina offline para navegacao
        if (request.mode === 'navigate') {
            const offlineCache = await caches.open(CACHE_NAME);
            return offlineCache.match('/index.html');
        }

        return new Response('Offline', { status: 503 });
    }
}

/**
 * Evento de fetch - Interceptar requisicoes
 */
self.addEventListener('fetch', (event) => {
    const { request } = event;
    const url = new URL(request.url);

    // Ignorar requisicoes para outros dominios
    if (url.origin !== location.origin) {
        return;
    }

    // Ignorar requisicoes WebSocket
    if (request.url.includes('/ws')) {
        return;
    }

    // Network only para streams ao vivo
    if (NETWORK_ONLY_URLS.some(path => request.url.includes(path))) {
        event.respondWith(fetch(request));
        return;
    }

    // Cache first para recursos estaticos
    if (CACHE_FIRST_URLS.some(path => request.url.includes(path))) {
        event.respondWith(cacheFirst(request));
        return;
    }

    // Requisicoes de API - Network first
    if (request.url.includes('/api/')) {
        event.respondWith(networkFirst(request));
        return;
    }

    // Navegacao - Stale while revalidate
    if (request.mode === 'navigate') {
        event.respondWith(
            caches.match('/index.html')
                .then(response => response || fetch(request))
        );
        return;
    }

    // Demais recursos - Stale while revalidate
    event.respondWith(staleWhileRevalidate(request));
});

/**
 * Evento de push - Notificacoes push
 */
self.addEventListener('push', (event) => {
    console.log('[SW] Notificacao push recebida');

    let data = {
        title: 'SkyCamOS',
        body: 'Nova notificacao',
        icon: '/icons/icon-192x192.svg',
        badge: '/icons/icon-96x96.svg',
        tag: 'default',
        data: {}
    };

    if (event.data) {
        try {
            data = { ...data, ...event.data.json() };
        } catch (e) {
            data.body = event.data.text();
        }
    }

    const options = {
        body: data.body,
        icon: data.icon,
        badge: data.badge,
        tag: data.tag,
        data: data.data,
        vibrate: [200, 100, 200],
        requireInteraction: data.requireInteraction || false,
        actions: data.actions || [
            { action: 'view', title: 'Ver' },
            { action: 'dismiss', title: 'Dispensar' }
        ]
    };

    event.waitUntil(
        self.registration.showNotification(data.title, options)
    );
});

/**
 * Evento de click em notificacao
 */
self.addEventListener('notificationclick', (event) => {
    console.log('[SW] Click em notificacao:', event.action);

    event.notification.close();

    const action = event.action;
    const data = event.notification.data || {};

    if (action === 'dismiss') {
        return;
    }

    // URL para abrir baseada nos dados da notificacao
    let urlToOpen = '/';

    if (data.type === 'event') {
        urlToOpen = `/#/events/${data.eventId}`;
    } else if (data.type === 'camera') {
        urlToOpen = `/#/dashboard?camera=${data.cameraId}`;
    } else if (data.url) {
        urlToOpen = data.url;
    }

    event.waitUntil(
        clients.matchAll({ type: 'window', includeUncontrolled: true })
            .then((clientList) => {
                // Verificar se ja existe uma janela aberta
                for (const client of clientList) {
                    if (client.url.includes(self.location.origin) && 'focus' in client) {
                        client.postMessage({
                            type: 'NOTIFICATION_CLICK',
                            data: data,
                            url: urlToOpen
                        });
                        return client.focus();
                    }
                }

                // Abrir nova janela
                if (clients.openWindow) {
                    return clients.openWindow(urlToOpen);
                }
            })
    );
});

/**
 * Evento de fechamento de notificacao
 */
self.addEventListener('notificationclose', (event) => {
    console.log('[SW] Notificacao fechada:', event.notification.tag);
});

/**
 * Evento de mensagem do cliente
 */
self.addEventListener('message', (event) => {
    console.log('[SW] Mensagem recebida:', event.data);

    if (event.data.type === 'SKIP_WAITING') {
        self.skipWaiting();
    }

    if (event.data.type === 'CLEAR_CACHE') {
        event.waitUntil(
            caches.keys().then((names) =>
                Promise.all(names.map(name => caches.delete(name)))
            )
        );
    }

    if (event.data.type === 'CACHE_URLS') {
        const urls = event.data.urls || [];
        event.waitUntil(
            caches.open(RUNTIME_CACHE)
                .then(cache => cache.addAll(urls))
        );
    }
});

/**
 * Evento de sincronizacao em background
 */
self.addEventListener('sync', (event) => {
    console.log('[SW] Sync event:', event.tag);

    if (event.tag === 'sync-events') {
        event.waitUntil(syncEvents());
    }

    if (event.tag === 'sync-settings') {
        event.waitUntil(syncSettings());
    }
});

/**
 * Sincronizar eventos pendentes
 */
async function syncEvents() {
    try {
        // Buscar eventos pendentes do IndexedDB
        // Implementar quando o storage estiver pronto
        console.log('[SW] Sincronizando eventos...');
    } catch (error) {
        console.error('[SW] Erro ao sincronizar eventos:', error);
    }
}

/**
 * Sincronizar configuracoes
 */
async function syncSettings() {
    try {
        console.log('[SW] Sincronizando configuracoes...');
    } catch (error) {
        console.error('[SW] Erro ao sincronizar configuracoes:', error);
    }
}

/**
 * Evento de periodic sync (Background Sync periodico)
 */
self.addEventListener('periodicsync', (event) => {
    console.log('[SW] Periodic sync:', event.tag);

    if (event.tag === 'check-cameras') {
        event.waitUntil(checkCamerasStatus());
    }
});

/**
 * Verificar status das cameras
 */
async function checkCamerasStatus() {
    try {
        const response = await fetch('/api/cameras/status');
        const data = await response.json();

        // Notificar sobre cameras offline
        const offlineCameras = data.cameras?.filter(c => !c.online) || [];

        if (offlineCameras.length > 0) {
            await self.registration.showNotification('Cameras Offline', {
                body: `${offlineCameras.length} camera(s) estao offline`,
                icon: '/icons/icon-192x192.svg',
                badge: '/icons/icon-96x96.svg',
                tag: 'camera-status',
                data: { type: 'camera-status', cameras: offlineCameras }
            });
        }
    } catch (error) {
        console.error('[SW] Erro ao verificar cameras:', error);
    }
}

console.log('[SW] Service Worker carregado');
