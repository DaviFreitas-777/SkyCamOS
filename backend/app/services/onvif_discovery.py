"""
Servico de Descoberta ONVIF do SkyCamOS.

Este modulo implementa a descoberta automatica de cameras IP
utilizando o protocolo ONVIF e WS-Discovery (SSDP).
"""

import asyncio
import logging
import socket
import struct
from dataclasses import dataclass
from typing import Optional
from xml.etree import ElementTree

from app.config import settings

logger = logging.getLogger(__name__)

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
    ) -> Optional[str]:
        """
        Obtem a URL RTSP de uma camera via ONVIF.

        Args:
            ip_address: IP da camera.
            port: Porta ONVIF.
            username: Usuario para autenticacao.
            password: Senha para autenticacao.

        Returns:
            Optional[str]: URL RTSP ou None se falhar.
        """
        try:
            # TODO: Implementar obtencao de stream URI via ONVIF
            # Por enquanto, tenta URLs comuns

            common_paths = [
                "/stream1",
                "/h264/ch1/main/av_stream",
                "/cam/realmonitor",
                "/Streaming/Channels/101",
                "/live/ch00_0",
            ]

            auth = ""
            if username and password:
                auth = f"{username}:{password}@"

            # Retorna URL padrao mais comum
            return f"rtsp://{auth}{ip_address}:554{common_paths[0]}"

        except Exception as e:
            logger.error(f"Erro ao obter RTSP URL de {ip_address}: {e}")
            return None

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
