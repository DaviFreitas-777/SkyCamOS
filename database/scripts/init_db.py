#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SkyCamOS - Script de Inicializacao do Banco de Dados
=====================================================

Este script inicializa o banco de dados SQLite do SkyCamOS,
executando todas as migrations em ordem.

Uso:
    python init_db.py [--reset] [--verbose]

Opcoes:
    --reset     Apaga o banco existente e cria um novo
    --verbose   Mostra mensagens detalhadas
    --dry-run   Simula execucao sem modificar o banco
"""

import os
import sys
import sqlite3
import argparse
import hashlib
import secrets
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Tuple


# Configuracoes
DATABASE_DIR = Path(__file__).parent.parent
MIGRATIONS_DIR = DATABASE_DIR / "migrations"
DATABASE_FILE = DATABASE_DIR / "skycamos.db"


class DatabaseInitializer:
    """Classe para inicializar e gerenciar o banco de dados."""

    def __init__(self, db_path: Path, verbose: bool = False):
        self.db_path = db_path
        self.verbose = verbose
        self.conn: Optional[sqlite3.Connection] = None

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

    def connect(self) -> sqlite3.Connection:
        """Conecta ao banco de dados."""
        self.log(f"Conectando ao banco: {self.db_path}", "debug")
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        # Habilitar foreign keys
        self.conn.execute("PRAGMA foreign_keys = ON")
        return self.conn

    def close(self) -> None:
        """Fecha conexao com o banco."""
        if self.conn:
            self.conn.close()
            self.conn = None
            self.log("Conexao fechada", "debug")

    def get_current_version(self) -> Optional[str]:
        """Retorna a versao atual do banco de dados."""
        try:
            cursor = self.conn.execute(
                "SELECT valor FROM configuracoes WHERE chave = 'db_version'"
            )
            row = cursor.fetchone()
            return row["valor"] if row else None
        except sqlite3.OperationalError:
            return None

    def get_migrations(self) -> List[Tuple[str, Path]]:
        """Lista todas as migrations disponiveis."""
        migrations = []
        if MIGRATIONS_DIR.exists():
            for file in sorted(MIGRATIONS_DIR.glob("*.sql")):
                # Extrair numero da migration (ex: 001 de 001_initial_schema.sql)
                version = file.stem.split("_")[0]
                migrations.append((version, file))
        return migrations

    def execute_migration(self, migration_path: Path, dry_run: bool = False) -> bool:
        """Executa uma migration SQL."""
        self.log(f"Executando migration: {migration_path.name}")

        try:
            with open(migration_path, "r", encoding="utf-8") as f:
                sql_content = f.read()

            if dry_run:
                self.log(f"[DRY-RUN] Migration seria executada: {migration_path.name}", "debug")
                return True

            # Executar SQL
            self.conn.executescript(sql_content)
            self.conn.commit()
            self.log(f"Migration executada com sucesso: {migration_path.name}", "success")
            return True

        except sqlite3.Error as e:
            self.log(f"Erro ao executar migration {migration_path.name}: {e}", "error")
            self.conn.rollback()
            return False
        except IOError as e:
            self.log(f"Erro ao ler arquivo {migration_path.name}: {e}", "error")
            return False

    def create_admin_password_hash(self, password: str) -> str:
        """Cria hash seguro para senha do administrador."""
        salt = secrets.token_hex(16)
        iterations = 600000
        hash_bytes = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            iterations
        )
        hash_hex = hash_bytes.hex()
        return f"pbkdf2:sha256:{iterations}${salt}${hash_hex}"

    def update_admin_password(self, password: str) -> bool:
        """Atualiza senha do administrador padrao."""
        try:
            password_hash = self.create_admin_password_hash(password)
            self.conn.execute(
                "UPDATE usuarios SET senha_hash = ? WHERE email = 'admin@skycamos.local'",
                (password_hash,)
            )
            self.conn.commit()
            self.log("Senha do administrador atualizada", "success")
            return True
        except sqlite3.Error as e:
            self.log(f"Erro ao atualizar senha: {e}", "error")
            return False

    def initialize(self, reset: bool = False, dry_run: bool = False) -> bool:
        """Inicializa o banco de dados."""
        self.log("=" * 60)
        self.log("SkyCamOS - Inicializacao do Banco de Dados")
        self.log("=" * 60)

        # Verificar se deve resetar
        if reset and self.db_path.exists():
            if dry_run:
                self.log("[DRY-RUN] Banco seria removido", "warning")
            else:
                self.log("Removendo banco existente...", "warning")
                self.db_path.unlink()

        # Conectar ao banco
        self.connect()

        # Verificar versao atual
        current_version = self.get_current_version()
        if current_version:
            self.log(f"Versao atual do banco: {current_version}")
        else:
            self.log("Banco de dados vazio ou nao inicializado")

        # Obter migrations
        migrations = self.get_migrations()
        if not migrations:
            self.log("Nenhuma migration encontrada!", "error")
            return False

        self.log(f"Migrations encontradas: {len(migrations)}")

        # Executar migrations pendentes
        executed = 0
        for version, migration_path in migrations:
            # Pular migrations ja executadas
            if current_version and version <= current_version:
                self.log(f"Migration {version} ja executada, pulando...", "debug")
                continue

            if not self.execute_migration(migration_path, dry_run):
                self.log("Inicializacao interrompida devido a erro", "error")
                return False

            executed += 1

        # Resultado
        if executed == 0:
            self.log("Banco de dados ja esta atualizado", "success")
        else:
            self.log(f"{executed} migration(s) executada(s) com sucesso", "success")

        # Verificar versao final
        if not dry_run:
            final_version = self.get_current_version()
            self.log(f"Versao final do banco: {final_version}")

        self.log("=" * 60)
        self.log("Inicializacao concluida!")
        self.log("=" * 60)

        return True

    def show_stats(self) -> None:
        """Mostra estatisticas do banco de dados."""
        if not self.conn:
            self.connect()

        self.log("\n--- Estatisticas do Banco ---")

        tables = [
            ("usuarios", "Usuarios"),
            ("cameras", "Cameras"),
            ("eventos_movimento", "Eventos de Movimento"),
            ("gravacoes", "Gravacoes"),
            ("configuracoes", "Configuracoes"),
            ("sessoes", "Sessoes"),
            ("logs_sistema", "Logs do Sistema")
        ]

        for table, label in tables:
            try:
                cursor = self.conn.execute(f"SELECT COUNT(*) as count FROM {table}")
                row = cursor.fetchone()
                count = row["count"] if row else 0
                self.log(f"  {label}: {count} registro(s)")
            except sqlite3.OperationalError:
                self.log(f"  {label}: Tabela nao existe", "warning")

    def verify_integrity(self) -> bool:
        """Verifica integridade do banco de dados."""
        if not self.conn:
            self.connect()

        self.log("\n--- Verificando Integridade ---")

        try:
            cursor = self.conn.execute("PRAGMA integrity_check")
            result = cursor.fetchone()

            if result and result[0] == "ok":
                self.log("Integridade do banco: OK", "success")
                return True
            else:
                self.log(f"Problema de integridade: {result[0] if result else 'desconhecido'}", "error")
                return False

        except sqlite3.Error as e:
            self.log(f"Erro na verificacao: {e}", "error")
            return False


def main():
    """Funcao principal."""
    parser = argparse.ArgumentParser(
        description="SkyCamOS - Inicializador do Banco de Dados",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
    python init_db.py                  # Inicializa ou atualiza o banco
    python init_db.py --reset          # Recria o banco do zero
    python init_db.py --verbose        # Modo detalhado
    python init_db.py --dry-run        # Simula sem modificar

Arquivos:
    Banco: database/skycamos.db
    Migrations: database/migrations/
        """
    )

    parser.add_argument(
        "--reset",
        action="store_true",
        help="Apaga o banco existente e cria um novo"
    )

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Modo detalhado com mais mensagens"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simula a execucao sem modificar o banco"
    )

    parser.add_argument(
        "--stats",
        action="store_true",
        help="Mostra estatisticas do banco apos inicializacao"
    )

    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verifica integridade do banco"
    )

    parser.add_argument(
        "--set-admin-password",
        type=str,
        metavar="SENHA",
        help="Define nova senha para o usuario admin"
    )

    args = parser.parse_args()

    # Criar diretorio se nao existir
    DATABASE_DIR.mkdir(parents=True, exist_ok=True)

    # Inicializar
    initializer = DatabaseInitializer(DATABASE_FILE, verbose=args.verbose)

    try:
        # Executar inicializacao
        success = initializer.initialize(reset=args.reset, dry_run=args.dry_run)

        if not success:
            sys.exit(1)

        # Definir senha do admin se solicitado
        if args.set_admin_password:
            if not initializer.update_admin_password(args.set_admin_password):
                sys.exit(1)

        # Mostrar estatisticas
        if args.stats:
            initializer.show_stats()

        # Verificar integridade
        if args.verify:
            if not initializer.verify_integrity():
                sys.exit(1)

    finally:
        initializer.close()


if __name__ == "__main__":
    main()
