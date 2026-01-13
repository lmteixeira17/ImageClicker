# ImageClicker - Instruções para Agentes Claude

## Visão Geral

ImageClicker é uma ferramenta de automação de cliques baseada em reconhecimento de imagem para **macOS**. Suporta execução paralela de múltiplas tasks em diferentes janelas simultaneamente.

**Versão**: 3.1 (macOS Native)
**Última Atualização**: 2026-01-13
**Plataforma**: macOS (Quartz/AppKit/PyObjC)

## Instalação e Execução

### Pré-requisitos

- Python 3.8+ (recomendado: Python 3.11+)
- macOS 10.15+ (Catalina ou superior)
- Permissões de **Acessibilidade** (obrigatório para cliques)
- Permissões de **Gravação de Tela** (obrigatório para captura)

### Instalação Rápida

```bash
# 1. Navegar para o diretório do projeto
cd "/Users/luismarceloteixeira/Library/CloudStorage/OneDrive-Personal/LM/Projetos/_ImageClicker_MAC"

# 2. Criar ambiente virtual
python3 -m venv venv

# 3. Instalar dependências
source venv/bin/activate
pip install -r requirements.txt
```

### Aliases Globais (zsh)

Adicione ao `~/.zshrc`:

```bash
# ImageClicker
IMAGECLICKER_DIR="/caminho/para/ImageClicker_MAC"
alias iclick='"$IMAGECLICKER_DIR/venv/bin/python3" "$IMAGECLICKER_DIR/iclick.py"'
alias imageclicker='"$IMAGECLICKER_DIR/venv/bin/python3" "$IMAGECLICKER_DIR/app_qt.py"'
```

Depois: `source ~/.zshrc`

### Execução

```bash
# GUI
imageclicker

# CLI
iclick --help
iclick tasks
iclick capture nome_botao
```

### Permissões macOS (OBRIGATÓRIO)

1. **Ajustes do Sistema** → **Privacidade e Segurança** → **Acessibilidade**
   - Adicionar **Terminal** (ou app que executa Python)
   - Se usar VS Code terminal, adicionar **Visual Studio Code**

2. **Ajustes do Sistema** → **Privacidade e Segurança** → **Gravação de Tela**
   - Adicionar **Terminal** (ou app que executa Python)

> **Importante**: Reinicie o Terminal após conceder permissões.

## Estrutura do Projeto

```text
ImageClicker/
├── app_qt.py              # GUI - Entrada principal PyQt6
├── iclick.py              # CLI - Interface de linha de comando
├── iclick                 # Script shell para CLI (alias)
├── images/                # Templates capturados (PNG)
├── scripts/               # Scripts de automação sequencial (JSON)
├── tasks.json             # Configuração de tasks paralelas
├── venv/                  # Ambiente virtual Python
├── core/                  # Módulo core
│   ├── __init__.py        # Exports principais
│   ├── task_manager.py    # Gerenciador de tasks paralelas
│   ├── image_matcher.py   # Template matching com OpenCV + Quartz
│   └── window_utils.py    # Utilitários de janelas macOS (Quartz/AppKit)
├── ui_qt/                 # Interface PyQt6
│   ├── main_window.py     # Janela principal
│   ├── theme.py           # Tema glassmorphism
│   ├── keyboard_manager.py # Atalhos de teclado globais
│   ├── pages/             # Páginas da aplicação
│   │   ├── base_page.py   # Classe base para páginas
│   │   ├── dashboard.py   # Dashboard com logs em tempo real
│   │   ├── tasks.py       # Gerenciamento de tasks (unificado)
│   │   ├── templates.py   # Galeria de templates
│   │   └── settings.py    # Configurações
│   └── components/        # Componentes reutilizáveis
│       ├── sidebar.py     # Navegação lateral
│       ├── task_row.py    # Widget de task individual
│       ├── edit_dialog.py # Dialog de edição (unificado)
│       ├── glass_panel.py # Painéis glassmorphism
│       ├── log_panel.py   # Painel de logs
│       ├── toast_notification.py  # Notificações toast
│       ├── help_dialog.py # Dialog de ajuda/atalhos
│       ├── onboarding.py  # Onboarding para novos usuários
│       ├── confirm_dialog.py # Dialog de confirmação
│       ├── capture_overlay.py # Overlay de captura de tela
│       └── icons.py       # Ícones Unicode
├── docs/                  # Documentação estruturada
│   └── ...                # Guias e referências
├── claude.md              # Este arquivo (instruções para agentes)
├── CHANGELOG.md           # Histórico de mudanças
├── requirements.txt       # Dependências Python
├── .imageclicker_config.json # Config do usuário (auto-gerado)
├── install.command        # Instalador de dependências (macOS)
├── ImageClicker.command   # Launcher macOS (GUI)
├── iclick.command         # Launcher macOS (CLI)
└── final_icon.ico         # Ícone da aplicação
```

