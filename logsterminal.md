Microsoft Windows [versão 10.0.19045.6466]
(c) Microsoft Corporation. Todos os direitos reservados.

C:\Users\WVP24K\Desktop\SkyCamOS_Claude\backend>pip install -r requirements.txt
WARNING: Ignoring invalid distribution ~andas (C:\Users\WVP24K\AppData\Local\Programs\Python\Python311\Lib\site-packages)
Collecting fastapi>=0.104.0 (from -r requirements.txt (line 3))
  Downloading fastapi-0.121.3-py3-none-any.whl.metadata (30 kB)
Collecting uvicorn>=0.24.0 (from uvicorn[standard]>=0.24.0->-r requirements.txt (line 4))
  Downloading uvicorn-0.38.0-py3-none-any.whl.metadata (6.8 kB)
Collecting python-multipart>=0.0.6 (from -r requirements.txt (line 5))
  Downloading python_multipart-0.0.20-py3-none-any.whl.metadata (1.8 kB)
Collecting python-jose>=3.3.0 (from python-jose[cryptography]>=3.3.0->-r requirements.txt (line 8))
  Downloading python_jose-3.5.0-py2.py3-none-any.whl.metadata (5.5 kB)
Collecting passlib>=1.7.4 (from passlib[bcrypt]>=1.7.4->-r requirements.txt (line 9))
  Downloading passlib-1.7.4-py2.py3-none-any.whl.metadata (1.7 kB)
Requirement already satisfied: sqlalchemy>=2.0.0 in c:\users\wvp24k\appdata\local\programs\python\python311\lib\site-packages (from -r requirements.txt (line 12)) (2.0.21)
Collecting aiosqlite>=0.19.0 (from -r requirements.txt (line 13))
  Downloading aiosqlite-0.21.0-py3-none-any.whl.metadata (4.3 kB)
Requirement already satisfied: python-dotenv>=1.0.0 in c:\users\wvp24k\appdata\local\programs\python\python311\lib\site-packages (from -r requirements.txt (line 16)) (1.0.1)
Collecting opencv-python-headless>=4.8.0 (from -r requirements.txt (line 19))
  Downloading opencv_python_headless-4.12.0.88-cp37-abi3-win_amd64.whl.metadata (20 kB)
Requirement already satisfied: numpy>=1.24.0 in c:\users\wvp24k\appdata\local\programs\python\python311\lib\site-packages (from -r requirements.txt (line 20)) (2.3.1)
Collecting onvif-zeep>=0.2.12 (from -r requirements.txt (line 23))
  Downloading onvif_zeep-0.2.12.tar.gz (163 kB)
  Preparing metadata (setup.py) ... done
Collecting zeep>=4.2.1 (from -r requirements.txt (line 24))
  Downloading zeep-4.3.2-py3-none-any.whl.metadata (4.4 kB)
Collecting aiortc>=1.6.0 (from -r requirements.txt (line 27))
  Downloading aiortc-1.14.0-py3-none-any.whl.metadata (4.9 kB)
Collecting websockets>=12.0 (from -r requirements.txt (line 28))
  Downloading websockets-15.0.1-cp311-cp311-win_amd64.whl.metadata (7.0 kB)
Collecting av>=11.0.0 (from -r requirements.txt (line 29))
  Downloading av-16.0.1-cp311-cp311-win_amd64.whl.metadata (4.7 kB)
Collecting httpx>=0.25.0 (from -r requirements.txt (line 32))
  Downloading httpx-0.28.1-py3-none-any.whl.metadata (7.1 kB)
Requirement already satisfied: aiohttp>=3.9.0 in c:\users\wvp24k\appdata\local\programs\python\python311\lib\site-packages (from -r requirements.txt (line 33)) (3.9.5)
Collecting pydantic>=2.5.0 (from -r requirements.txt (line 36))
  Downloading pydantic-2.12.4-py3-none-any.whl.metadata (89 kB)
Collecting pydantic-settings>=2.1.0 (from -r requirements.txt (line 37))
  Downloading pydantic_settings-2.12.0-py3-none-any.whl.metadata (3.4 kB)
Requirement already satisfied: python-dateutil>=2.8.2 in c:\users\wvp24k\appdata\local\programs\python\python311\lib\site-packages (from -r requirements.txt (line 38)) (2.9.0.post0)
Collecting aiofiles>=23.2.1 (from -r requirements.txt (line 39))
  Downloading aiofiles-25.1.0-py3-none-any.whl.metadata (6.3 kB)
