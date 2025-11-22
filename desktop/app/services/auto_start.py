# -*- coding: utf-8 -*-
"""
SkyCamOS Desktop Manager - Auto Start
Gerenciador de inicializacao automatica com o Windows
"""

import os
import sys
import ctypes
from enum import Enum
from pathlib import Path
from typing import Optional, Dict, Any
import subprocess

from ..utils.logger import get_logger, LoggerMixin

logger = get_logger("auto_start")


class AutoStartMethod(Enum):
    """Metodos de auto-start disponiveis."""
    REGISTRY = "registry"           # Registro do Windows
    STARTUP_FOLDER = "startup"      # Pasta de Inicializacao
    TASK_SCHEDULER = "scheduler"    # Agendador de Tarefas
    SERVICE = "service"             # Servico do Windows


class AutoStartManager(LoggerMixin):
    """
    Gerenciador de inicializacao automatica.
    Permite registrar a aplicacao para iniciar com o Windows.
    """

    # Constantes do Registro
    REGISTRY_RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
    REGISTRY_RUNONCE_KEY = r"Software\Microsoft\Windows\CurrentVersion\RunOnce"

    # Nome da aplicacao no registro
    APP_NAME = "SkyCamOS"
    APP_DESCRIPTION = "SkyCamOS Desktop Manager - Sistema de monitoramento de cameras"

    def __init__(self, executable_path: Optional[Path] = None):
        """
        Inicializa o gerenciador de auto-start.

        Args:
            executable_path: Caminho para o executavel (padrao: script atual)
        """
        self.executable_path = executable_path or Path(sys.executable)
        self._is_windows = sys.platform == "win32"

        if self._is_windows:
            try:
                import winreg
                self._winreg = winreg
            except ImportError:
                self._winreg = None
                self.logger.warning("Modulo winreg nao disponivel")

    def is_admin(self) -> bool:
        """
        Verifica se esta executando como administrador.

        Returns:
            True se for administrador
        """
        if not self._is_windows:
            return os.getuid() == 0

        try:
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception:
            return False

    def is_enabled(self, method: AutoStartMethod = AutoStartMethod.REGISTRY) -> bool:
        """
        Verifica se o auto-start esta habilitado.

        Args:
            method: Metodo de auto-start a verificar

        Returns:
            True se estiver habilitado
        """
        if not self._is_windows:
            self.logger.warning("Auto-start so e suportado no Windows")
            return False

        if method == AutoStartMethod.REGISTRY:
            return self._check_registry()
        elif method == AutoStartMethod.STARTUP_FOLDER:
            return self._check_startup_folder()
        elif method == AutoStartMethod.TASK_SCHEDULER:
            return self._check_task_scheduler()
        elif method == AutoStartMethod.SERVICE:
            return self._check_service()

        return False

    def enable(
        self,
        method: AutoStartMethod = AutoStartMethod.REGISTRY,
        start_minimized: bool = True,
        delay_seconds: float = 0
    ) -> bool:
        """
        Habilita auto-start.

        Args:
            method: Metodo de auto-start
            start_minimized: Se deve iniciar minimizado
            delay_seconds: Delay antes de iniciar

        Returns:
            True se habilitou com sucesso
        """
        if not self._is_windows:
            self.logger.warning("Auto-start so e suportado no Windows")
            return False

        self.logger.info(f"Habilitando auto-start via {method.value}...")

        if method == AutoStartMethod.REGISTRY:
            return self._enable_registry(start_minimized)
        elif method == AutoStartMethod.STARTUP_FOLDER:
            return self._enable_startup_folder(start_minimized)
        elif method == AutoStartMethod.TASK_SCHEDULER:
            return self._enable_task_scheduler(start_minimized, delay_seconds)
        elif method == AutoStartMethod.SERVICE:
            return self._enable_service()

        return False

    def disable(self, method: AutoStartMethod = AutoStartMethod.REGISTRY) -> bool:
        """
        Desabilita auto-start.

        Args:
            method: Metodo de auto-start

        Returns:
            True se desabilitou com sucesso
        """
        if not self._is_windows:
            return False

        self.logger.info(f"Desabilitando auto-start via {method.value}...")

        if method == AutoStartMethod.REGISTRY:
            return self._disable_registry()
        elif method == AutoStartMethod.STARTUP_FOLDER:
            return self._disable_startup_folder()
        elif method == AutoStartMethod.TASK_SCHEDULER:
            return self._disable_task_scheduler()
        elif method == AutoStartMethod.SERVICE:
            return self._disable_service()

        return False

    # ========== Registro do Windows ==========

    def _check_registry(self) -> bool:
        """Verifica se esta registrado no Registry."""
        if not self._winreg:
            return False

        try:
            key = self._winreg.OpenKey(
                self._winreg.HKEY_CURRENT_USER,
                self.REGISTRY_RUN_KEY,
                0,
                self._winreg.KEY_READ
            )
            try:
                value, _ = self._winreg.QueryValueEx(key, self.APP_NAME)
                self._winreg.CloseKey(key)
                return bool(value)
            except WindowsError:
                self._winreg.CloseKey(key)
                return False
        except Exception as e:
            self.logger.debug(f"Erro ao verificar registro: {e}")
            return False

    def _enable_registry(self, start_minimized: bool = True) -> bool:
        """Adiciona ao registro do Windows."""
        if not self._winreg:
            return False

        try:
            # Monta comando
            command = f'"{self.executable_path}"'
            if start_minimized:
                command += " --minimized"

            # Abre chave do registro
            key = self._winreg.OpenKey(
                self._winreg.HKEY_CURRENT_USER,
                self.REGISTRY_RUN_KEY,
                0,
                self._winreg.KEY_SET_VALUE
            )

            # Define valor
            self._winreg.SetValueEx(
                key,
                self.APP_NAME,
                0,
                self._winreg.REG_SZ,
                command
            )

            self._winreg.CloseKey(key)
            self.logger.info("Auto-start habilitado no registro")
            return True

        except PermissionError:
            self.logger.error("Permissao negada para modificar registro")
            return False
        except Exception as e:
            self.logger.error(f"Erro ao adicionar ao registro: {e}")
            return False

    def _disable_registry(self) -> bool:
        """Remove do registro do Windows."""
        if not self._winreg:
            return False

        try:
            key = self._winreg.OpenKey(
                self._winreg.HKEY_CURRENT_USER,
                self.REGISTRY_RUN_KEY,
                0,
                self._winreg.KEY_SET_VALUE
            )

            try:
                self._winreg.DeleteValue(key, self.APP_NAME)
            except WindowsError:
                pass  # Valor ja nao existe

            self._winreg.CloseKey(key)
            self.logger.info("Auto-start removido do registro")
            return True

        except Exception as e:
            self.logger.error(f"Erro ao remover do registro: {e}")
            return False

    # ========== Pasta de Inicializacao ==========

    def _get_startup_folder(self) -> Path:
        """Obtem pasta de inicializacao do Windows."""
        startup = Path(os.environ.get(
            "APPDATA",
            Path.home() / "AppData" / "Roaming"
        )) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
        return startup

    def _get_shortcut_path(self) -> Path:
        """Obtem caminho do atalho."""
        return self._get_startup_folder() / f"{self.APP_NAME}.lnk"

    def _check_startup_folder(self) -> bool:
        """Verifica se atalho existe na pasta de inicializacao."""
        return self._get_shortcut_path().exists()

    def _enable_startup_folder(self, start_minimized: bool = True) -> bool:
        """Cria atalho na pasta de inicializacao."""
        try:
            # Usa PowerShell para criar atalho
            shortcut_path = self._get_shortcut_path()
            target = str(self.executable_path)
            arguments = "--minimized" if start_minimized else ""

            ps_script = f'''
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("{shortcut_path}")
$Shortcut.TargetPath = "{target}"
$Shortcut.Arguments = "{arguments}"
$Shortcut.WorkingDirectory = "{self.executable_path.parent}"
$Shortcut.Description = "{self.APP_DESCRIPTION}"
$Shortcut.Save()
'''
            result = subprocess.run(
                ["powershell", "-Command", ps_script],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                self.logger.info(f"Atalho criado em {shortcut_path}")
                return True
            else:
                self.logger.error(f"Erro ao criar atalho: {result.stderr}")
                return False

        except Exception as e:
            self.logger.error(f"Erro ao criar atalho: {e}")
            return False

    def _disable_startup_folder(self) -> bool:
        """Remove atalho da pasta de inicializacao."""
        try:
            shortcut_path = self._get_shortcut_path()
            if shortcut_path.exists():
                shortcut_path.unlink()
                self.logger.info("Atalho removido da pasta de inicializacao")
            return True
        except Exception as e:
            self.logger.error(f"Erro ao remover atalho: {e}")
            return False

    # ========== Agendador de Tarefas ==========

    def _check_task_scheduler(self) -> bool:
        """Verifica se tarefa existe no agendador."""
        try:
            result = subprocess.run(
                ["schtasks", "/Query", "/TN", self.APP_NAME],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except Exception:
            return False

    def _enable_task_scheduler(self, start_minimized: bool = True, delay_seconds: float = 0) -> bool:
        """Cria tarefa no agendador do Windows."""
        try:
            command = str(self.executable_path)
            if start_minimized:
                command += " --minimized"

            # Monta delay
            delay_str = ""
            if delay_seconds > 0:
                minutes = int(delay_seconds // 60) or 1
                delay_str = f"/DELAY 0000:{minutes:02d}:00"

            # Cria tarefa
            result = subprocess.run([
                "schtasks", "/Create",
                "/TN", self.APP_NAME,
                "/TR", command,
                "/SC", "ONLOGON",
                "/RL", "LIMITED",
                "/F"  # Forca substituicao se existir
            ] + ([delay_str] if delay_str else []),
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                self.logger.info("Tarefa agendada criada com sucesso")
                return True
            else:
                self.logger.error(f"Erro ao criar tarefa: {result.stderr}")
                return False

        except Exception as e:
            self.logger.error(f"Erro ao criar tarefa agendada: {e}")
            return False

    def _disable_task_scheduler(self) -> bool:
        """Remove tarefa do agendador."""
        try:
            result = subprocess.run(
                ["schtasks", "/Delete", "/TN", self.APP_NAME, "/F"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                self.logger.info("Tarefa agendada removida")
            return True
        except Exception as e:
            self.logger.error(f"Erro ao remover tarefa: {e}")
            return False

    # ========== Servico do Windows ==========

    def _check_service(self) -> bool:
        """Verifica se servico existe."""
        try:
            result = subprocess.run(
                ["sc", "query", self.APP_NAME],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except Exception:
            return False

    def _enable_service(self) -> bool:
        """
        Instala como servico do Windows.
        Requer privilégios de administrador.
        """
        if not self.is_admin():
            self.logger.error("Requer privilegios de administrador para instalar servico")
            return False

        try:
            # Usa NSSM ou sc.exe para criar servico
            # Aqui usamos sc.exe como exemplo basico
            command = str(self.executable_path) + " --service"

            result = subprocess.run([
                "sc", "create", self.APP_NAME,
                f'binPath= "{command}"',
                "start=", "auto",
                f'DisplayName= "{self.APP_DESCRIPTION}"'
            ], capture_output=True, text=True)

            if result.returncode == 0:
                self.logger.info("Servico instalado com sucesso")
                return True
            else:
                self.logger.error(f"Erro ao instalar servico: {result.stderr}")
                return False

        except Exception as e:
            self.logger.error(f"Erro ao instalar servico: {e}")
            return False

    def _disable_service(self) -> bool:
        """Remove servico do Windows."""
        if not self.is_admin():
            self.logger.error("Requer privilegios de administrador")
            return False

        try:
            # Para o servico
            subprocess.run(
                ["sc", "stop", self.APP_NAME],
                capture_output=True
            )

            # Remove o servico
            result = subprocess.run(
                ["sc", "delete", self.APP_NAME],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                self.logger.info("Servico removido com sucesso")
            return True

        except Exception as e:
            self.logger.error(f"Erro ao remover servico: {e}")
            return False

    def get_status(self) -> Dict[str, Any]:
        """
        Retorna status de todos os metodos de auto-start.

        Returns:
            Dicionario com status
        """
        return {
            "is_windows": self._is_windows,
            "is_admin": self.is_admin(),
            "executable": str(self.executable_path),
            "methods": {
                "registry": {
                    "enabled": self.is_enabled(AutoStartMethod.REGISTRY),
                    "available": self._winreg is not None
                },
                "startup_folder": {
                    "enabled": self.is_enabled(AutoStartMethod.STARTUP_FOLDER),
                    "path": str(self._get_startup_folder()),
                    "available": True
                },
                "task_scheduler": {
                    "enabled": self.is_enabled(AutoStartMethod.TASK_SCHEDULER),
                    "available": True
                },
                "service": {
                    "enabled": self.is_enabled(AutoStartMethod.SERVICE),
                    "available": self.is_admin()
                }
            }
        }

    def enable_all(self, method: AutoStartMethod = AutoStartMethod.REGISTRY, **kwargs) -> bool:
        """
        Metodo de conveniencia para habilitar auto-start.

        Args:
            method: Metodo preferido
            **kwargs: Argumentos adicionais

        Returns:
            True se habilitou com sucesso
        """
        return self.enable(method, **kwargs)

    def disable_all(self) -> bool:
        """
        Desabilita todos os metodos de auto-start.

        Returns:
            True se todos foram desabilitados
        """
        success = True

        for method in AutoStartMethod:
            if self.is_enabled(method):
                if not self.disable(method):
                    success = False

        return success
