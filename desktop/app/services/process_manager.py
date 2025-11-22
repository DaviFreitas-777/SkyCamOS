# -*- coding: utf-8 -*-
"""
SkyCamOS Desktop Manager - Process Manager
Gerenciador de processos do backend FastAPI
"""

import os
import sys
import asyncio
import subprocess
import signal
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional, Dict, Any, Callable, List
import threading

try:
    import psutil
except ImportError:
    psutil = None

from ..utils.logger import get_logger, LoggerMixin
from ..utils.network import is_port_available, find_available_port

logger = get_logger("process_manager")


class ProcessState(Enum):
    """Estados possiveis de um processo."""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    CRASHED = "crashed"
    RESTARTING = "restarting"


@dataclass
class ProcessInfo:
    """Informacoes sobre um processo gerenciado."""
    name: str
    state: ProcessState = ProcessState.STOPPED
    pid: Optional[int] = None
    port: Optional[int] = None
    start_time: Optional[datetime] = None
    restart_count: int = 0
    last_error: str = ""
    cpu_percent: float = 0.0
    memory_mb: float = 0.0
    command: str = ""
    working_dir: str = ""
    environment: Dict[str, str] = field(default_factory=dict)


class ProcessManager(LoggerMixin):
    """
    Gerenciador de processos do backend.
    Responsavel por iniciar, parar e monitorar o servidor FastAPI.
    """

    def __init__(
        self,
        backend_dir: Optional[Path] = None,
        host: str = "127.0.0.1",
        port: int = 8000,
        auto_restart: bool = True,
        restart_delay: float = 5.0,
        max_restarts: int = 5,
        health_check_interval: float = 30.0
    ):
        """
        Inicializa o gerenciador de processos.

        Args:
            backend_dir: Diretorio do backend FastAPI
            host: Host para o servidor
            port: Porta para o servidor
            auto_restart: Se deve reiniciar automaticamente em caso de falha
            restart_delay: Delay entre reinicializacoes
            max_restarts: Numero maximo de reinicializacoes consecutivas
            health_check_interval: Intervalo de verificacao de saude
        """
        self.backend_dir = backend_dir or Path(__file__).parent.parent.parent.parent / "backend"
        self.host = host
        self.port = port
        self.auto_restart = auto_restart
        self.restart_delay = restart_delay
        self.max_restarts = max_restarts
        self.health_check_interval = health_check_interval

        self._process: Optional[subprocess.Popen] = None
        self._info = ProcessInfo(name="skycamos-backend")
        self._running = False
        self._monitor_task: Optional[asyncio.Task] = None
        self._restart_count = 0
        self._callbacks: List[Callable[[ProcessState], None]] = []

    @property
    def info(self) -> ProcessInfo:
        """Retorna informacoes do processo."""
        self._update_process_info()
        return self._info

    @property
    def is_running(self) -> bool:
        """Verifica se o processo esta rodando."""
        return self._info.state == ProcessState.RUNNING

    def add_state_callback(self, callback: Callable[[ProcessState], None]) -> None:
        """Adiciona callback para mudancas de estado."""
        self._callbacks.append(callback)

    def _notify_state_change(self, state: ProcessState) -> None:
        """Notifica callbacks sobre mudanca de estado."""
        self._info.state = state
        for callback in self._callbacks:
            try:
                callback(state)
            except Exception as e:
                self.logger.error(f"Erro em callback de estado: {e}")

    def _update_process_info(self) -> None:
        """Atualiza informacoes do processo."""
        if self._process and self._process.poll() is None:
            self._info.pid = self._process.pid

            if psutil:
                try:
                    proc = psutil.Process(self._process.pid)
                    self._info.cpu_percent = proc.cpu_percent(interval=0.1)
                    self._info.memory_mb = proc.memory_info().rss / (1024 * 1024)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
        else:
            self._info.pid = None
            self._info.cpu_percent = 0.0
            self._info.memory_mb = 0.0

    def _find_python(self) -> str:
        """
        Encontra o executavel Python.

        Returns:
            Caminho para o Python
        """
        # Tenta usar o mesmo Python que esta executando
        python = sys.executable

        # Verifica se existe venv no backend
        venv_python = self.backend_dir / "venv" / "Scripts" / "python.exe"
        if venv_python.exists():
            python = str(venv_python)

        return python

    def _build_command(self) -> List[str]:
        """
        Constroi o comando para iniciar o backend.

        Returns:
            Lista de argumentos do comando
        """
        python = self._find_python()

        # Comando padrao: uvicorn
        command = [
            python, "-m", "uvicorn",
            "app.main:app",
            "--host", self.host,
            "--port", str(self.port),
            "--reload"  # Para desenvolvimento
        ]

        return command

    async def start(self) -> bool:
        """
        Inicia o servidor backend.

        Returns:
            True se iniciou com sucesso
        """
        if self.is_running:
            self.logger.warning("Backend ja esta em execucao")
            return True

        self.logger.info(f"Iniciando backend em {self.host}:{self.port}...")
        self._notify_state_change(ProcessState.STARTING)

        try:
            # Verifica se a porta esta disponivel
            if not is_port_available(self.port, self.host):
                # Tenta encontrar outra porta
                new_port = find_available_port(self.port, self.port + 100)
                if new_port:
                    self.logger.warning(f"Porta {self.port} em uso, usando {new_port}")
                    self.port = new_port
                else:
                    self._info.last_error = f"Porta {self.port} em uso e sem alternativas"
                    self._notify_state_change(ProcessState.CRASHED)
                    return False

            # Verifica se o diretorio do backend existe
            if not self.backend_dir.exists():
                self._info.last_error = f"Diretorio do backend nao encontrado: {self.backend_dir}"
                self._notify_state_change(ProcessState.CRASHED)
                return False

            # Constroi e executa comando
            command = self._build_command()
            self._info.command = " ".join(command)
            self._info.working_dir = str(self.backend_dir)

            # Ambiente
            env = os.environ.copy()
            env.update(self._info.environment)
            env["PYTHONUNBUFFERED"] = "1"

            # Inicia processo
            self._process = subprocess.Popen(
                command,
                cwd=self.backend_dir,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            )

            self._info.pid = self._process.pid
            self._info.port = self.port
            self._info.start_time = datetime.now()

            # Aguarda um pouco para verificar se iniciou
            await asyncio.sleep(2)

            if self._process.poll() is None:
                self._notify_state_change(ProcessState.RUNNING)
                self._restart_count = 0
                self.logger.info(f"Backend iniciado com PID {self._process.pid}")

                # Inicia monitoramento
                await self._start_monitoring()
                return True
            else:
                # Processo terminou imediatamente
                stdout, stderr = self._process.communicate()
                self._info.last_error = stderr.decode('utf-8', errors='ignore')[-500:]
                self._notify_state_change(ProcessState.CRASHED)
                self.logger.error(f"Backend falhou ao iniciar: {self._info.last_error}")
                return False

        except FileNotFoundError as e:
            self._info.last_error = f"Python ou uvicorn nao encontrado: {e}"
            self._notify_state_change(ProcessState.CRASHED)
            self.logger.error(self._info.last_error)
            return False

        except Exception as e:
            self._info.last_error = str(e)
            self._notify_state_change(ProcessState.CRASHED)
            self.logger.error(f"Erro ao iniciar backend: {e}")
            return False

    async def stop(self, timeout: float = 10.0) -> bool:
        """
        Para o servidor backend.

        Args:
            timeout: Timeout para parada graceful

        Returns:
            True se parou com sucesso
        """
        if not self._process:
            self.logger.warning("Backend nao esta em execucao")
            return True

        self.logger.info("Parando backend...")
        self._notify_state_change(ProcessState.STOPPING)

        # Para monitoramento
        await self._stop_monitoring()

        try:
            # Tenta parada graceful
            if sys.platform == "win32":
                self._process.terminate()
            else:
                self._process.send_signal(signal.SIGTERM)

            # Aguarda termino
            try:
                self._process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                self.logger.warning("Timeout na parada graceful, forcando...")
                self._process.kill()
                self._process.wait(timeout=5)

            self._notify_state_change(ProcessState.STOPPED)
            self.logger.info("Backend parado com sucesso")
            return True

        except Exception as e:
            self.logger.error(f"Erro ao parar backend: {e}")
            self._notify_state_change(ProcessState.CRASHED)
            return False

        finally:
            self._process = None
            self._info.pid = None

    async def restart(self) -> bool:
        """
        Reinicia o servidor backend.

        Returns:
            True se reiniciou com sucesso
        """
        self.logger.info("Reiniciando backend...")
        self._notify_state_change(ProcessState.RESTARTING)

        await self.stop()
        await asyncio.sleep(1)
        return await self.start()

    async def _start_monitoring(self) -> None:
        """Inicia monitoramento do processo."""
        if self._monitor_task:
            return

        self._running = True

        async def monitor_loop():
            while self._running:
                try:
                    await self._check_health()
                except Exception as e:
                    self.logger.error(f"Erro no monitoramento: {e}")

                await asyncio.sleep(self.health_check_interval)

        self._monitor_task = asyncio.create_task(monitor_loop())
        self.logger.debug("Monitoramento do backend iniciado")

    async def _stop_monitoring(self) -> None:
        """Para monitoramento do processo."""
        self._running = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
            self._monitor_task = None
        self.logger.debug("Monitoramento do backend parado")

    async def _check_health(self) -> None:
        """Verifica saude do processo."""
        if not self._process:
            return

        # Verifica se processo ainda esta rodando
        if self._process.poll() is not None:
            # Processo terminou
            exit_code = self._process.returncode
            self.logger.warning(f"Backend terminou com codigo {exit_code}")

            # Captura saida de erro
            try:
                _, stderr = self._process.communicate(timeout=1)
                self._info.last_error = stderr.decode('utf-8', errors='ignore')[-500:]
            except Exception:
                pass

            self._notify_state_change(ProcessState.CRASHED)
            self._process = None

            # Tenta reiniciar se configurado
            if self.auto_restart and self._restart_count < self.max_restarts:
                self._restart_count += 1
                self._info.restart_count += 1
                self.logger.info(f"Tentando reiniciar ({self._restart_count}/{self.max_restarts})...")

                await asyncio.sleep(self.restart_delay)
                await self.start()
            else:
                if self._restart_count >= self.max_restarts:
                    self.logger.error("Numero maximo de reinicializacoes atingido")
                    self._restart_count = 0

        else:
            # Processo rodando - atualiza metricas
            self._update_process_info()

    async def health_check(self) -> Dict[str, Any]:
        """
        Verifica saude do backend via HTTP.

        Returns:
            Dicionario com status de saude
        """
        import aiohttp

        try:
            async with aiohttp.ClientSession() as session:
                url = f"http://{self.host}:{self.port}/health"
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                    if response.status == 200:
                        return {
                            "healthy": True,
                            "status_code": response.status,
                            "data": await response.json()
                        }
                    else:
                        return {
                            "healthy": False,
                            "status_code": response.status,
                            "error": "Status code inesperado"
                        }

        except asyncio.TimeoutError:
            return {"healthy": False, "error": "Timeout"}
        except aiohttp.ClientError as e:
            return {"healthy": False, "error": str(e)}
        except Exception as e:
            return {"healthy": False, "error": str(e)}

    def get_logs(self, lines: int = 100) -> str:
        """
        Obtem logs recentes do processo.

        Args:
            lines: Numero de linhas a retornar

        Returns:
            String com logs
        """
        if not self._process:
            return "Processo nao esta em execucao"

        try:
            # Tenta ler stdout/stderr sem bloquear
            output = []

            if self._process.stdout:
                try:
                    import select
                    if sys.platform != "win32":
                        ready, _, _ = select.select([self._process.stdout], [], [], 0)
                        if ready:
                            output.append(self._process.stdout.read().decode('utf-8', errors='ignore'))
                except Exception:
                    pass

            return "\n".join(output[-lines:]) if output else "Sem logs disponiveis"

        except Exception as e:
            return f"Erro ao obter logs: {e}"

    def get_status_dict(self) -> Dict[str, Any]:
        """
        Retorna status como dicionario.

        Returns:
            Dicionario com status
        """
        self._update_process_info()
        return {
            "name": self._info.name,
            "state": self._info.state.value,
            "pid": self._info.pid,
            "port": self._info.port,
            "start_time": self._info.start_time.isoformat() if self._info.start_time else None,
            "restart_count": self._info.restart_count,
            "cpu_percent": round(self._info.cpu_percent, 1),
            "memory_mb": round(self._info.memory_mb, 1),
            "last_error": self._info.last_error
        }