## Tecnologias e Dependências

### Python

- **Versão**: 3.8+
- **Dependências**:
  - `pyautogui` - Automação de mouse/teclado
  - `pillow` - Manipulação de imagens
  - `opencv-python` - Reconhecimento de imagem (template matching)
  - `PyQt6` - Interface gráfica moderna (Glassmorphism)
  - `pyobjc-core` - Bridge Python-Objective-C
  - `pyobjc-framework-Quartz` - APIs CoreGraphics/Quartz (captura, cliques)
  - `pyobjc-framework-Cocoa` - APIs AppKit (janelas, processos)
  - `pyobjc-framework-ApplicationServices` - APIs de acessibilidade
  - `mss` - Captura de tela cross-platform
  - `numpy` - Operações com arrays
  - `easyocr` - OCR para extração de texto em capturas (opcional)

### Arquitetura

- **CLI (iclick.py)**: Comandos para captura, clique, scripts e tasks
- **GUI (app_qt.py)**: Interface gráfica PyQt6 com páginas (Dashboard, Tasks, Templates, Settings)
- **TaskManager**: Gerenciador de execução paralela com ThreadPoolExecutor
- **Templates**: Imagens PNG para template matching (OpenCV TM_CCOEFF_NORMED)
- **Ghost Click**: Cliques via CGEvent (CoreGraphics)
- **Tasks Unificadas**: Uma única entidade Task suporta modo simples e múltiplas opções

### APIs macOS Utilizadas

- **CGWindowListCopyWindowInfo**: Listar janelas visíveis (inclui todos os Spaces)
- **CGWindowListCreateImage**: Capturar conteúdo de janelas (pixels físicos Retina)
- **CGEventCreateMouseEvent**: Criar eventos de mouse
- **CGEventPost**: Enviar eventos de clique (coordenadas em pontos lógicos)
- **NSScreen**: Informações de monitores e DPI (Retina)
- **NSWorkspace**: Listar aplicativos em execução

### Conceitos Importantes - macOS Retina

O macOS usa dois sistemas de coordenadas:

| Tipo | Descrição | Uso |
|------|-----------|-----|
| **Pontos Lógicos** | Coordenadas independentes de DPI | CGEvent (cliques), kCGWindowBounds |
| **Pixels Físicos** | Pixels reais da tela (2x em Retina) | CGWindowListCreateImage, template matching |

**Fator de escala Retina**: Em telas Retina, 1 ponto lógico = 2 pixels físicos.

O código faz a conversão automaticamente:
- **Captura**: Converte pontos lógicos → pixels físicos para recortar corretamente
- **Clique**: Converte pixels físicos → pontos lógicos para clicar na posição correta

### Suporte a Fullscreen e Spaces

O ImageClicker suporta janelas em **fullscreen** (que ficam em Spaces separados no macOS):

| Cenário | Funciona? |
|---------|-----------|
| Janela normal (mesmo Space) | ✅ Sim |
| Janela fullscreen (Space dedicado, ativo) | ✅ Sim |
| Janela em outro Space (não visível) | ❌ Não* |
| Janela minimizada | ❌ Não |

