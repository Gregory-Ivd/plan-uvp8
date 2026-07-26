@echo off
chcp 65001 >nul
echo.
echo  Збірка портативної версії «Мій план»
echo  ------------------------------------
echo.

cd /d "%~dp0"

python -m pip install --quiet --upgrade pyinstaller python-docx reportlab pillow
if errorlevel 1 (
    echo  Не вдалося встановити залежності. Перевірте, чи є Python і інтернет.
    pause
    exit /b 1
)

python -m PyInstaller --noconfirm --clean plan-app.spec
if errorlevel 1 (
    echo.
    echo  Збірка не вдалася.
    pause
    exit /b 1
)

copy /y "README.txt" "dist\Мій план\README.txt" >nul

echo.
echo  Готово. Скопіюйте на флешку теку:
echo     dist\Мій план\
echo.
pause