class MultiProcessManager(LoggerMixin):
    """
    Gerenciador de multiplos processos.
    Permite gerenciar varios servicos simultaneamente.
    """

    def __init__(self):
        """Inicializa o gerenciador multi-processo."""
        self._managers: Dict[str, ProcessManager] = {}

    def add_process(self, name: str, manager: ProcessManager) -> None:
        """
        Adiciona um processo ao gerenciador.

        Args:
            name: Nome unico do processo
            manager: Instancia do ProcessManager
        """
        self._managers[name] = manager
        self.logger.info(f"Processo '{name}' adicionado ao gerenciador")

    def remove_process(self, name: str) -> bool:
        """
        Remove um processo do gerenciador.

        Args:
            name: Nome do processo

        Returns:
            True se removeu com sucesso
        """
        if name in self._managers:
            del self._managers[name]
            self.logger.info(f"Processo '{name}' removido do gerenciador")
            return True
        return False

    def get_process(self, name: str) -> Optional[ProcessManager]:
        """
        Obtem um gerenciador de processo pelo nome.

        Args:
            name: Nome do processo

        Returns:
            ProcessManager ou None
        """
        return self._managers.get(name)

    async def start_all(self) -> Dict[str, bool]:
        """
        Inicia todos os processos.

        Returns:
            Dicionario {nome: sucesso}
        """
        results = {}
        for name, manager in self._managers.items():
            results[name] = await manager.start()
        return results

    async def stop_all(self) -> Dict[str, bool]:
        """
        Para todos os processos.

        Returns:
            Dicionario {nome: sucesso}
        """
        results = {}
        for name, manager in self._managers.items():
            results[name] = await manager.stop()
        return results

    def get_all_status(self) -> Dict[str, Dict[str, Any]]:
        """
        Obtem status de todos os processos.

        Returns:
            Dicionario com status de todos os processos
        """
        return {
            name: manager.get_status_dict()
            for name, manager in self._managers.items()
        }
