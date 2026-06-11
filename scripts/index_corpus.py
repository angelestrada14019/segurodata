# -*- coding: utf-8 -*-
"""Indexación OFFLINE del corpus GraphRAG → Supabase documents_corpus.

Fuentes:
  F9  — PDFs de boletines SCJ en datos/raw/boletines_scj/   (pdfplumber)
  F10 — feeds RSS de noticias de seguridad                   (feedparser)
  --seed-demo — corpus de demostración integrado (12 fragmentos, source='SEED_DEV')
                para que /graphrag sea demostrable mientras F9/F10 maduran.

Embeddings: all-MiniLM-L6-v2 (384 dims) — el MISMO modelo que usa el backend en
query-time. NUNCA cambiar de modelo sin reindexar todo el corpus.

Corre en la máquina local, NUNCA en Railway.

Uso:
    python scripts/index_corpus.py --seed-demo               # demo → DB (SUPABASE_DB_URL)
    python scripts/index_corpus.py                           # F9+F10 reales → DB
    python scripts/index_corpus.py --seed-demo --emit-sql    # sin credenciales: genera .sql
    python scripts/index_corpus.py --dry-run                 # reporta chunks sin insertar
"""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import sys
from datetime import date
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")
load_dotenv(ROOT / "backend" / ".env")

BOLETINES_DIR = ROOT / "datos" / "raw" / "boletines_scj"
OUT_SQL = ROOT / "datos" / "grafo" / "corpus_seed.sql"

RSS_FEEDS = {
    "RSS_ELTIEMPO": "https://www.eltiempo.com/rss/bogota.xml",
    "RSS_ESPECTADOR": "https://www.elespectador.com/arc/outboundfeeds/rss/section/bogota/",
    "RSS_INFORMANTE": "https://elinformantesoyyo.com/feed/",
}

CHUNK_CHARS = 1800  # ~500 tokens
OVERLAP_CHARS = 200  # ~50 tokens

# Heurística de etiquetado UPZ: nombre → código (subset de alto tráfico)
UPZ_NOMBRES = {
    "kennedy": "047", "americas": "044", "américas": "044", "timiza": "048",
    "patio bonito": "082", "corabastos": "080", "bosa central": "085", "bosa": "085",
    "el rincon": "028", "el rincón": "028", "rincon de suba": "028", "suba": "027",
    "tibabuyes": "071", "gran yomasa": "057", "chapinero": "099", "la sabana": "102",
    "las nieves": "093", "restrepo": "038", "venecia": "042", "lucero": "067",
    "ismael perdomo": "069", "engativa": "074", "engativá": "074", "fontibon": "075",
    "fontibón": "075", "verbenal": "009", "toberin": "012", "toberín": "012",
}