> *Limitação do macOS: não é possível capturar ou clicar em janelas de Spaces não ativos.

## Funcionalidades Principais

### 1. Template Matching

- **OpenCV**: Busca em janela específica (threshold configurável por task, default 85%)
- **Multi-instância**: Busca em TODAS as janelas do mesmo processo (ex: 3 janelas do Safari)
- Suporte multi-monitor via virtual screen
- Escalonamento automático de DPI

### 2. Sistema de Tasks Unificado

- **Dois modos em uma única entidade**:
  - **Template Único**: Monitora uma imagem, clica quando encontrar
  - **Múltiplas Opções**: Monitora N imagens, clica na selecionada quando TODAS visíveis
- Execução simultânea de múltiplas automações
- Cada task monitora uma janela específica (por processo ou título)
- **Busca multi-janela**: Encontra template em todas as instâncias do processo
- Controle individual (play/stop por task)
- **Threshold configurável**: Cada task pode ter seu próprio threshold (50-99%)
- Persistência em `tasks.json`
- Status em tempo real com contadores de cliques
- **Logging inteligente**: Evita repetição de logs idênticos

### 3. Clique Fantasma (Ghost Click)

- **Cliques via CGEvent**: Usa CoreGraphics para enviar eventos de mouse
- Suporta click, double_click, right_click
- **Nota**: No macOS, CGEvent move o cursor momentaneamente (diferente do Windows PostMessage)
- **Conversão Retina**: Coordenadas são convertidas de pixels físicos para pontos lógicos automaticamente

```python
# Exemplo de conversão (interno)
scale_x = win_width_points / img_width  # ~0.5 em Retina
rel_x = int(pixel_x * scale_x)          # Converte para pontos
```

### 4. Captura Visual com OCR

- Overlay fullscreen multi-monitor
- Preview em tempo real com dimensões
- **Captura via Quartz**: Usa `CGWindowListCreateImage` para compatibilidade com matching
- **Conversão Retina**: Coordenadas lógicas são convertidas para pixels físicos
- **OCR automático**: Extrai texto do botão capturado (EasyOCR)
- **DPI automático**: Detecta escala DPI da janela e salva nos metadados PNG
- Nome sugerido: `{TextoOCR}_{Processo}` (DPI removido do nome)
- ESC para cancelar, botão direito para reiniciar

> **Nota técnica**: A captura usa o mesmo método que o template matching (`CGWindowListCreateImage`) para garantir consistência nos resultados.

### 5. Galeria de Templates

- Grid de thumbnails 4 colunas (150x130px)
- **Hover preview**: Preview ampliado ao passar o mouse
- Preview ampliável no painel lateral
- Teste, renomeação e exclusão de templates
- Integração com Finder (duplo clique abre no Finder)

### 6. Sistema de Atalhos de Teclado

- **Navegação**: Cmd+1-5 para páginas (Ctrl também funciona)
- **Ações**: Cmd+N (nova task), Cmd+Shift+C (captura), Cmd+E/Shift+S (start/stop all)
- **Ajuda**: F1 ou Cmd+H (lista de atalhos)
- KeyboardManager centralizado em `ui_qt/keyboard_manager.py`

### 7. Toast Notifications

- Feedback visual para ações do usuário
- Tipos: success, error, warning, info
- Auto-dismiss configurável
- Empilhável (máx 3 visíveis)

### 8. Onboarding

- Welcome modal na primeira execução
- Tour guiado pelas páginas
- Quick Start Checklist no Dashboard
- Estado persistido em `.imageclicker_config.json`

### 9. UX Profissional

- **Tooltips informativos**: Todos os elementos têm dicas contextuais
- **Sidebar com navegação por atalhos**: Ctrl+1 a Ctrl+4
- **Feedback visual**: Estados de botões, animações de pulse em tasks ativas
- **Combos editáveis**: Campos de janela/processo permitem digitação livre
- **Botões de refresh**: Atualização dinâmica de listas de janelas/processos

## Comandos CLI Principais