Collecting loguru>=0.7.2 (from -r requirements.txt (line 42))
  Downloading loguru-0.7.3-py3-none-any.whl.metadata (22 kB)
Collecting starlette<0.51.0,>=0.40.0 (from fastapi>=0.104.0->-r requirements.txt (line 3))
  Downloading starlette-0.50.0-py3-none-any.whl.metadata (6.3 kB)
Requirement already satisfied: typing-extensions>=4.8.0 in c:\users\wvp24k\appdata\local\programs\python\python311\lib\site-packages (from fastapi>=0.104.0->-r requirements.txt (line 3)) (4.14.0)
Collecting annotated-doc>=0.0.2 (from fastapi>=0.104.0->-r requirements.txt (line 3))
  Downloading annotated_doc-0.0.4-py3-none-any.whl.metadata (6.6 kB)
Collecting annotated-types>=0.6.0 (from pydantic>=2.5.0->-r requirements.txt (line 36))
  Downloading annotated_types-0.7.0-py3-none-any.whl.metadata (15 kB)
Collecting pydantic-core==2.41.5 (from pydantic>=2.5.0->-r requirements.txt (line 36))
  Downloading pydantic_core-2.41.5-cp311-cp311-win_amd64.whl.metadata (7.4 kB)
Collecting typing-extensions>=4.8.0 (from fastapi>=0.104.0->-r requirements.txt (line 3))
  Using cached typing_extensions-4.15.0-py3-none-any.whl.metadata (3.3 kB)
Collecting typing-inspection>=0.4.2 (from pydantic>=2.5.0->-r requirements.txt (line 36))
  Downloading typing_inspection-0.4.2-py3-none-any.whl.metadata (2.6 kB)
Collecting anyio<5,>=3.6.2 (from starlette<0.51.0,>=0.40.0->fastapi>=0.104.0->-r requirements.txt (line 3))
  Downloading anyio-4.11.0-py3-none-any.whl.metadata (4.1 kB)
Requirement already satisfied: idna>=2.8 in c:\users\wvp24k\appdata\local\programs\python\python311\lib\site-packages (from anyio<5,>=3.6.2->starlette<0.51.0,>=0.40.0->fastapi>=0.104.0->-r requirements.txt (line 3)) (3.10)
Collecting sniffio>=1.1 (from anyio<5,>=3.6.2->starlette<0.51.0,>=0.40.0->fastapi>=0.104.0->-r requirements.txt (line 3))
  Downloading sniffio-1.3.1-py3-none-any.whl.metadata (3.9 kB)
Requirement already satisfied: click>=7.0 in c:\users\wvp24k\appdata\local\programs\python\python311\lib\site-packages (from uvicorn>=0.24.0->uvicorn[standard]>=0.24.0->-r requirements.txt (line 4)) (8.1.7)
Collecting h11>=0.8 (from uvicorn>=0.24.0->uvicorn[standard]>=0.24.0->-r requirements.txt (line 4))
  Downloading h11-0.16.0-py3-none-any.whl.metadata (8.3 kB)
Collecting ecdsa!=0.15 (from python-jose>=3.3.0->python-jose[cryptography]>=3.3.0->-r requirements.txt (line 8))
  Downloading ecdsa-0.19.1-py2.py3-none-any.whl.metadata (29 kB)
Collecting rsa!=4.1.1,!=4.4,<5.0,>=4.0 (from python-jose>=3.3.0->python-jose[cryptography]>=3.3.0->-r requirements.txt (line 8))
  Downloading rsa-4.9.1-py3-none-any.whl.metadata (5.6 kB)
Collecting pyasn1>=0.5.0 (from python-jose>=3.3.0->python-jose[cryptography]>=3.3.0->-r requirements.txt (line 8))
  Downloading pyasn1-0.6.1-py3-none-any.whl.metadata (8.4 kB)
Requirement already satisfied: greenlet!=0.4.17 in c:\users\wvp24k\appdata\local\programs\python\python311\lib\site-packages (from sqlalchemy>=2.0.0->-r requirements.txt (line 12)) (3.2.3)
Collecting numpy>=1.24.0 (from -r requirements.txt (line 20))
  Downloading numpy-2.2.6-cp311-cp311-win_amd64.whl.metadata (60 kB)
