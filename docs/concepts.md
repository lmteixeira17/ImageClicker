# Conceitos Básicos

Entenda os conceitos fundamentais do ImageClicker.

## Template Matching

### O que é?

Template Matching é a técnica de encontrar uma imagem pequena (template) dentro de uma imagem maior (screenshot).

### Como Funciona?

1. **Captura do Template**: Você seleciona uma região da tela
2. **Screenshot**: O programa captura a tela (ou janela)
3. **Comparação**: Algoritmo busca o template no screenshot
4. **Match Score**: Calcula similaridade (0-100%)
5. **Threshold**: Se score >= threshold, considera encontrado
6. **Clique**: Clica no centro do template encontrado

### Métodos de Reconhecimento

#### pyautogui (Tela Toda)

- Busca em toda a tela (todos os monitores)
- Threshold: 90% (CONFIDENCE = 0.9)
- Mais lento, mais simples
- Usado na CLI (modo padrão)

#### OpenCV (Janela Específica)

- Busca apenas em janela selecionada
- Threshold: 85% (0.85 no cv2.matchTemplate)
- Mais rápido, mais preciso
- Usado na GUI e CLI (com --window)
- Método: TM_CCOEFF_NORMED

### Fatores que Afetam Reconhecimento

**Positivos** (melhoram match):

- Elementos com cores únicas
- Formas distintas
- Tamanho adequado (não muito pequeno/grande)
- Sem animação ou mudança
- Mesma resolução

**Negativos** (dificultam match):

- Elementos genéricos (texto simples)
- Animações
- Mudança de cor/tema
- Resolução diferente
- Elementos parcialmente cobertos

## Templates

### O que são?

Templates são imagens PNG que representam elementos da interface que você quer clicar.

### Estrutura

- Armazenados em: `images/`
- Formato: PNG
- Nomenclatura: `nome_descritivo.png` (snake_case)
- Típicamente < 50KB

### Tipos de Templates

**Botões**:

- Tamanho: Pequeno a médio
- Características: Formas definidas, texto/ícone único
- Exemplo: `botao_salvar.png`, `btn_refresh.png`

**Ícones**:

- Tamanho: Pequeno
- Características: Símbolos únicos
- Exemplo: `icone_config.png`, `menu_icon.png`

**Texto**:

- Tamanho: Pequeno a médio
- Características: Fonte única, cor distinta
- Exemplo: `titulo_pagina.png`
- ⚠️ Sensível a mudanças de fonte/DPI

**Regiões**:

- Tamanho: Médio a grande
- Características: Combinação de elementos
- Exemplo: `area_login.png`

### Boas Práticas de Captura

```text
✅ BOM:
- Capturar apenas o elemento necessário
- Incluir padding único (bordas, sombras)
- Usar cores/formas distintas
- Testar após captura

❌ RUIM:
- Capturar área muito grande
- Incluir fundo genérico
- Elementos com animação
- Texto pequeno/genérico
```

## Tasks (Sistema Paralelo)

### O que são?

Tasks são automações que rodam em paralelo, cada uma monitorando uma janela específica.

### Estrutura de uma Task

```python
Task:
  id: 1                          # ID único
  window_title: "Chrome*"        # Janela alvo (wildcard)
  image_name: "refresh_btn"      # Template (sem .png)
  action: "click"                # Tipo de clique
  repeat: True                   # Repetir?
  interval: 10.0                 # Segundos entre repetições
  enabled: True                  # Habilitada?
```

### Ciclo de Vida de uma Task

1. **Criação**: Usuário adiciona via GUI
2. **Persistência**: Salva em `tasks.json`
3. **Carregamento**: Lê de `tasks.json` ao abrir GUI
4. **Execução**: Thread dedicada por task
5. **Loop**:
   - Encontra janela (por título)
   - Captura screenshot da janela
   - Busca template (OpenCV)
   - Clica se encontrar
   - Aguarda intervalo
   - Repete (se repeat=True)
6. **Parada**: Stop event sinaliza thread para terminar

### Task Manager

Gerencia execução paralela:

- ThreadPoolExecutor para threads
- Dicionário de tasks por ID
- Stop events por task (parada individual)
- Callbacks para UI (status, logs)
- Persistência em JSON

### Estados de uma Task

- `Aguardando`: Inicial
- `🔍 Buscando...`: Procurando template
- `✓ 95%`: Encontrado e clicado (com % de match)
- `✗ 78%`: Não encontrado (match < 85%)
- `⚠ Janela?`: Janela não encontrada
- `⚠ Img?`: Template não existe
- `⏳ 5s`: Aguardando próxima execução
- `Parado`: Task parada

## Scripts (Sistema Sequencial)

### O que são?

Scripts são sequências de ações executadas uma após a outra, definidas em JSON.

### Estrutura de um Script

```json
{
  "name": "nome_do_script",
  "description": "O que o script faz",
  "actions": [
    { "type": "click", "image": "btn1" },
    { "type": "wait", "seconds": 2 },
    { "type": "type", "text": "Hello" },
    { "type": "hotkey", "keys": ["ctrl", "s"] }
  ]
}
```

### Tipos de Ações