```bash
# Usando alias (recomendado)
iclick capture <nome>
iclick click <nome>
iclick tasks
iclick list

# Ou diretamente
python iclick.py capture <nome>

# Clique
python iclick.py click <nome>                # Tela toda
python iclick.py click <nome> --window "App" # Janela específica

# Outros
python iclick.py wait <nome>                 # Espera e clica
python iclick.py run <script>                # Executa script JSON
python iclick.py tasks                       # Executa tasks.json
python iclick.py list                        # Lista recursos
```

## Troubleshooting macOS

### Clique não funciona

**Sintoma**: Template é encontrado mas o clique não acontece.

**Causa**: Falta permissão de Acessibilidade.

**Solução**:
1. Ajustes do Sistema → Privacidade e Segurança → Acessibilidade
2. Adicione o Terminal (ou VS Code)
3. Reinicie o Terminal

### Captura retorna tela inteira

**Sintoma**: Ao capturar, salva a janela toda em vez da seleção.

**Causa**: Problema na conversão de coordenadas Retina.

**Solução**: Verifique se está usando a versão mais recente do `capture_overlay.py` com suporte a escala Retina.

### Template não encontrado (baixo match)

**Sintoma**: Match sempre abaixo do threshold, mesmo com imagem visível.

**Causas possíveis**:
1. Template capturado em DPI diferente
2. Tema claro/escuro diferente
3. Janela em outro Space (não visível)

**Soluções**:
1. Recapture o template no mesmo monitor/DPI
2. Use o mesmo tema (claro/escuro) da captura
3. Mova a janela para o Space atual ou use fullscreen ativo

### Janela fullscreen não detectada

**Sintoma**: Tasks não encontram janelas em fullscreen.

**Causa**: Janela em Space não ativo.

**Solução**:
- Mantenha o Space da janela fullscreen ativo
- Ou use a janela no mesmo Space do ImageClicker

### Erro "externally-managed-environment"

**Sintoma**: Erro ao instalar dependências com pip.

**Causa**: macOS protege o Python do sistema.

**Solução**: Use ambiente virtual:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Processo com nome diferente do Windows

**Sintoma**: Task configurada com `Code.exe` não encontra janelas.

**Causa**: Nomes de processo são diferentes no macOS.

**Solução**: Use nomes sem `.exe`:
- Windows: `Code.exe` → macOS: `Code`
- Windows: `chrome.exe` → macOS: `Google Chrome`

## Padrões de Código

### Nomenclatura

- **Templates**: `nome_descritivo.png` (snake_case)
- **Scripts**: `nome_script.json` (snake_case)
- **Variáveis**: snake_case
- **Classes**: PascalCase
- **Constantes**: UPPER_CASE
- **Métodos privados**: `_prefixed`

### Paths

- Usar `BASE_DIR` como raiz
- Todos os paths são absolutos
- Hard-coded nos arquivos (editar se necessário)

### Error Handling

- Try-except em operações críticas
- Mensagens descritivas com emojis
- Logs detalhados

### Threading

- ThreadPoolExecutor para tasks paralelas
- threading.Event para stop events (parada graceful)
- threading.Lock para dicionários compartilhados
- GUI PyQt6: usar `QTimer.singleShot()` ou signals para thread-safety

### Encoding

- UTF-8 para todos os arquivos JSON
- Logs com timestamp `[HH:MM:SS]`

---

## 📚 MANUTENÇÃO DA DOCUMENTAÇÃO

### Princípios de Documentação

1. **Documentação é Código**: Trate docs com o mesmo rigor que código
2. **Consistência Absoluta**: Siga padrões estabelecidos
3. **Clareza e Simplicidade**: Escreva para iniciantes e avançados
4. **Atualização Obrigatória**: Mudanças no código = mudanças nos docs
5. **Versionamento**: Documente versão e data de atualização

### Estrutura de Documentação

