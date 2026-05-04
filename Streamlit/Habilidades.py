import requests
import zipfile
import io
import re
import os
import pandas as pd
import matplotlib.pyplot as plt
import duckdb
from bs4 import BeautifulSoup

# ============================================================
# CONFIGURACIÓN
# ============================================================

DB_PATH   = "observatorio_laboral.duckdb"
TABLA_SK  = "skills"
TABLA_KN  = "knowledge"
TABLA_OCC = "ocupaciones"

PALETTE = {
    "bg":      "#0d1117",
    "panel":   "#161b22",
    "accent1": "#58a6ff",
    "accent2": "#3fb950",
    "accent3": "#f78166",
    "text":    "#e6edf3",
    "muted":   "#8b949e",
}


# ============================================================
# 1. PIPELINE DE DATOS  →  DuckDB
# ============================================================

def pipeline_datos(db_path: str = DB_PATH) -> None:
    """
    Descarga la versión más reciente de O*NET, procesa los datos
    y los persiste en DuckDB con la siguiente lógica:

    - Si la BD no existe            → la crea y crea las tablas.
    - Si la BD existe, sin tabla    → crea solo esa tabla.
    - Si la BD y la tabla existen   → reemplaza la tabla.
    """

    # ── 1a. Scraping ──────────────────────────────────────────
    url = _get_latest_url()

    # ── 1b. Descarga en memoria ───────────────────────────────
    archivos = _descargar_en_memoria(url)

    # ── 1c. Construir DataFrames limpios ──────────────────────
    df_occ, df_sk, df_kn = _cargar_dataframes(archivos)

    # ── 1d. Persistir en DuckDB ───────────────────────────────
    _guardar_en_duckdb(df_occ, df_sk, df_kn, db_path)

    print(f"\n✅ Pipeline completado. Base de datos: '{db_path}'")


# ----------------------------------------------------------
# Helpers internos del pipeline
# ----------------------------------------------------------

def _get_latest_url() -> str:
    BASE    = "https://www.onetcenter.org"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    page    = requests.get(f"{BASE}/database.html", headers=headers, timeout=30)
    page.raise_for_status()

    soup       = BeautifulSoup(page.content, "html.parser")
    candidates = []
    for a in soup.find_all("a", href=True):
        href  = a["href"]
        match = re.search(r"db_(\d+)_(\d+)_text\.zip", href)
        if match:
            major    = int(match.group(1))
            minor    = int(match.group(2))
            full_url = href if href.startswith("http") else f"{BASE}{href}"
            candidates.append(((major, minor), full_url))

    if not candidates:
        raise ValueError("No se encontró ningún link de descarga en onetcenter.org")

    candidates.sort(key=lambda x: x[0], reverse=True)
    version, url = candidates[0]
    print(f"✅ Versión más reciente: {version[0]}.{version[1]}")
    print(f"   URL: {url}")
    return url


def _descargar_en_memoria(url: str) -> dict:
    print("\n⬇️  Descargando base de datos O*NET...")
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers, timeout=120)
    r.raise_for_status()

    archivos = {}
    with zipfile.ZipFile(io.BytesIO(r.content)) as z:
        for nombre in z.namelist():
            archivos[nombre.lower()] = z.read(nombre)

    print(f"   {len(archivos)} archivos cargados en memoria.")
    return archivos


def _buscar_archivo(archivos: dict, nombre_exacto: str):
    """Coincidencia exacta sobre el nombre base del archivo."""
    clave = nombre_exacto.lower()
    for ruta, contenido in archivos.items():
        if os.path.basename(ruta) == clave:
            return contenido
    return None


def _leer_tsv(archivos: dict, nombre_exacto: str) -> pd.DataFrame:
    contenido = _buscar_archivo(archivos, nombre_exacto)
    if contenido is None:
        raise FileNotFoundError(f"No se encontró '{nombre_exacto}' en el ZIP.")
    return pd.read_csv(io.BytesIO(contenido), sep="\t", encoding="latin1")


def _detectar_col_valor(df: pd.DataFrame) -> str:
    for candidato in ["Data Value", "Value", "data value", "Score"]:
        if candidato in df.columns:
            return candidato
    for col in df.columns:
        if "value" in col.lower() or "score" in col.lower():
            return col
    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            return col
    raise ValueError(f"Sin columna numérica. Columnas: {df.columns.tolist()}")


def _cargar_dataframes(archivos: dict):
    print("\n🔧 Procesando dataframes...")

    df_occ = _leer_tsv(archivos, "occupation data.txt")
    df_sk  = _leer_tsv(archivos, "skills.txt")
    df_kn  = _leer_tsv(archivos, "knowledge.txt")

    for df, nombre in [(df_sk, "Skills"), (df_kn, "Knowledge")]:
        col = _detectar_col_valor(df)
        if col != "Data Value":
            df.rename(columns={col: "Data Value"}, inplace=True)
        df["Data Value"] = pd.to_numeric(df["Data Value"], errors="coerce").round(2)

    print(f"   ✅ Ocupaciones : {df_occ.shape}")
    print(f"   ✅ Skills      : {df_sk.shape}")
    print(f"   ✅ Knowledge   : {df_kn.shape}")
    return df_occ, df_sk, df_kn


