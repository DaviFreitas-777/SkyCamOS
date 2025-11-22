#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SkyCamOS Desktop Manager - Run Script
Script de execucao do Desktop Manager

Uso:
    python run.py                # Inicia normalmente
    python run.py --minimized    # Inicia minimizado (apenas tray)
    python run.py --debug        # Modo de debug
    python run.py --help         # Exibe ajuda
"""

import sys
import os
from pathlib import Path

# Adiciona o diretorio do app ao path
APP_DIR = Path(__file__).parent
sys.path.insert(0, str(APP_DIR))

# Importa e executa o main
from app.main import main

if __name__ == "__main__":
    sys.exit(main())
