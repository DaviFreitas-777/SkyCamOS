"""
Servico de Descoberta ONVIF do SkyCamOS.

Este modulo implementa a descoberta automatica de cameras IP
utilizando o protocolo ONVIF e WS-Discovery (SSDP).
"""

import asyncio
import logging
import socket
import struct
from dataclasses import dataclass, field
from typing import Optional
from xml.etree import ElementTree

from app.config import settings

logger = logging.getLogger(__name__)

# URLs RTSP padrao por fabricante
RTSP_PATHS_BY_MANUFACTURER = {
    "hikvision": [
        "/Streaming/Channels/101",
        "/Streaming/Channels/102",
        "/h264/ch1/main/av_stream",
        "/h264/ch1/sub/av_stream",
    ],
    "dahua": [
        "/cam/realmonitor?channel=1&subtype=0",
        "/cam/realmonitor?channel=1&subtype=1",
        "/live",
    ],
    "axis": [
        "/axis-media/media.amp",
        "/mjpg/video.mjpg",
        "/axis-media/media.amp?videocodec=h264",
    ],
    "foscam": [
        "/videoMain",
        "/videoSub",
        "/cgi-bin/CGIStream.cgi?cmd=GetMJStream",
    ],
    "reolink": [
        "/h264Preview_01_main",
        "/h264Preview_01_sub",
    ],
    "amcrest": [
        "/cam/realmonitor?channel=1&subtype=0",
        "/cam/realmonitor?channel=1&subtype=1",
    ],
    "vivotek": [
        "/live.sdp",
        "/live2.sdp",
    ],
    "intelbras": [
        "/cam/realmonitor?channel=1&subtype=0",
        "/h264/ch1/main/av_stream",
    ],
    "generic": [
        "/stream1",
        "/stream",
        "/live/ch00_0",
        "/h264/ch1/main/av_stream",
        "/cam/realmonitor?channel=1&subtype=0",
        "/Streaming/Channels/101",
        "/video1",
        "/MediaInput/h264",
        "/1/stream1",
        "/ch0_0.h264",
    ],
}

# Credenciais padrao por fabricante
DEFAULT_CREDENTIALS = {
    "hikvision": [("admin", "admin"), ("admin", "12345"), ("admin", "")],
    "dahua": [("admin", "admin"), ("admin", ""), ("admin", "123456")],
    "axis": [("root", "pass"), ("root", "root"), ("admin", "admin")],
    "foscam": [("admin", ""), ("admin", "admin")],
    "reolink": [("admin", ""), ("admin", "123456")],
    "intelbras": [("admin", "admin"), ("admin", "")],
    "generic": [("admin", "admin"), ("admin", ""), ("admin", "123456"), ("admin", "12345"), ("root", "root")],
}

# Mensagem WS-Discovery para busca de dispositivos ONVIF
WS_DISCOVERY_MESSAGE = """<?xml version="1.0" encoding="UTF-8"?>
<e:Envelope xmlns:e="http://www.w3.org/2003/05/soap-envelope"
    xmlns:w="http://schemas.xmlsoap.org/ws/2004/08/addressing"
    xmlns:d="http://schemas.xmlsoap.org/ws/2005/04/discovery"
    xmlns:dn="http://www.onvif.org/ver10/network/wsdl">
    <e:Header>
        <w:MessageID>uuid:{message_id}</w:MessageID>
        <w:To e:mustUnderstand="true">urn:schemas-xmlsoap-org:ws:2005:04:discovery</w:To>
        <w:Action e:mustUnderstand="true">
            http://schemas.xmlsoap.org/ws/2005/04/discovery/Probe
        </w:Action>
    </e:Header>
    <e:Body>
        <d:Probe>
            <d:Types>dn:NetworkVideoTransmitter</d:Types>
        </d:Probe>
    </e:Body>
</e:Envelope>"""

# Endereco multicast WS-Discovery
MULTICAST_ADDRESS = "239.255.255.250"
MULTICAST_PORT = 3702


