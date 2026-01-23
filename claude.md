# ImageClicker - Instruções para Agentes Claude

## Visão Geral

ImageClicker é uma ferramenta de automação de cliques baseada em reconhecimento de imagem para **macOS**. Suporta execução paralela de múltiplas tasks em diferentes janelas simultaneamente.

**Versão**: 3.2 (macOS Native)
**Última Atualização**: 2026-01-23
**Plataforma**: macOS (Quartz/AppKit/PyObjC/mss)
**Repositório**: https://github.com/lmteixeira17/ImageClicker

## Instalação e Execução

### Pré-requisitos

- Python 3.8+ (recomendado: Python 3.11+)
- macOS 10.15+ (Catalina ou superior)
- Permissões de **Acessibilidade** (obrigatório para cliques)
- Permissões de **Gravação de Tela** (obrigatório para captura)

### Instalação Rápida

```bash
# 1. Clonar o repositório
git clone https://github.com/lmteixeira17/ImageClicker.git
cd ImageClicker

# 2. Criar ambiente virtual (OBRIGATÓRIO no macOS moderno)
python3 -m venv venv

# 3. Ativar ambiente virtual
source venv/bin/activate

# 4. Instalar dependências
pip install -r requirements.txt
```

### Instalação Local (sem clone)

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
IMAGECLICKER_DIR="/caminho/para/ImageClicker"
alias iclick='"$IMAGECLICKER_DIR/venv/bin/python3" "$IMAGECLICKER_DIR/iclick.py"'
alias imageclicker='"$IMAGECLICKER_DIR/venv/bin/python3" "$IMAGECLICKER_DIR/app_qt.py"'
```

Depois: `source ~/.zshrc`

### Execução

```bash
# GUI (interface gráfica)
imageclicker
# ou
./ImageClicker.command

# CLI (linha de comando)
iclick --help
iclick tasks
iclick capture nome_botao
# ou
./iclick.command tasks
```

### Scripts de Execução macOS

O projeto inclui scripts `.command` para execução fácil:

| Script | Descrição |
|--------|-----------|
| `ImageClicker.command` | Abre a GUI (duplo clique no Finder) |
| `iclick.command` | Abre CLI interativo |
| `install.command` | Instala dependências automaticamente |

Para usar: duplo clique no Finder ou `chmod +x *.command` e execute.

### App em /Applications (v3.2)

O ImageClicker pode ser instalado como app em `/Applications/ImageClicker.app`:

```bash
# O app é um launcher que abre via Terminal para herdar permissões
/Applications/ImageClicker.app
```

**Como funciona o launcher**:
- Verifica se o app já está rodando (evita múltiplas instâncias)
- Abre o Terminal e executa `app_qt.py` com o venv correto
- Herda permissões de Acessibilidade e Gravação de Tela do Terminal

**Arquivo do launcher**: `/Applications/ImageClicker.app/Contents/MacOS/ImageClicker`

```bash
#!/bin/bash
# Verificar se já está rodando
if pgrep -f "app_qt.py" > /dev/null; then
    osascript -e 'tell application "System Events" to set frontmost of (first process whose name contains "Python") to true'
    exit 0
fi
# Abrir via Terminal para herdar permissões
osascript <<EOF
tell application "Terminal"
    activate
    do script "cd '/caminho/para/ImageClicker' && ./venv/bin/python3 app_qt.py"
end tell
EOF
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
├── iclick.command         # Launcher macOS (CLI)
├── ImageClicker.command   # Launcher macOS (GUI)
├── install.command        # Instalador de dependências (macOS)
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
│   ├── theme.py           # Tema glassmorphism (dark/light)
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
│       ├── capture_overlay.py # Overlay de captura de tela (Retina-aware)
│       └── icons.py       # Ícones Unicode
├── docs/                  # Documentação estruturada
│   └── ...                # Guias e referências
├── claude.md              # Este arquivo (instruções para agentes)
├── CHANGELOG.md           # Histórico de mudanças
├── requirements.txt       # Dependências Python
├── .imageclicker_config.json # Config do usuário (auto-gerado)
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

| API | Função | Notas |
|-----|--------|-------|
| `CGWindowListCopyWindowInfo` | Listar janelas | Inclui todos os Spaces |
| `mss` (biblioteca) | Capturar tela | Substitui CGWindowListCreateImage (v3.2) |
| `CGEventCreateMouseEvent` | Criar eventos de mouse | - |
| `CGEventPost` | Enviar cliques | Espera pontos lógicos |
| `NSScreen` | Info de monitores | DPI e escala Retina |
| `NSWorkspace` | Listar aplicativos | Processos em execução |

> **Nota v3.2**: A captura de tela agora usa `mss` em vez de `CGWindowListCreateImage` para evitar vazamento de memória. A biblioteca `mss` captura a região da tela onde a janela está posicionada.

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
| Janela normal (mesmo Space) | Sim |
| Janela fullscreen (Space dedicado, ativo) | Sim |
| Janela em outro Space (não visível) | Não* |
| Janela minimizada | Não |

