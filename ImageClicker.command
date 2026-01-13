#!/bin/bash
# ImageClicker - Launcher (macOS)
# Duplo clique neste arquivo para executar

cd "$(dirname "$0")"

# Verifica se dependências estão instaladas
python3 -c "import cv2, PyQt6, Quartz" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Dependências não encontradas. Executando instalador..."
    echo ""
    ./install.command
fi

# Executa o aplicativo
python3 app_qt.py