DEMO_CORPUS = [
    ("SEED_DEV", "Demo: Boletín SCJ — hurto en Américas", "2025-11-01", None, "044",
     "El boletín mensual de la Secretaría de Seguridad reporta un incremento del 18% en hurto a "
     "personas en la UPZ Américas durante octubre, concentrado en el entorno de Plaza de las "
     "Américas entre las 18:00 y las 21:00. El análisis atribuye el patrón a bandas de receptación "
     "de celulares que operan sobre la avenida Primero de Mayo."),
    ("SEED_DEV", "Demo: Boletín SCJ — riñas en Kennedy Central", "2025-10-01", None, "047",
     "Las riñas con lesiones personales en Kennedy Central aumentaron los fines de semana, "
     "asociadas al entorno de establecimientos nocturnos. La SCJ recomienda coordinación con la "
     "Secretaría de Gobierno para control de horarios y mediación de conflictos."),
    ("SEED_DEV", "Demo: Boletín SCJ — El Rincón iluminación", "2025-09-01", None, "028",
     "En la UPZ El Rincón de Suba persiste la concentración de hurtos en corredores peatonales con "
     "iluminación deficiente. El diagnóstico territorial identifica 14 segmentos críticos donde la "
     "UAESP priorizará recambio de luminarias a LED."),
    ("SEED_DEV", "Demo: noticia — operativo en Corabastos", "2025-10-20", "https://demo.segurodata/corabastos", "080",
     "La Policía Metropolitana desarticuló una banda dedicada al hurto de carga en el entorno de "
     "Corabastos. El operativo incluyó 12 capturas y la recuperación de mercancía. Comerciantes "
     "señalan que la madrugada sigue siendo la franja de mayor riesgo."),
    ("SEED_DEV", "Demo: noticia — hurto de celulares en TransMilenio", "2025-11-10", "https://demo.segurodata/tm", None,
     "El hurto de celulares en el sistema TransMilenio se concentra en estaciones de alta afluencia "
     "en hora pico. Las troncales Caracas y NQS acumulan la mayor cantidad de denuncias. La empresa "
     "anunció refuerzo de personal de seguridad privada en 15 estaciones."),
    ("SEED_DEV", "Demo: Boletín SCJ — Gran Yomasa nocturno", "2025-08-01", None, "057",
     "Gran Yomasa registra patrón delictivo de madrugada: el 42% de los incidentes ocurre entre las "
     "00:00 y las 06:00. La SCJ plantea operativos nocturnos focalizados y articulación con el "
     "turno nocturno de la MEBOG."),
    ("SEED_DEV", "Demo: noticia — obras IDU y seguridad en Bosa", "2025-09-15", "https://demo.segurodata/bosa-obras", "085",
     "Vecinos de Bosa Central reportan aumento de hurtos en los desvíos peatonales generados por "
     "las obras de la avenida Ciudad de Cali. El IDU y la Policía acordaron un plan de iluminación "
     "provisional y patrullaje perimetral mientras avanza la intervención."),
    ("SEED_DEV", "Demo: Boletín SCJ — subregistro en llamadas 123", "2025-07-01", None, None,
     "El análisis del C4 evidencia que por cada delito denunciado formalmente se reciben en "
     "promedio 3,2 llamadas al 123 relacionadas con seguridad. Las UPZ con mayor brecha entre "
     "llamadas y denuncias se concentran en el suroccidente, lo que sugiere subregistro."),
    ("SEED_DEV", "Demo: noticia — cámaras Salvavidas en Chapinero", "2025-10-05", "https://demo.segurodata/camaras", "099",
     "La SDSCJ instaló 24 nuevas cámaras del programa Salvavidas en Chapinero, priorizando la zona "
     "rosa y corredores hacia estaciones de TransMilenio. Estudios distritales asocian la "
     "videovigilancia con reducciones de hurto callejero en el entorno inmediato."),
    ("SEED_DEV", "Demo: Boletín SCJ — La Sabana receptación", "2025-11-15", None, "102",
     "La UPZ La Sabana concentra puntos de receptación de autopartes y celulares en el entorno de "
     "la calle 13 y Paloquemao. La SIJIN georreferenció 9 puntos de comercialización de hurtado y "
     "ejecutó allanamientos durante noviembre."),
    ("SEED_DEV", "Demo: noticia — Jóvenes en Paz en Ciudad Bolívar", "2025-09-30", "https://demo.segurodata/jovenes", "067",
     "El programa Jóvenes en Paz amplió cupos en Lucero y otras UPZ de Ciudad Bolívar. La "
     "estrategia distrital combina transferencias condicionadas, formación y acompañamiento "
     "psicosocial para jóvenes en riesgo de vinculación a estructuras criminales."),
    ("SEED_DEV", "Demo: Boletín SCJ — estacionalidad diciembre", "2025-12-01", None, None,
     "Históricamente, diciembre incrementa el hurto a personas y las riñas en Bogotá: zonas "
     "comerciales, prima navideña y consumo de licor elevan la exposición. El plan Navidad refuerza "
     "presencia en 40 zonas comerciales y controla pólvora y licor adulterado."),
]


def sha(texto: str) -> str:
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def detectar_upz(texto: str) -> str | None:
    t = texto.lower()
    for nombre, cod in UPZ_NOMBRES.items():
        if nombre in t:
            return cod
    return None


def chunk_texto(texto: str) -> list[str]:
    """Chunking por párrafos con ventana ~500 tokens y overlap ~50."""
    parrafos = [p.strip() for p in re.split(r"\n\s*\n", texto) if p.strip()]
    chunks, actual = [], ""
    for p in parrafos:
        if len(actual) + len(p) > CHUNK_CHARS and actual:
            chunks.append(actual.strip())
            actual = actual[-OVERLAP_CHARS:] + "\n" + p
        else:
            actual += "\n" + p
    if actual.strip():
        chunks.append(actual.strip())
    return [c for c in chunks if len(c) > 80]


def extraer_f9() -> list[tuple]:
    if not BOLETINES_DIR.exists():
        return []
    import pdfplumber

    docs = []
    for pdf_path in sorted(BOLETINES_DIR.glob("*.pdf")):
        try:
            with pdfplumber.open(pdf_path) as pdf:
                texto = "\n\n".join(page.extract_text() or "" for page in pdf.pages)
        except Exception as exc:
            print(f"  [F9] {pdf_path.name}: error {exc}")
            continue
        for chunk in chunk_texto(texto):
            docs.append(("SCJ_BOLETIN", pdf_path.stem, None, None, detectar_upz(chunk), chunk))
    print(f"F9: {len(docs)} chunks de {BOLETINES_DIR}")
    return docs