> *Limitação do macOS: não é possível capturar ou clicar em janelas de Spaces não ativos.

## Funcionalidades Principais

### 1. Template Matching

- **OpenCV**: Busca em janela específica (threshold configurável por task, default 85%)
- **Multi-instância**: Busca em TODAS as janelas do mesmo processo (ex: 3 janelas do Safari)
- Suporte multi-monitor via virtual screen
- Escalonamento automático de DPI
- **Conversão Retina automática**: Coordenadas são convertidas corretamente

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
# Exemplo de conversão (interno - image_matcher.py)
# Template matching retorna coordenadas em pixels físicos
pixel_x = max_loc[0] + w // 2
pixel_y = max_loc[1] + h // 2

# Converter para pontos lógicos para CGEvent
window_rect = get_window_rect(window_id)
win_width_points = window_rect[2] - window_rect[0]
img_height, img_width = screenshot_gray.shape

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

```python
# Exemplo de conversão de captura (interno - capture_overlay.py)
# Coordenadas da seleção estão em pontos lógicos
screen_x, screen_y = selection_start

# Calcular fator de escala Retina
scale_x = img_width / win_width  # ~2.0 em Retina
scale_y = img_height / win_height

# Converter para pixels físicos para recorte
rel_x = int((screen_x - win_left) * scale_x)
rel_y = int((screen_y - win_top) * scale_y)
region_width = int(width * scale_x)
region_height = int(height * scale_y)
```

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
- **Tema dark/light**: Toggle na interface

## Comandos CLI Principais

```bash
# Usando alias (recomendado)
iclick capture <nome>      # Captura template
iclick click <nome>        # Clica no template
iclick tasks               # Executa tasks.json
iclick list                # Lista recursos

# Ou diretamente
python iclick.py capture <nome>

# Clique em janela específica
python iclick.py click <nome> --window "App"

# Outros
python iclick.py wait <nome>     # Espera e clica
python iclick.py run <script>    # Executa script JSON
python iclick.py tasks           # Executa tasks.json
python iclick.py list            # Lista recursos
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

**Solução**: Verifique se está usando a versão mais recente do `capture_overlay.py` com suporte a escala Retina (v3.1+).

### Clique na posição errada

**Sintoma**: Template é encontrado, mas o clique acontece em lugar errado.

**Causa**: Coordenadas em pixels físicos não convertidas para pontos lógicos.

**Solução**: Atualize para v3.1+ que inclui conversão automática em `image_matcher.py`.

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
- Windows: `Antigravity.exe` → macOS: `Antigravity`

### GitHub CLI não autenticado

**Sintoma**: Erro ao usar `gh` commands.

**Solução**:
```bash
gh auth login
# Seguir instruções interativas
# Ou usar token:
gh auth login --with-token <<< "ghp_seu_token_aqui"
```

### Vazamento de memória (versões anteriores a 3.2)

**Sintoma**: Python consome 10+ GB de RAM após rodar por algum tempo.

**Causa**: `CGWindowListCreateImage` do PyObjC não liberava objetos CoreGraphics corretamente.

**Solução**: Atualize para v3.2+ que usa `mss` para captura de tela.

**Detalhes técnicos**:
- Antes (v3.1): `CGWindowListCreateImage` → vazamento de ~500MB/minuto
- Depois (v3.2): `mss.grab()` → memória estável em ~200MB

Se ainda usar v3.1, a única solução é reiniciar o app periodicamente.

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

## Manutenção da Documentação

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

---

## Instruções Específicas para Agentes

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
Código funciona
Testes passam (se houver)
Docs atualizados
Exemplos testados
Links funcionam
CHANGELOG.md atualizado (se aplicável)
claude.md atualizado (se afeta agentes)
```

---

## Referências Rápidas

### Comandos Úteis

```bash
# Executar GUI
imageclicker
# ou
./ImageClicker.command

# Executar CLI
iclick tasks
iclick capture <nome>

# Buscar em docs
grep -r "termo" docs/

# Listar todos os docs
ls docs/*.md

# Git operations
git status
git add -A
git commit -m "mensagem"
git push
```

### Links Internos Importantes

- [Documentação Principal](docs/README.md)
- [Instalação](docs/installation.md)
- [Início Rápido](docs/quickstart.md)
- [Conceitos](docs/concepts.md)
- [FAQ](docs/faq.md)
- [Changelog](CHANGELOG.md)

### Contato e Suporte

- **GitHub Issues**: https://github.com/lmteixeira17/ImageClicker/issues
- **Docs**: Sempre consulte primeiro
- **Claude.md**: Para instruções aos agentes (este arquivo)

---

**Manutenção deste documento**: Atualize sempre que:

- Estrutura do projeto mudar
- Novos padrões forem estabelecidos
- Regras de documentação forem modificadas
- Workflow de desenvolvimento mudar

