/**
 * SkyCamOS - Service Worker
 * PWA com cache, push notifications e background sync
 */

const CACHE_NAME = 'skycamos-v4';
const STATIC_CACHE = 'skycamos-static-v4';
const DYNAMIC_CACHE = 'skycamos-dynamic-v4';

// Arquivos para cache estatico
const STATIC_ASSETS = [
    '/',
    '/index.html',
    '/src/index.js',
    '/src/App.js',
    '/src/styles/main.css',
    '/src/styles/components.css',
    '/manifest.json',
    '/icons/icon-192x192.svg',
    '/icons/icon-512x512.svg'
];

// Timeout para requisicoes de rede (5 segundos)
const NETWORK_TIMEOUT = 5000;

// Funcao helper para fetch com timeout
function fetchWithTimeout(request, timeout = NETWORK_TIMEOUT) {
    return Promise.race([
        fetch(request),
        new Promise((_, reject) =>
            setTimeout(() => reject(new Error('Network timeout')), timeout)
        )
    ]);
}

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

    // Arquivos JS sempre usam Network First com timeout (para pegar atualizacoes)
    if (url.pathname.endsWith('.js')) {
        event.respondWith(
            fetchWithTimeout(event.request)
                .then((response) => {
                    if (response.ok) {
                        const responseClone = response.clone();
                        caches.open(DYNAMIC_CACHE)
                            .then((cache) => cache.put(event.request, responseClone));
                    }
                    return response;
                })
                .catch((err) => {
                    console.log('[SW] Network timeout/error para JS, usando cache:', err.message);
                    return caches.match(event.request);
                })
        );
        return;
    }

    // Estrategia: Cache First para assets estaticos (CSS, imagens, fontes)
    if (STATIC_ASSETS.some(asset => url.pathname.endsWith(asset) || url.pathname === asset)) {
        event.respondWith(
            caches.match(event.request)
                .then((cachedResponse) => {
                    if (cachedResponse) {
                        // Atualiza cache em background (stale-while-revalidate)
                        fetch(event.request)
                            .then((networkResponse) => {
                                if (networkResponse.ok) {
                                    caches.open(STATIC_CACHE)
                                        .then((cache) => cache.put(event.request, networkResponse));
                                }
                            })
                            .catch(() => { /* Silencioso se offline */ });
                        return cachedResponse;
                    }
                    // Se nao estiver em cache, busca da rede
                    return fetch(event.request)
                        .then((response) => {
                            if (response.ok) {
                                const responseClone = response.clone();
                                caches.open(STATIC_CACHE)
                                    .then((cache) => cache.put(event.request, responseClone));
                            }
                            return response;
                        })
                        .catch((err) => {
                            console.log('[SW] Erro ao buscar asset estatico:', err.message);
                            return createOfflineResponse(event.request);
                        });
                })
        );
        return;
    }

    // Estrategia: Network First com timeout para paginas dinamicas
    event.respondWith(
        fetchWithTimeout(event.request)
            .then((response) => {
                if (response.ok) {
                    // Clonar resposta para cache
                    const responseClone = response.clone();
                    caches.open(DYNAMIC_CACHE)
                        .then((cache) => cache.put(event.request, responseClone));
                }
                return response;
            })
            .catch((err) => {
                console.log('[SW] Network timeout/error, usando fallback:', err.message);
                // Fallback para cache se offline
                return caches.match(event.request)
                    .then((response) => {
                        if (response) return response;
                        // Retornar pagina offline para navegacao
                        if (event.request.mode === 'navigate') {
                            return caches.match('/').then((indexResponse) => {
                                if (indexResponse) return indexResponse;
                                return createOfflinePage();
                            });
                        }
                        // Retornar resposta generica para outros assets
                        return createOfflineResponse(event.request);
                    });
            })
    );
});

// Criar resposta offline generica para assets faltando
function createOfflineResponse(request) {
    const url = new URL(request.url);
    const ext = url.pathname.split('.').pop().toLowerCase();

    // Resposta vazia apropriada para cada tipo de arquivo
    const responses = {
        'css': new Response('/* offline */', {
            status: 200,
            headers: { 'Content-Type': 'text/css' }
        }),
        'js': new Response('// offline', {
            status: 200,
            headers: { 'Content-Type': 'application/javascript' }
        }),
        'json': new Response('{}', {
            status: 200,
            headers: { 'Content-Type': 'application/json' }
        }),
        'svg': new Response('<svg xmlns="http://www.w3.org/2000/svg"></svg>', {
            status: 200,
            headers: { 'Content-Type': 'image/svg+xml' }
        }),
        'png': new Response('', {
            status: 200,
            headers: { 'Content-Type': 'image/png' }
        }),
        'jpg': new Response('', {
            status: 200,
            headers: { 'Content-Type': 'image/jpeg' }
        }),
        'jpeg': new Response('', {
            status: 200,
            headers: { 'Content-Type': 'image/jpeg' }
        })
    };

    return responses[ext] || new Response('Offline', {
        status: 503,
        statusText: 'Service Unavailable',
        headers: { 'Content-Type': 'text/plain' }
    });
}

