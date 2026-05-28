@echo off
REM Run this script AFTER creating the first wiki page via GitHub web UI.
REM 1. Go to https://github.com/angelestrada14019/segurodata/wiki
REM 2. Click "Create the first page", save it (any content).
REM 3. Then run this script.

cd /d "%~dp0"
cd ..

git clone https://github.com/angelestrada14019/segurodata.wiki.git wiki_temp_push
if %errorlevel% neq 0 (
    echo ERROR: Clone failed. Did you create the first wiki page via the GitHub web UI?
    pause
    exit /b 1
)

copy wiki_pages\Home.md wiki_temp_push\Home.md
copy wiki_pages\Fuentes-de-Datos.md wiki_temp_push\Fuentes-de-Datos.md
copy wiki_pages\Arquitectura.md wiki_temp_push\Arquitectura.md
copy wiki_pages\Modulos.md wiki_temp_push\Modulos.md
copy wiki_pages\Metodologia.md wiki_temp_push\Metodologia.md
copy wiki_pages\Replicacion.md wiki_temp_push\Replicacion.md
copy wiki_pages\Instalacion.md wiki_temp_push\Instalacion.md

cd wiki_temp_push
git add .
git commit -m "Add 7 wiki pages: architecture, sources, methodology, modules, replication, installation"
git push

cd ..
rmdir /s /q wiki_temp_push

echo Done! Visit https://github.com/angelestrada14019/segurodata/wiki
pause
