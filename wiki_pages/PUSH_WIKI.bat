@echo off
REM Publica todas las wiki_pages/ al GitHub Wiki.
REM Requisito: haber creado la primera pagina desde https://github.com/angelestrada14019/segurodata/wiki

cd /d "%~dp0"
cd ..

git clone https://github.com/angelestrada14019/segurodata.wiki.git wiki_temp_push
if %errorlevel% neq 0 (
    echo ERROR: Clone failed. Did you create the first wiki page via the GitHub web UI?
    pause
    exit /b 1
)

REM --- Paginas originales ---
copy wiki_pages\Home.md                  wiki_temp_push\Home.md
copy wiki_pages\Fuentes-de-Datos.md      wiki_temp_push\Fuentes-de-Datos.md
copy wiki_pages\Arquitectura.md          wiki_temp_push\Arquitectura.md
copy wiki_pages\Modulos.md               wiki_temp_push\Modulos.md
copy wiki_pages\Metodologia.md           wiki_temp_push\Metodologia.md
copy wiki_pages\Replicacion.md           wiki_temp_push\Replicacion.md
copy wiki_pages\Instalacion.md           wiki_temp_push\Instalacion.md

REM --- Paginas nuevas (documentacion tecnica) ---
copy wiki_pages\Transformacion.md        wiki_temp_push\Transformacion.md
copy wiki_pages\Estado-del-Arte.md       wiki_temp_push\Estado-del-Arte.md
copy wiki_pages\Provenance.md            wiki_temp_push\Provenance.md
copy wiki_pages\Investigacion-Fuentes.md wiki_temp_push\Investigacion-Fuentes.md
copy wiki_pages\Reglas-Concurso.md       wiki_temp_push\Reglas-Concurso.md

REM --- Assets ---
copy wiki_pages\diagrama_arquitectura.svg wiki_temp_push\diagrama_arquitectura.svg

cd wiki_temp_push
git add .
git commit -m "wiki: 12 paginas + diagrama SVG arquitectura"
git push

cd ..
rmdir /s /q wiki_temp_push

echo Done! Visit https://github.com/angelestrada14019/segurodata/wiki
pause
