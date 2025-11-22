============================================================
           SkyCamOS - Sistema de Monitoramento
============================================================

[1/3] Instalando dependencias do backend...

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
[32mINFO[0m:     Started reloader process [[36m[1m20100[0m] using [36m[1mWatchFiles[0m
[32mINFO[0m:     Started server process [[36m18496[0m]
[32mINFO[0m:     Waiting for application startup.
2025-11-22 15:58:38,436 - app.main - INFO - Iniciando SkyCamOS v1.0.0
2025-11-22 15:58:38,436 - app.core.database - INFO - Inicializando banco de dados...
2025-11-22 15:58:38,445 - app.core.database - INFO - Banco de dados inicializado com sucesso.
2025-11-22 15:58:38,446 - app.core.database - INFO - Verificando dados iniciais...
2025-11-22 15:58:38,468 - app.core.database - INFO - Criando usuario administrador padrao...
2025-11-22 15:58:38,468 - passlib.handlers.bcrypt - WARNING - (trapped) error reading bcrypt version
Traceback (most recent call last):
  File "C:\Users\WVP24K\AppData\Local\Programs\Python\Python311\Lib\site-packages\passlib\handlers\bcrypt.py", line 620, in _load_backend_mixin
    version = _bcrypt.__about__.__version__
              ^^^^^^^^^^^^^^^^^
AttributeError: module 'bcrypt' has no attribute '__about__'
2025-11-22 15:58:38,475 - app.main - ERROR - Erro na inicializacao: password cannot be longer than 72 bytes, truncate manually if necessary (e.g. my_password[:72])
[31mERROR[0m:    Traceback (most recent call last):
  File "C:\Users\WVP24K\AppData\Local\Programs\Python\Python311\Lib\site-packages\starlette\routing.py", line 694, in lifespan
    async with self.lifespan_context(app) as maybe_state:
  File "C:\Users\WVP24K\AppData\Local\Programs\Python\Python311\Lib\contextlib.py", line 210, in __aenter__
    return await anext(self.gen)
           ^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\WVP24K\AppData\Local\Programs\Python\Python311\Lib\site-packages\fastapi\routing.py", line 211, in merged_lifespan
    async with original_context(app) as maybe_original_state:
  File "C:\Users\WVP24K\AppData\Local\Programs\Python\Python311\Lib\contextlib.py", line 210, in __aenter__
    return await anext(self.gen)
           ^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\WVP24K\Desktop\SkyCamOS_Claude\backend\app\main.py", line 57, in lifespan
    await create_initial_data()
  File "C:\Users\WVP24K\Desktop\SkyCamOS_Claude\backend\app\core\database.py", line 136, in create_initial_data
    hashed_password=get_password_hash("admin123"),
                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\WVP24K\Desktop\SkyCamOS_Claude\backend\app\core\security.py", line 56, in get_password_hash
    return pwd_context.hash(password)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\WVP24K\AppData\Local\Programs\Python\Python311\Lib\site-packages\passlib\context.py", line 2258, in hash
    return record.hash(secret, **kwds)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\WVP24K\AppData\Local\Programs\Python\Python311\Lib\site-packages\passlib\utils\handlers.py", line 779, in hash
    self.checksum = self._calc_checksum(secret)
                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\WVP24K\AppData\Local\Programs\Python\Python311\Lib\site-packages\passlib\handlers\bcrypt.py", line 591, in _calc_checksum
    self._stub_requires_backend()
  File "C:\Users\WVP24K\AppData\Local\Programs\Python\Python311\Lib\site-packages\passlib\utils\handlers.py", line 2254, in _stub_requires_backend
    cls.set_backend()
  File "C:\Users\WVP24K\AppData\Local\Programs\Python\Python311\Lib\site-packages\passlib\utils\handlers.py", line 2156, in set_backend
    return owner.set_backend(name, dryrun=dryrun)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\WVP24K\AppData\Local\Programs\Python\Python311\Lib\site-packages\passlib\utils\handlers.py", line 2163, in set_backend
    return cls.set_backend(name, dryrun=dryrun)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\WVP24K\AppData\Local\Programs\Python\Python311\Lib\site-packages\passlib\utils\handlers.py", line 2188, in set_backend
    cls._set_backend(name, dryrun)
  File "C:\Users\WVP24K\AppData\Local\Programs\Python\Python311\Lib\site-packages\passlib\utils\handlers.py", line 2311, in _set_backend
    super(SubclassBackendMixin, cls)._set_backend(name, dryrun)
  File "C:\Users\WVP24K\AppData\Local\Programs\Python\Python311\Lib\site-packages\passlib\utils\handlers.py", line 2224, in _set_backend
    ok = loader(**kwds)
         ^^^^^^^^^^^^^^
  File "C:\Users\WVP24K\AppData\Local\Programs\Python\Python311\Lib\site-packages\passlib\handlers\bcrypt.py", line 626, in _load_backend_mixin
    return mixin_cls._finalize_backend_mixin(name, dryrun)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\WVP24K\AppData\Local\Programs\Python\Python311\Lib\site-packages\passlib\handlers\bcrypt.py", line 421, in _finalize_backend_mixin
    if detect_wrap_bug(IDENT_2A):
       ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\WVP24K\AppData\Local\Programs\Python\Python311\Lib\site-packages\passlib\handlers\bcrypt.py", line 380, in detect_wrap_bug
    if verify(secret, bug_hash):
       ^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\WVP24K\AppData\Local\Programs\Python\Python311\Lib\site-packages\passlib\utils\handlers.py", line 792, in verify
    return consteq(self._calc_checksum(secret), chk)
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\WVP24K\AppData\Local\Programs\Python\Python311\Lib\site-packages\passlib\handlers\bcrypt.py", line 655, in _calc_checksum
    hash = _bcrypt.hashpw(secret, config)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
ValueError: password cannot be longer than 72 bytes, truncate manually if necessary (e.g. my_password[:72])

[31mERROR[0m:    Application startup failed. Exiting.
