#!/bin/bash
# ImageClicker CLI - Launcher (macOS)
# Uso: ./iclick.command [comandos]
# Ou abra o Terminal nesta pasta e use: python3 iclick.py [comandos]

cd "$(dirname "$0")"

# Verifica se dependências estão instaladas
python3 -c "import cv2, Quartz" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Dependências não encontradas. Executando instalador..."
    echo ""
    ./install.command
fi

# Se executado sem argumentos, mostra ajuda
if [ $# -eq 0 ]; then
    python3 iclick.py --help
else
    python3 iclick.py "$@"
fi