def _guardar_en_duckdb(
    df_occ: pd.DataFrame,
    df_sk:  pd.DataFrame,
    df_kn:  pd.DataFrame,
    db_path: str,
) -> None:
    """
    Persiste los tres DataFrames en DuckDB.

    CREATE OR REPLACE TABLE cubre los tres casos en una sola instrucción:
      - BD nueva         → duckdb.connect() crea el archivo, luego crea la tabla.
      - BD sin tabla     → crea solo la tabla que falta.
      - BD con tabla     → descarta la tabla existente y la reemplaza.
    """
    print(f"\n💾 Guardando en DuckDB: '{db_path}'")
    con = duckdb.connect(db_path)   # crea el .duckdb si no existe

    for nombre_tabla, df in [(TABLA_OCC, df_occ), (TABLA_SK, df_sk), (TABLA_KN, df_kn)]:
        con.execute(f"CREATE OR REPLACE TABLE {nombre_tabla} AS SELECT * FROM df")
        n = con.execute(f"SELECT COUNT(*) FROM {nombre_tabla}").fetchone()[0]
        print(f"   📋 '{nombre_tabla}' → {n:,} filas guardadas")

    con.close()


# ============================================================
# 2. GRÁFICOS
# ============================================================

def _agregar(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby("Element Name")["Data Value"]
        .mean()
        .round(2)
        .sort_values(ascending=False)
        .reset_index()
        .rename(columns={"Data Value": "Promedio"})
    )


def _base_fig(title: str, figsize=(14, 7)):
    fig, ax = plt.subplots(figsize=figsize)
    fig.patch.set_facecolor(PALETTE["bg"])
    ax.set_facecolor(PALETTE["panel"])
    ax.set_title(title, color=PALETTE["text"], fontsize=14, fontweight="bold", pad=14)
    ax.tick_params(colors=PALETTE["muted"], labelsize=9)
    for spine in ax.spines.values():
        spine.set_edgecolor(PALETTE["panel"])
    ax.grid(axis="x", color="#30363d", linewidth=0.6, linestyle="--")
    ax.set_axisbelow(True)
    return fig, ax


def grafico_skills_top(df_skills: pd.DataFrame) -> None:
    """Top 20 skills por promedio de Data Value."""
    agg     = _agregar(df_skills).head(20)
    fig, ax = _base_fig("Top 20 Skills más demandadas en O*NET", figsize=(14, 8))
    bars    = ax.barh(
        agg["Element Name"][::-1], agg["Promedio"][::-1],
        color=PALETTE["accent1"], edgecolor="none", height=0.65,
    )
    for bar in bars:
        ax.text(
            bar.get_width() + 0.05, bar.get_y() + bar.get_height() / 2,
            f"{bar.get_width():.2f}", va="center", ha="left",
            color=PALETTE["muted"], fontsize=8,
        )
    ax.set_xlabel("Promedio del Data Value", color=PALETTE["muted"], fontsize=10)
    ax.tick_params(axis="y", labelcolor=PALETTE["text"])
    plt.tight_layout()
    plt.show()


def grafico_knowledge_top(df_knowledge: pd.DataFrame) -> None:
    """Top 20 áreas de conocimiento por promedio de Data Value."""
    agg     = _agregar(df_knowledge).head(20)
    fig, ax = _base_fig("Top 20 Áreas de Conocimiento más demandadas en O*NET", figsize=(14, 8))
    bars    = ax.barh(
        agg["Element Name"][::-1], agg["Promedio"][::-1],
        color=PALETTE["accent2"], edgecolor="none", height=0.65,
    )
    for bar in bars:
        ax.text(
            bar.get_width() + 0.05, bar.get_y() + bar.get_height() / 2,
            f"{bar.get_width():.2f}", va="center", ha="left",
            color=PALETTE["muted"], fontsize=8,
        )
    ax.set_xlabel("Promedio del Data Value", color=PALETTE["muted"], fontsize=10)
    ax.tick_params(axis="y", labelcolor=PALETTE["text"])
    plt.tight_layout()
    plt.show()


def grafico_skills_dist(df_skills: pd.DataFrame) -> None:
    """Histograma de distribución de valores de skills."""
    vals    = df_skills["Data Value"].dropna()
    fig, ax = _base_fig("Distribución de valores — Skills", figsize=(12, 5))
    ax.hist(vals, bins=40, color=PALETTE["accent1"], edgecolor=PALETTE["bg"], linewidth=0.4)
    ax.set_xlabel("Data Value", color=PALETTE["muted"], fontsize=10)
    ax.set_ylabel("Frecuencia",  color=PALETTE["muted"], fontsize=10)
    ax.tick_params(axis="both",  labelcolor=PALETTE["muted"])
    plt.tight_layout()
    plt.show()