Requirement already satisfied: attrs>=17.2.0 in c:\users\wvp24k\appdata\local\programs\python\python311\lib\site-packages (from zeep>=4.2.1->-r requirements.txt (line 24)) (25.3.0)
Collecting isodate>=0.5.4 (from zeep>=4.2.1->-r requirements.txt (line 24))
  Downloading isodate-0.7.2-py3-none-any.whl.metadata (11 kB)
Collecting lxml>=4.6.0 (from zeep>=4.2.1->-r requirements.txt (line 24))
  Downloading lxml-6.0.2-cp311-cp311-win_amd64.whl.metadata (3.7 kB)
Collecting platformdirs>=1.4.0 (from zeep>=4.2.1->-r requirements.txt (line 24))
  Downloading platformdirs-4.5.0-py3-none-any.whl.metadata (12 kB)
Requirement already satisfied: requests>=2.7.0 in c:\users\wvp24k\appdata\local\programs\python\python311\lib\site-packages (from zeep>=4.2.1->-r requirements.txt (line 24)) (2.32.4)
Collecting requests-toolbelt>=0.7.1 (from zeep>=4.2.1->-r requirements.txt (line 24))
  Downloading requests_toolbelt-1.0.0-py2.py3-none-any.whl.metadata (14 kB)
Collecting requests-file>=1.5.1 (from zeep>=4.2.1->-r requirements.txt (line 24))
  Downloading requests_file-3.0.1-py2.py3-none-any.whl.metadata (1.7 kB)
Requirement already satisfied: pytz in c:\users\wvp24k\appdata\local\programs\python\python311\lib\site-packages (from zeep>=4.2.1->-r requirements.txt (line 24)) (2024.1)
Collecting aioice<1.0.0,>=0.10.1 (from aiortc>=1.6.0->-r requirements.txt (line 27))
  Downloading aioice-0.10.1-py3-none-any.whl.metadata (4.1 kB)
Collecting cryptography>=44.0.0 (from aiortc>=1.6.0->-r requirements.txt (line 27))
  Using cached cryptography-46.0.3-cp311-abi3-win_amd64.whl.metadata (5.7 kB)
Collecting google-crc32c>=1.1 (from aiortc>=1.6.0->-r requirements.txt (line 27))
  Downloading google_crc32c-1.7.1-cp311-cp311-win_amd64.whl.metadata (2.4 kB)
Requirement already satisfied: pyee>=13.0.0 in c:\users\wvp24k\appdata\local\programs\python\python311\lib\site-packages (from aiortc>=1.6.0->-r requirements.txt (line 27)) (13.0.0)
Collecting pylibsrtp>=0.10.0 (from aiortc>=1.6.0->-r requirements.txt (line 27))
  Downloading pylibsrtp-1.0.0-cp310-abi3-win_amd64.whl.metadata (4.2 kB)
Collecting pyopenssl>=25.0.0 (from aiortc>=1.6.0->-r requirements.txt (line 27))
  Downloading pyopenssl-25.3.0-py3-none-any.whl.metadata (17 kB)
Collecting dnspython>=2.0.0 (from aioice<1.0.0,>=0.10.1->aiortc>=1.6.0->-r requirements.txt (line 27))
  Downloading dnspython-2.8.0-py3-none-any.whl.metadata (5.7 kB)
Collecting ifaddr>=0.2.0 (from aioice<1.0.0,>=0.10.1->aiortc>=1.6.0->-r requirements.txt (line 27))
  Downloading ifaddr-0.2.0-py3-none-any.whl.metadata (4.9 kB)
Requirement already satisfied: certifi in c:\users\wvp24k\appdata\local\programs\python\python311\lib\site-packages (from httpx>=0.25.0->-r requirements.txt (line 32)) (2025.6.15)
Collecting httpcore==1.* (from httpx>=0.25.0->-r requirements.txt (line 32))
  Downloading httpcore-1.0.9-py3-none-any.whl.metadata (21 kB)