@dataclass
class DiscoveredCamera:
    """
    Representa uma camera descoberta via ONVIF.

    Attributes:
        ip_address: Endereco IP da camera.
        port: Porta do servico ONVIF.
        onvif_url: URL completa do servico ONVIF.
        manufacturer: Fabricante (se disponivel).
        model: Modelo (se disponivel).
        name: Nome do dispositivo.
        hardware_id: ID do hardware.
        mac_address: Endereco MAC.
        scopes: Lista de escopos ONVIF.
    """

    ip_address: str
    port: int = 80
    onvif_url: Optional[str] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    name: Optional[str] = None
    hardware_id: Optional[str] = None
    mac_address: Optional[str] = None
    scopes: list[str] = None

    def __post_init__(self) -> None:
        """Inicializa lista de scopes se None."""
        if self.scopes is None:
            self.scopes = []

    def to_dict(self) -> dict:
        """Converte para dicionario."""
        return {
            "ip_address": self.ip_address,
            "port": self.port,
            "onvif_url": self.onvif_url,
            "manufacturer": self.manufacturer,
            "model": self.model,
            "name": self.name,
            "hardware_id": self.hardware_id,
            "mac_address": self.mac_address,
            "protocol": "onvif",
            "requires_auth": True,
        }


class ONVIFDiscoveryService:
    """
    Servico de descoberta de cameras ONVIF.

    Utiliza WS-Discovery (SSDP) para encontrar cameras
    compativeis com ONVIF na rede local.
    """

    def __init__(self, timeout: Optional[int] = None) -> None:
        """
        Inicializa o servico de descoberta.

        Args:
            timeout: Timeout em segundos para a descoberta.
        """
        self.timeout = timeout or settings.onvif_discovery_timeout
        self._discovered_cameras: dict[str, DiscoveredCamera] = {}

    async def discover(self) -> list[DiscoveredCamera]:
        """
        Executa a descoberta de cameras na rede.

        Returns:
            list[DiscoveredCamera]: Lista de cameras descobertas.
        """
        logger.info("Iniciando descoberta ONVIF...")
        self._discovered_cameras.clear()

        try:
            # Executa descoberta em thread separada (socket e bloqueante)
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._discover_sync)
        except Exception as e:
            logger.error(f"Erro na descoberta ONVIF: {e}")

        cameras = list(self._discovered_cameras.values())
        logger.info(f"Descoberta concluida. {len(cameras)} cameras encontradas.")

        return cameras

    def _discover_sync(self) -> None:
        """
        Executa a descoberta de forma sincrona.

        Esta funcao e executada em uma thread separada
        para nao bloquear o event loop.
        """
        import uuid

        # Cria socket UDP
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.settimeout(self.timeout)

        try:
            # Configura multicast
            mreq = struct.pack(
                "4sl",
                socket.inet_aton(MULTICAST_ADDRESS),
                socket.INADDR_ANY,
            )
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

            # Envia mensagem de descoberta
            message = WS_DISCOVERY_MESSAGE.format(message_id=uuid.uuid4())
            sock.sendto(
                message.encode("utf-8"),
                (MULTICAST_ADDRESS, MULTICAST_PORT),
            )

            logger.debug("Mensagem WS-Discovery enviada, aguardando respostas...")

            # Coleta respostas
            while True:
                try:
                    data, addr = sock.recvfrom(65535)
                    self._parse_response(data.decode("utf-8"), addr[0])
                except socket.timeout:
                    break
                except Exception as e:
                    logger.debug(f"Erro ao processar resposta: {e}")

        except Exception as e:
            logger.error(f"Erro no socket de descoberta: {e}")
        finally:
            sock.close()

    def _parse_response(self, xml_data: str, ip_address: str) -> None:
        """
        Parseia a resposta XML de um dispositivo.

        Args:
            xml_data: Dados XML da resposta.
            ip_address: IP de onde veio a resposta.
        """
        try:
            # Namespaces ONVIF
            namespaces = {
                "s": "http://www.w3.org/2003/05/soap-envelope",
                "d": "http://schemas.xmlsoap.org/ws/2005/04/discovery",
                "wsadis": "http://schemas.xmlsoap.org/ws/2004/08/addressing",
            }

            root = ElementTree.fromstring(xml_data)

            # Busca XAddrs (enderecos de servico)
            xaddrs_element = root.find(".//d:XAddrs", namespaces)
            if xaddrs_element is None or not xaddrs_element.text:
                return

            xaddrs = xaddrs_element.text.strip().split()
            onvif_url = xaddrs[0] if xaddrs else None

            # Extrai porta da URL
            port = 80
            if onvif_url:
                try:
                    from urllib.parse import urlparse
                    parsed = urlparse(onvif_url)
                    port = parsed.port or 80
                except Exception:
                    pass

            # Busca scopes
            scopes = []
            scopes_element = root.find(".//d:Scopes", namespaces)
            if scopes_element is not None and scopes_element.text:
                scopes = scopes_element.text.strip().split()

            # Extrai informacoes dos scopes
            manufacturer = None
            model = None
            name = None
            hardware_id = None

            for scope in scopes:
                scope_lower = scope.lower()
                if "hardware" in scope_lower:
                    hardware_id = scope.split("/")[-1]
                elif "name" in scope_lower:
                    name = scope.split("/")[-1].replace("%20", " ")
                elif "manufacturer" in scope_lower or "mfr" in scope_lower:
                    manufacturer = scope.split("/")[-1].replace("%20", " ")
                elif "model" in scope_lower:
                    model = scope.split("/")[-1].replace("%20", " ")

            # Cria objeto de camera descoberta
            camera = DiscoveredCamera(
                ip_address=ip_address,
                port=port,
                onvif_url=onvif_url,
                manufacturer=manufacturer,
                model=model,
                name=name or f"Camera {ip_address}",
                hardware_id=hardware_id,
                scopes=scopes,
            )

            self._discovered_cameras[ip_address] = camera
            logger.info(f"Camera descoberta: {ip_address} ({manufacturer} {model})")

        except ElementTree.ParseError as e:
            logger.debug(f"Erro ao parsear XML de {ip_address}: {e}")
        except Exception as e:
            logger.debug(f"Erro ao processar resposta de {ip_address}: {e}")

    async def get_camera_info(
        self,
        ip_address: str,
        port: int = 80,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ) -> Optional[dict]:
        """
        Obtem informacoes detalhadas de uma camera via ONVIF.

        Args:
            ip_address: IP da camera.
            port: Porta ONVIF.
            username: Usuario para autenticacao.
            password: Senha para autenticacao.

        Returns:
            Optional[dict]: Informacoes da camera ou None se falhar.
        """
        try:
            # TODO: Implementar conexao ONVIF completa usando onvif-zeep
            # Por enquanto, retorna informacoes basicas
            logger.info(f"Obtendo informacoes ONVIF de {ip_address}:{port}")

            # Tenta descoberta primeiro
            await self.discover()

            if ip_address in self._discovered_cameras:
                return self._discovered_cameras[ip_address].to_dict()

            return {
                "ip_address": ip_address,
                "port": port,
                "protocol": "onvif",
                "status": "connection_required",
                "message": "Autenticacao necessaria para obter detalhes",
            }

        except Exception as e:
            logger.error(f"Erro ao obter info ONVIF de {ip_address}: {e}")
            return None

    async def get_rtsp_url(
        self,
        ip_address: str,
        port: int = 80,
        username: Optional[str] = None,
        password: Optional[str] = None,
        manufacturer: Optional[str] = None,
    ) -> Optional[str]:
        """
        Obtem a URL RTSP de uma camera via ONVIF ou por fabricante.

        Args:
            ip_address: IP da camera.
            port: Porta ONVIF.
            username: Usuario para autenticacao.
            password: Senha para autenticacao.
            manufacturer: Fabricante da camera.

        Returns:
            Optional[str]: URL RTSP ou None se falhar.
        """
        try:
            # Primeiro tenta via ONVIF com onvif-zeep
            rtsp_url = await self._get_rtsp_via_onvif(ip_address, port, username, password)
            if rtsp_url:
                return rtsp_url

            # Fallback: usa URLs padrao por fabricante
            mfr = (manufacturer or "").lower()
            paths = RTSP_PATHS_BY_MANUFACTURER.get(mfr, RTSP_PATHS_BY_MANUFACTURER["generic"])

            auth = ""
            if username and password:
                auth = f"{username}:{password}@"

            # Retorna primeira URL do fabricante
            return f"rtsp://{auth}{ip_address}:554{paths[0]}"

        except Exception as e:
            logger.error(f"Erro ao obter RTSP URL de {ip_address}: {e}")
            return None

    async def _get_rtsp_via_onvif(
        self,
        ip_address: str,
        port: int,
        username: Optional[str],
        password: Optional[str],
    ) -> Optional[str]:
        """
        Obtem URL RTSP via protocolo ONVIF usando onvif-zeep.
        """
        try:
            from onvif import ONVIFCamera

            loop = asyncio.get_event_loop()

            def get_stream_uri():
                try:
                    cam = ONVIFCamera(ip_address, port, username or "admin", password or "")
                    media = cam.create_media_service()
                    profiles = media.GetProfiles()

                    if profiles:
                        stream_setup = {
                            "Stream": "RTP-Unicast",
                            "Transport": {"Protocol": "RTSP"}
                        }
                        uri = media.GetStreamUri({
                            "StreamSetup": stream_setup,
                            "ProfileToken": profiles[0].token
                        })
                        return uri.Uri
                except Exception as e:
                    logger.debug(f"ONVIF GetStreamUri falhou: {e}")
                return None

            return await loop.run_in_executor(None, get_stream_uri)

        except ImportError:
            logger.warning("onvif-zeep nao instalado, usando fallback")
            return None
        except Exception as e:
            logger.debug(f"Erro ao obter RTSP via ONVIF: {e}")
            return None

    async def test_credentials(
        self,
        ip_address: str,
        port: int = 554,
        username: str = "admin",
        password: str = "",
        manufacturer: Optional[str] = None,
    ) -> dict:
        """
        Testa credenciais em uma camera tentando conectar via RTSP.

        Returns:
            dict com success, rtsp_url, message
        """
        import subprocess

        mfr = (manufacturer or "").lower()
        paths = RTSP_PATHS_BY_MANUFACTURER.get(mfr, RTSP_PATHS_BY_MANUFACTURER["generic"])

        auth = f"{username}:{password}@" if password else f"{username}@" if username else ""

        for path in paths[:5]:  # Testa ate 5 URLs
            rtsp_url = f"rtsp://{auth}{ip_address}:{port}{path}"

            try:
                # Usa ffprobe para testar conexao (timeout 3s)
                result = subprocess.run(
                    ["ffprobe", "-v", "error", "-rtsp_transport", "tcp",
                     "-i", rtsp_url, "-show_entries", "stream=codec_type",
                     "-of", "default=noprint_wrappers=1"],
                    capture_output=True,
                    timeout=5,
                    text=True
                )

                if result.returncode == 0 or "video" in result.stdout.lower():
                    logger.info(f"Credenciais validas para {ip_address}: {path}")
                    return {
                        "success": True,
                        "rtsp_url": rtsp_url,
                        "path": path,
                        "message": "Conexao bem sucedida"
                    }
            except subprocess.TimeoutExpired:
                continue
            except FileNotFoundError:
                # ffprobe nao instalado, tenta socket simples
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(2)
                    result = sock.connect_ex((ip_address, port))
                    sock.close()
                    if result == 0:
                        return {
                            "success": True,
                            "rtsp_url": rtsp_url,
                            "path": path,
                            "message": "Porta RTSP acessivel (ffprobe nao disponivel)"
                        }
                except Exception:
                    pass
                break
            except Exception as e:
                logger.debug(f"Erro testando {rtsp_url}: {e}")
                continue

        return {
            "success": False,
            "rtsp_url": None,
            "message": "Nenhuma URL RTSP funcionou"
        }

    async def discover_and_test(
        self,
        username: str = "admin",
        password: str = "",
    ) -> list[dict]:
        """
        Descobre cameras na rede e testa credenciais em cada uma.

        Args:
            username: Usuario para testar
            password: Senha para testar

        Returns:
            Lista de cameras com status de conexao
        """
        # Descobre cameras
        cameras = await self.discover()
        results = []

        for camera in cameras:
            # Testa credenciais
            test_result = await self.test_credentials(
                ip_address=camera.ip_address,
                port=554,
                username=username,
                password=password,
                manufacturer=camera.manufacturer,
            )

            result = camera.to_dict()
            result["connection_test"] = test_result
            result["rtsp_url"] = test_result.get("rtsp_url")
            result["is_accessible"] = test_result.get("success", False)

            results.append(result)

        return results

    async def test_connection(
        self,
        ip_address: str,
        port: int = 80,
        username: Optional[str] = None,
        password: Optional[str] = None,
        timeout: int = 5,
    ) -> dict:
        """
        Testa a conexao com uma camera ONVIF.

        Args:
            ip_address: IP da camera.
            port: Porta ONVIF.
            username: Usuario para autenticacao.
            password: Senha para autenticacao.
            timeout: Timeout em segundos.

        Returns:
            dict: Resultado do teste com status e mensagem.
        """
        import httpx

        try:
            # Tenta conectar na porta ONVIF
            url = f"http://{ip_address}:{port}/onvif/device_service"

            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(url)

                if response.status_code in (200, 401, 405):
                    return {
                        "success": True,
                        "message": "Dispositivo ONVIF encontrado",
                        "requires_auth": response.status_code == 401,
                        "ip_address": ip_address,
                        "port": port,
                    }

                return {
                    "success": False,
                    "message": f"Resposta inesperada: {response.status_code}",
                }

        except httpx.TimeoutException:
            return {
                "success": False,
                "message": "Timeout ao conectar",
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Erro de conexao: {str(e)}",
            }


# Instancia global do servico
onvif_discovery_service = ONVIFDiscoveryService()
