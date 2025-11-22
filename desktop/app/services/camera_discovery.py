# -*- coding: utf-8 -*-
"""
SkyCamOS Desktop Manager - Camera Discovery Service
Servico de descoberta automatica de cameras ONVIF e SSDP
"""

import asyncio
import socket
import struct
import time
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Dict, Optional, Callable, Any
from xml.etree import ElementTree as ET

from ..utils.logger import get_logger, LoggerMixin
from ..utils.network import (
    get_local_ip,
    get_broadcast_addresses,
    get_network_interfaces,
    scan_port
)

logger = get_logger("camera_discovery")


class CameraProtocol(Enum):
    """Protocolo de descoberta utilizado."""
    ONVIF = "onvif"
    SSDP = "ssdp"
    RTSP = "rtsp"
    UNKNOWN = "unknown"


@dataclass
class DiscoveredCamera:
    """Representa uma camera descoberta na rede."""
    ip_address: str
    port: int
    protocol: CameraProtocol
    manufacturer: str = "Unknown"
    model: str = "Unknown"
    serial_number: str = ""
    firmware_version: str = ""
    hardware_id: str = ""
    name: str = ""
    location: str = ""
    mac_address: str = ""
    rtsp_url: str = ""
    onvif_url: str = ""
    discovered_at: datetime = field(default_factory=datetime.now)
    last_seen: datetime = field(default_factory=datetime.now)
    is_online: bool = True
    capabilities: List[str] = field(default_factory=list)
    raw_data: Dict[str, Any] = field(default_factory=dict)

    @property
    def unique_id(self) -> str:
        """Identificador unico da camera."""
        if self.serial_number:
            return f"{self.manufacturer}_{self.serial_number}"
        if self.mac_address:
            return f"mac_{self.mac_address.replace(':', '')}"
        return f"{self.ip_address}_{self.port}"

    def __hash__(self):
        return hash(self.unique_id)

    def __eq__(self, other):
        if isinstance(other, DiscoveredCamera):
            return self.unique_id == other.unique_id
        return False