Requirement already satisfied: aiosignal>=1.1.2 in c:\users\wvp24k\appdata\local\programs\python\python311\lib\site-packages (from aiohttp>=3.9.0->-r requirements.txt (line 33)) (1.4.0)
Requirement already satisfied: frozenlist>=1.1.1 in c:\users\wvp24k\appdata\local\programs\python\python311\lib\site-packages (from aiohttp>=3.9.0->-r requirements.txt (line 33)) (1.7.0)
Requirement already satisfied: multidict<7.0,>=4.5 in c:\users\wvp24k\appdata\local\programs\python\python311\lib\site-packages (from aiohttp>=3.9.0->-r requirements.txt (line 33)) (6.6.4)
Requirement already satisfied: yarl<2.0,>=1.0 in c:\users\wvp24k\appdata\local\programs\python\python311\lib\site-packages (from aiohttp>=3.9.0->-r requirements.txt (line 33)) (1.20.1)
Requirement already satisfied: propcache>=0.2.1 in c:\users\wvp24k\appdata\local\programs\python\python311\lib\site-packages (from yarl<2.0,>=1.0->aiohttp>=3.9.0->-r requirements.txt (line 33)) (0.3.2)
Requirement already satisfied: six>=1.5 in c:\users\wvp24k\appdata\local\programs\python\python311\lib\site-packages (from python-dateutil>=2.8.2->-r requirements.txt (line 38)) (1.17.0)
Requirement already satisfied: colorama>=0.3.4 in c:\users\wvp24k\appdata\local\programs\python\python311\lib\site-packages (from loguru>=0.7.2->-r requirements.txt (line 42)) (0.4.6)
Collecting win32-setctime>=1.0.0 (from loguru>=0.7.2->-r requirements.txt (line 42))
  Downloading win32_setctime-1.2.0-py3-none-any.whl.metadata (2.4 kB)
Collecting cffi>=2.0.0 (from cryptography>=44.0.0->aiortc>=1.6.0->-r requirements.txt (line 27))
  Using cached cffi-2.0.0-cp311-cp311-win_amd64.whl.metadata (2.6 kB)
Requirement already satisfied: pycparser in c:\users\wvp24k\appdata\local\programs\python\python311\lib\site-packages (from cffi>=2.0.0->cryptography>=44.0.0->aiortc>=1.6.0->-r requirements.txt (line 27)) (2.22)
Collecting bcrypt>=3.1.0 (from passlib[bcrypt]>=1.7.4->-r requirements.txt (line 9))
  Downloading bcrypt-5.0.0-cp39-abi3-win_amd64.whl.metadata (10 kB)
Requirement already satisfied: charset_normalizer<4,>=2 in c:\users\wvp24k\appdata\local\programs\python\python311\lib\site-packages (from requests>=2.7.0->zeep>=4.2.1->-r requirements.txt (line 24)) (2.1.1)
Requirement already satisfied: urllib3<3,>=1.21.1 in c:\users\wvp24k\appdata\local\programs\python\python311\lib\site-packages (from requests>=2.7.0->zeep>=4.2.1->-r requirements.txt (line 24)) (1.26.20)
Collecting httptools>=0.6.3 (from uvicorn[standard]>=0.24.0->-r requirements.txt (line 4))
  Downloading httptools-0.7.1-cp311-cp311-win_amd64.whl.metadata (3.6 kB)
Collecting pyyaml>=5.1 (from uvicorn[standard]>=0.24.0->-r requirements.txt (line 4))
  Downloading pyyaml-6.0.3-cp311-cp311-win_amd64.whl.metadata (2.4 kB)
Collecting watchfiles>=0.13 (from uvicorn[standard]>=0.24.0->-r requirements.txt (line 4))
  Downloading watchfiles-1.1.1-cp311-cp311-win_amd64.whl.metadata (5.0 kB)
Downloading fastapi-0.121.3-py3-none-any.whl (109 kB)
Downloading pydantic-2.12.4-py3-none-any.whl (463 kB)
Downloading pydantic_core-2.41.5-cp311-cp311-win_amd64.whl (2.0 MB)
   ---------------------------------------- 2.0/2.0 MB 11.2 MB/s  0:00:00
Downloading starlette-0.50.0-py3-none-any.whl (74 kB)
Downloading anyio-4.11.0-py3-none-any.whl (109 kB)
Downloading uvicorn-0.38.0-py3-none-any.whl (68 kB)
Downloading python_multipart-0.0.20-py3-none-any.whl (24 kB)
Downloading python_jose-3.5.0-py2.py3-none-any.whl (34 kB)
Downloading rsa-4.9.1-py3-none-any.whl (34 kB)
Downloading passlib-1.7.4-py2.py3-none-any.whl (525 kB)
   ---------------------------------------- 525.6/525.6 kB 8.5 MB/s  0:00:00
