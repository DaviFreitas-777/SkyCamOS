# -*- coding: utf-8 -*-
"""
SkyCamOS Desktop Manager - Services Module
Modulo de servicos para gerenciamento do sistema
"""

from .camera_discovery import (
    CameraDiscoveryService,
    DiscoveredCamera,
    ONVIFScanner,
    SSDPScanner
)
from .process_manager import (
    ProcessManager,
    ProcessInfo,
    ProcessState
)
from .disk_manager import (
    DiskManager,
    DiskUsage,
    StoragePolicy
)
from .auto_start import (
    AutoStartManager,
    AutoStartMethod
)

__all__ = [
    # Camera Discovery
    'CameraDiscoveryService',
    'DiscoveredCamera',
    'ONVIFScanner',
    'SSDPScanner',
    # Process Manager
    'ProcessManager',
    'ProcessInfo',
    'ProcessState',
    # Disk Manager
    'DiskManager',
    'DiskUsage',
    'StoragePolicy',
    # Auto Start
    'AutoStartManager',
    'AutoStartMethod'
]