class ONVIFScanner(LoggerMixin):
    """
    Scanner para descoberta de cameras ONVIF.
    Usa WS-Discovery para encontrar dispositivos na rede.
    """

    # Namespaces ONVIF/WS-Discovery
    NAMESPACES = {
        'd': 'http://schemas.xmlsoap.org/ws/2005/04/discovery',
        'dn': 'http://www.onvif.org/ver10/network/wsdl',
        'tds': 'http://www.onvif.org/ver10/device/wsdl',
        'soap': 'http://www.w3.org/2003/05/soap-envelope',
        'wsa': 'http://schemas.xmlsoap.org/ws/2004/08/addressing'
    }

    # Endereco multicast WS-Discovery
    MULTICAST_IP = "239.255.255.250"
    MULTICAST_PORT = 3702

    # Template da mensagem Probe
    PROBE_MESSAGE = '''<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope"
               xmlns:wsa="http://schemas.xmlsoap.org/ws/2004/08/addressing"
               xmlns:d="http://schemas.xmlsoap.org/ws/2005/04/discovery"
               xmlns:dn="http://www.onvif.org/ver10/network/wsdl">
    <soap:Header>
        <wsa:MessageID>uuid:{message_id}</wsa:MessageID>
        <wsa:To>urn:schemas-xmlsoap-org:ws:2005:04:discovery</wsa:To>
        <wsa:Action>http://schemas.xmlsoap.org/ws/2005/04/discovery/Probe</wsa:Action>
    </soap:Header>
    <soap:Body>
        <d:Probe>
            <d:Types>dn:NetworkVideoTransmitter</d:Types>
        </d:Probe>
    </soap:Body>
</soap:Envelope>'''

    def __init__(self, timeout: float = 5.0):
        """
        Inicializa o scanner ONVIF.

        Args:
            timeout: Timeout para descoberta em segundos
        """
        self.timeout = timeout
        self._discovered: Dict[str, DiscoveredCamera] = {}

    async def scan(self) -> List[DiscoveredCamera]:
        """
        Realiza scan de cameras ONVIF na rede.

        Returns:
            Lista de cameras descobertas
        """
        self.logger.info("Iniciando scan ONVIF via WS-Discovery...")
        self._discovered.clear()

        try:
            # Cria socket UDP para multicast
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
            sock.setblocking(False)

            # Gera message ID unico
            import uuid
            message_id = str(uuid.uuid4())
            probe_data = self.PROBE_MESSAGE.format(message_id=message_id).encode('utf-8')

            # Envia probe multicast
            sock.sendto(probe_data, (self.MULTICAST_IP, self.MULTICAST_PORT))
            self.logger.debug(f"Probe ONVIF enviado para {self.MULTICAST_IP}:{self.MULTICAST_PORT}")

            # Aguarda respostas
            start_time = time.time()
            loop = asyncio.get_event_loop()

            while (time.time() - start_time) < self.timeout:
                try:
                    data, addr = await asyncio.wait_for(
                        loop.sock_recvfrom(sock, 65535),
                        timeout=0.5
                    )

                    camera = self._parse_probe_response(data, addr[0])
                    if camera:
                        self._discovered[camera.unique_id] = camera
                        self.logger.info(f"Camera ONVIF encontrada: {camera.ip_address} - {camera.manufacturer} {camera.model}")

                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    self.logger.debug(f"Erro ao receber resposta: {e}")

            sock.close()

        except Exception as e:
            self.logger.error(f"Erro no scan ONVIF: {e}")

        cameras = list(self._discovered.values())
        self.logger.info(f"Scan ONVIF concluido: {len(cameras)} cameras encontradas")
        return cameras

    def _parse_probe_response(self, data: bytes, ip: str) -> Optional[DiscoveredCamera]:
        """
        Faz parse da resposta WS-Discovery.

        Args:
            data: Dados XML recebidos
            ip: IP do dispositivo

        Returns:
            Camera descoberta ou None
        """
        try:
            # Parse XML
            root = ET.fromstring(data.decode('utf-8'))

            # Extrai informacoes
            camera = DiscoveredCamera(
                ip_address=ip,
                port=80,
                protocol=CameraProtocol.ONVIF
            )

            # Busca XAddrs (URL do servico)
            for xaddr in root.iter():
                if 'XAddrs' in xaddr.tag:
                    urls = xaddr.text.split() if xaddr.text else []
                    for url in urls:
                        if 'http' in url:
                            camera.onvif_url = url
                            # Extrai porta da URL
                            match = re.search(r':(\d+)', url)
                            if match:
                                camera.port = int(match.group(1))
                            break

            # Busca Scopes
            for scope in root.iter():
                if 'Scopes' in scope.tag and scope.text:
                    scopes = scope.text.split()
                    for s in scopes:
                        if 'onvif://www.onvif.org/name/' in s:
                            camera.name = s.split('/')[-1]
                        elif 'onvif://www.onvif.org/hardware/' in s:
                            camera.model = s.split('/')[-1]
                        elif 'onvif://www.onvif.org/location/' in s:
                            camera.location = s.split('/')[-1]

            # Salva dados brutos
            camera.raw_data['probe_response'] = data.decode('utf-8', errors='ignore')

            return camera

        except ET.ParseError as e:
            self.logger.debug(f"Erro ao fazer parse XML: {e}")
            return None
        except Exception as e:
            self.logger.debug(f"Erro ao processar resposta: {e}")
            return None

    async def get_device_info(self, camera: DiscoveredCamera, username: str = "admin", password: str = "admin") -> bool:
        """
        Obtem informacoes detalhadas do dispositivo via ONVIF.

        Args:
            camera: Camera a consultar
            username: Usuario ONVIF
            password: Senha ONVIF

        Returns:
            True se obteve informacoes com sucesso
        """
        try:
            # Tenta importar onvif-zeep
            from onvif import ONVIFCamera

            cam = ONVIFCamera(
                camera.ip_address,
                camera.port,
                username,
                password
            )

            # Obtem informacoes do dispositivo
            device_info = cam.devicemgmt.GetDeviceInformation()

            camera.manufacturer = device_info.Manufacturer or camera.manufacturer
            camera.model = device_info.Model or camera.model
            camera.serial_number = device_info.SerialNumber or camera.serial_number
            camera.firmware_version = device_info.FirmwareVersion or camera.firmware_version
            camera.hardware_id = device_info.HardwareId or camera.hardware_id

            # Tenta obter URL RTSP
            try:
                media = cam.create_media_service()
                profiles = media.GetProfiles()
                if profiles:
                    stream_uri = media.GetStreamUri({
                        'StreamSetup': {
                            'Stream': 'RTP-Unicast',
                            'Transport': {'Protocol': 'RTSP'}
                        },
                        'ProfileToken': profiles[0].token
                    })
                    camera.rtsp_url = stream_uri.Uri
            except Exception as e:
                self.logger.debug(f"Nao foi possivel obter RTSP URL: {e}")

            self.logger.info(f"Informacoes obtidas: {camera.manufacturer} {camera.model}")
            return True

        except ImportError:
            self.logger.warning("Biblioteca onvif-zeep nao instalada")
            return False
        except Exception as e:
            self.logger.error(f"Erro ao obter info do dispositivo: {e}")
            return False


