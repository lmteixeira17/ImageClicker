#!/bin/bash
# ImageClicker - Instalador de Dependências (macOS)
# Duplo clique neste arquivo para instalar

cd "$(dirname "$0")"

echo "========================================"
echo "  ImageClicker - Instalador macOS"
echo "========================================"
echo ""

# Verifica se Python está instalado
if ! command -v python3 &> /dev/null; then
    echo "ERRO: Python 3 não encontrado!"
    echo "Instale Python 3 em: https://www.python.org/downloads/"
    echo ""
    read -p "Pressione Enter para sair..."
    exit 1
fi

echo "Python encontrado: $(python3 --version)"
echo ""

# Instala dependências
echo "Instalando dependências..."
echo ""
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt

if [ $? -eq 0 ]; then
    echo ""
    echo "========================================"
    echo "  Instalação concluída com sucesso!"
    echo "========================================"
    echo ""
    echo "Para executar o ImageClicker:"
    echo "  - Duplo clique em: ImageClicker.command"
    echo "  - Ou no terminal: python3 app_qt.py"
    echo ""
    echo "IMPORTANTE: Conceda permissões de Acessibilidade:"
    echo "  System Preferences > Security & Privacy > Privacy > Accessibility"
    echo ""
else
    echo ""
    echo "ERRO: Falha na instalação!"
    echo ""
fi

read -p "Pressione Enter para sair..."
