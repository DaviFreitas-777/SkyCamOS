# -*- coding: utf-8 -*-
"""
SkyCamOS Desktop Manager
========================

Aplicacao de gerenciamento do SkyCamOS para desktop.
Fornece interface para descoberta de cameras, gerenciamento do backend,
monitoramento de disco e integracao com o sistema operacional.

Modulos:
    - config: Configuracoes da aplicacao
    - services: Servicos de descoberta, processo e disco
    - ui: Interface de usuario (CLI e System Tray)
    - utils: Utilitarios de rede e logging
"""

__version__ = "1.0.0"
__author__ = "SkyCamOS Team"
__description__ = "Desktop Manager para o sistema SkyCamOS"

from .config import (
    AppConfig,
    ConfigManager,
    get_config,
    save_config,
    APP_NAME,
    APP_VERSION
)

__all__ = [
    # Versao
    '__version__',
    '__author__',
    '__description__',
    # Config
    'AppConfig',
    'ConfigManager',
    'get_config',
    'save_config',
    'APP_NAME',
    'APP_VERSION'
]
