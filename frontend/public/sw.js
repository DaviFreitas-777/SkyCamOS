/**
 * SkyCamOS - Service Worker
 * PWA com cache, push notifications e background sync
 */

const CACHE_NAME = 'skycamos-v2';
const STATIC_CACHE = 'skycamos-static-v2';
const DYNAMIC_CACHE = 'skycamos-dynamic-v2';

// Arquivos para cache estatico
const STATIC_ASSETS = [
    '/',
    '/index.html',
    '/src/index.js',
    '/src/App.js',
    '/src/styles/main.css',
    '/src/styles/theme.css',
    '/src/styles/components.css',
    '/manifest.json',
    '/icons/icon-192x192.svg',
    '/icons/icon-512x512.svg'
];

// Instalar Service Worker
self.addEventListener('install', (event) => {
    console.log('[SW] Instalando Service Worker...');

    event.waitUntil(
        caches.open(STATIC_CACHE)
            .then((cache) => {
                console.log('[SW] Cache de assets estaticos');
                return cache.addAll(STATIC_ASSETS);
            })
            .then(() => self.skipWaiting())
            .catch((err) => console.log('[SW] Erro no cache:', err))
    );
});

// Ativar Service Worker
self.addEventListener('activate', (event) => {
    console.log('[SW] Service Worker ativado');

    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames
                    .filter((name) => name !== STATIC_CACHE && name !== DYNAMIC_CACHE)
                    .map((name) => {
                        console.log('[SW] Removendo cache antigo:', name);
                        return caches.delete(name);
                    })
            );
        }).then(() => self.clients.claim())
    );
});

// Interceptar requisicoes
self.addEventListener('fetch', (event) => {
    const url = new URL(event.request.url);

    // Ignorar requisicoes de API e WebSocket
    if (url.pathname.startsWith('/api/') || url.protocol === 'ws:' || url.protocol === 'wss:') {
        return;
    }

    // Arquivos JS sempre usam Network First (para pegar atualizacoes)
    if (url.pathname.endsWith('.js')) {
        event.respondWith(
            fetch(event.request)
                .then((response) => {
                    const responseClone = response.clone();
                    caches.open(DYNAMIC_CACHE)
                        .then((cache) => cache.put(event.request, responseClone));
                    return response;
                })
                .catch(() => caches.match(event.request))
        );
        return;
    }

    // Estrategia: Cache First para assets estaticos (CSS, imagens, fontes)
    if (STATIC_ASSETS.some(asset => url.pathname.endsWith(asset) || url.pathname === asset)) {
        event.respondWith(
            caches.match(event.request)
                .then((response) => response || fetch(event.request))
        );
        return;
    }

    // Estrategia: Network First para paginas dinamicas
    event.respondWith(
        fetch(event.request)
            .then((response) => {
                // Clonar resposta para cache
                const responseClone = response.clone();
                caches.open(DYNAMIC_CACHE)
                    .then((cache) => cache.put(event.request, responseClone));
                return response;
            })
            .catch(() => {
                // Fallback para cache se offline
                return caches.match(event.request)
                    .then((response) => {
                        if (response) return response;
                        // Retornar pagina offline se necessario
                        if (event.request.mode === 'navigate') {
                            return caches.match('/');
                        }
                    });
            })
    );
});

// Push Notifications
self.addEventListener('push', (event) => {
    console.log('[SW] Push notification recebida');

    let data = {
        title: 'SkyCamOS',
        body: 'Nova notificacao',
        icon: '/icons/icon-192x192.svg',
        badge: '/icons/icon-96x96.svg',
        tag: 'skycamos-notification',
        data: {}
    };

    if (event.data) {
        try {
            const payload = event.data.json();
            data = { ...data, ...payload };
        } catch (e) {
            data.body = event.data.text();
        }
    }

    const options = {
        body: data.body,
        icon: data.icon,
        badge: data.badge,
        tag: data.tag,
        vibrate: [100, 50, 100],
        data: data.data,
        actions: [
            { action: 'view', title: 'Ver' },
            { action: 'dismiss', title: 'Dispensar' }
        ],
        requireInteraction: data.type === 'motion' || data.type === 'alert'
    };

    event.waitUntil(
        self.registration.showNotification(data.title, options)
    );
});

// Clique em notificacao
self.addEventListener('notificationclick', (event) => {
    console.log('[SW] Clique na notificacao:', event.action);

    event.notification.close();

    if (event.action === 'dismiss') {
        return;
    }

    // Abrir ou focar na janela
    const urlToOpen = event.notification.data?.url || '/#/dashboard';

    event.waitUntil(
        clients.matchAll({ type: 'window', includeUncontrolled: true })
            .then((windowClients) => {
                // Verificar se ja tem uma janela aberta
                for (const client of windowClients) {
                    if (client.url.includes(self.location.origin) && 'focus' in client) {
                        client.navigate(urlToOpen);
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

// Background Sync
self.addEventListener('sync', (event) => {
    console.log('[SW] Background sync:', event.tag);

    if (event.tag === 'sync-events') {
        event.waitUntil(syncEvents());
    }
});

// Funcao para sincronizar eventos pendentes
async function syncEvents() {
    try {
        // Buscar eventos pendentes do IndexedDB
        const db = await openDatabase();
        const events = await getPendingEvents(db);

        for (const evt of events) {
            try {
                await fetch('/api/v1/events/sync', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(evt)
                });
                await markEventSynced(db, evt.id);
            } catch (e) {
                console.log('[SW] Erro ao sincronizar evento:', e);
            }
        }
    } catch (e) {
        console.log('[SW] Erro no sync:', e);
    }
}

// Helpers para IndexedDB
function openDatabase() {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open('skycamos-sw', 1);
        request.onerror = () => reject(request.error);
        request.onsuccess = () => resolve(request.result);
        request.onupgradeneeded = (event) => {
            const db = event.target.result;
            if (!db.objectStoreNames.contains('pending-events')) {
                db.createObjectStore('pending-events', { keyPath: 'id' });
            }
        };
    });
}

function getPendingEvents(db) {
    return new Promise((resolve, reject) => {
        const tx = db.transaction('pending-events', 'readonly');
        const store = tx.objectStore('pending-events');
        const request = store.getAll();
        request.onerror = () => reject(request.error);
        request.onsuccess = () => resolve(request.result);
    });
}

function markEventSynced(db, id) {
    return new Promise((resolve, reject) => {
        const tx = db.transaction('pending-events', 'readwrite');
        const store = tx.objectStore('pending-events');
        const request = store.delete(id);
        request.onerror = () => reject(request.error);
        request.onsuccess = () => resolve();
    });
}

// Mensagens do cliente
self.addEventListener('message', (event) => {
    if (event.data && event.data.type === 'SKIP_WAITING') {
        self.skipWaiting();
    }
});

console.log('[SW] Service Worker carregado');
