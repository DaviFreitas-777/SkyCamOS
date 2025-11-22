Microsoft Windows [versão 10.0.19045.6466]
(c) Microsoft Corporation. Todos os direitos reservados.

C:\Users\WVP24K\Desktop\SkyCamOS_Claude\backend>cd C:\Users\WVP24K\Desktop\SkyCamOS_Claude\backend

C:\Users\WVP24K\Desktop\SkyCamOS_Claude\backend>  py -m uvicorn app.main:app --reload
←[32mINFO←[0m:     Will watch for changes in these directories: ['C:\\Users\\WVP24K\\Desktop\\SkyCamOS_Claude\\backend']
←[32mINFO←[0m:     Uvicorn running on ←[1mhttp://127.0.0.1:8000←[0m (Press CTRL+C to quit)
←[32mINFO←[0m:     Started reloader process [←[36m←[1m16396←[0m] using ←[36m←[1mWatchFiles←[0m
Process SpawnProcess-1:
Traceback (most recent call last):
  File "C:\Users\WVP24K\AppData\Local\Programs\Python\Python311\Lib\site-packages\pydantic\networks.py", line 965, in import_email_validator
    import email_validator
ModuleNotFoundError: No module named 'email_validator'

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "C:\Users\WVP24K\AppData\Local\Programs\Python\Python311\Lib\multiprocessing\process.py", line 314, in _bootstrap
    self.run()
  File "C:\Users\WVP24K\AppData\Local\Programs\Python\Python311\Lib\multiprocessing\process.py", line 108, in run
    self._target(*self._args, **self._kwargs)
  File "C:\Users\WVP24K\AppData\Local\Programs\Python\Python311\Lib\site-packages\uvicorn\_subprocess.py", line 80, in subprocess_started
    target(sockets=sockets)
  File "C:\Users\WVP24K\AppData\Local\Programs\Python\Python311\Lib\site-packages\uvicorn\server.py", line 67, in run
    return asyncio_run(self.serve(sockets=sockets), loop_factory=self.config.get_loop_factory())
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\WVP24K\AppData\Local\Programs\Python\Python311\Lib\site-packages\uvicorn\_compat.py", line 30, in asyncio_run
    return runner.run(main)
           ^^^^^^^^^^^^^^^^
  File "C:\Users\WVP24K\AppData\Local\Programs\Python\Python311\Lib\asyncio\runners.py", line 118, in run
    return self._loop.run_until_complete(task)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\WVP24K\AppData\Local\Programs\Python\Python311\Lib\asyncio\base_events.py", line 654, in run_until_complete
    return future.result()
           ^^^^^^^^^^^^^^^
  File "C:\Users\WVP24K\AppData\Local\Programs\Python\Python311\Lib\site-packages\uvicorn\server.py", line 71, in serve
    await self._serve(sockets)
  File "C:\Users\WVP24K\AppData\Local\Programs\Python\Python311\Lib\site-packages\uvicorn\server.py", line 78, in _serve
    config.load()
  File "C:\Users\WVP24K\AppData\Local\Programs\Python\Python311\Lib\site-packages\uvicorn\config.py", line 439, in load
    self.loaded_app = import_from_string(self.app)
                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\WVP24K\AppData\Local\Programs\Python\Python311\Lib\site-packages\uvicorn\importer.py", line 19, in import_from_string
    module = importlib.import_module(module_str)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\WVP24K\AppData\Local\Programs\Python\Python311\Lib\importlib\__init__.py", line 126, in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "<frozen importlib._bootstrap>", line 1204, in _gcd_import
  File "<frozen importlib._bootstrap>", line 1176, in _find_and_load
  File "<frozen importlib._bootstrap>", line 1147, in _find_and_load_unlocked
  File "<frozen importlib._bootstrap>", line 690, in _load_unlocked
  File "<frozen importlib._bootstrap_external>", line 940, in exec_module
  File "<frozen importlib._bootstrap>", line 241, in _call_with_frames_removed
  File "C:\Users\WVP24K\Desktop\SkyCamOS_Claude\backend\app\main.py", line 19, in <module>
    from app.api import api_router
  File "C:\Users\WVP24K\Desktop\SkyCamOS_Claude\backend\app\api\__init__.py", line 9, in <module>
    from app.api.routes import auth, cameras, events, recordings, stream
  File "C:\Users\WVP24K\Desktop\SkyCamOS_Claude\backend\app\api\routes\__init__.py", line 7, in <module>
    from app.api.routes import auth, cameras, events, recordings, stream
  File "C:\Users\WVP24K\Desktop\SkyCamOS_Claude\backend\app\api\routes\auth.py", line 28, in <module>
    from app.schemas.user import (
  File "C:\Users\WVP24K\Desktop\SkyCamOS_Claude\backend\app\schemas\__init__.py", line 30, in <module>
    from app.schemas.user import (
  File "C:\Users\WVP24K\Desktop\SkyCamOS_Claude\backend\app\schemas\user.py", line 14, in <module>
    class UserBase(BaseModel):
  File "C:\Users\WVP24K\AppData\Local\Programs\Python\Python311\Lib\site-packages\pydantic\_internal\_model_construction.py", line 255, in __new__
    complete_model_class(
  File "C:\Users\WVP24K\AppData\Local\Programs\Python\Python311\Lib\site-packages\pydantic\_internal\_model_construction.py", line 648, in complete_model_class
    schema = gen_schema.generate_schema(cls)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\WVP24K\AppData\Local\Programs\Python\Python311\Lib\site-packages\pydantic\_internal\_generate_schema.py", line 729, in generate_schema
    schema = self._generate_schema_inner(obj)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\WVP24K\AppData\Local\Programs\Python\Python311\Lib\site-packages\pydantic\_internal\_generate_schema.py", line 1023, in _generate_schema_inner
    return self._model_schema(obj)
           ^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\WVP24K\AppData\Local\Programs\Python\Python311\Lib\site-packages\pydantic\_internal\_generate_schema.py", line 856, in _model_schema
    {k: self._generate_md_field_schema(k, v, decorators) for k, v in fields.items()},
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\WVP24K\AppData\Local\Programs\Python\Python311\Lib\site-packages\pydantic\_internal\_generate_schema.py", line 856, in <dictcomp>
    {k: self._generate_md_field_schema(k, v, decorators) for k, v in fields.items()},
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\WVP24K\AppData\Local\Programs\Python\Python311\Lib\site-packages\pydantic\_internal\_generate_schema.py", line 1228, in _generate_md_field_schema
    schema, metadata = self._common_field_schema(name, field_info, decorators)
                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\WVP24K\AppData\Local\Programs\Python\Python311\Lib\site-packages\pydantic\_internal\_generate_schema.py", line 1282, in _common_field_schema
    schema = self._apply_annotations(
             ^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\WVP24K\AppData\Local\Programs\Python\Python311\Lib\site-packages\pydantic\_internal\_generate_schema.py", line 2227, in _apply_annotations
    schema = get_inner_schema(source_type)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\WVP24K\AppData\Local\Programs\Python\Python311\Lib\site-packages\pydantic\_internal\_schema_generation_shared.py", line 83, in __call__
    schema = self._handler(source_type)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\WVP24K\AppData\Local\Programs\Python\Python311\Lib\site-packages\pydantic\_internal\_generate_schema.py", line 2203, in inner_handler
    schema = self._generate_schema_from_get_schema_method(obj, source_type)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\WVP24K\AppData\Local\Programs\Python\Python311\Lib\site-packages\pydantic\_internal\_generate_schema.py", line 919, in _generate_schema_from_get_schema_method
    schema = get_schema(
             ^^^^^^^^^^^
  File "C:\Users\WVP24K\AppData\Local\Programs\Python\Python311\Lib\site-packages\pydantic\networks.py", line 1005, in __get_pydantic_core_schema__
    import_email_validator()
  File "C:\Users\WVP24K\AppData\Local\Programs\Python\Python311\Lib\site-packages\pydantic\networks.py", line 967, in import_email_validator
    raise ImportError("email-validator is not installed, run `pip install 'pydantic[email]'`") from e
ImportError: email-validator is not installed, run `pip install 'pydantic[email]'`
