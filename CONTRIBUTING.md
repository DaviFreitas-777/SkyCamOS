# Guia de Contribuicao

Obrigado pelo interesse em contribuir com o SkyCamOS! Este documento fornece diretrizes para contribuir com o projeto de forma efetiva.

---

## Sumario

- [Codigo de Conduta](#codigo-de-conduta)
- [Como Posso Contribuir?](#como-posso-contribuir)
- [Configurando o Ambiente de Desenvolvimento](#configurando-o-ambiente-de-desenvolvimento)
- [Padrao de Commits](#padrao-de-commits)
- [Fluxo de Branches (Git Flow)](#fluxo-de-branches-git-flow)
- [Code Style](#code-style)
- [Submetendo Pull Requests](#submetendo-pull-requests)
- [Processo de Code Review](#processo-de-code-review)

---

## Codigo de Conduta

Este projeto adota um Codigo de Conduta que esperamos que todos os participantes sigam. Por favor, seja respeitoso e construtivo em todas as interacoes.

**Comportamentos esperados:**
- Uso de linguagem acolhedora e inclusiva
- Respeito por diferentes pontos de vista e experiencias
- Aceitacao de criticas construtivas
- Foco no que e melhor para a comunidade

---

## Como Posso Contribuir?

### Reportando Bugs

Antes de criar um bug report:
1. Verifique se o bug ja foi reportado nas [Issues](https://github.com/seu-usuario/skycamos/issues)
2. Colete informacoes sobre o ambiente (SO, versao do Python, etc.)

Ao criar o report, inclua:
- **Titulo claro e descritivo**
- **Passos para reproduzir** o problema
- **Comportamento esperado** vs **comportamento atual**
- **Screenshots ou logs** se aplicavel
- **Ambiente** (sistema operacional, versao, etc.)

### Sugerindo Melhorias

Abra uma issue do tipo "Feature Request" incluindo:
- **Descricao clara** da funcionalidade
- **Caso de uso** que ela resolveria
- **Alternativas** que voce considerou
- **Mockups ou diagramas** se relevante

### Contribuindo com Codigo

1. Escolha uma issue para trabalhar (ou crie uma)
2. Comente na issue que voce vai trabalhar nela
3. Siga o fluxo de desenvolvimento descrito abaixo

---

## Configurando o Ambiente de Desenvolvimento

### Pre-requisitos

- Python 3.10 ou superior
- Git
- FFmpeg (para processamento de video)
- Node.js 18+ (para o frontend PWA)

### Passo a Passo

```bash
# 1. Fork o repositorio no GitHub

# 2. Clone seu fork
git clone https://github.com/seu-usuario/skycamos.git
cd skycamos

# 3. Adicione o repositorio original como upstream
git remote add upstream https://github.com/skycamos/skycamos.git

# 4. Crie o ambiente virtual
py -m venv venv

# Windows
venv\Scripts\activate

# Linux/macOS
source venv/bin/activate

# 5. Instale as dependencias de desenvolvimento
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 6. Instale os hooks de pre-commit
pre-commit install

# 7. Verifique se tudo esta funcionando
py -m pytest
```

### Estrutura do Projeto

```
skycamos/
├── src/
│   ├── api/           # Endpoints da API REST
│   ├── core/          # Logica central do sistema
│   ├── services/      # Servicos (gravacao, deteccao, etc.)
│   ├── models/        # Modelos de dados
│   └── utils/         # Utilitarios
├── frontend/          # Codigo do PWA
│   ├── src/
│   └── public/
├── tests/             # Testes automatizados
├── docs/              # Documentacao
├── scripts/           # Scripts auxiliares
└── config/            # Arquivos de configuracao
```

### Executando em Desenvolvimento

```bash
# Backend com hot reload
py -m uvicorn src.main:app --reload --port 8000

# Frontend (em outro terminal)
cd frontend
npm install
npm run dev
```

---

## Padrao de Commits

Utilizamos **Conventional Commits** para manter um historico de commits limpo e gerar changelogs automaticamente.

### Formato

```
<tipo>(<escopo>): <descricao>

[corpo opcional]

[rodape opcional]
```

### Tipos Permitidos

| Tipo | Descricao |
|------|-----------|
| `feat` | Nova funcionalidade |
| `fix` | Correcao de bug |
| `docs` | Alteracoes na documentacao |
| `style` | Formatacao, ponto e virgula, etc. (sem mudanca de codigo) |
| `refactor` | Refatoracao de codigo |
| `perf` | Melhoria de performance |
| `test` | Adicao ou correcao de testes |
| `chore` | Tarefas de manutencao |
| `ci` | Alteracoes de CI/CD |
| `build` | Alteracoes no sistema de build |

### Exemplos

```bash
# Nova funcionalidade
feat(camera): adiciona suporte a descoberta ONVIF

# Correcao de bug
fix(recording): corrige gravacao que parava apos 1 hora

# Documentacao
docs(api): documenta endpoints de autenticacao

# Refatoracao
refactor(services): extrai logica de deteccao para classe separada

# Breaking change
feat(api)!: altera formato de resposta do endpoint /cameras

BREAKING CHANGE: o campo 'camera_id' agora se chama 'id'
```

### Dicas

- Use o imperativo: "adiciona" em vez de "adicionado" ou "adicionando"
- Primeira linha com no maximo 72 caracteres
- Corpo do commit explica o "por que", nao o "o que"
- Referencie issues quando aplicavel: `fix(api): corrige erro 500 (#123)`

---

## Fluxo de Branches (Git Flow)

### Branches Principais

| Branch | Proposito |
|--------|-----------|
| `main` | Codigo de producao, sempre estavel |
| `develop` | Branch de integracao para desenvolvimento |

### Branches de Trabalho

| Prefixo | Uso |
|---------|-----|
| `feature/` | Novas funcionalidades |
| `fix/` | Correcoes de bugs |
| `hotfix/` | Correcoes urgentes em producao |
| `docs/` | Alteracoes na documentacao |
| `refactor/` | Refatoracao de codigo |

### Fluxo de Trabalho

```
main ─────────────────────────────────────────────────
       │                                    ▲
       ▼                                    │
develop ──────┬───────────────────┬─────────┴─────────
              │                   │
              ▼                   ▼
        feature/nova-camera  fix/bug-gravacao
              │                   │
              ▼                   │
         [commits]               [commits]
              │                   │
              └─────────┬─────────┘
                        │
                        ▼
                   Pull Request
                        │
                        ▼
                   Code Review
                        │
                        ▼
                   Merge → develop
```

### Comandos Praticos

```bash
# Atualizar sua branch develop local
git checkout develop
git pull upstream develop

# Criar branch de feature
git checkout -b feature/nome-da-feature develop

# Trabalhar na feature (commits frequentes)
git add .
git commit -m "feat(escopo): descricao"

# Atualizar com mudancas recentes do develop
git fetch upstream
git rebase upstream/develop

# Subir para seu fork
git push origin feature/nome-da-feature

# Criar Pull Request no GitHub
```

---

## Code Style

### Python

Seguimos as convencoes do **PEP 8** com algumas customizacoes:

```python
# Imports organizados
import os
import sys
from typing import Optional, List

import fastapi
from pydantic import BaseModel

from src.core import camera
from src.utils import helpers


# Classes com docstrings
class CameraService:
    """Servico para gerenciamento de cameras IP.

    Attributes:
        cameras: Lista de cameras registradas.
        max_cameras: Numero maximo de cameras suportadas.
    """

    def __init__(self, max_cameras: int = 10) -> None:
        self.cameras: List[Camera] = []
        self.max_cameras = max_cameras

    def discover_cameras(self, timeout: float = 5.0) -> List[Camera]:
        """Descobre cameras na rede local.

        Args:
            timeout: Tempo maximo de espera em segundos.

        Returns:
            Lista de cameras descobertas.

        Raises:
            NetworkError: Se houver falha na rede.
        """
        pass


# Funcoes com type hints
def process_frame(
    frame: bytes,
    width: int,
    height: int,
    *,
    detect_motion: bool = True,
) -> Optional[MotionEvent]:
    """Processa um frame de video."""
    pass
```

### Ferramentas de Linting

```bash
# Formatacao automatica
black src/ tests/

# Ordenacao de imports
isort src/ tests/

# Linting
flake8 src/ tests/
mypy src/

# Executar todos
pre-commit run --all-files
```

### Frontend (TypeScript/JavaScript)

- ESLint + Prettier para formatacao
- Componentes Vue/React com TypeScript
- Nomes de variaveis em camelCase
- Componentes em PascalCase

```typescript
// Componente Vue exemplo
<script setup lang="ts">
import { ref, computed } from 'vue'
import type { Camera } from '@/types'

interface Props {
  camera: Camera
  isLive?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  isLive: true,
})

const isPlaying = ref(false)

const streamUrl = computed(() => {
  return `${props.camera.streamUrl}?live=${props.isLive}`
})
</script>
```

---

## Submetendo Pull Requests

### Antes de Criar o PR

1. **Atualize sua branch** com o develop mais recente
2. **Execute os testes** localmente: `python -m pytest`
3. **Verifique o linting**: `pre-commit run --all-files`
4. **Revise suas mudancas**: `git diff develop`

### Criando o Pull Request

1. Acesse seu fork no GitHub
2. Clique em "New Pull Request"
3. Selecione `base: develop` ← `compare: sua-branch`

### Template do Pull Request

```markdown
## Descricao

Breve descricao do que este PR faz.

## Tipo de Mudanca

- [ ] Bug fix (correcao que nao quebra funcionalidades existentes)
- [ ] Nova feature (adicao que nao quebra funcionalidades existentes)
- [ ] Breaking change (correcao ou feature que quebra funcionalidades existentes)
- [ ] Documentacao

## Como Testar

1. Passo 1
2. Passo 2
3. Verificar que...

## Checklist

- [ ] Meu codigo segue o style guide do projeto
- [ ] Fiz self-review do meu codigo
- [ ] Comentei codigo complexo
- [ ] Atualizei a documentacao
- [ ] Adicionei testes que provam que minha correcao/feature funciona
- [ ] Testes novos e existentes passam localmente

## Screenshots (se aplicavel)

## Issues Relacionadas

Closes #123
```

---

## Processo de Code Review

### Para Autores

- Responda a todos os comentarios
- Faca commits adicionais para enderencar feedback
- Marque conversas como resolvidas apos implementar mudancas
- Solicite re-review quando pronto

### Para Revisores

Verifique:

1. **Funcionalidade** - O codigo faz o que deveria?
2. **Design** - O codigo esta bem estruturado?
3. **Legibilidade** - O codigo e facil de entender?
4. **Testes** - Ha testes adequados?
5. **Documentacao** - Esta atualizada?
6. **Seguranca** - Ha vulnerabilidades?

### Labels de Aprovacao

| Label | Significado |
|-------|-------------|
| `approved` | Aprovado para merge |
| `changes-requested` | Necessita alteracoes |
| `needs-discussion` | Requer discussao adicional |

### Merge

- PRs precisam de pelo menos 1 aprovacao
- Todos os checks de CI devem passar
- Sem conflitos com a branch base
- Preferimos "Squash and merge" para features pequenas

---

## Duvidas?

- Abra uma [Discussion](https://github.com/seu-usuario/skycamos/discussions)
- Pergunte na issue relevante
- Entre em contato com os maintainers

Obrigado por contribuir!
