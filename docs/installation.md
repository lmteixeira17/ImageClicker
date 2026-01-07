# Instalação

## Requisitos

### Sistema Operacional

- Windows 10 ou superior (requerido para funcionalidades completas)
- Python 3.8 ou superior

### Hardware

- Mínimo: 4GB RAM, processador dual-core
- Recomendado: 8GB RAM, processador quad-core
- Suporte a múltiplos monitores

## Dependências Python

### Instalação Completa

```bash
pip install pyautogui pillow opencv-python customtkinter pywin32 numpy
```

### Dependências Individuais

| Pacote | Versão | Propósito |
|--------|--------|-----------|
| pyautogui | >= 0.9.53 | Automação de mouse/teclado |
| pillow | >= 9.0.0 | Manipulação de imagens |
| opencv-python | >= 4.5.0 | Reconhecimento de imagem |
| customtkinter | >= 5.0.0 | Interface gráfica moderna |
| pywin32 | >= 300 | Controle de janelas Windows |
| numpy | >= 1.21.0 | Operações com arrays |

### Instalação Mínima (CLI apenas)

```bash
pip install pyautogui pillow
```

Nota: Funcionalidades de janela específica e GUI não estarão disponíveis.

## Instalação do Projeto

### Opção 1: Clone do Repositório

```bash
git clone https://github.com/user/ImageClicker.git
cd ImageClicker
pip install -r requirements.txt
```

### Opção 2: Download Manual

1. Baixe o ZIP do projeto
2. Extraia para uma pasta de sua escolha
3. Navegue até a pasta no terminal
4. Execute: `pip install -r requirements.txt`

## Verificação da Instalação

### Testar CLI

```bash
python iclick.py help
```

Saída esperada: Menu de ajuda com comandos disponíveis

### Testar GUI

```bash
python gui.py
```

Saída esperada: Janela da aplicação se abre

### Verificar Dependências

```bash
python -c "import pyautogui, PIL, cv2, customtkinter, win32gui; print('OK')"
```

Saída esperada: `OK`

## Estrutura de Diretórios

Após instalação, a estrutura será:

```text
ImageClicker/
├── iclick.py           # CLI principal
├── gui.py              # GUI principal
├── images/             # Templates (criado automaticamente)
├── scripts/            # Scripts JSON (criado automaticamente)
├── tasks.json          # Tasks (criado pela GUI)
├── docs/               # Documentação
├── iclick.bat          # Launcher Windows (CLI)
├── ImageClicker.bat    # Launcher Windows (GUI)
├── final_icon.ico      # Ícone
└── requirements.txt    # Dependências
```

## Configuração Inicial

### 1. Verificar Paths

Os paths são hard-coded no código. Se necessário, edite:

**iclick.py**:

```python
BASE_DIR = Path(r"C:\Users\SEU_USUARIO\...\ImageClicker")
```

**gui.py**:

```python
BASE_DIR = Path(r'C:\Users\SEU_USUARIO\...\ImageClicker')
```

### 2. Testar Captura

```bash
python iclick.py capture teste
```

Siga as instruções para capturar uma região de teste.

### 3. Primeira Task (GUI)

1. Execute `python gui.py`
2. Clique em "📸 Capturar" ou Ctrl+Shift+C
3. Capture um elemento da tela
4. Adicione uma task na aba Tasks
5. Clique em "▶" para testar

## Solução de Problemas Comuns

### Erro: Module not found

```bash
pip install <nome_do_modulo>
```

### Erro: win32gui não disponível

Instale pywin32:

```bash
pip install pywin32
```

Após instalação, execute:

```bash
python Scripts/pywin32_postinstall.py -install
```

### GUI não abre

Verifique customtkinter:

```bash
pip install --upgrade customtkinter
```

### OpenCV não funciona

Reinstale opencv-python:

```bash
pip uninstall opencv-python
pip install opencv-python
```

## Próximos Passos

- Leia o [Guia de Início Rápido](quickstart.md)
- Explore os [Conceitos Básicos](concepts.md)
- Veja exemplos no [CLI Guide](cli-guide.md)

## Desinstalação

```bash
pip uninstall pyautogui pillow opencv-python customtkinter pywin32 numpy
```

Delete a pasta do projeto manualmente.