A documentação está organizada em **docs/** com arquivos específicos:

- **README.md**: Índice e navegação
- **Guias de Uso**: installation, quickstart, conceitos básicos
- **Guias Técnicos**: CLI, GUI, templates, tasks, scripts
- **Referência**: API, arquitetura, configuração
- **Suporte**: FAQ, troubleshooting, best practices

### Regras de Manutenção

#### QUANDO Atualizar Documentação

Você DEVE atualizar a documentação quando:

1. **Adicionar Funcionalidade**:
   - Novo comando CLI
   - Nova feature na GUI
   - Novo tipo de ação em scripts
   - Nova configuração

2. **Modificar Comportamento**:
   - Mudança em algoritmos
   - Alteração de thresholds/defaults
   - Mudança em estrutura de dados

3. **Corrigir Bugs**:
   - Se o bug afeta comportamento documentado
   - Se a correção muda o uso esperado

4. **Refatoração Significativa**:
   - Mudança em arquitetura
   - Rename de funções/classes públicas
   - Alteração em APIs

5. **Deprecação/Remoção**:
   - Features removidas
   - APIs depreciadas

#### O QUE Atualizar

##### 1. Mudanças em Código → Docs Afetados

| Tipo de Mudança | Arquivos para Atualizar |
|-----------------|-------------------------|
| Nova funcionalidade CLI | cli-guide.md, quickstart.md, README.md |
| Nova funcionalidade GUI | gui-guide.md, quickstart.md, README.md |
| Novo tipo de ação (script) | scripts-guide.md, concepts.md, api-reference.md |
| Nova configuração | configuration.md, installation.md |
| Mudança em threshold/default | concepts.md, configuration.md, troubleshooting.md |
| Bug fix significativo | troubleshooting.md, faq.md, CHANGELOG.md |
| Refatoração de API | api-reference.md, architecture.md |
| Novo comando | cli-guide.md, quickstart.md, README.md (índice) |
| Nova dependência | installation.md, requirements.txt |
| Mudança em estrutura de arquivos | Todos os guias afetados + claude.md |

##### 2. Sempre Atualizar

- **claude.md**: Se mudanças afetam instruções para agentes
- **CHANGELOG.md**: Todas as mudanças user-facing
- **README.md** (raiz): Se mudanças afetam quick-start geral
- **docs/README.md**: Se novos docs foram adicionados

#### COMO Atualizar Documentação

##### Processo Passo-a-Passo

1. **Identifique Impacto**:
   - Quais features foram afetadas?
   - Quais docs mencionam essas features?
   - Use `grep` para buscar termos relevantes em docs/

2. **Atualize Docs Específicos**:
   - Edite seções relevantes
   - Mantenha estrutura existente
   - Siga padrões de formatação

3. **Atualize Referências Cruzadas**:
   - Links entre docs
   - Exemplos que usam a feature
   - Troubleshooting relacionado

4. **Atualize Changelog**:
   - Adicione entrada em CHANGELOG.md
   - Use formato: `## [Unreleased]` ou `## [X.Y.Z] - YYYY-MM-DD`
   - Categorias: Added, Changed, Deprecated, Removed, Fixed, Security

5. **Atualize Versão/Data**:
   - claude.md: `Última Atualização: YYYY-MM-DD`
   - docs afetados: Adicionar nota de atualização se significativo

##### Padrões de Formatação Markdown

**Headings**:

```markdown
# Título Principal (H1 - apenas um por arquivo)

## Seção Principal (H2)

### Subseção (H3)

#### Sub-subseção (H4)
```

**Listas**:

```markdown
- Item (usar hífen)
  - Sub-item (indent 2 espaços)
- Outro item

1. Item numerado
2. Outro item
```

**Code Blocks**:

````markdown
```python
# Código Python com linguagem especificada
```

```bash
# Comandos bash
```

```json
{
  "json": "example"
}
```
````

**Tabelas**:

```markdown
| Coluna 1 | Coluna 2 | Coluna 3 |
|----------|----------|----------|
| Valor 1  | Valor 2  | Valor 3  |
```

**Links**:

```markdown
[Texto do Link](arquivo.md)
[Link Externo](https://example.com)
[Seção](#titulo-da-secao)
```

**Ênfase**:

```markdown
**Negrito**
*Itálico*
`código inline`
```

**Avisos e Notas**:

```markdown
> **Nota**: Informação importante

> **Aviso**: Cuidado com isso

> **Dica**: Sugestão útil
```

##### Estrutura de Novos Docs

Se criar novo arquivo em docs/:

```markdown
# Título do Documento

Breve descrição (1-2 parágrafos).

## Conteúdo Principal

### Seção 1

Conteúdo...

### Seção 2

Conteúdo...

## Exemplos

### Exemplo 1

```code
exemplo
```

### Exemplo 2

```code
exemplo
```

## Próximos Passos

- [Documento Relacionado 1](link.md)
- [Documento Relacionado 2](link.md)

## Referências

- [API Reference](api-reference.md)
- [Outros links relevantes]
```

#### Regras de CRIAR Novos Docs

**Quando Criar**:

- Nova funcionalidade complexa (> 200 linhas doc)
- Novo conceito fundamental
- Guia tutorial específico
- Referência técnica extensa

**Onde Criar**:

- **docs/** para documentação user-facing
- **docs/dev/** (criar se necessário) para docs técnicos internos
- Atualizar **docs/README.md** com link

**Processo**:

1. Verifique se não existe doc similar
2. Planeje estrutura (outline)
3. Escreva conteúdo
4. Adicione exemplos práticos
5. Adicione links relacionados
6. Atualize docs/README.md (índice)
7. Adicione referências cruzadas em outros docs

#### Regras de REMOVER Docs

**Quando Remover**:

- Feature foi completamente removida
- Doc foi consolidado em outro
- Informação está obsoleta e não aplicável

**Processo**:

1. **Nunca Delete Imediatamente**: Marque como deprecated primeiro
2. Adicione aviso no topo:

```markdown
> **⚠️ DEPRECATED**: Este documento está obsoleto.
> Veja [Novo Documento](link.md) para informação atualizada.
```

3. Após 1-2 versões, delete arquivo
4. Remova links para o doc em outros arquivos
5. Atualize docs/README.md
6. Adicione nota em CHANGELOG.md: "Removed: docs/old-file.md"

#### Regras de ATUALIZAR Docs Existentes

**Edições Menores** (typos, clareza, exemplos):

- Edite diretamente
- Não precisa mencionar em changelog

**Edições Significativas** (mudança de comportamento, novos conceitos):

- Edite conteúdo
- Adicione nota de atualização (se relevante):

```markdown
> **Atualizado em YYYY-MM-DD**: [Descrição da mudança]
```

- Adicione entrada em CHANGELOG.md

**Reestruturação Completa**:

1. Crie novo arquivo com `_new` suffix
2. Reescreva conteúdo
3. Revise e valide
4. Renomeie old → old_deprecated
5. Renomeie new → nome correto
6. Atualize links
7. Delete old após confirmar

### Validação de Documentação

#### Checklist Antes de Commit

- [ ] Todos os links funcionam (internos e externos)
- [ ] Code blocks têm linguagem especificada
- [ ] Exemplos foram testados
- [ ] Sem typos (use spell checker)
- [ ] Formatação markdown correta (.markdownlint.json)
- [ ] Referências cruzadas atualizadas
- [ ] docs/README.md reflete estrutura atual
- [ ] CHANGELOG.md atualizado (se aplicável)
- [ ] claude.md atualizado (se afeta agentes)

#### Linting

Use markdownlint (configurado em .markdownlint.json):

```bash
# Instalar (se disponível)
npm install -g markdownlint-cli

# Validar
markdownlint docs/**/*.md claude.md