class SSDPScanner(LoggerMixin):
    """
    Scanner para descoberta de cameras via SSDP.
    Simple Service Discovery Protocol (parte do UPnP).
    """

    MULTICAST_IP = "239.255.255.250"
    MULTICAST_PORT = 1900

    # Template da mensagem M-SEARCH
    MSEARCH_MESSAGE = """M-SEARCH * HTTP/1.1\r
HOST: 239.255.255.250:1900\r
MAN: "ssdp:discover"\r
MX: 3\r
ST: {search_target}\r
\r
"""

    # Alvos de busca
    SEARCH_TARGETS = [
        "upnp:rootdevice",
        "urn:schemas-upnp-org:device:MediaServer:1",
        "urn:schemas-upnp-org:service:ContentDirectory:1",
        "ssdp:all"
    ]

    def __init__(self, timeout: float = 5.0):
        """
        Inicializa o scanner SSDP.

        Args:
            timeout: Timeout para descoberta em segundos
        """
        self.timeout = timeout
        self._discovered: Dict[str, DiscoveredCamera] = {}

    async def scan(self) -> List[DiscoveredCamera]:
        """
        Realiza scan de dispositivos SSDP na rede.

        Returns:
            Lista de cameras/dispositivos descobertos
        """
        self.logger.info("Iniciando scan SSDP...")
        self._discovered.clear()

        try:
            # Cria socket UDP
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
            sock.setblocking(False)

            # Envia M-SEARCH para cada target
            for target in self.SEARCH_TARGETS:
                message = self.MSEARCH_MESSAGE.format(search_target=target).encode('utf-8')
                sock.sendto(message, (self.MULTICAST_IP, self.MULTICAST_PORT))
                self.logger.debug(f"M-SEARCH enviado: {target}")

            # Aguarda respostas
            start_time = time.time()
            loop = asyncio.get_event_loop()

            while (time.time() - start_time) < self.timeout:
                try:
                    data, addr = await asyncio.wait_for(
                        loop.sock_recvfrom(sock, 65535),
                        timeout=0.5
                    )

                    camera = self._parse_ssdp_response(data, addr[0])
                    if camera:
                        self._discovered[camera.unique_id] = camera
                        self.logger.info(f"Dispositivo SSDP encontrado: {camera.ip_address}")

                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    self.logger.debug(f"Erro ao receber resposta: {e}")

            sock.close()

        except Exception as e:
            self.logger.error(f"Erro no scan SSDP: {e}")

        cameras = list(self._discovered.values())
        self.logger.info(f"Scan SSDP concluido: {len(cameras)} dispositivos encontrados")
        return cameras

    def _parse_ssdp_response(self, data: bytes, ip: str) -> Optional[DiscoveredCamera]:
        """
        Faz parse da resposta SSDP.

        Args:
            data: Dados HTTP recebidos
            ip: IP do dispositivo

        Returns:
            Camera descoberta ou None
        """
        try:
            response = data.decode('utf-8', errors='ignore')
            headers = {}

            # Parse dos headers HTTP
            for line in response.split('\r\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    headers[key.upper().strip()] = value.strip()

            # Verifica se e um dispositivo relevante
            server = headers.get('SERVER', '')
            st = headers.get('ST', '')
            usn = headers.get('USN', '')
            location = headers.get('LOCATION', '')

            # Filtra apenas dispositivos de midia/cameras
            if not any(keyword in server.lower() or keyword in st.lower()
                      for keyword in ['camera', 'ipcam', 'nvr', 'dvr', 'media', 'video', 'upnp']):
                if 'rootdevice' not in st.lower():
                    return None

            camera = DiscoveredCamera(
                ip_address=ip,
                port=80,
                protocol=CameraProtocol.SSDP
            )

            # Extrai informacoes
            if server:
                parts = server.split('/')
                if len(parts) >= 1:
                    camera.manufacturer = parts[0].strip()
                if len(parts) >= 2:
                    camera.firmware_version = parts[-1].strip()

            if usn:
                # USN geralmente contem UUID
                match = re.search(r'uuid:([a-f0-9-]+)', usn, re.IGNORECASE)
                if match:
                    camera.serial_number = match.group(1)

            if location:
                # Extrai porta da URL de localizacao
                match = re.search(r':(\d+)', location)
                if match:
                    camera.port = int(match.group(1))

            camera.raw_data = {
                'ssdp_response': response,
                'headers': headers
            }

            return camera

        except Exception as e:
            self.logger.debug(f"Erro ao processar resposta SSDP: {e}")
            return None


class CameraDiscoveryService(LoggerMixin):
    """
    Servico principal de descoberta de cameras.
    Combina ONVIF e SSDP para descoberta abrangente.
    """

    def __init__(
        self,
        onvif_enabled: bool = True,
        ssdp_enabled: bool = True,
        scan_timeout: float = 10.0,
        onvif_ports: Optional[List[int]] = None
    ):
        """
        Inicializa o servico de descoberta.

        Args:
            onvif_enabled: Habilita descoberta ONVIF
            ssdp_enabled: Habilita descoberta SSDP
            scan_timeout: Timeout para cada scan
            onvif_ports: Portas ONVIF a verificar
        """
        self.onvif_enabled = onvif_enabled
        self.ssdp_enabled = ssdp_enabled
        self.scan_timeout = scan_timeout
        self.onvif_ports = onvif_ports or [80, 8080, 554, 8899]

        self._onvif_scanner = ONVIFScanner(timeout=scan_timeout)
        self._ssdp_scanner = SSDPScanner(timeout=scan_timeout)

        self._cameras: Dict[str, DiscoveredCamera] = {}
        self._running = False
        self._scan_task: Optional[asyncio.Task] = None
        self._callbacks: List[Callable[[DiscoveredCamera], None]] = []

    @property
    def cameras(self) -> List[DiscoveredCamera]:
        """Retorna lista de cameras descobertas."""
        return list(self._cameras.values())

    def add_callback(self, callback: Callable[[DiscoveredCamera], None]) -> None:
        """
        Adiciona callback para quando uma camera for descoberta.

        Args:
            callback: Funcao a ser chamada
        """
        self._callbacks.append(callback)

    def remove_callback(self, callback: Callable[[DiscoveredCamera], None]) -> None:
        """Remove um callback."""
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    def _notify_callbacks(self, camera: DiscoveredCamera) -> None:
        """Notifica todos os callbacks sobre uma camera descoberta."""
        for callback in self._callbacks:
            try:
                callback(camera)
            except Exception as e:
                self.logger.error(f"Erro em callback: {e}")

    async def scan_once(self) -> List[DiscoveredCamera]:
        """
        Realiza um unico scan de cameras.

        Returns:
            Lista de cameras descobertas
        """
        self.logger.info("Iniciando scan de cameras...")
        discovered = []

        # Scan ONVIF
        if self.onvif_enabled:
            try:
                onvif_cameras = await self._onvif_scanner.scan()
                for camera in onvif_cameras:
                    if camera.unique_id not in self._cameras:
                        self._cameras[camera.unique_id] = camera
                        self._notify_callbacks(camera)
                    else:
                        # Atualiza last_seen
                        self._cameras[camera.unique_id].last_seen = datetime.now()
                        self._cameras[camera.unique_id].is_online = True
                    discovered.extend(onvif_cameras)
            except Exception as e:
                self.logger.error(f"Erro no scan ONVIF: {e}")

        # Scan SSDP
        if self.ssdp_enabled:
            try:
                ssdp_cameras = await self._ssdp_scanner.scan()
                for camera in ssdp_cameras:
                    if camera.unique_id not in self._cameras:
                        self._cameras[camera.unique_id] = camera
                        self._notify_callbacks(camera)
                    else:
                        self._cameras[camera.unique_id].last_seen = datetime.now()
                        self._cameras[camera.unique_id].is_online = True
                    discovered.extend(ssdp_cameras)
            except Exception as e:
                self.logger.error(f"Erro no scan SSDP: {e}")

        self.logger.info(f"Scan concluido: {len(self._cameras)} cameras no total")
        return list(self._cameras.values())

    async def start_periodic_scan(self, interval: float = 300.0) -> None:
        """
        Inicia scan periodico de cameras.

        Args:
            interval: Intervalo entre scans em segundos
        """
        if self._running:
            self.logger.warning("Scan periodico ja esta em execucao")
            return

        self._running = True
        self.logger.info(f"Iniciando scan periodico a cada {interval}s")

        async def scan_loop():
            while self._running:
                try:
                    await self.scan_once()
                except Exception as e:
                    self.logger.error(f"Erro no scan periodico: {e}")

                await asyncio.sleep(interval)

        self._scan_task = asyncio.create_task(scan_loop())

    async def stop_periodic_scan(self) -> None:
        """Para o scan periodico."""
        if self._running:
            self._running = False
            if self._scan_task:
                self._scan_task.cancel()
                try:
                    await self._scan_task
                except asyncio.CancelledError:
                    pass
            self.logger.info("Scan periodico parado")

    def get_camera(self, unique_id: str) -> Optional[DiscoveredCamera]:
        """
        Obtem uma camera pelo ID unico.

        Args:
            unique_id: ID unico da camera

        Returns:
            Camera ou None
        """
        return self._cameras.get(unique_id)

    def get_cameras_by_manufacturer(self, manufacturer: str) -> List[DiscoveredCamera]:
        """
        Filtra cameras por fabricante.

        Args:
            manufacturer: Nome do fabricante

        Returns:
            Lista de cameras do fabricante
        """
        return [
            cam for cam in self._cameras.values()
            if manufacturer.lower() in cam.manufacturer.lower()
        ]

    def clear_cameras(self) -> None:
        """Limpa a lista de cameras descobertas."""
        self._cameras.clear()
        self.logger.info("Lista de cameras limpa")

    def to_dict(self) -> List[Dict]:
        """
        Converte cameras para formato de dicionario.

        Returns:
            Lista de dicionarios
        """
        result = []
        for camera in self._cameras.values():
            result.append({
                'unique_id': camera.unique_id,
                'ip_address': camera.ip_address,
                'port': camera.port,
                'protocol': camera.protocol.value,
                'manufacturer': camera.manufacturer,
                'model': camera.model,
                'serial_number': camera.serial_number,
                'name': camera.name,
                'rtsp_url': camera.rtsp_url,
                'onvif_url': camera.onvif_url,
                'is_online': camera.is_online,
                'discovered_at': camera.discovered_at.isoformat(),
                'last_seen': camera.last_seen.isoformat()
            })
        return result