Downloading aiosqlite-0.21.0-py3-none-any.whl (15 kB)
Downloading opencv_python_headless-4.12.0.88-cp37-abi3-win_amd64.whl (38.9 MB)
   ---------------------------------------- 38.9/38.9 MB 10.4 MB/s  0:00:03
Downloading numpy-2.2.6-cp311-cp311-win_amd64.whl (12.9 MB)
   ---------------------------------------- 12.9/12.9 MB 10.9 MB/s  0:00:01
Downloading zeep-4.3.2-py3-none-any.whl (101 kB)
Downloading aiortc-1.14.0-py3-none-any.whl (93 kB)
Downloading av-16.0.1-cp311-cp311-win_amd64.whl (32.3 MB)
   ---------------------------------------- 32.3/32.3 MB 10.8 MB/s  0:00:02
Downloading aioice-0.10.1-py3-none-any.whl (24 kB)
Downloading websockets-15.0.1-cp311-cp311-win_amd64.whl (176 kB)
Downloading httpx-0.28.1-py3-none-any.whl (73 kB)
Downloading httpcore-1.0.9-py3-none-any.whl (78 kB)
Downloading pydantic_settings-2.12.0-py3-none-any.whl (51 kB)
Downloading aiofiles-25.1.0-py3-none-any.whl (14 kB)
Downloading loguru-0.7.3-py3-none-any.whl (61 kB)
Downloading annotated_doc-0.0.4-py3-none-any.whl (5.3 kB)
Downloading annotated_types-0.7.0-py3-none-any.whl (13 kB)
Using cached cryptography-46.0.3-cp311-abi3-win_amd64.whl (3.5 MB)
Using cached cffi-2.0.0-cp311-cp311-win_amd64.whl (182 kB)
Downloading dnspython-2.8.0-py3-none-any.whl (331 kB)
Downloading ecdsa-0.19.1-py2.py3-none-any.whl (150 kB)
Downloading google_crc32c-1.7.1-cp311-cp311-win_amd64.whl (33 kB)
Downloading h11-0.16.0-py3-none-any.whl (37 kB)
Downloading ifaddr-0.2.0-py3-none-any.whl (12 kB)
Downloading isodate-0.7.2-py3-none-any.whl (22 kB)
Downloading lxml-6.0.2-cp311-cp311-win_amd64.whl (4.0 MB)
   ---------------------------------------- 4.0/4.0 MB 11.0 MB/s  0:00:00
Downloading bcrypt-5.0.0-cp39-abi3-win_amd64.whl (150 kB)
Downloading platformdirs-4.5.0-py3-none-any.whl (18 kB)
Downloading pyasn1-0.6.1-py3-none-any.whl (83 kB)
Downloading pylibsrtp-1.0.0-cp310-abi3-win_amd64.whl (1.6 MB)
   ---------------------------------------- 1.6/1.6 MB 9.5 MB/s  0:00:00
Downloading pyopenssl-25.3.0-py3-none-any.whl (57 kB)
Downloading requests_file-3.0.1-py2.py3-none-any.whl (4.5 kB)
Downloading requests_toolbelt-1.0.0-py2.py3-none-any.whl (54 kB)
Downloading sniffio-1.3.1-py3-none-any.whl (10 kB)
Using cached typing_extensions-4.15.0-py3-none-any.whl (44 kB)
Downloading typing_inspection-0.4.2-py3-none-any.whl (14 kB)
Downloading httptools-0.7.1-cp311-cp311-win_amd64.whl (86 kB)
Downloading pyyaml-6.0.3-cp311-cp311-win_amd64.whl (158 kB)
Downloading watchfiles-1.1.1-cp311-cp311-win_amd64.whl (287 kB)
Downloading win32_setctime-1.2.0-py3-none-any.whl (4.1 kB)
Building wheels for collected packages: onvif-zeep
  DEPRECATION: Building 'onvif-zeep' using the legacy setup.py bdist_wheel mechanism, which will be removed in a future version. pip 25.3 will enforce this behaviour change. A possible replacement is to use the standardized build interface by setting the `--use-pep517` option, (possibly combined with `--no-build-isolation`), or adding a `pyproject.toml` file to the source tree of 'onvif-zeep'. Discussion can be found at https://github.com/pypa/pip/issues/6334
  Building wheel for onvif-zeep (setup.py) ... done
  Created wheel for onvif-zeep: filename=onvif_zeep-0.2.12-py3-none-any.whl size=192130 sha256=2e77a0d969ddc444a4998acd2dd7665d221ec57123e3e27e4bcb5e4c3a8c2e62
  Stored in directory: c:\users\wvp24k\appdata\local\pip\cache\wheels\e1\de\2e\3472f5027ee682cab73e8c4f5063de77040f71e15d795802d2
