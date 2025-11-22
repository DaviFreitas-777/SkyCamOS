# ==============================================================================
# SkyCamOS - Makefile
# Comandos uteis para desenvolvimento, testes e deploy
# ==============================================================================
# Uso: make <comando>
# Listar comandos: make help
# ==============================================================================

# Configuracoes
.PHONY: help install dev test build clean docker-up docker-down docker-build \
        docker-logs lint format check security migrate db-reset \
        frontend-install frontend-dev frontend-build frontend-test \
        backend-install backend-dev backend-test docs release

# Cores para output
BLUE := \033[34m
GREEN := \033[32m
YELLOW := \033[33m
RED := \033[31m
NC := \033[0m # No Color

# Detecta SO
ifeq ($(OS),Windows_NT)
    SHELL := cmd.exe
    PYTHON := python
    PIP := pip
    RM := del /Q
    RMDIR := rmdir /S /Q
else
    PYTHON := python3
    PIP := pip3
    RM := rm -f
    RMDIR := rm -rf
endif

# Variaveis
DOCKER_COMPOSE := docker-compose
PYTEST := pytest
RUFF := ruff
BLACK := black
MYPY := mypy

# ==============================================================================
# Ajuda
# ==============================================================================
help: ## Mostra esta mensagem de ajuda
	@echo "================================================================================"
	@echo "SkyCamOS - Comandos Disponiveis"
	@echo "================================================================================"
	@echo ""
	@echo "Instalacao e Setup:"
	@echo "  make install          - Instala todas as dependencias (backend + frontend)"
	@echo "  make setup            - Configura ambiente de desenvolvimento"
	@echo ""
	@echo "Desenvolvimento:"
	@echo "  make dev              - Inicia ambiente de desenvolvimento completo"
	@echo "  make backend-dev      - Inicia apenas o backend com hot-reload"
	@echo "  make frontend-dev     - Inicia apenas o frontend com hot-reload"
	@echo ""
	@echo "Testes:"
	@echo "  make test             - Executa todos os testes"
	@echo "  make test-cov         - Executa testes com cobertura"
	@echo "  make backend-test     - Executa testes do backend"
	@echo "  make frontend-test    - Executa testes do frontend"
	@echo ""
	@echo "Qualidade de Codigo:"
	@echo "  make lint             - Executa linters (ruff, eslint)"
	@echo "  make format           - Formata codigo (black, prettier)"
	@echo "  make check            - Verifica tipos e qualidade"
	@echo "  make security         - Verifica vulnerabilidades"
	@echo ""
	@echo "Build:"
	@echo "  make build            - Build de producao (backend + frontend)"
	@echo "  make frontend-build   - Build do frontend"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-up        - Inicia containers Docker"
	@echo "  make docker-down      - Para containers Docker"
	@echo "  make docker-build     - Rebuild das imagens Docker"
	@echo "  make docker-logs      - Mostra logs dos containers"
	@echo "  make docker-clean     - Remove containers, volumes e imagens"
	@echo ""
	@echo "Banco de Dados:"
	@echo "  make migrate          - Executa migracoes do banco"
	@echo "  make db-reset         - Reset do banco de dados"
	@echo ""
	@echo "Outros:"
	@echo "  make clean            - Limpa arquivos temporarios e cache"
	@echo "  make docs             - Gera documentacao"
	@echo "  make release          - Prepara release"
	@echo ""

# ==============================================================================
# Instalacao
# ==============================================================================
install: backend-install frontend-install ## Instala todas as dependencias
	@echo "$(GREEN)Todas as dependencias instaladas com sucesso!$(NC)"

setup: install ## Configura ambiente de desenvolvimento
	@echo "$(BLUE)Configurando ambiente de desenvolvimento...$(NC)"
	@if [ ! -f .env ]; then cp .env.example .env; echo "$(YELLOW)Arquivo .env criado a partir do .env.example$(NC)"; fi
	@mkdir -p data recordings logs
	@echo "$(GREEN)Ambiente configurado com sucesso!$(NC)"

backend-install: ## Instala dependencias do backend
	@echo "$(BLUE)Instalando dependencias do backend...$(NC)"
	$(PYTHON) -m pip install --upgrade pip
	$(PIP) install -r requirements.txt
	$(PIP) install -r requirements-dev.txt 2>/dev/null || true
	@echo "$(GREEN)Backend instalado!$(NC)"

frontend-install: ## Instala dependencias do frontend
	@echo "$(BLUE)Instalando dependencias do frontend...$(NC)"
	cd frontend && npm ci
	@echo "$(GREEN)Frontend instalado!$(NC)"

# ==============================================================================
# Desenvolvimento
# ==============================================================================
dev: docker-up ## Inicia ambiente de desenvolvimento completo
	@echo "$(GREEN)Ambiente de desenvolvimento iniciado!$(NC)"
	@echo "$(BLUE)Backend: http://localhost:8000$(NC)"
	@echo "$(BLUE)Frontend: http://localhost:8080$(NC)"
	@echo "$(BLUE)API Docs: http://localhost:8000/docs$(NC)"

backend-dev: ## Inicia backend com hot-reload
	@echo "$(BLUE)Iniciando backend...$(NC)"
	cd backend && uvicorn main:app --host 0.0.0.0 --port 8000 --reload

frontend-dev: ## Inicia frontend com hot-reload
	@echo "$(BLUE)Iniciando frontend...$(NC)"
	cd frontend && npm run dev

# ==============================================================================
# Testes
# ==============================================================================
test: backend-test frontend-test ## Executa todos os testes
	@echo "$(GREEN)Todos os testes executados!$(NC)"

test-cov: ## Executa testes com cobertura
	@echo "$(BLUE)Executando testes com cobertura...$(NC)"
	$(PYTEST) backend/tests/ --cov=backend --cov-report=html --cov-report=term-missing
	@echo "$(GREEN)Relatorio de cobertura em htmlcov/index.html$(NC)"

backend-test: ## Executa testes do backend
	@echo "$(BLUE)Executando testes do backend...$(NC)"
	$(PYTEST) backend/tests/ -v

frontend-test: ## Executa testes do frontend
	@echo "$(BLUE)Executando testes do frontend...$(NC)"
	cd frontend && npm run test:unit

# ==============================================================================
# Qualidade de Codigo
# ==============================================================================
lint: ## Executa linters
	@echo "$(BLUE)Executando linters...$(NC)"
	$(RUFF) check backend/
	cd frontend && npm run lint
	@echo "$(GREEN)Lint concluido!$(NC)"

format: ## Formata codigo
	@echo "$(BLUE)Formatando codigo...$(NC)"
	$(BLACK) backend/
	$(RUFF) check backend/ --fix
	cd frontend && npm run format
	@echo "$(GREEN)Codigo formatado!$(NC)"

check: lint ## Verifica tipos e qualidade
	@echo "$(BLUE)Verificando tipos...$(NC)"
	$(MYPY) backend/ --ignore-missing-imports
	cd frontend && npm run type-check 2>/dev/null || true
	@echo "$(GREEN)Verificacao concluida!$(NC)"

security: ## Verifica vulnerabilidades
	@echo "$(BLUE)Verificando vulnerabilidades...$(NC)"
	$(PIP) install bandit safety pip-audit
	bandit -r backend/ -ll
	safety check -r requirements.txt || true
	pip-audit -r requirements.txt || true
	cd frontend && npm audit || true
	@echo "$(GREEN)Verificacao de seguranca concluida!$(NC)"

# ==============================================================================
# Build
# ==============================================================================
build: frontend-build ## Build de producao
	@echo "$(GREEN)Build de producao concluido!$(NC)"

frontend-build: ## Build do frontend
	@echo "$(BLUE)Fazendo build do frontend...$(NC)"
	cd frontend && npm run build
	@echo "$(GREEN)Frontend build concluido!$(NC)"

# ==============================================================================
# Docker
# ==============================================================================
docker-up: ## Inicia containers Docker
	@echo "$(BLUE)Iniciando containers Docker...$(NC)"
	$(DOCKER_COMPOSE) up -d
	@echo "$(GREEN)Containers iniciados!$(NC)"
	@$(DOCKER_COMPOSE) ps

docker-down: ## Para containers Docker
	@echo "$(BLUE)Parando containers Docker...$(NC)"
	$(DOCKER_COMPOSE) down
	@echo "$(GREEN)Containers parados!$(NC)"

docker-build: ## Rebuild das imagens Docker
	@echo "$(BLUE)Reconstruindo imagens Docker...$(NC)"
	$(DOCKER_COMPOSE) build --no-cache
	@echo "$(GREEN)Imagens reconstruidas!$(NC)"

docker-logs: ## Mostra logs dos containers
	$(DOCKER_COMPOSE) logs -f

docker-restart: docker-down docker-up ## Reinicia containers Docker
	@echo "$(GREEN)Containers reiniciados!$(NC)"

docker-clean: ## Remove containers, volumes e imagens
	@echo "$(YELLOW)Removendo containers, volumes e imagens...$(NC)"
	$(DOCKER_COMPOSE) down -v --rmi all --remove-orphans
	docker system prune -f
	@echo "$(GREEN)Limpeza Docker concluida!$(NC)"

docker-shell-backend: ## Acessa shell do container backend
	$(DOCKER_COMPOSE) exec backend /bin/bash

docker-shell-frontend: ## Acessa shell do container frontend
	$(DOCKER_COMPOSE) exec frontend /bin/sh

# ==============================================================================
# Banco de Dados
# ==============================================================================
migrate: ## Executa migracoes do banco
	@echo "$(BLUE)Executando migracoes...$(NC)"
	cd backend && alembic upgrade head
	@echo "$(GREEN)Migracoes aplicadas!$(NC)"

migrate-create: ## Cria nova migracao (uso: make migrate-create MSG="descricao")
	@echo "$(BLUE)Criando nova migracao...$(NC)"
	cd backend && alembic revision --autogenerate -m "$(MSG)"
	@echo "$(GREEN)Migracao criada!$(NC)"

db-reset: ## Reset do banco de dados
	@echo "$(YELLOW)Resetando banco de dados...$(NC)"
	$(RM) data/*.db 2>/dev/null || true
	cd backend && alembic upgrade head
	@echo "$(GREEN)Banco de dados resetado!$(NC)"

# ==============================================================================
# Limpeza
# ==============================================================================
clean: ## Limpa arquivos temporarios e cache
	@echo "$(BLUE)Limpando arquivos temporarios...$(NC)"
	# Python
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name htmlcov -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
	# Node
	$(RMDIR) frontend/node_modules 2>/dev/null || true
	$(RMDIR) frontend/dist 2>/dev/null || true
	$(RMDIR) frontend/.vite 2>/dev/null || true
	# Logs
	$(RM) logs/*.log 2>/dev/null || true
	@echo "$(GREEN)Limpeza concluida!$(NC)"

clean-all: clean docker-clean ## Limpeza completa (inclui Docker)
	@echo "$(GREEN)Limpeza completa concluida!$(NC)"

# ==============================================================================
# Documentacao
# ==============================================================================
docs: ## Gera documentacao
	@echo "$(BLUE)Gerando documentacao...$(NC)"
	cd backend && pdoc --html --output-dir ../docs/api .
	@echo "$(GREEN)Documentacao gerada em docs/$(NC)"

# ==============================================================================
# Release
# ==============================================================================
release: check test build ## Prepara release
	@echo "$(GREEN)Release preparado!$(NC)"
	@echo "$(BLUE)Proximos passos:$(NC)"
	@echo "  1. Atualize a versao em pyproject.toml e package.json"
	@echo "  2. Atualize o CHANGELOG.md"
	@echo "  3. Commit e crie uma tag: git tag -a vX.Y.Z -m 'Release vX.Y.Z'"
	@echo "  4. Push da tag: git push origin vX.Y.Z"

version: ## Mostra versao atual
	@$(PYTHON) -c "import toml; print(toml.load('pyproject.toml')['project']['version'])" 2>/dev/null || echo "Versao nao encontrada"

# ==============================================================================
# Atalhos
# ==============================================================================
up: docker-up ## Alias para docker-up
down: docker-down ## Alias para docker-down
logs: docker-logs ## Alias para docker-logs
ps: ## Mostra status dos containers
	$(DOCKER_COMPOSE) ps
