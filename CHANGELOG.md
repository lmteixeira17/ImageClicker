# Changelog

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Versionamento Semântico](https://semver.org/lang/pt-BR/).

## [Unreleased]

### Added

- Sistema de documentação estruturada em `docs/`
- Guias completos: instalação, quickstart, conceitos
- Instruções detalhadas de manutenção de documentação no claude.md
- Configuração markdownlint (.markdownlint.json)

## [2.0.0] - 2026-01-06

### Added

- Sistema de tasks paralelas (multi-task, multi-window)
- TaskManager para execução simultânea
- Controle individual de tasks (play/stop por task)
- Persistência de tasks em tasks.json
- Aba de galeria de imagens na GUI
- Preview ampliável de templates
- Teste, renomeação e exclusão de templates via GUI
- Captura visual com overlay fullscreen
- Suporte completo a múltiplos monitores
- Wildcards em títulos de janelas (*, início, fim, contém)
- Comando CLI `tasks` para execução paralela
- Comando CLI `list` mostra tasks configuradas
- Hotkey global Ctrl+Shift+C para captura rápida
- Threading com stop events para parada graceful
- Status em tempo real nas tasks

### Changed

- GUI completamente redesenhada com tabs (Tasks, Imagens)
- Captura agora usa overlay visual em vez de timer
- OpenCV como método preferencial (mais rápido)
- Estrutura de diretórios expandida (docs/)
- iclick.py suporta janela específica com --window

### Fixed

- Suporte a coordenadas negativas em multi-monitor
- Vazamento de memória ao deletar imagens
- Performance melhorada com busca em janela específica

## [1.0.0] - Data Inicial

### Added

- CLI básico (iclick.py) com comandos: capture, click, wait, run
- GUI simples com CustomTkinter
- Sistema de scripts sequenciais (JSON)
- Reconhecimento de imagem com pyautogui
- 8 tipos de ações em scripts
- Captura de templates via mouse positioning
- Suporte a cliques: simples, duplo, direito
- Simulação de teclado: type, press, hotkey
- Failsafe e pause de segurança
- Estrutura de pastas: images/, scripts/

---

## Tipos de Mudanças

- **Added**: Novas funcionalidades
- **Changed**: Mudanças em funcionalidades existentes
- **Deprecated**: Funcionalidades que serão removidas
- **Removed**: Funcionalidades removidas
- **Fixed**: Correções de bugs
- **Security**: Correções de vulnerabilidades de segurança
