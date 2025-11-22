#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SkyCamOS - Script de Backup do Banco de Dados
==============================================

Este script realiza backup do banco de dados SQLite do SkyCamOS,
com suporte a compressao, rotacao e restauracao.

Uso:
    python backup_db.py                    # Cria backup
    python backup_db.py --restore arquivo  # Restaura backup
    python backup_db.py --list             # Lista backups
    python backup_db.py --cleanup          # Remove backups antigos

Opcoes:
    --compress      Comprime o backup com gzip
    --max-backups   Numero maximo de backups a manter (padrao: 10)
    --output-dir    Diretorio para salvar backups
    --verbose       Mostra mensagens detalhadas
"""

import os
import sys
import sqlite3
import argparse
import shutil
import gzip
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List, Tuple


# Configuracoes
DATABASE_DIR = Path(__file__).parent.parent
DATABASE_FILE = DATABASE_DIR / "skycamos.db"
DEFAULT_BACKUP_DIR = DATABASE_DIR / "backups"
MAX_BACKUPS = 10
BACKUP_PREFIX = "skycamos_backup_"


class DatabaseBackup:
    """Classe para gerenciar backups do banco de dados."""

    def __init__(
        self,
        db_path: Path,
        backup_dir: Path,
        verbose: bool = False,
        max_backups: int = MAX_BACKUPS
    ):
        self.db_path = db_path
        self.backup_dir = backup_dir
        self.verbose = verbose
        self.max_backups = max_backups

    def log(self, message: str, level: str = "info") -> None:
        """Registra mensagem no console."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        prefix = {
            "info": "[INFO]",
            "warning": "[WARN]",
            "error": "[ERRO]",
            "success": "[OK]",
            "debug": "[DEBUG]"
        }.get(level, "[INFO]")

        if level == "debug" and not self.verbose:
            return

        print(f"{timestamp} {prefix} {message}")

    def ensure_backup_dir(self) -> None:
        """Cria diretorio de backup se nao existir."""
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.log(f"Diretorio de backup: {self.backup_dir}", "debug")

    def generate_backup_name(self, compress: bool = False) -> str:
        """Gera nome unico para o arquivo de backup."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        extension = ".db.gz" if compress else ".db"
        return f"{BACKUP_PREFIX}{timestamp}{extension}"

    def create_backup(self, compress: bool = False) -> Optional[Path]:
        """Cria backup do banco de dados."""
        self.log("=" * 60)
        self.log("SkyCamOS - Backup do Banco de Dados")
        self.log("=" * 60)

        # Verificar se banco existe
        if not self.db_path.exists():
            self.log(f"Banco de dados nao encontrado: {self.db_path}", "error")
            return None

        # Criar diretorio de backup
        self.ensure_backup_dir()

        # Gerar nome do backup
        backup_name = self.generate_backup_name(compress)
        backup_path = self.backup_dir / backup_name

        self.log(f"Origem: {self.db_path}")
        self.log(f"Destino: {backup_path}")

        try:
            # Conectar ao banco para garantir integridade
            conn = sqlite3.connect(str(self.db_path))

            # Verificar integridade antes do backup
            cursor = conn.execute("PRAGMA integrity_check")
            result = cursor.fetchone()
            if result[0] != "ok":
                self.log(f"Banco com problemas de integridade: {result[0]}", "warning")

            # Usar backup API do SQLite para backup seguro
            self.log("Criando backup...")

            if compress:
                # Backup com compressao
                temp_backup = self.backup_dir / f"temp_{backup_name.replace('.gz', '')}"

                # Criar backup temporario
                backup_conn = sqlite3.connect(str(temp_backup))
                conn.backup(backup_conn)
                backup_conn.close()

                # Comprimir
                self.log("Comprimindo backup...", "debug")
                with open(temp_backup, "rb") as f_in:
                    with gzip.open(backup_path, "wb", compresslevel=9) as f_out:
                        shutil.copyfileobj(f_in, f_out)

                # Remover temporario
                temp_backup.unlink()

            else:
                # Backup direto
                backup_conn = sqlite3.connect(str(backup_path))
                conn.backup(backup_conn)
                backup_conn.close()

            conn.close()

            # Obter tamanho do backup
            backup_size = backup_path.stat().st_size
            original_size = self.db_path.stat().st_size

            self.log(f"Tamanho original: {self._format_size(original_size)}")
            self.log(f"Tamanho do backup: {self._format_size(backup_size)}")

            if compress:
                ratio = (1 - backup_size / original_size) * 100
                self.log(f"Taxa de compressao: {ratio:.1f}%")

            self.log(f"Backup criado com sucesso: {backup_path.name}", "success")
            self.log("=" * 60)

            return backup_path

        except sqlite3.Error as e:
            self.log(f"Erro SQLite durante backup: {e}", "error")
            return None
        except IOError as e:
            self.log(f"Erro de I/O durante backup: {e}", "error")
            return None

    def restore_backup(self, backup_path: Path) -> bool:
        """Restaura backup do banco de dados."""
        self.log("=" * 60)
        self.log("SkyCamOS - Restauracao de Backup")
        self.log("=" * 60)

        # Verificar se backup existe
        if not backup_path.exists():
            self.log(f"Arquivo de backup nao encontrado: {backup_path}", "error")
            return False

        self.log(f"Restaurando de: {backup_path}")
        self.log(f"Destino: {self.db_path}")

        try:
            # Criar backup do banco atual antes de restaurar
            if self.db_path.exists():
                safety_backup = self.db_path.with_suffix(".db.before_restore")
                self.log(f"Criando backup de seguranca: {safety_backup.name}", "warning")
                shutil.copy2(self.db_path, safety_backup)

            # Verificar se eh comprimido
            is_compressed = backup_path.suffix == ".gz"

            if is_compressed:
                self.log("Descomprimindo backup...", "debug")
                with gzip.open(backup_path, "rb") as f_in:
                    with open(self.db_path, "wb") as f_out:
                        shutil.copyfileobj(f_in, f_out)
            else:
                shutil.copy2(backup_path, self.db_path)

            # Verificar integridade apos restauracao
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.execute("PRAGMA integrity_check")
            result = cursor.fetchone()
            conn.close()

            if result[0] != "ok":
                self.log(f"Banco restaurado com problemas: {result[0]}", "warning")
            else:
                self.log("Integridade verificada: OK", "success")

            self.log("Restauracao concluida com sucesso!", "success")
            self.log("=" * 60)

            return True

        except Exception as e:
            self.log(f"Erro durante restauracao: {e}", "error")
            return False

    def list_backups(self) -> List[Tuple[Path, datetime, int]]:
        """Lista todos os backups disponiveis."""
        backups = []

        if not self.backup_dir.exists():
            return backups

        for file in self.backup_dir.glob(f"{BACKUP_PREFIX}*"):
            if file.is_file():
                try:
                    # Extrair data do nome do arquivo
                    date_str = file.stem.replace(BACKUP_PREFIX, "").replace(".db", "")
                    backup_date = datetime.strptime(date_str, "%Y%m%d_%H%M%S")
                    file_size = file.stat().st_size
                    backups.append((file, backup_date, file_size))
                except ValueError:
                    # Arquivo com nome invalido, pular
                    continue

        # Ordenar por data (mais recente primeiro)
        backups.sort(key=lambda x: x[1], reverse=True)
        return backups

    def cleanup_old_backups(self) -> int:
        """Remove backups antigos, mantendo apenas os mais recentes."""
        self.log("=" * 60)
        self.log("SkyCamOS - Limpeza de Backups Antigos")
        self.log("=" * 60)

        backups = self.list_backups()
        removed = 0

        if len(backups) <= self.max_backups:
            self.log(f"Backups atuais: {len(backups)} (limite: {self.max_backups})")
            self.log("Nenhum backup a remover", "success")
            return 0

        # Remover backups excedentes
        backups_to_remove = backups[self.max_backups:]
        self.log(f"Removendo {len(backups_to_remove)} backup(s) antigo(s)...")

        for backup_path, backup_date, _ in backups_to_remove:
            try:
                backup_path.unlink()
                self.log(f"Removido: {backup_path.name}", "debug")
                removed += 1
            except IOError as e:
                self.log(f"Erro ao remover {backup_path.name}: {e}", "error")

        self.log(f"{removed} backup(s) removido(s)", "success")
        self.log("=" * 60)

        return removed

    def show_backups(self) -> None:
        """Exibe lista de backups formatada."""
        backups = self.list_backups()

        print("\n" + "=" * 70)
        print("BACKUPS DISPONIVEIS")
        print("=" * 70)

        if not backups:
            print("Nenhum backup encontrado.")
            print(f"Diretorio: {self.backup_dir}")
            print("=" * 70)
            return

        print(f"{'#':<3} {'DATA/HORA':<20} {'TAMANHO':<12} {'ARQUIVO'}")
        print("-" * 70)

        for i, (backup_path, backup_date, file_size) in enumerate(backups, 1):
            date_str = backup_date.strftime("%Y-%m-%d %H:%M:%S")
            size_str = self._format_size(file_size)
            compressed = "[GZ]" if backup_path.suffix == ".gz" else ""

            print(f"{i:<3} {date_str:<20} {size_str:<12} {backup_path.name} {compressed}")

        print("-" * 70)
        print(f"Total: {len(backups)} backup(s)")
        print(f"Diretorio: {self.backup_dir}")
        print("=" * 70)

    def _format_size(self, size_bytes: int) -> str:
        """Formata tamanho em bytes para leitura humana."""
        for unit in ["B", "KB", "MB", "GB"]:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} TB"


def main():
    """Funcao principal."""
    parser = argparse.ArgumentParser(
        description="SkyCamOS - Gerenciador de Backups",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
    python backup_db.py                      # Cria backup simples
    python backup_db.py --compress           # Cria backup comprimido
    python backup_db.py --list               # Lista backups existentes
    python backup_db.py --cleanup            # Remove backups antigos
    python backup_db.py --restore backup.db  # Restaura um backup

Arquivos:
    Banco: database/skycamos.db
    Backups: database/backups/
        """
    )

    parser.add_argument(
        "--compress", "-c",
        action="store_true",
        help="Comprime o backup com gzip"
    )

    parser.add_argument(
        "--restore", "-r",
        type=str,
        metavar="ARQUIVO",
        help="Restaura um backup especifico"
    )

    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="Lista todos os backups disponiveis"
    )

    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Remove backups antigos (mantem os mais recentes)"
    )

    parser.add_argument(
        "--max-backups",
        type=int,
        default=MAX_BACKUPS,
        metavar="N",
        help=f"Numero maximo de backups a manter (padrao: {MAX_BACKUPS})"
    )

    parser.add_argument(
        "--output-dir", "-o",
        type=str,
        metavar="DIR",
        help="Diretorio para salvar backups"
    )

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Modo detalhado com mais mensagens"
    )

    args = parser.parse_args()

    # Definir diretorio de backup
    backup_dir = Path(args.output_dir) if args.output_dir else DEFAULT_BACKUP_DIR

    # Criar gerenciador de backup
    backup_manager = DatabaseBackup(
        db_path=DATABASE_FILE,
        backup_dir=backup_dir,
        verbose=args.verbose,
        max_backups=args.max_backups
    )

    # Executar acao solicitada
    if args.list:
        backup_manager.show_backups()

    elif args.restore:
        restore_path = Path(args.restore)
        # Se caminho relativo, procurar no diretorio de backups
        if not restore_path.is_absolute():
            restore_path = backup_dir / restore_path

        if backup_manager.restore_backup(restore_path):
            sys.exit(0)
        else:
            sys.exit(1)

    elif args.cleanup:
        backup_manager.cleanup_old_backups()

    else:
        # Criar backup
        backup_path = backup_manager.create_backup(compress=args.compress)

        if backup_path:
            # Executar limpeza automatica apos criar backup
            backup_manager.cleanup_old_backups()
            sys.exit(0)
        else:
            sys.exit(1)


if __name__ == "__main__":
    main()