**Última Revisão Completa**: 2026-01-23

---

## Histórico de Correções macOS (v3.1)

### Correções Retina/DPI

1. **Captura de região** (`capture_overlay.py`):
   - Corrigido cálculo de escala para telas Retina
   - Coordenadas lógicas são convertidas para pixels físicos antes do recorte
   - Método `capture_window_region_quartz` atualizado

2. **Clique em posição correta** (`image_matcher.py`):
   - Coordenadas do template matching (pixels físicos) são convertidas para pontos lógicos
   - CGEvent recebe coordenadas em pontos lógicos corretamente
   - Função `find_and_click` atualizada com conversão automática

3. **Suporte a fullscreen** (`window_utils.py`):
   - `_get_all_windows_info` agora inclui janelas de todos os Spaces
   - Usa `kCGWindowListOptionAll` em vez de `kCGWindowListOptionOnScreenOnly`
   - `get_windows_by_process` busca em todos os Spaces
   - `is_window_visible` considera janelas fullscreen

### Arquivos Modificados na v3.1

| Arquivo | Mudança |
|---------|---------|
| `core/image_matcher.py` | Conversão pixels→pontos para cliques |
| `core/window_utils.py` | Suporte a fullscreen/Spaces |
| `ui_qt/components/capture_overlay.py` | Captura Retina correta |
| `tasks.json` | Nomes de processo sem `.exe` |
| `claude.md` | Documentação completa macOS |
| `CHANGELOG.md` | Histórico de mudanças v3.1 |

### Diferenças Windows vs macOS

| Aspecto | Windows | macOS |
|---------|---------|-------|
| Nomes de processo | `Code.exe` | `Code` |
| Clique fantasma | PostMessage (não move cursor) | CGEvent (move cursor momentaneamente) |
| Coordenadas | Sempre pixels | Pontos lógicos (CGEvent) vs Pixels (captura) |
| Fullscreen | Janela normal | Space dedicado |
| Permissões | Nenhuma especial | Acessibilidade + Gravação de Tela |
| Ambiente Python | Direto ou venv | venv obrigatório (macOS moderno) |

---

## Histórico de Correções macOS (v3.2)

### Correção de Vazamento de Memória

**Problema**: O app consumia 40+ GB de RAM após rodar por alguns minutos.

**Causa raiz**: `CGWindowListCreateImage` do PyObjC/Quartz não liberava objetos CoreGraphics corretamente. Mesmo usando `NSAutoreleasePool`, `del`, e `gc.collect()`, a memória continuava vazando.

**Solução implementada**: Substituição de `CGWindowListCreateImage` pela biblioteca `mss` para captura de tela.

### Mudanças em `core/image_matcher.py`

```python
# ANTES (v3.1) - vazava memória
from Quartz import CGWindowListCreateImage
cg_image = CGWindowListCreateImage(...)  # PyObjC não liberava

# DEPOIS (v3.2) - memória estável
import mss
sct = mss.mss()
screenshot = sct.grab(monitor)  # Python puro, sem vazamento
```

### Funções adicionadas

1. **`_get_mss()`**: Retorna instância global do mss (singleton)
2. **`_get_main_display_scale()`**: Detecta fator de escala Retina via `NSScreen.backingScaleFactor()`

### Tratamento de Retina

A captura com `mss` requer ajuste para telas Retina:
- `mss` recebe coordenadas em pontos lógicos
- Retorna imagem em pixels físicos (2x em Retina)
- O código redimensiona automaticamente para manter compatibilidade com templates

### Arquivos Modificados na v3.2

| Arquivo | Mudança |
|---------|---------|
| `core/image_matcher.py` | Substituição de CGWindowListCreateImage por mss |
| `core/task_manager.py` | Adição de gc.collect() periódico (precaução) |
| `/Applications/ImageClicker.app` | Launcher via Terminal para permissões |
| `CLAUDE.md` | Documentação atualizada |

### Resultados de Memória

| Métrica | v3.1 (CGWindowListCreateImage) | v3.2 (mss) |
|---------|-------------------------------|------------|
| Memória inicial | ~1.8 GB | ~200 MB |
| Após 5 minutos | 5-10 GB | ~200 MB |
| Após 30 minutos | 40+ GB (crash) | ~200 MB |
| Tendência | Crescente (vazamento) | **Estável** |

### Limitação da nova abordagem

A biblioteca `mss` captura a **região da tela** onde a janela está, não a janela em si. Isso significa que:
- Se outra janela estiver cobrindo, a captura incluirá a janela sobreposta
- Funciona bem para prompts/dialogs que ficam em primeiro plano
- Não funciona para janelas cobertas (diferente de `CGWindowListCreateImage`)

Para o caso de uso principal (clicar em prompts do Claude Code/VSCode), isso não é problema pois os prompts sempre aparecem em primeiro plano.

---

**Última Revisão Completa**: 2026-01-23
