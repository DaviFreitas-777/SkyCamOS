"""
Servico de Descoberta SSDP do SkyCamOS.

Este modulo implementa a descoberta automatica de dispositivos
utilizando o protocolo UPnP/SSDP (Simple Service Discovery Protocol).
"""

import asyncio
import logging
import socket
import re
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlparse

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

# Mensagem M-SEARCH para descoberta SSDP
SSDP_MSEARCH = (
    "M-SEARCH * HTTP/1.1\r\n"
    "HOST: 239.255.255.250:1900\r\n"
    "MAN: \"ssdp:discover\"\r\n"
    "MX: 3\r\n"
    "ST: {search_target}\r\n"
    "\r\n"
)

# Endereco multicast SSDP
SSDP_MULTICAST_ADDRESS = "239.255.255.250"
SSDP_MULTICAST_PORT = 1900

# Targets de busca para cameras IP
SEARCH_TARGETS = [
    "ssdp:all",
    "urn:schemas-upnp-org:device:MediaServer:1",
    "urn:schemas-upnp-org:device:Basic:1",
    "upnp:rootdevice",
]


@dataclass
class SSDPDevice:
    """
    Representa um dispositivo descoberto via SSDP.

    Attributes:
        ip_address: Endereco IP do dispositivo.
        port: Porta HTTP do dispositivo.
        location: URL de descricao do dispositivo.
        server: Informacao do servidor.
        usn: Unique Service Name.
        st: Search Target.
        friendly_name: Nome amigavel.
        manufacturer: Fabricante.
        model: Modelo.
        is_camera: Se parece ser uma camera IP.
    """

    ip_address: str
    port: int = 80
    location: Optional[str] = None
    server: Optional[str] = None
    usn: Optional[str] = None
    st: Optional[str] = None
    friendly_name: Optional[str] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    is_camera: bool = False

    def to_dict(self) -> dict:
        """Converte para dicionario."""
        return {
            "ip_address": self.ip_address,
            "port": self.port,
            "protocol": "ssdp",
            "manufacturer": self.manufacturer,
            "model": self.model,
            "name": self.friendly_name or f"Dispositivo {self.ip_address}",
            "requires_auth": True,
            "is_camera": self.is_camera,
        }