def extraer_f10() -> list[tuple]:
    import feedparser

    KEYWORDS = re.compile(
        r"hurto|robo|atraco|inseguridad|homicidio|riña|delincuen|crimen|polic[ií]a|captur", re.I
    )
    docs = []
    for source, url in RSS_FEEDS.items():
        try:
            feed = feedparser.parse(url)
        except Exception as exc:
            print(f"  [F10] {source}: error {exc}")
            continue
        for entry in feed.entries[:50]:
            texto = re.sub(r"<[^>]+>", " ", f"{entry.get('title', '')}. {entry.get('summary', '')}")
            texto = re.sub(r"\s+", " ", texto).strip()
            if len(texto) < 100 or not KEYWORDS.search(texto):
                continue
            fecha = None
            if entry.get("published_parsed"):
                p = entry.published_parsed
                fecha = f"{p.tm_year:04d}-{p.tm_mon:02d}-{p.tm_mday:02d}"
            docs.append((source, entry.get("title", "")[:200], fecha,
                         entry.get("link"), detectar_upz(texto), texto))
    print(f"F10: {len(docs)} entradas relevantes de {len(RSS_FEEDS)} feeds")
    return docs


def embeber(textos: list[str], backend: str) -> list[list[float]]:
    modelo = "sentence-transformers/all-MiniLM-L6-v2"
    print(f"Embeddings: {backend} / {modelo} ({len(textos)} textos)")
    if backend == "fastembed":
        from fastembed import TextEmbedding

        model = TextEmbedding(modelo)
        return [[round(float(x), 6) for x in v] for v in model.embed(textos, batch_size=32)]
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(modelo)
    vecs = model.encode(textos, batch_size=64, normalize_embeddings=True)
    return [[round(float(x), 6) for x in v] for v in vecs]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed-demo", action="store_true", help="incluir corpus demo SEED_DEV")
    ap.add_argument("--emit-sql", action="store_true", help="escribir SQL en vez de insertar")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--backend", default=os.environ.get("EMBEDDINGS_BACKEND", "fastembed"),
                    choices=["fastembed", "sentence-transformers"])
    args = ap.parse_args()

    docs: list[tuple] = []
    if args.seed_demo:
        docs += [(s, t, f, u, upz, c) for s, t, f, u, upz, c in DEMO_CORPUS]
    docs += extraer_f9()
    docs += extraer_f10()

    # Dedup por hash de contenido
    vistos, unicos = set(), []
    for d in docs:
        h = sha(d[5])
        if h not in vistos:
            vistos.add(h)
            unicos.append((*d, h))
    print(f"Total: {len(unicos)} chunks únicos")
    if args.dry_run or not unicos:
        return

    vectores = embeber([d[5] for d in unicos], args.backend)

    filas = []
    for (source, titulo, fecha, url, upz, content, h), vec in zip(unicos, vectores):
        filas.append({
            "content": content, "content_hash": h, "source": source, "titulo": titulo,
            "fecha": fecha, "url": url, "upz_cod": upz,
            "embedding": vec,  # list[float] para REST API y emit_sql
        })

    if args.emit_sql:
        OUT_SQL.parent.mkdir(exist_ok=True)

        def q(v):
            if v is None:
                return "NULL"
            return "'" + str(v).replace("'", "''") + "'"

        def fmt_vec(v):
            vec_str = "[" + ",".join(str(x) for x in v) + "]"
            return f"'{vec_str}'::vector"

        with open(OUT_SQL, "w", encoding="utf-8") as f:
            for r in filas:
                f.write(
                    "INSERT INTO documents_corpus (content, content_hash, source, titulo, fecha, url, upz_cod, embedding) "
                    f"VALUES ({q(r['content'])}, {q(r['content_hash'])}, {q(r['source'])}, {q(r['titulo'])}, "
                    f"{q(r['fecha'])}, {q(r['url'])}, {q(r['upz_cod'])}, {fmt_vec(r['embedding'])}) "
                    "ON CONFLICT (content_hash) DO NOTHING;\n"
                )
        print(f"SQL escrito en {OUT_SQL} ({len(filas)} INSERTs)")
        return

    try:
        from supabase import create_client
    except ImportError:
        sys.exit("Falta supabase-py: pip install supabase")
    supa_url = os.environ.get("SUPABASE_URL", "")
    supa_key = os.environ.get("SUPABASE_SERVICE_KEY", "")
    if not supa_url or not supa_key:
        sys.exit("Faltan SUPABASE_URL / SUPABASE_SERVICE_KEY en backend/.env (o usa --emit-sql)")
    client = create_client(supa_url, supa_key)

    BATCH = 50  # vectores de 384 dims son pesados (~12 KB/fila)
    total = len(filas)
    for i in range(0, total, BATCH):
        client.table("documents_corpus").upsert(
            filas[i:i + BATCH], on_conflict="content_hash"
        ).execute()
        print(f"  {min(i + BATCH, total):,}/{total:,}", end="\r")

    print()
    from collections import Counter
    counts = Counter(r["source"] for r in filas)
    for src, cnt in sorted(counts.items()):
        print(f"  documents_corpus [{src}]: {cnt} chunks (esta ejecución)")
    print("Indexación completa.")


if __name__ == "__main__":
    main()