def grafico_knowledge_dist(df_knowledge: pd.DataFrame) -> None:
    """Histograma de distribución de valores de knowledge."""
    vals    = df_knowledge["Data Value"].dropna()
    fig, ax = _base_fig("Distribución de valores — Knowledge", figsize=(12, 5))
    ax.hist(vals, bins=40, color=PALETTE["accent2"], edgecolor=PALETTE["bg"], linewidth=0.4)
    ax.set_xlabel("Data Value", color=PALETTE["muted"], fontsize=10)
    ax.set_ylabel("Frecuencia",  color=PALETTE["muted"], fontsize=10)
    ax.tick_params(axis="both",  labelcolor=PALETTE["muted"])
    plt.tight_layout()
    plt.show()


def grafico_ocupaciones(df_occ: pd.DataFrame) -> None:
    """Barras: cantidad de ocupaciones por grupo SOC (2 dígitos)."""
    if "O*NET-SOC Code" not in df_occ.columns:
        print("   ⚠️  Sin columna 'O*NET-SOC Code' — se omite.")
        return

    df             = df_occ.copy()
    df["Grupo"]    = df["O*NET-SOC Code"].astype(str).str[:2]
    conteo         = df["Grupo"].value_counts().head(20).reset_index()
    conteo.columns = ["Grupo SOC", "Cantidad"]

    fig, ax = _base_fig("Top 20 Grupos Ocupacionales (por código SOC)", figsize=(12, 6))
    bars    = ax.bar(
        conteo["Grupo SOC"], conteo["Cantidad"],
        color=PALETTE["accent3"], edgecolor="none", width=0.6,
    )
    for bar in bars:
        ax.text(
            bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
            str(int(bar.get_height())), ha="center", va="bottom",
            color=PALETTE["muted"], fontsize=8,
        )
    ax.set_xlabel("Código de grupo SOC (2 dígitos)", color=PALETTE["muted"], fontsize=10)
    ax.set_ylabel("Nº de ocupaciones",               color=PALETTE["muted"], fontsize=10)
    ax.tick_params(axis="both", labelcolor=PALETTE["muted"])
    plt.tight_layout()
    plt.show()


def grafico_scatter_skills_vs_knowledge(
    df_skills: pd.DataFrame, df_knowledge: pd.DataFrame
) -> None:
    """Scatter: promedio skill vs promedio knowledge para elementos comunes."""
    sk_agg = _agregar(df_skills).rename(columns={"Promedio": "Skill"})
    kn_agg = _agregar(df_knowledge).rename(columns={"Promedio": "Knowledge"})
    merged = sk_agg.merge(kn_agg, on="Element Name", how="inner")

    if merged.empty:
        print("   ⚠️  Sin elementos comunes — se omite scatter.")
        return

    fig, ax = _base_fig("Skills vs Knowledge — Elementos en común", figsize=(10, 7))
    sc = ax.scatter(
        merged["Skill"], merged["Knowledge"],
        c=merged["Skill"] + merged["Knowledge"],
        cmap="cool", s=60, alpha=0.8, edgecolors="none",
    )
    cbar = fig.colorbar(sc, ax=ax)
    cbar.ax.yaxis.set_tick_params(color=PALETTE["muted"])
    cbar.outline.set_edgecolor(PALETTE["panel"])
    plt.setp(plt.getp(cbar.ax.axes, "yticklabels"), color=PALETTE["muted"])

    for _, row in merged.nlargest(5, "Skill").iterrows():
        ax.annotate(
            row["Element Name"], (row["Skill"], row["Knowledge"]),
            textcoords="offset points", xytext=(6, 4),
            color=PALETTE["text"], fontsize=7,
        )
    ax.set_xlabel("Promedio Skill",     color=PALETTE["muted"], fontsize=10)
    ax.set_ylabel("Promedio Knowledge", color=PALETTE["muted"], fontsize=10)
    ax.tick_params(axis="both", labelcolor=PALETTE["muted"])
    plt.tight_layout()
    plt.show()


def generar_todos_los_graficos(db_path: str = DB_PATH) -> None:
    """
    Lee los datos desde DuckDB y genera todos los gráficos.
    Requiere haber ejecutado pipeline_datos() al menos una vez.
    """
    con    = duckdb.connect(db_path, read_only=True)
    df_sk  = con.execute(f"SELECT * FROM {TABLA_SK}").df()
    df_kn  = con.execute(f"SELECT * FROM {TABLA_KN}").df()
    df_occ = con.execute(f"SELECT * FROM {TABLA_OCC}").df()
    con.close()

    print("📊 Generando gráficos...")
    grafico_skills_top(df_sk)
    grafico_knowledge_top(df_kn)
    grafico_skills_dist(df_sk)
    grafico_knowledge_dist(df_kn)
    grafico_ocupaciones(df_occ)
    grafico_scatter_skills_vs_knowledge(df_sk, df_kn)
    print("✅ Gráficos listos.")


# ============================================================
# 3. ENTRY POINT
# ============================================================

# if __name__ == "__main__":
#     # Paso 1 — descarga, procesa y guarda en DuckDB
#     pipeline_datos()

#     # Paso 2 — lee desde DuckDB y muestra los gráficos
#     generar_todos_los_graficos()