# Auto-fix (cuidado!)
markdownlint --fix docs/**/*.md
```

Regras desabilitadas (ver .markdownlint.json):

- MD013 - Line length (linhas podem ser longas)
- MD033 - HTML inline (permitido quando necessário)
- MD041 - First line heading (nem sempre aplicável)

### Workflow de Atualização Completo

#### Exemplo: Adicionando Nova Feature

**Cenário**: Adicionei suporte a `triple_click` em tasks.

**Steps**:

1. **Identifique Impacto**:
   ```bash
   cd docs/
   grep -r "double_click" .
   # Encontrou: concepts.md, tasks-guide.md, api-reference.md
   ```

2. **Atualize Docs Específicos**:

   **tasks-guide.md**:
   ```markdown
   ## Tipos de Ação

   - `click` - Clique simples
   - `double_click` - Duplo clique
   - `triple_click` - Triplo clique (novo!)
   - `right_click` - Clique direito
   ```

   **concepts.md**:
   ```markdown
   ### Estrutura de uma Task

   action: "click" | "double_click" | "triple_click" | "right_click"
   ```

   **api-reference.md**:
   ```markdown
   #### find_and_click()

   **Parameters**:
   - action (str): "click" | "double_click" | "triple_click" | "right_click"
   ```

3. **Atualize CHANGELOG.md**:
   ```markdown
   ## [Unreleased]

   ### Added
   - Suporte a triplo clique (`triple_click`) em tasks e scripts
   ```

4. **Atualize claude.md**:
   ```markdown
   ## Funcionalidades Principais

   ### 2. Sistema de Tasks
   - Suporte a múltiplos tipos de clique (simples, duplo, triplo, direito)
   ```

5. **Valide**:
   - Teste exemplos
   - Verifique links
   - Markdownlint
   - Review completo

#### Exemplo: Corrigindo Bug Documentado

**Cenário**: Bug em multi-monitor foi corrigido (coordenadas negativas).

**Steps**:

1. **Atualize troubleshooting.md**:
   ```markdown
   ## Multi-Monitor Issues

   ### ~~Coordenadas Negativas~~

   **Status**: Resolvido na v2.0.1

   ~~Problema: Templates em monitor secundário (esquerda) não funcionavam.~~

   Solução: Atualizado para usar virtual screen corretamente.
   ```

2. **Atualize concepts.md** (se aplicável):
   ```markdown
   ## Multi-Monitor

   - Suporte completo a coordenadas negativas (monitor à esquerda)
   ```

3. **CHANGELOG.md**:
   ```markdown
   ## [2.0.1] - 2026-01-06

   ### Fixed
   - Corrigido suporte a coordenadas negativas em multi-monitor
   ```

4. **faq.md** (adicione se comum):
   ```markdown
   **P: Funciona com monitor à esquerda?**

   R: Sim! A partir da v2.0.1, suporte completo a múltiplos monitores.
   ```

### Templates para Docs Comuns

#### Novo Guia Tutorial

```markdown
# [Nome do Guia]

