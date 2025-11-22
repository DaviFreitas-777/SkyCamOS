# -*- coding: utf-8 -*-
"""
SkyCamOS Desktop Manager - Logger
Sistema de logging configurado para o Desktop Manager
"""

import os
import sys
import logging
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from datetime import datetime
from pathlib import Path
from typing import Optional


# Diretorio padrao para logs
DEFAULT_LOG_DIR = Path.home() / ".skycamos" / "logs"

# Formato padrao dos logs
DEFAULT_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Niveis de log disponiveis
LOG_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL
}


class ColoredFormatter(logging.Formatter):
    """
    Formatter com cores para output no console.
    Facilita a visualizacao dos diferentes niveis de log.
    """

    # Codigos ANSI para cores
    COLORS = {
        logging.DEBUG: "\033[36m",      # Ciano
        logging.INFO: "\033[32m",       # Verde
        logging.WARNING: "\033[33m",    # Amarelo
        logging.ERROR: "\033[31m",      # Vermelho
        logging.CRITICAL: "\033[41m",   # Fundo vermelho
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        """Formata o registro de log com cores."""
        # Adiciona cor baseada no nivel
        color = self.COLORS.get(record.levelno, self.RESET)

        # Formata a mensagem original
        message = super().format(record)

        # Retorna com cor (apenas no console)
        return f"{color}{message}{self.RESET}"


def setup_logging(
    log_dir: Optional[Path] = None,
    log_level: str = "INFO",
    console_output: bool = True,
    file_output: bool = True,
    max_file_size_mb: int = 10,
    backup_count: int = 5
) -> None:
    """
    Configura o sistema de logging para toda a aplicacao.

    Args:
        log_dir: Diretorio para salvar os arquivos de log
        log_level: Nivel de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        console_output: Se deve exibir logs no console
        file_output: Se deve salvar logs em arquivo
        max_file_size_mb: Tamanho maximo de cada arquivo de log em MB
        backup_count: Numero de arquivos de backup a manter
    """
    # Define diretorio de logs
    log_path = log_dir or DEFAULT_LOG_DIR
    log_path.mkdir(parents=True, exist_ok=True)

    # Obtem nivel de log
    level = LOG_LEVELS.get(log_level.upper(), logging.INFO)

    # Configura o logger raiz
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Remove handlers existentes
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Handler para console
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)

        # Usa formatter colorido se o terminal suportar
        if sys.stdout.isatty():
            console_handler.setFormatter(
                ColoredFormatter(DEFAULT_FORMAT, DATE_FORMAT)
            )
        else:
            console_handler.setFormatter(
                logging.Formatter(DEFAULT_FORMAT, DATE_FORMAT)
            )

        root_logger.addHandler(console_handler)

    # Handler para arquivo
    if file_output:
        # Arquivo principal com rotacao por tamanho
        log_file = log_path / "skycamos.log"
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_file_size_mb * 1024 * 1024,
            backupCount=backup_count,
            encoding="utf-8"
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(
            logging.Formatter(DEFAULT_FORMAT, DATE_FORMAT)
        )
        root_logger.addHandler(file_handler)

        # Arquivo separado para erros
        error_file = log_path / "skycamos_errors.log"
        error_handler = RotatingFileHandler(
            error_file,
            maxBytes=max_file_size_mb * 1024 * 1024,
            backupCount=backup_count,
            encoding="utf-8"
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(
            logging.Formatter(DEFAULT_FORMAT, DATE_FORMAT)
        )
        root_logger.addHandler(error_handler)

    # Log inicial
    root_logger.info("=" * 60)
    root_logger.info("SkyCamOS Desktop Manager - Logging inicializado")
    root_logger.info(f"Nivel de log: {log_level.upper()}")
    root_logger.info(f"Diretorio de logs: {log_path}")
    root_logger.info("=" * 60)


def get_logger(name: str) -> logging.Logger:
    """
    Obtem um logger com o nome especificado.

    Args:
        name: Nome do modulo/componente

    Returns:
        Logger configurado
    """
    return logging.getLogger(f"skycamos.{name}")


class LoggerMixin:
    """
    Mixin que adiciona logging a uma classe.
    Uso: class MinhaClasse(LoggerMixin): ...
    """

    @property
    def logger(self) -> logging.Logger:
        """Retorna o logger para esta classe."""
        if not hasattr(self, "_logger"):
            self._logger = get_logger(self.__class__.__name__)
        return self._logger


def log_exception(logger: logging.Logger, exc: Exception, message: str = "") -> None:
    """
    Loga uma excecao com detalhes completos.

    Args:
        logger: Logger a utilizar
        exc: Excecao a logar
        message: Mensagem adicional
    """
    if message:
        logger.error(f"{message}: {type(exc).__name__}: {exc}")
    else:
        logger.error(f"{type(exc).__name__}: {exc}")
    logger.debug("Stack trace:", exc_info=True)


def create_session_log(log_dir: Optional[Path] = None) -> Path:
    """
    Cria um arquivo de log para a sessao atual.
    Util para debugging de sessoes especificas.

    Args:
        log_dir: Diretorio para o log

    Returns:
        Caminho para o arquivo de log da sessao
    """
    log_path = log_dir or DEFAULT_LOG_DIR
    log_path.mkdir(parents=True, exist_ok=True)

    # Nome do arquivo com timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_file = log_path / f"session_{timestamp}.log"

    # Cria handler para a sessao
    session_handler = logging.FileHandler(session_file, encoding="utf-8")
    session_handler.setLevel(logging.DEBUG)
    session_handler.setFormatter(
        logging.Formatter(DEFAULT_FORMAT, DATE_FORMAT)
    )

    # Adiciona ao logger raiz
    logging.getLogger().addHandler(session_handler)

    return session_file