class SSDPDiscoveryService:
    """
    Servico de descoberta de dispositivos via SSDP/UPnP.

    Utiliza mensagens M-SEARCH multicast para encontrar
    dispositivos de rede compativeis.
    """

    def __init__(self, timeout: Optional[int] = None) -> None:
        """
        Inicializa o servico de descoberta.

        Args:
            timeout: Timeout em segundos para a descoberta.
        """
        self.timeout = timeout or settings.onvif_discovery_timeout
        self._discovered_devices: dict[str, SSDPDevice] = {}

    async def discover(self, cameras_only: bool = True) -> list[SSDPDevice]:
        """
        Executa a descoberta de dispositivos na rede.

        Args:
            cameras_only: Se True, filtra apenas dispositivos que parecem cameras.

        Returns:
            list[SSDPDevice]: Lista de dispositivos descobertos.
        """
        logger.info("Iniciando descoberta SSDP...")
        self._discovered_devices.clear()

        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._discover_sync)

            # Obtem informacoes adicionais dos dispositivos
            await self._fetch_device_descriptions()

        except Exception as e:
            logger.error(f"Erro na descoberta SSDP: {e}")

        devices = list(self._discovered_devices.values())

        if cameras_only:
            devices = [d for d in devices if d.is_camera]

        logger.info(f"Descoberta SSDP concluida. {len(devices)} dispositivos encontrados.")

        return devices

    def _discover_sync(self) -> None:
        """
        Executa a descoberta de forma sincrona.
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.settimeout(self.timeout)

        try:
            # Envia para cada target
            for target in SEARCH_TARGETS:
                message = SSDP_MSEARCH.format(search_target=target)
                sock.sendto(
                    message.encode("utf-8"),
                    (SSDP_MULTICAST_ADDRESS, SSDP_MULTICAST_PORT),
                )

            logger.debug("Mensagens SSDP enviadas, aguardando respostas...")

            # Coleta respostas
            while True:
                try:
                    data, addr = sock.recvfrom(65535)
                    self._parse_response(data.decode("utf-8"), addr[0])
                except socket.timeout:
                    break
                except Exception as e:
                    logger.debug(f"Erro ao processar resposta SSDP: {e}")

        except Exception as e:
            logger.error(f"Erro no socket SSDP: {e}")
        finally:
            sock.close()

    def _parse_response(self, response: str, ip_address: str) -> None:
        """
        Parseia a resposta SSDP.

        Args:
            response: Resposta HTTP.
            ip_address: IP de onde veio a resposta.
        """
        try:
            headers = {}
            lines = response.split("\r\n")

            for line in lines[1:]:
                if ":" in line:
                    key, value = line.split(":", 1)
                    headers[key.strip().upper()] = value.strip()

            location = headers.get("LOCATION", "")
            server = headers.get("SERVER", "")
            usn = headers.get("USN", "")
            st = headers.get("ST", "")

            # Extrai porta da location
            port = 80
            if location:
                try:
                    parsed = urlparse(location)
                    port = parsed.port or 80
                except Exception:
                    pass

            # Verifica se parece ser uma camera
            is_camera = self._is_likely_camera(server, usn, st)

            device = SSDPDevice(
                ip_address=ip_address,
                port=port,
                location=location,
                server=server,
                usn=usn,
                st=st,
                is_camera=is_camera,
            )

            # Adiciona apenas se nao existir ou se for mais completo
            if ip_address not in self._discovered_devices:
                self._discovered_devices[ip_address] = device
                logger.debug(f"Dispositivo SSDP descoberto: {ip_address}")

        except Exception as e:
            logger.debug(f"Erro ao parsear resposta SSDP de {ip_address}: {e}")

    def _is_likely_camera(self, server: str, usn: str, st: str) -> bool:
        """
        Verifica se o dispositivo parece ser uma camera IP.

        Args:
            server: Header Server.
            usn: Unique Service Name.
            st: Search Target.

        Returns:
            bool: True se parece ser uma camera.
        """
        camera_keywords = [
            "camera", "cam", "ipcam", "nvr", "dvr", "hikvision",
            "dahua", "axis", "foscam", "reolink", "amcrest",
            "wyze", "eufy", "ring", "arlo", "nest", "blink",
            "tp-link", "tapo", "imou", "ezviz", "vivotek",
            "onvif", "rtsp", "video", "surveillance",
        ]

        combined = f"{server} {usn} {st}".lower()

        for keyword in camera_keywords:
            if keyword in combined:
                return True

        return False

    async def _fetch_device_descriptions(self) -> None:
        """
        Busca informacoes detalhadas dos dispositivos via HTTP.
        """
        async with httpx.AsyncClient(timeout=5) as client:
            for ip, device in self._discovered_devices.items():
                if device.location:
                    try:
                        response = await client.get(device.location)
                        if response.status_code == 200:
                            self._parse_device_description(device, response.text)
                    except Exception as e:
                        logger.debug(f"Erro ao buscar descricao de {ip}: {e}")

    def _parse_device_description(self, device: SSDPDevice, xml_data: str) -> None:
        """
        Parseia a descricao XML do dispositivo.

        Args:
            device: Dispositivo a atualizar.
            xml_data: Dados XML.
        """
        try:
            # Busca por tags comuns (simplificado, sem namespace)
            friendly_match = re.search(r"<friendlyName>(.+?)</friendlyName>", xml_data, re.I)
            if friendly_match:
                device.friendly_name = friendly_match.group(1)

            mfr_match = re.search(r"<manufacturer>(.+?)</manufacturer>", xml_data, re.I)
            if mfr_match:
                device.manufacturer = mfr_match.group(1)

            model_match = re.search(r"<modelName>(.+?)</modelName>", xml_data, re.I)
            if model_match:
                device.model = model_match.group(1)

            # Atualiza deteccao de camera baseado em informacoes
            if device.manufacturer or device.model:
                combined = f"{device.manufacturer or ''} {device.model or ''} {device.friendly_name or ''}".lower()
                device.is_camera = device.is_camera or self._is_likely_camera(combined, "", "")

        except Exception as e:
            logger.debug(f"Erro ao parsear descricao XML: {e}")


# Instancia global do servico
ssdp_discovery_service = SSDPDiscoveryService()
