============================================================
           SkyCamOS - Sistema de Monitoramento
============================================================

[1/3] Instalando dependencias...

WARNING: Ignoring invalid distribution ~andas (C:\Users\WVP24K\AppData\Local\Programs\Python\Python311\Lib\site-packages)
WARNING: Ignoring invalid distribution ~andas (C:\Users\WVP24K\AppData\Local\Programs\Python\Python311\Lib\site-packages)
WARNING: Ignoring invalid distribution ~andas (C:\Users\WVP24K\AppData\Local\Programs\Python\Python311\Lib\site-packages)
[OK] Dependencias instaladas

[2/3] Verificando banco de dados...

[OK] Banco de dados ja existe

[3/3] Iniciando servidor...

Servidor rodando em: http://127.0.0.1:8000
Documentacao API: http://127.0.0.1:8000/docs

Pressione CTRL+C para parar o servidor
============================================================

[32mINFO[0m:     Will watch for changes in these directories: ['C:\\Users\\WVP24K\\Desktop\\SkyCamOS_Claude\\backend']
[32mINFO[0m:     Uvicorn running on [1mhttp://127.0.0.1:8000[0m (Press CTRL+C to quit)
[32mINFO[0m:     Started reloader process [[36m[1m3888[0m] using [36m[1mWatchFiles[0m
[32mINFO[0m:     Started server process [[36m17588[0m]
[32mINFO[0m:     Waiting for application startup.
2025-11-22 16:03:25,507 - app.main - INFO - Iniciando SkyCamOS v1.0.0
2025-11-22 16:03:25,507 - app.core.database - INFO - Inicializando banco de dados...
2025-11-22 16:03:25,514 - app.core.database - INFO - Banco de dados inicializado com sucesso.
2025-11-22 16:03:25,514 - app.core.database - INFO - Verificando dados iniciais...
2025-11-22 16:03:25,533 - app.core.database - INFO - Criando usuario administrador padrao...
2025-11-22 16:03:25,793 - app.core.database - INFO - Usuario admin criado. Login: admin / Senha: admin123 (ALTERE A SENHA EM PRODUCAO!)
2025-11-22 16:03:25,793 - app.services.storage_manager - INFO - Gerenciador de armazenamento iniciado. Limite: 100GB, Retencao: 30 dias
2025-11-22 16:03:25,794 - app.main - INFO - Aplicacao iniciada com sucesso
2025-11-22 16:03:25,795 - app.services.storage_manager - INFO - Iniciando limpeza de armazenamento...
2025-11-22 16:03:25,795 - app.services.storage_manager - INFO - Limpeza concluida: 0 arquivos removidos, 0.0MB liberados
[32mINFO[0m:     Application startup complete.