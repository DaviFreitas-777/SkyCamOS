# -*- coding: utf-8 -*-
"""
SkyCamOS Desktop Manager - Utils Module
Modulo de utilitarios para o Desktop Manager
"""

from .logger import get_logger, setup_logging
from .network import (
    get_local_ip,
    get_network_interfaces,
    is_port_available,
    find_available_port,
    ping_host
)

__all__ = [
    'get_logger',
    'setup_logging',
    'get_local_ip',
    'get_network_interfaces',
    'is_port_available',
    'find_available_port',
    'ping_host'
]