[Breve descrição em 1-2 parágrafos]

## Pré-requisitos

- Item 1
- Item 2

## [Seção Principal 1]

### Conceito

Explicação...

### Exemplo Prático

```code
exemplo
```

## [Seção Principal 2]

...

## Troubleshooting

### Problema Comum 1

**Sintoma**: Descrição

**Solução**: Passos

## Próximos Passos

- [Doc Relacionado](link.md)

## Referências

- [API](api-reference.md)
```

#### Nova Entrada de FAQ

```markdown
**P: [Pergunta]?**

R: [Resposta clara e concisa]

[Exemplo de código ou comando, se aplicável]

```bash
comando exemplo
```

Veja também: [Doc Relacionado](link.md)
```

#### Nova Entrada de Troubleshooting

```markdown
### [Nome do Problema]

**Sintomas**:
- Sintoma 1
- Sintoma 2

**Causa Provável**:
Explicação técnica breve.

**Solução**:

1. Passo 1
   ```bash
   comando
   ```

2. Passo 2

3. Passo 3

**Verificação**:
Como confirmar que foi resolvido.

**Se Não Resolver**:
- Alternativa 1
- Alternativa 2
- Link para support/issue tracker
```

---

## 🤖 INSTRUÇÕES ESPECÍFICAS PARA AGENTES

### Ao Modificar Código

**SEMPRE**:

1. Identifique docs impactados
2. Atualize docs relevantes NA MESMA SESSÃO
3. Valide exemplos de código em docs
4. Atualize CHANGELOG.md se user-facing
5. Mencione mudanças em docs no commit/resposta

**NUNCA**:

- Deixe docs desatualizados "para depois"
- Assuma que mudança é "pequena demais" para docs
- Crie inconsistências entre código e docs

### Ao Responder Perguntas

**Use a Documentação**:

1. Busque primeiro em docs/ (Read tool)
2. Referencie docs em respostas: "Veja [Guia X](docs/X.md)"
3. Se doc não existe, sugira criar

**Atualize se Necessário**:

- Se resposta revela gap em docs → adicione em FAQ
- Se problema comum → adicione em troubleshooting
- Se conceito não documentado → adicione em concepts.md

### Ao Adicionar Features

**Processo Obrigatório**:

1. Implemente feature
2. Teste funcionamento
3. **Escreva/atualize docs**:
   - Guia relevante (cli/gui/tasks/scripts)
   - Exemplos práticos
   - API reference (se aplicável)
   - Troubleshooting (problemas conhecidos)
4. Atualize CHANGELOG.md
5. Atualize claude.md (se afeta agentes)
6. Valide exemplos
7. Commit tudo junto

### Ao Fazer Refatoração

**Se Refatoração Interna** (não afeta usuário):

- Atualize apenas architecture.md e api-reference.md (se necessário)
- Não precisa changelog

**Se Refatoração Afeta API/Uso**:

- Trate como "mudança de comportamento"
- Atualize todos os docs relevantes
- Deprecation notice se aplicável
- CHANGELOG.md: seção "Changed"

### Verificação Final

Antes de considerar tarefa completa:

```text
✅ Código funciona
✅ Testes passam (se houver)
✅ Docs atualizados
✅ Exemplos testados
✅ Links funcionam
✅ CHANGELOG.md atualizado (se aplicável)
✅ claude.md atualizado (se afeta agentes)
✅ Sem markdown warnings (.markdownlint.json)
```

---

## Referências Rápidas

### Comandos Úteis

```bash
# Buscar em docs
grep -r "termo" docs/