| Tipo | Descrição | Parâmetros |
|------|-----------|------------|
| `click` | Clique simples | image, wait, required |
| `double_click` | Duplo clique | image, wait, required |
| `right_click` | Clique direito | image, wait, required |
| `type` | Digitar texto | text, interval |
| `press` | Pressionar tecla | key |
| `hotkey` | Atalho (combo) | keys (array) |
| `wait` | Aguardar tempo | seconds |
| `wait_for` | Aguardar imagem | image, timeout |

### Fluxo de Execução

1. Carrega script JSON
2. Valida estrutura
3. Executa ações em ordem
4. Se action.required=True e falhar: aborta
5. Senão: continua para próxima ação
6. Log de cada passo

### Diferença: Tasks vs Scripts

| Aspecto | Tasks | Scripts |
|---------|-------|---------|
| Execução | Paralela | Sequencial |
| Propósito | Monitoramento contínuo | Workflow complexo |
| Janela | Específica (por task) | Tela toda |
| Complexidade | Baixa (1 ação) | Alta (N ações) |
| Loop | Built-in (repeat) | Manual (chamar script) |
| Interface | GUI (tasks.json) | CLI + JSON manual |

**Use Tasks quando:**

- Múltiplas janelas simultâneas
- Monitoramento contínuo
- Ações repetitivas simples

**Use Scripts quando:**

- Workflow multi-step
- Sequência complexa
- Combinação de cliques e teclado
- Deploy, formulários, CI/CD

## Wildcards de Janela

Usados para encontrar janelas por título parcial.

### Sintaxe

- `*` = Qualquer caractere (0 ou mais)
- Match é case-insensitive

### Exemplos

| Pattern | Matches |
|---------|---------|
| `"Chrome*"` | "Chrome", "Chrome - Google", "Chrome Settings" |
| `"*YouTube*"` | "Watch - YouTube", "YouTube Music", "my video - YouTube" |
| `"*- Notepad"` | "file.txt - Notepad", "Untitled - Notepad" |
| `"Excel"` | "Excel" (exato) |

### Algoritmo de Busca

```python
if pattern.startswith("*") and pattern.endswith("*"):
    # Contém
    match = pattern_text in window_title
elif pattern.startswith("*"):
    # Termina com
    match = window_title.endswith(pattern_text)
elif pattern.endswith("*"):
    # Começa com
    match = window_title.startswith(pattern_text)
else:
    # Exato ou contém
    match = pattern_text == window_title or pattern_text in window_title
```

## Multi-Monitor

### Suporte

ImageClicker suporta múltiplos monitores nativamente.

### Virtual Screen

- Windows trata múltiplos monitores como "virtual screen"
- Coordenadas podem ser negativas (monitor à esquerda)
- Overlay de captura cobre todas as telas

### Implementação

**Captura**:

```python
# Detecta virtual screen bounds
virtual_left = user32.GetSystemMetrics(76)    # SM_XVIRTUALSCREEN
virtual_top = user32.GetSystemMetrics(77)     # SM_YVIRTUALSCREEN
virtual_width = user32.GetSystemMetrics(78)   # SM_CXVIRTUALSCREEN
virtual_height = user32.GetSystemMetrics(79)  # SM_CYVIRTUALSCREEN

# ImageGrab com all_screens=True
img = ImageGrab.grab(rect, all_screens=True)
```

**Busca**:

- pyautogui: Busca em todos os monitores automaticamente
- OpenCV: Busca apenas na janela (independente de monitor)

## Threading e Concorrência

### Modelo de Threads

```text
Main Thread (GUI)
│
├─ ThreadPoolExecutor
│  ├─ Task #1 Thread
│  ├─ Task #2 Thread
│  └─ Task #N Thread
│
└─ Background Operations
   ├─ Image capture (blocks)
   └─ Window refresh
```

### Thread Safety

**Locks**:

```python
self._lock = threading.Lock()

with self._lock:
    # Acesso a self.tasks (Dict compartilhado)
```

**Stop Events**:

```python
stop_event = threading.Event()

# Thread
while not stop_event.is_set():
    # Work...

# Controller
stop_event.set()  # Sinaliza parada
```

**GUI Callbacks**:

```python
# De thread para GUI (thread-safe)
self.after(0, lambda: self._update_ui())
```

### Considerações

- Cada task = 1 thread
- Máximo recomendado: < 10 tasks paralelas
- Tasks não coordenam entre si
- Possível conflito se duas tasks clicam no mesmo lugar

## Persistência

### Arquivos de Estado

**tasks.json**:

- Salvo automaticamente ao modificar tasks na GUI
- Carregado ao abrir GUI
- Versionável (pode commitar no Git)
- Estrutura: Array de objetos Task

**Não Persistido**:

- Templates (imagens em `images/`)
- Scripts (JSON em `scripts/`)
- Logs
- Estado de execução (rodando/parado)

### Format de tasks.json

```json
[
  {
    "id": 1,
    "window_title": "Chrome*",
    "image_name": "refresh",
    "action": "click",
    "repeat": true,
    "interval": 10.0,
    "enabled": true
  }
]
```

## Próximos Passos

- Explore [CLI Guide](cli-guide.md) para uso da linha de comando
- Veja [GUI Guide](gui-guide.md) para interface gráfica
- Aprenda [Tasks Guide](tasks-guide.md) para automação avançada
- Leia [Best Practices](best-practices.md) para otimizar uso