// Criar pagina offline completa
function createOfflinePage() {
    const html = `
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SkyCamOS - Offline</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #fff;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .container {
            text-align: center;
            padding: 2rem;
        }
        .icon {
            font-size: 4rem;
            margin-bottom: 1rem;
        }
        h1 { margin-bottom: 0.5rem; font-size: 1.5rem; }
        p { color: #a0a0a0; margin-bottom: 1.5rem; }
        button {
            background: #0ea5e9;
            color: #fff;
            border: none;
            padding: 0.75rem 1.5rem;
            border-radius: 8px;
            cursor: pointer;
            font-size: 1rem;
        }
        button:hover { background: #0284c7; }
    </style>
</head>
<body>
    <div class="container">
        <div class="icon">&#128268;</div>
        <h1>Voce esta offline</h1>
        <p>Verifique sua conexao com a internet e tente novamente.</p>
        <button onclick="location.reload()">Tentar novamente</button>
    </div>
</body>
</html>`;
    return new Response(html, {
        status: 200,
        headers: { 'Content-Type': 'text/html; charset=utf-8' }
    });
}

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

// Configuracoes de retry
const MAX_RETRY_ATTEMPTS = 3;
const BASE_RETRY_DELAY = 1000; // 1 segundo

// Funcao para delay com Promise
function delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// Funcao para sincronizar um evento com retry e backoff exponencial
async function syncEventWithRetry(evt, db) {
    let lastError = null;

    for (let attempt = 1; attempt <= MAX_RETRY_ATTEMPTS; attempt++) {
        try {
            console.log(`[SW] Tentativa ${attempt}/${MAX_RETRY_ATTEMPTS} para evento ${evt.id}`);

            const response = await fetchWithTimeout('/api/v1/events/sync', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(evt)
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            // Sucesso - marcar como sincronizado
            await markEventSynced(db, evt.id);
            console.log(`[SW] Evento ${evt.id} sincronizado com sucesso`);
            return { success: true, eventId: evt.id };

        } catch (error) {
            lastError = error;
            console.log(`[SW] Tentativa ${attempt} falhou para evento ${evt.id}:`, error.message);

            // Se ainda ha tentativas, aguardar com backoff exponencial
            if (attempt < MAX_RETRY_ATTEMPTS) {
                const delayMs = BASE_RETRY_DELAY * Math.pow(2, attempt - 1);
                console.log(`[SW] Aguardando ${delayMs}ms antes da proxima tentativa...`);
                await delay(delayMs);
            }
        }
    }

    // Todas as tentativas falharam
    console.log(`[SW] Evento ${evt.id} falhou apos ${MAX_RETRY_ATTEMPTS} tentativas:`, lastError?.message);

    // Incrementar contador de falhas no evento
    await incrementEventFailCount(db, evt.id);

    return { success: false, eventId: evt.id, error: lastError?.message };
}

// Funcao para sincronizar eventos pendentes
async function syncEvents() {
    const results = { synced: 0, failed: 0, failedEvents: [] };

    try {
        const db = await openDatabase();
        const events = await getPendingEvents(db);

        if (events.length === 0) {
            console.log('[SW] Nenhum evento pendente para sincronizar');
            return results;
        }

        console.log(`[SW] Sincronizando ${events.length} evento(s) pendente(s)...`);

        for (const evt of events) {
            // Verificar se evento ja excedeu limite de tentativas
            if (evt.failCount && evt.failCount >= MAX_RETRY_ATTEMPTS) {
                console.log(`[SW] Evento ${evt.id} excedeu limite de tentativas, pulando`);
                results.failed++;
                results.failedEvents.push({
                    id: evt.id,
                    reason: 'Limite de tentativas excedido'
                });
                continue;
            }

            const result = await syncEventWithRetry(evt, db);

            if (result.success) {
                results.synced++;
            } else {
                results.failed++;
                results.failedEvents.push({
                    id: result.eventId,
                    reason: result.error
                });
            }
        }

        console.log(`[SW] Sync concluido: ${results.synced} sucesso, ${results.failed} falhas`);

        // Log de eventos que falharam
        if (results.failedEvents.length > 0) {
            console.log('[SW] Eventos que falharam:', JSON.stringify(results.failedEvents, null, 2));
        }

    } catch (e) {
        console.log('[SW] Erro critico no sync:', e);
        throw e; // Re-throw para que o sync seja reagendado
    }

    return results;
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

function incrementEventFailCount(db, id) {
    return new Promise((resolve, reject) => {
        const tx = db.transaction('pending-events', 'readwrite');
        const store = tx.objectStore('pending-events');
        const getRequest = store.get(id);

        getRequest.onerror = () => reject(getRequest.error);
        getRequest.onsuccess = () => {
            const evt = getRequest.result;
            if (evt) {
                evt.failCount = (evt.failCount || 0) + 1;
                evt.lastFailedAt = new Date().toISOString();
                const putRequest = store.put(evt);
                putRequest.onerror = () => reject(putRequest.error);
                putRequest.onsuccess = () => resolve();
            } else {
                resolve();
            }
        };
    });
}

// Mensagens do cliente
self.addEventListener('message', (event) => {
    if (event.data && event.data.type === 'SKIP_WAITING') {
        self.skipWaiting();
    }
});

console.log('[SW] Service Worker carregado');
