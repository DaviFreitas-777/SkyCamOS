# -*- coding: utf-8 -*-
"""
SkyCamOS Desktop Manager - Network Utils
Utilitarios de rede para descoberta e comunicacao
"""

import socket
import asyncio
import subprocess
import platform
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import ipaddress

from .logger import get_logger

logger = get_logger("network")


@dataclass
class NetworkInterface:
    """Representa uma interface de rede."""
    name: str
    ip_address: str
    netmask: str
    broadcast: Optional[str]
    is_up: bool
    is_loopback: bool


def get_local_ip() -> str:
    """
    Obtem o IP local principal da maquina.
    Tenta conectar a um servidor externo para determinar a interface correta.

    Returns:
        IP local como string
    """
    try:
        # Cria socket UDP (nao precisa realmente conectar)
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            # Tenta "conectar" a um IP externo
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            logger.debug(f"IP local detectado: {local_ip}")
            return local_ip
    except Exception as e:
        logger.warning(f"Erro ao obter IP local: {e}")
        # Fallback para localhost
        return "127.0.0.1"


def get_network_interfaces() -> List[NetworkInterface]:
    """
    Lista todas as interfaces de rede disponiveis.

    Returns:
        Lista de NetworkInterface
    """
    interfaces = []

    try:
        import psutil

        # Obtem informacoes das interfaces
        addrs = psutil.net_if_addrs()
        stats = psutil.net_if_stats()

        for iface_name, addr_list in addrs.items():
            for addr in addr_list:
                # Apenas IPv4
                if addr.family == socket.AF_INET:
                    is_up = stats.get(iface_name, None)
                    is_up = is_up.isup if is_up else False

                    interface = NetworkInterface(
                        name=iface_name,
                        ip_address=addr.address,
                        netmask=addr.netmask or "255.255.255.0",
                        broadcast=addr.broadcast,
                        is_up=is_up,
                        is_loopback=addr.address.startswith("127.")
                    )
                    interfaces.append(interface)
                    logger.debug(f"Interface encontrada: {iface_name} - {addr.address}")

    except ImportError:
        logger.warning("psutil nao disponivel, usando metodo alternativo")
        # Fallback basico
        local_ip = get_local_ip()
        interfaces.append(NetworkInterface(
            name="default",
            ip_address=local_ip,
            netmask="255.255.255.0",
            broadcast=None,
            is_up=True,
            is_loopback=local_ip.startswith("127.")
        ))

    except Exception as e:
        logger.error(f"Erro ao listar interfaces: {e}")

    return interfaces