Successfully built onvif-zeep
WARNING: Ignoring invalid distribution ~andas (C:\Users\WVP24K\AppData\Local\Programs\Python\Python311\Lib\site-packages)
Installing collected packages: passlib, ifaddr, win32-setctime, websockets, typing-extensions, sniffio, pyyaml, python-multipart, pyasn1, platformdirs, numpy, lxml, isodate, httptools, h11, google-crc32c, ecdsa, dnspython, cffi, bcrypt, av, annotated-types, annotated-doc, aiofiles, uvicorn, typing-inspection, rsa, requests-toolbelt, requests-file, pylibsrtp, pydantic-core, opencv-python-headless, loguru, httpcore, cryptography, anyio, aiosqlite, aioice, zeep, watchfiles, starlette, python-jose, pyopenssl, pydantic, httpx, pydantic-settings, onvif-zeep, fastapi, aiortc
  Attempting uninstall: typing-extensions
    Found existing installation: typing_extensions 4.14.0
    Uninstalling typing_extensions-4.14.0:
      Successfully uninstalled typing_extensions-4.14.0
  Attempting uninstall: numpy
    Found existing installation: numpy 2.3.1
    Uninstalling numpy-2.3.1:
      Successfully uninstalled numpy-2.3.1
  Attempting uninstall: cffi
    Found existing installation: cffi 1.17.1
    Uninstalling cffi-1.17.1:
      Successfully uninstalled cffi-1.17.1
  Attempting uninstall: cryptography
    Found existing installation: cryptography 41.0.7
    Uninstalling cryptography-41.0.7:
      Successfully uninstalled cryptography-41.0.7
WARNING: Ignoring invalid distribution ~andas (C:\Users\WVP24K\AppData\Local\Programs\Python\Python311\Lib\site-packages)
Successfully installed aiofiles-25.1.0 aioice-0.10.1 aiortc-1.14.0 aiosqlite-0.21.0 annotated-doc-0.0.4 annotated-types-0.7.0 anyio-4.11.0 av-16.0.1 bcrypt-5.0.0 cffi-2.0.0 cryptography-46.0.3 dnspython-2.8.0 ecdsa-0.19.1 fastapi-0.121.3 google-crc32c-1.7.1 h11-0.16.0 httpcore-1.0.9 httptools-0.7.1 httpx-0.28.1 ifaddr-0.2.0 isodate-0.7.2 loguru-0.7.3 lxml-6.0.2 numpy-2.2.6 onvif-zeep-0.2.12 opencv-python-headless-4.12.0.88 passlib-1.7.4 platformdirs-4.5.0 pyasn1-0.6.1 pydantic-2.12.4 pydantic-core-2.41.5 pydantic-settings-2.12.0 pylibsrtp-1.0.0 pyopenssl-25.3.0 python-jose-3.5.0 python-multipart-0.0.20 pyyaml-6.0.3 requests-file-3.0.1 requests-toolbelt-1.0.0 rsa-4.9.1 sniffio-1.3.1 starlette-0.50.0 typing-extensions-4.15.0 typing-inspection-0.4.2 uvicorn-0.38.0 watchfiles-1.1.1 websockets-15.0.1 win32-setctime-1.2.0 zeep-4.3.2

[notice] A new release of pip is available: 25.2 -> 25.3
[notice] To update, run: C:\Users\WVP24K\AppData\Local\Programs\Python\Python311\python.exe -m pip install --upgrade pip

C:\Users\WVP24K\Desktop\SkyCamOS_Claude\backend>C:\Users\WVP24K\AppData\Local\Programs\Python\Python311\python.exe -m pip install --upgrade pip
WARNING: Ignoring invalid distribution ~andas (C:\Users\WVP24K\AppData\Local\Programs\Python\Python311\Lib\site-packages)
Requirement already satisfied: pip in c:\users\wvp24k\appdata\local\programs\python\python311\lib\site-packages (25.2)
Collecting pip
  Using cached pip-25.3-py3-none-any.whl.metadata (4.7 kB)