# Listar todos os docs
ls docs/*.md

# Validar markdown (se markdownlint instalado)
markdownlint docs/**/*.md

# Contar linhas de doc
wc -l docs/*.md
```

### Links Internos Importantes

- [Documentação Principal](../docs/README.md)
- [Instalação](../docs/installation.md)
- [Início Rápido](../docs/quickstart.md)
- [Conceitos](../docs/concepts.md)
- [FAQ](../docs/faq.md)
- [Changelog](../CHANGELOG.md)

### Contato e Suporte

- **GitHub Issues**: Para bugs e feature requests
- **Docs**: Sempre consulte primeiro
- **Claude.md**: Para instruções aos agentes (este arquivo)

---

**Manutenção deste documento**: Atualize sempre que:

- Estrutura do projeto mudar
- Novos padrões forem estabelecidos
- Regras de documentação forem modificadas
- Workflow de desenvolvimento mudar

**Última Revisão Completa**: 2026-01-13

---

## Histórico de Correções macOS (v3.1)

### Correções Retina/DPI

1. **Captura de região** (`capture_overlay.py`):
   - Corrigido cálculo de escala para telas Retina
   - Coordenadas lógicas são convertidas para pixels físicos antes do recorte

2. **Clique em posição correta** (`image_matcher.py`):
   - Coordenadas do template matching (pixels físicos) são convertidas para pontos lógicos
   - CGEvent recebe coordenadas em pontos lógicos corretamente

3. **Suporte a fullscreen** (`window_utils.py`):
   - `_get_all_windows_info` agora inclui janelas de todos os Spaces
   - `get_windows_by_process` busca em todos os Spaces
   - `is_window_visible` considera janelas fullscreen

### Arquivos Modificados

- `core/image_matcher.py` - Conversão pixels→pontos para cliques
- `core/window_utils.py` - Suporte a fullscreen/Spaces
- `ui_qt/components/capture_overlay.py` - Captura Retina correta