def is_port_available(port: int, host: str = "127.0.0.1") -> bool:
    """
    Verifica se uma porta esta disponivel para uso.

    Args:
        port: Numero da porta
        host: Host a verificar

    Returns:
        True se a porta esta disponivel
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            result = s.connect_ex((host, port))
            available = result != 0
            logger.debug(f"Porta {port} em {host}: {'disponivel' if available else 'em uso'}")
            return available
    except Exception as e:
        logger.error(f"Erro ao verificar porta {port}: {e}")
        return False


def find_available_port(start_port: int = 8000, end_port: int = 9000, host: str = "127.0.0.1") -> Optional[int]:
    """
    Encontra uma porta disponivel em um range.

    Args:
        start_port: Porta inicial do range
        end_port: Porta final do range
        host: Host a verificar

    Returns:
        Numero da porta disponivel ou None
    """
    for port in range(start_port, end_port + 1):
        if is_port_available(port, host):
            logger.info(f"Porta disponivel encontrada: {port}")
            return port

    logger.warning(f"Nenhuma porta disponivel no range {start_port}-{end_port}")
    return None


async def ping_host(host: str, timeout: float = 2.0) -> Tuple[bool, float]:
    """
    Verifica se um host esta acessivel via ping.

    Args:
        host: Host a verificar (IP ou hostname)
        timeout: Timeout em segundos

    Returns:
        Tupla (acessivel, latencia_ms)
    """
    try:
        # Comando ping diferente por sistema operacional
        if platform.system().lower() == "windows":
            cmd = ["ping", "-n", "1", "-w", str(int(timeout * 1000)), host]
        else:
            cmd = ["ping", "-c", "1", "-W", str(int(timeout)), host]

        # Executa ping
        start_time = asyncio.get_event_loop().time()

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        try:
            await asyncio.wait_for(process.communicate(), timeout=timeout + 1)
        except asyncio.TimeoutError:
            process.kill()
            return False, 0.0

        end_time = asyncio.get_event_loop().time()
        latency = (end_time - start_time) * 1000  # Em milissegundos

        success = process.returncode == 0
        logger.debug(f"Ping para {host}: {'OK' if success else 'FALHOU'} ({latency:.1f}ms)")

        return success, latency

    except Exception as e:
        logger.error(f"Erro ao fazer ping para {host}: {e}")
        return False, 0.0


def get_subnet_range(ip: str, netmask: str = "255.255.255.0") -> List[str]:
    """
    Obtem todos os IPs em uma subnet.

    Args:
        ip: IP base
        netmask: Mascara de rede

    Returns:
        Lista de IPs na subnet
    """
    try:
        # Cria objeto de rede
        network = ipaddress.IPv4Network(f"{ip}/{netmask}", strict=False)

        # Retorna todos os hosts (exclui rede e broadcast)
        hosts = [str(host) for host in network.hosts()]
        logger.debug(f"Subnet {network}: {len(hosts)} hosts")

        return hosts

    except Exception as e:
        logger.error(f"Erro ao calcular subnet: {e}")
        return []


async def scan_port(host: str, port: int, timeout: float = 1.0) -> bool:
    """
    Verifica se uma porta esta aberta em um host remoto.

    Args:
        host: Host a verificar
        port: Porta a verificar
        timeout: Timeout em segundos

    Returns:
        True se a porta esta aberta
    """
    try:
        # Cria conexao assincrona
        _, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port),
            timeout=timeout
        )
        writer.close()
        await writer.wait_closed()
        return True

    except (asyncio.TimeoutError, ConnectionRefusedError, OSError):
        return False

    except Exception as e:
        logger.debug(f"Erro ao escanear {host}:{port}: {e}")
        return False


async def scan_ports(host: str, ports: List[int], timeout: float = 1.0) -> Dict[int, bool]:
    """
    Escaneia multiplas portas em um host.

    Args:
        host: Host a verificar
        ports: Lista de portas
        timeout: Timeout por porta

    Returns:
        Dicionario {porta: aberta}
    """
    tasks = {port: scan_port(host, port, timeout) for port in ports}
    results = {}

    for port, task in tasks.items():
        results[port] = await task

    open_ports = [p for p, is_open in results.items() if is_open]
    if open_ports:
        logger.debug(f"Portas abertas em {host}: {open_ports}")

    return results


def get_broadcast_addresses() -> List[str]:
    """
    Obtem todos os enderecos de broadcast disponiveis.
    Util para descoberta de dispositivos na rede.

    Returns:
        Lista de enderecos de broadcast
    """
    broadcasts = []

    for iface in get_network_interfaces():
        if iface.broadcast and not iface.is_loopback and iface.is_up:
            broadcasts.append(iface.broadcast)
            logger.debug(f"Broadcast disponivel: {iface.broadcast} ({iface.name})")

    # Fallback para broadcast generico
    if not broadcasts:
        broadcasts.append("255.255.255.255")

    return broadcasts


def resolve_hostname(hostname: str) -> Optional[str]:
    """
    Resolve um hostname para IP.

    Args:
        hostname: Nome do host

    Returns:
        IP ou None
    """
    try:
        ip = socket.gethostbyname(hostname)
        logger.debug(f"Hostname {hostname} resolvido para {ip}")
        return ip
    except socket.gaierror as e:
        logger.warning(f"Falha ao resolver hostname {hostname}: {e}")
        return None


def get_hostname() -> str:
    """
    Obtem o hostname da maquina local.

    Returns:
        Hostname
    """
    return socket.gethostname()
