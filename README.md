# ImageClicker

Ferramenta de automação de cliques baseada em reconhecimento de imagem para Windows. Suporta execução paralela de múltiplas tasks em diferentes janelas simultaneamente.

![Version](https://img.shields.io/badge/version-2.0.0-blue)
![Python](https://img.shields.io/badge/python-3.8+-green)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey)

## Funcionalidades

- ✅ **Template Matching**: Reconhecimento de imagem via pyautogui + OpenCV
- ✅ **Multi-Task Paralelo**: Execute várias automações simultaneamente
- ✅ **Multi-Window**: Cada task pode monitorar janela diferente
- ✅ **Scripts Sequenciais**: Workflows complexos em JSON
- ✅ **GUI Moderna**: Interface gráfica com CustomTkinter
- ✅ **CLI Poderosa**: Comandos para automação rápida
- ✅ **Multi-Monitor**: Suporte completo a múltiplos monitores
- ✅ **Captura Visual**: Overlay fullscreen com preview em tempo real

## Instalação Rápida

```bash
# Clone o repositório
git clone https://github.com/user/ImageClicker.git
cd ImageClicker

# Instale dependências
pip install pyautogui pillow opencv-python customtkinter pywin32 numpy

# Execute a GUI
python gui.py
```

[Ver guia de instalação completo](docs/installation.md)

## Uso Rápido

### GUI

```bash
python gui.py
```

1. Pressione `Ctrl+Shift+C` para capturar um template
2. Adicione uma task na aba "📋 Tasks"
3. Clique "▶" para iniciar
4. Pronto! Automação rodando

### CLI

```bash
# Capturar template
python iclick.py capture meu_botao

# Clicar no template
python iclick.py click meu_botao

# Clicar em janela específica
python iclick.py click meu_botao --window "Chrome*"

# Executar script
python iclick.py run meu_script

# Executar tasks paralelas
python iclick.py tasks
```

[Ver guia de início rápido](docs/quickstart.md)

## Documentação

- 📖 [Documentação Completa](docs/README.md)
- 🚀 [Início Rápido](docs/quickstart.md)
- 💡 [Conceitos Básicos](docs/concepts.md)
- 🖥️ [Guia CLI](docs/cli-guide.md)
- 🖱️ [Guia GUI](docs/gui-guide.md)
- ❓ [FAQ](docs/faq.md)
- 🔧 [Troubleshooting](docs/troubleshooting.md)

## Exemplos

### Task Paralela (GUI)

Monitorar múltiplas janelas simultaneamente:

- Task 1: Refresh no Chrome a cada 10s
- Task 2: Save no Excel a cada 5s
- Task 3: Backup no Notepad a cada 60s

### Script Sequencial (CLI)

```json
{
  "name": "login_automatico",
  "description": "Faz login na aplicação",
  "actions": [
    {"type": "click", "image": "campo_usuario"},
    {"type": "type", "text": "meu_usuario"},
    {"type": "press", "key": "tab"},
    {"type": "type", "text": "minha_senha"},
    {"type": "click", "image": "botao_entrar"}
  ]
}
```

## Requisitos

- Windows 10+
- Python 3.8+
- 4GB RAM (recomendado: 8GB)

## Estrutura do Projeto

```text
ImageClicker/
├── iclick.py           # CLI
├── gui.py              # GUI
├── images/             # Templates
├── scripts/            # Scripts JSON
├── tasks.json          # Tasks paralelas
├── docs/               # Documentação
└── claude.md           # Instruções para agentes
```

## Tecnologias

- **pyautogui**: Automação de mouse/teclado
- **OpenCV**: Reconhecimento de imagem
- **CustomTkinter**: Interface gráfica moderna
- **pywin32**: Controle de janelas Windows

## Licença

Projeto pessoal. Use com responsabilidade.

## Contribuindo

Veja [CONTRIBUTING.md](CONTRIBUTING.md) para informações sobre como contribuir.

## Changelog

Veja [CHANGELOG.md](CHANGELOG.md) para histórico de mudanças.

## Suporte

- 📚 [Documentação](docs/README.md)
- ❓ [FAQ](docs/faq.md)
- 🐛 [Report Bugs](https://github.com/user/ImageClicker/issues)

---

**Versão**: 2.0.0 (Multi-Task & Multi-Window)
**Última Atualização**: 2026-01-06
