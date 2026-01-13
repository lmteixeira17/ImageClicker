@echo off
echo ========================================
echo    ImageClicker - Build Executavel
echo ========================================
echo.

:: Garante que PyInstaller esta instalado
echo [0/3] Verificando PyInstaller...
python -m pip install pyinstaller --quiet
echo      OK!

:: Limpa builds anteriores
echo [1/3] Limpando builds anteriores...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
echo      Limpo!
echo.

:: Executa PyInstaller
echo [2/3] Gerando executavel (pode demorar alguns minutos)...
python -m PyInstaller ImageClicker.spec --noconfirm
echo.

:: Verifica se foi criado com sucesso
if exist "dist\ImageClicker\ImageClicker.exe" (
    echo [3/3] Sucesso! Executavel criado em:
    echo.
    echo      dist\ImageClicker\ImageClicker.exe
    echo.
    echo ========================================
    echo    Para distribuir, envie a pasta:
    echo    dist\ImageClicker\
    echo.
    echo    Ou crie um ZIP dela.
    echo ========================================

    :: Abre a pasta no Explorer
    explorer "dist\ImageClicker"
) else (
    echo [ERRO] Falha ao criar o executavel.
    echo        Verifique os erros acima.
)

echo.
pause