Using cached pip-25.3-py3-none-any.whl (1.8 MB)
WARNING: Ignoring invalid distribution ~andas (C:\Users\WVP24K\AppData\Local\Programs\Python\Python311\Lib\site-packages)
Installing collected packages: pip
  Attempting uninstall: pip
    Found existing installation: pip 25.2
    Uninstalling pip-25.2:
      Successfully uninstalled pip-25.2
WARNING: Ignoring invalid distribution ~andas (C:\Users\WVP24K\AppData\Local\Programs\Python\Python311\Lib\site-packages)
Successfully installed pip-25.3

C:\Users\WVP24K\Desktop\SkyCamOS_Claude\backend>cd ../database/scripts

C:\Users\WVP24K\Desktop\SkyCamOS_Claude\database\scripts>py init_db.py
2025-11-22 15:47:51 [INFO] ============================================================
2025-11-22 15:47:51 [INFO] SkyCamOS - Inicializacao do Banco de Dados
2025-11-22 15:47:51 [INFO] ============================================================
2025-11-22 15:47:51 [INFO] Banco de dados vazio ou nao inicializado
2025-11-22 15:47:51 [INFO] Migrations encontradas: 2
2025-11-22 15:47:51 [INFO] Executando migration: 001_initial_schema.sql
2025-11-22 15:47:51 [OK] Migration executada com sucesso: 001_initial_schema.sql
2025-11-22 15:47:51 [INFO] Executando migration: 002_seed_data.sql
2025-11-22 15:47:51 [OK] Migration executada com sucesso: 002_seed_data.sql
2025-11-22 15:47:51 [OK] 2 migration(s) executada(s) com sucesso
2025-11-22 15:47:51 [INFO] Versao final do banco: 002
2025-11-22 15:47:51 [INFO] ============================================================
2025-11-22 15:47:51 [INFO] Inicializacao concluida!
2025-11-22 15:47:51 [INFO] ============================================================

C:\Users\WVP24K\Desktop\SkyCamOS_Claude\database\scripts>cd ../../backend

C:\Users\WVP24K\Desktop\SkyCamOS_Claude\backend>py -m uvicorn app.main:app --reload
←[32mINFO←[0m:     Will watch for changes in these directories: ['C:\\Users\\WVP24K\\Desktop\\SkyCamOS_Claude\\backend']
←[32mINFO←[0m:     Uvicorn running on ←[1mhttp://127.0.0.1:8000←[0m (Press CTRL+C to quit)
←[32mINFO←[0m:     Started reloader process [←[36m←[1m15016←[0m] using ←[36m←[1mWatchFiles←[0m
Process SpawnProcess-1:
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
  File "C:\Users\WVP24K\Desktop\SkyCamOS_Claude\backend\app\api\routes\auth.py", line 27, in <module>
    from app.models.user import User
  File "C:\Users\WVP24K\Desktop\SkyCamOS_Claude\backend\app\models\__init__.py", line 9, in <module>
    from app.models.event import Event
  File "C:\Users\WVP24K\Desktop\SkyCamOS_Claude\backend\app\models\event.py", line 54, in <module>
    class Event(Base):
  File "C:\Users\WVP24K\AppData\Local\Programs\Python\Python311\Lib\site-packages\sqlalchemy\orm\decl_api.py", line 847, in __init_subclass__
    _as_declarative(cls._sa_registry, cls, cls.__dict__)
  File "C:\Users\WVP24K\AppData\Local\Programs\Python\Python311\Lib\site-packages\sqlalchemy\orm\decl_base.py", line 247, in _as_declarative
    return _MapperConfig.setup_mapping(registry, cls, dict_, None, {})
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\WVP24K\AppData\Local\Programs\Python\Python311\Lib\site-packages\sqlalchemy\orm\decl_base.py", line 328, in setup_mapping
    return _ClassScanMapperConfig(
           ^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\WVP24K\AppData\Local\Programs\Python\Python311\Lib\site-packages\sqlalchemy\orm\decl_base.py", line 574, in __init__
    self._extract_mappable_attributes()
  File "C:\Users\WVP24K\AppData\Local\Programs\Python\Python311\Lib\site-packages\sqlalchemy\orm\decl_base.py", line 1507, in _extract_mappable_attributes
    raise exc.InvalidRequestError(
sqlalchemy.exc.InvalidRequestError: Attribute name 'metadata' is reserved when using the Declarative API.