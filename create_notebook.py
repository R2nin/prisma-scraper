"""
Gerador do notebook PRISMA 2020.
Execute: python create_notebook.py
Requer: pip install nbformat
"""
import nbformat
from nbformat.v4 import new_notebook, new_markdown_cell, new_code_cell

cells = []

# ===========================================================
# HEADER
# ===========================================================
cells.append(new_markdown_cell("""# Revisão Sistemática da Literatura — Protocolo PRISMA 2020
## Implementação com Selenium + BeautifulSoup + APIs Acadêmicas

---
| Campo | Valor |
|---|---|
| **Disciplina** | Python e Scraper/Crawler — 2º Semestre |
| **Professor** | Guilherme de Cleva Farto |
| **Aluno** | *(preencha seu nome)* |
| **RA** | *(preencha seu RA)* |
| **Curso** | Sistema de Informação |
| **Data** | *(data de execução)* |

---
## Sobre este Notebook

Este notebook implementa o **Protocolo PRISMA 2020** (*Preferred Reporting Items for Systematic Reviews and Meta-Analyses*)
para revisões sistemáticas da literatura científica, de forma automatizada.

### Bases de dados suportadas
| Base | Tecnologia usada | Acesso |
|---|---|---|
| **PubMed** | Selenium + BeautifulSoup + Entrez API | Gratuito |
| **arXiv** | BeautifulSoup (XML) | Gratuito |
| **Semantic Scholar** | REST API | Gratuito |
| **OpenAlex** | REST API | Gratuito |

### Fluxo PRISMA 2020
```
1. IDENTIFICAÇÃO  → Busca em cada base de dados
2. TRIAGEM        → Remove duplicatas, aplica filtros
3. ELEGIBILIDADE  → Avalia relevância por palavras-chave
4. INCLUSÃO       → Dataset final + visualizações + bibliografia
```
"""))

# ===========================================================
# SECAO 1 — INSTALAÇÃO
# ===========================================================
cells.append(new_markdown_cell("## 1. Instalação de Dependências"))

cells.append(new_code_cell('''\
# ============================================================
# Instalação automática das dependências
# ============================================================
import sys, subprocess

PACKAGES = [
    "selenium",
    "beautifulsoup4",
    "requests",
    "pandas",
    "numpy",
    "matplotlib",
    "plotly",
    "wordcloud",
    "biopython",
    "lxml",
    "tqdm",
    "kaleido",
    "webdriver-manager",
    "ipywidgets",
    "nbformat",
]

print("Instalando pacotes...")
for pkg in PACKAGES:
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", pkg, "-q"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    print(f"  ✓ {pkg}")

# ChromeDriver para Google Colab
if "google.colab" in sys.modules:
    subprocess.run(
        ["apt-get", "install", "-y", "chromium-chromedriver"],
        capture_output=True, check=True
    )
    print("  ✓ chromium-chromedriver (Colab)")

print("\\n✅ Todas as dependências instaladas!")
'''))

# ===========================================================
# SECAO 2 — IMPORTS
# ===========================================================
cells.append(new_markdown_cell("## 2. Importações"))

cells.append(new_code_cell('''\
import sys, os, re, time, json, warnings, hashlib
from datetime import datetime
from urllib.parse import quote_plus

import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import plotly.express as px
import plotly.graph_objects as go
from tqdm.notebook import tqdm
from IPython.display import display, HTML, clear_output

try:
    from wordcloud import WordCloud
    WORDCLOUD_OK = True
except ImportError:
    WORDCLOUD_OK = False
    print("⚠️  wordcloud não disponível — nuvem de palavras desativada")

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, NoSuchElementException, WebDriverException
)

try:
    from webdriver_manager.chrome import ChromeDriverManager
    WDM_OK = True
except ImportError:
    WDM_OK = False

from Bio import Entrez

warnings.filterwarnings("ignore")
print("✅ Importações concluídas!")
'''))

# ===========================================================
# SECAO 3 — CONFIGURAÇÃO
# ===========================================================
cells.append(new_markdown_cell("""\
## 3. Configuração — EDITE AQUI

> **Instruções:**
> 1. Altere `"tema"` para o assunto da sua pesquisa (use `AND`, `OR`, `NOT`)
> 2. Ative/desative bases em `"bases"`
> 3. Ajuste o período e limites conforme necessário
> 4. Execute todas as células em sequência
"""))

cells.append(new_code_cell('''\
# ============================================================
# ⚙️  CONFIGURAÇÃO — EDITE ESTA CÉLULA
# ============================================================

CONFIG = {
    # ----------------------------------------------------------
    # 🔍 TEMA DA PESQUISA
    # Escreva sua pergunta ou termos de busca.
    # Operadores aceitos: AND, OR, NOT
    # Exemplos:
    #   "machine learning AND healthcare"
    #   "deep learning AND image classification"
    #   "blockchain AND supply chain"
    #   "natural language processing AND sentiment analysis"
    # ----------------------------------------------------------
    "tema": "machine learning AND healthcare",

    # ----------------------------------------------------------
    # 🗄️  BASES DE DADOS ATIVAS (True = ativa, False = desativa)
    # ----------------------------------------------------------
    "bases": {
        "pubmed":            True,   # Literatura biomédica (NCBI)
        "arxiv":             True,   # Pré-prints (CS, Física, Matemática)
        "semantic_scholar":  True,   # Ampla cobertura multidisciplinar
        "openalex":          True,   # Base aberta e abrangente
    },

    # ----------------------------------------------------------
    # 📅  FILTROS
    # ----------------------------------------------------------
    "ano_min":         2019,
    "ano_max":         2024,
    "max_por_base":    50,                        # máx. artigos por base
    "idiomas_aceitos": ["eng", "por", "en", "pt"],# inglês e português

    # ----------------------------------------------------------
    # 🚫  CRITÉRIOS DE EXCLUSÃO
    # Artigos com qualquer uma dessas palavras no título/abstract
    # serão excluídos na triagem.
    # Deixe [] para não excluir nada.
    # Exemplo: ["retracted", "erratum", "correction"]
    # ----------------------------------------------------------
    "excluir_keywords": [],

    # ----------------------------------------------------------
    # ✅  CRITÉRIOS DE INCLUSÃO
    # Se preenchido, artigos devem conter PELO MENOS UMA dessas
    # palavras para passar para elegibilidade.
    # Deixe [] para passar todos.
    # ----------------------------------------------------------
    "incluir_keywords": [],

    # ----------------------------------------------------------
    # 📖  FORMATO DA BIBLIOGRAFIA: "abnt" ou "apa"
    # ----------------------------------------------------------
    "formato_bib": "abnt",

    # ----------------------------------------------------------
    # 📧  EMAIL PARA API NCBI (obrigatório pelo PubMed)
    # ----------------------------------------------------------
    "email_ncbi": "pesquisador@universidade.br",
}

# --- Resumo da configuração ---
print("=" * 55)
print("CONFIGURAÇÃO ATUAL")
print("=" * 55)
print(f"  Tema        : {CONFIG[\'tema\']}")
bases_ativas = [k for k, v in CONFIG["bases"].items() if v]
print(f"  Bases ativas: {bases_ativas}")
print(f"  Período     : {CONFIG[\'ano_min\']} – {CONFIG[\'ano_max\']}")
print(f"  Máx/base    : {CONFIG[\'max_por_base\']} artigos")
print(f"  Formato bib : {CONFIG[\'formato_bib\'].upper()}")
print("=" * 55)
'''))

# ===========================================================
# SECAO 4 — SELENIUM SETUP
# ===========================================================
cells.append(new_markdown_cell("""\
## 4. Configuração do Selenium (Chrome Headless)

O Selenium controla o navegador de forma automatizada, permitindo
navegar em páginas dinâmicas, realizar buscas e acionar paginação —
exatamente como um usuário faria manualmente.
"""))

cells.append(new_code_cell('''\
# ============================================================
# Inicialização do Chrome Headless via Selenium
# ============================================================

def criar_driver():
    """
    Cria e retorna uma instância do Chrome em modo headless.
    Detecta automaticamente se está rodando no Google Colab.
    """
    opts = Options()
    opts.add_argument("--headless")                 # sem interface gráfica
    opts.add_argument("--no-sandbox")               # necessário no Linux/Colab
    opts.add_argument("--disable-dev-shm-usage")    # evita erros de memória
    opts.add_argument("--disable-gpu")
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
    opts.add_experimental_option("excludeSwitches", ["enable-logging"])

    # Detecta ambiente de execução
    if "google.colab" in sys.modules:
        # Colab: ChromeDriver instalado via apt-get
        svc = Service("/usr/bin/chromedriver")
    elif WDM_OK:
        # Local com webdriver-manager: baixa o driver automaticamente
        svc = Service(ChromeDriverManager().install())
    else:
        # Fallback: ChromeDriver no PATH do sistema
        svc = Service()

    try:
        drv = webdriver.Chrome(service=svc, options=opts)
        drv.set_page_load_timeout(30)
        print("✅ Chrome Headless iniciado com sucesso!")
        return drv
    except WebDriverException as e:
        print(f"⚠️  Erro ao iniciar ChromeDriver: {e}")
        print("   → O PubMed usará fallback via API Entrez.")
        return None

driver = criar_driver()
'''))

# ===========================================================
# SECAO 5 — COLETORES
# ===========================================================
cells.append(new_markdown_cell("""\
## 5. Funções de Coleta por Base de Dados

Cada coletor retorna uma lista de dicionários com campos padronizados:
`titulo`, `autores`, `ano`, `abstract`, `journal`, `doi`, `url`, `fonte`, `idioma`
"""))

cells.append(new_code_cell('''\
# ============================================================
# COLETOR 1: PubMed
# Tecnologia: Selenium (navegação) + BeautifulSoup (HTML parsing)
#             + Entrez API (detalhes completos)
# ============================================================

def coletar_pubmed(query, max_results=50, ano_min=2019, ano_max=2024):
    """
    Coleta artigos do PubMed em duas etapas:
      1. Selenium navega na página de busca e extrai PMIDs via BeautifulSoup
      2. Entrez API busca os detalhes completos usando os PMIDs
    """
    artigos = []
    Entrez.email = CONFIG["email_ncbi"]
    pmids = []

    # ------ ETAPA 1: Selenium + BeautifulSoup ------
    if driver:
        try:
            url = (
                "https://pubmed.ncbi.nlm.nih.gov/?"
                f"term={quote_plus(query)}"
                f"&filter=years.{ano_min}-{ano_max}"
                "&size=50"
            )
            driver.get(url)
            time.sleep(3)

            paginas = 0
            while len(pmids) < max_results and paginas < 5:
                # BeautifulSoup parseia o HTML retornado pelo Selenium
                soup = BeautifulSoup(driver.page_source, "lxml")
                articles_html = soup.find_all("article", class_="full-docsum")

                for art in articles_html:
                    aid = art.get("data-article-id", "")
                    if aid and aid not in pmids:
                        pmids.append(aid)

                paginas += 1

                # Paginação: clica no botão "Próxima página"
                try:
                    btn = driver.find_element(
                        By.CSS_SELECTOR,
                        'button[aria-label="Next page"]'
                    )
                    if btn.is_enabled():
                        btn.click()
                        time.sleep(2)
                    else:
                        break
                except NoSuchElementException:
                    break

            print(f"    Selenium/BS4: {len(pmids)} PMIDs extraídos do HTML")

        except Exception as e:
            print(f"    Selenium PubMed erro: {e}")

    # ------ FALLBACK: Entrez E-Search (caso Selenium falhe) ------
    if not pmids:
        try:
            handle = Entrez.esearch(
                db="pubmed", term=query,
                retmax=max_results,
                mindate=str(ano_min), maxdate=str(ano_max),
                datetype="pdat"
            )
            record = Entrez.read(handle)
            handle.close()
            pmids = record["IdList"]
            print(f"    Entrez E-Search fallback: {len(pmids)} PMIDs")
        except Exception as e:
            print(f"    Entrez E-Search erro: {e}")
            return artigos

    # ------ ETAPA 2: Entrez E-Fetch — detalhes completos ------
    pmids = pmids[:max_results]
    if pmids:
        try:
            handle = Entrez.efetch(
                db="pubmed", id=",".join(pmids),
                rettype="xml", retmode="xml"
            )
            records = Entrez.read(handle)
            handle.close()

            for rec in records.get("PubmedArticle", []):
                try:
                    art = rec["MedlineCitation"]["Article"]
                    titulo = str(art.get("ArticleTitle", "")).strip()

                    # Autores
                    autores_list = []
                    for au in art.get("AuthorList", []):
                        sobrenome = au.get("LastName", "")
                        nome = au.get("ForeName", "")
                        if sobrenome:
                            ini = f" {nome[0]}." if nome else ""
                            autores_list.append(f"{sobrenome},{ini}")
                    autores = "; ".join(autores_list[:6])
                    if len(autores_list) > 6:
                        autores += " et al."

                    # Ano de publicação
                    try:
                        pub_date = art["Journal"]["JournalIssue"]["PubDate"]
                        ano = int(str(pub_date.get("Year", 0)))
                    except Exception:
                        ano = None

                    # Abstract
                    ab_list = art.get("Abstract", {}).get("AbstractText", [])
                    if isinstance(ab_list, list):
                        abstract = " ".join(str(a) for a in ab_list)
                    else:
                        abstract = str(ab_list)

                    journal = str(art.get("Journal", {}).get("Title", ""))

                    # DOI
                    doi = ""
                    for id_obj in rec.get("PubmedData", {}).get("ArticleIdList", []):
                        if str(id_obj.attributes.get("IdType", "")) == "doi":
                            doi = str(id_obj)
                            break

                    pmid_val = str(rec["MedlineCitation"].get("PMID", ""))

                    if titulo and ano and ano_min <= ano <= ano_max:
                        artigos.append({
                            "titulo":   titulo,
                            "autores":  autores,
                            "ano":      ano,
                            "abstract": abstract,
                            "journal":  journal,
                            "doi":      doi,
                            "pmid":     pmid_val,
                            "url":      f"https://pubmed.ncbi.nlm.nih.gov/{pmid_val}/",
                            "fonte":    "PubMed",
                            "idioma":   "eng",
                        })
                except Exception:
                    continue

        except Exception as e:
            print(f"    Entrez E-Fetch erro: {e}")

    print(f"    PubMed total: {len(artigos)} artigos")
    return artigos
'''))

cells.append(new_code_cell('''\
# ============================================================
# COLETOR 2: arXiv
# Tecnologia: requests (HTTP) + BeautifulSoup (XML parsing)
# ============================================================

def coletar_arxiv(query, max_results=50, ano_min=2019, ano_max=2024):
    """
    Coleta artigos do arXiv via API Atom/XML.
    Usa BeautifulSoup para parsear a resposta XML da API.
    """
    artigos = []

    params = {
        "search_query": f"all:{query}",
        "start":        0,
        "max_results":  max_results,
        "sortBy":       "relevance",
        "sortOrder":    "descending",
    }

    try:
        resp = requests.get(
            "https://export.arxiv.org/api/query",
            params=params, timeout=30
        )
        resp.raise_for_status()

        # BeautifulSoup parseia o XML da resposta
        soup = BeautifulSoup(resp.text, "xml")
        entries = soup.find_all("entry")

        for entry in entries:
            try:
                titulo   = entry.find("title").text.strip().replace("\n", " ")
                abstract = entry.find("summary").text.strip().replace("\n", " ")

                authors = entry.find_all("author")
                autores_list = [a.find("name").text for a in authors[:6]]
                autores = "; ".join(autores_list)
                if len(authors) > 6:
                    autores += " et al."

                published = entry.find("published").text[:4]
                ano = int(published) if published.isdigit() else None
                if ano and not (ano_min <= ano <= ano_max):
                    continue

                link = entry.find("link", rel="alternate")
                url_art = link["href"] if link else entry.find("id").text

                doi_tag = entry.find("arxiv:doi")
                doi = doi_tag.text.strip() if doi_tag else ""

                cat_tag = entry.find("arxiv:primary_category")
                journal = f"arXiv:{cat_tag[\'term\']}" if cat_tag else "arXiv"

                artigos.append({
                    "titulo":   titulo,
                    "autores":  autores,
                    "ano":      ano,
                    "abstract": abstract,
                    "journal":  journal,
                    "doi":      doi,
                    "pmid":     "",
                    "url":      url_art,
                    "fonte":    "arXiv",
                    "idioma":   "eng",
                })
            except Exception:
                continue

    except Exception as e:
        print(f"    arXiv erro: {e}")

    print(f"    arXiv total: {len(artigos)} artigos")
    return artigos
'''))

cells.append(new_code_cell('''\
# ============================================================
# COLETOR 3: Semantic Scholar
# Tecnologia: REST API JSON (Academic Graph)
# ============================================================

def coletar_semantic_scholar(query, max_results=50, ano_min=2019, ano_max=2024):
    """
    Coleta artigos via Semantic Scholar Academic Graph API.
    Documentação: https://api.semanticscholar.org/graph/v1
    """
    artigos = []
    batch   = min(100, max_results)
    offset  = 0

    while len(artigos) < max_results:
        params = {
            "query":  query,
            "limit":  min(batch, max_results - len(artigos)),
            "offset": offset,
            "fields": "title,authors,year,abstract,journal,externalIds,url",
        }

        try:
            resp = requests.get(
                "https://api.semanticscholar.org/graph/v1/paper/search",
                params=params, timeout=30
            )

            if resp.status_code == 429:   # rate limit
                time.sleep(10)
                continue

            resp.raise_for_status()
            papers = resp.json().get("data", [])

            if not papers:
                break

            for p in papers:
                try:
                    ano = p.get("year")
                    if ano and not (ano_min <= int(ano) <= ano_max):
                        continue

                    autores_raw  = p.get("authors", []) or []
                    autores_list = [a.get("name", "") for a in autores_raw[:6]]
                    autores = "; ".join(autores_list)
                    if len(autores_raw) > 6:
                        autores += " et al."

                    ids     = p.get("externalIds") or {}
                    doi     = ids.get("DOI", "")
                    pmid    = ids.get("PubMed", "")

                    jinfo   = p.get("journal") or {}
                    journal = jinfo.get("name", "Semantic Scholar") if isinstance(jinfo, dict) else str(jinfo)

                    url_art = p.get("url", "")
                    if not url_art and p.get("paperId"):
                        url_art = f"https://www.semanticscholar.org/paper/{p[\'paperId\']}"

                    artigos.append({
                        "titulo":   p.get("title", ""),
                        "autores":  autores,
                        "ano":      int(ano) if ano else None,
                        "abstract": p.get("abstract", "") or "",
                        "journal":  journal,
                        "doi":      doi,
                        "pmid":     str(pmid) if pmid else "",
                        "url":      url_art,
                        "fonte":    "Semantic Scholar",
                        "idioma":   "eng",
                    })
                except Exception:
                    continue

            if len(papers) < batch:
                break

            offset += batch
            time.sleep(0.5)   # respeita rate limit

        except Exception as e:
            print(f"    Semantic Scholar erro: {e}")
            break

    print(f"    Semantic Scholar total: {len(artigos)} artigos")
    return artigos
'''))

cells.append(new_code_cell('''\
# ============================================================
# COLETOR 4: OpenAlex
# Tecnologia: REST API JSON (base acadêmica aberta)
# ============================================================

def coletar_openalex(query, max_results=50, ano_min=2019, ano_max=2024):
    """
    Coleta artigos via OpenAlex API.
    OpenAlex é uma base acadêmica aberta com +200 milhões de artigos.
    Documentação: https://docs.openalex.org
    """
    artigos  = []
    per_page = min(50, max_results)
    page     = 1
    headers  = {"User-Agent": f"PrismaResearcher/1.0 (mailto:{CONFIG[\'email_ncbi\']})"}

    while len(artigos) < max_results:
        params = {
            "search":    query,
            "filter":    f"publication_year:{ano_min}-{ano_max},type:article",
            "sort":      "relevance_score:desc",
            "per-page":  min(per_page, max_results - len(artigos)),
            "page":      page,
            "select":    (
                "title,authorships,publication_year,"
                "abstract_inverted_index,primary_location,"
                "doi,id,language"
            ),
        }

        try:
            resp = requests.get(
                "https://api.openalex.org/works",
                params=params, headers=headers, timeout=30
            )
            resp.raise_for_status()
            results = resp.json().get("results", [])

            if not results:
                break

            for work in results:
                try:
                    titulo = work.get("title", "") or ""

                    # Autores
                    autores_raw  = work.get("authorships") or []
                    autores_list = []
                    for auth in autores_raw[:6]:
                        name = (auth.get("author") or {}).get("display_name", "")
                        if name:
                            autores_list.append(name)
                    autores = "; ".join(autores_list)
                    if len(autores_raw) > 6:
                        autores += " et al."

                    ano = work.get("publication_year")

                    # Abstract: OpenAlex usa índice invertido → reconstrói o texto
                    abstract  = ""
                    inv_index = work.get("abstract_inverted_index")
                    if inv_index:
                        word_pos = []
                        for word, positions in inv_index.items():
                            for pos in positions:
                                word_pos.append((pos, word))
                        word_pos.sort(key=lambda x: x[0])
                        abstract = " ".join(w for _, w in word_pos)

                    # Periódico
                    loc    = work.get("primary_location") or {}
                    source = loc.get("source") or {}
                    journal = source.get("display_name", "OpenAlex") if source else "OpenAlex"

                    doi    = (work.get("doi") or "").replace("https://doi.org/", "")
                    idioma = work.get("language", "en") or "en"

                    artigos.append({
                        "titulo":   titulo,
                        "autores":  autores,
                        "ano":      int(ano) if ano else None,
                        "abstract": abstract,
                        "journal":  journal,
                        "doi":      doi,
                        "pmid":     "",
                        "url":      (f"https://doi.org/{doi}" if doi
                                     else work.get("id", "")),
                        "fonte":    "OpenAlex",
                        "idioma":   idioma,
                    })
                except Exception:
                    continue

            if len(results) < per_page:
                break

            page += 1
            time.sleep(0.3)

        except Exception as e:
            print(f"    OpenAlex erro: {e}")
            break

    print(f"    OpenAlex total: {len(artigos)} artigos")
    return artigos
'''))

# ===========================================================
# SECAO 6 — COLETA
# ===========================================================
cells.append(new_markdown_cell("""\
## 6. Etapa 1 — Identificação: Coleta nas Bases de Dados

> Execute esta célula para iniciar a busca em todas as bases ativas.
> O tempo depende da quantidade de bases e do limite de artigos por base.
"""))

cells.append(new_code_cell('''\
# ============================================================
# ETAPA 1 — IDENTIFICAÇÃO
# ============================================================
print("=" * 60)
print("  ETAPA 1: IDENTIFICAÇÃO")
print("=" * 60)

todos_artigos      = []
contagem_por_base  = {}

_coletores = {
    "pubmed":           coletar_pubmed,
    "arxiv":            coletar_arxiv,
    "semantic_scholar": coletar_semantic_scholar,
    "openalex":         coletar_openalex,
}

for base, ativo in CONFIG["bases"].items():
    if not ativo:
        continue
    print(f"\\n  → Coletando: {base.upper()}")
    coletor    = _coletores[base]
    resultados = coletor(
        CONFIG["tema"],
        max_results = CONFIG["max_por_base"],
        ano_min     = CONFIG["ano_min"],
        ano_max     = CONFIG["ano_max"],
    )
    todos_artigos.extend(resultados)
    contagem_por_base[base] = len(resultados)

df_raw = pd.DataFrame(todos_artigos)

# Metadados para o fluxograma PRISMA
prisma_meta = {
    "identificados": len(df_raw),
    "por_base":      contagem_por_base.copy(),
}

print("\\n" + "=" * 60)
print(f"  Total bruto coletado: {len(df_raw)} artigos")
for b, n in contagem_por_base.items():
    print(f"    {b:20s}: {n}")
print("=" * 60)
'''))

# ===========================================================
# SECAO 7 — PIPELINE PRISMA
# ===========================================================
cells.append(new_markdown_cell("""\
## 7. Pipeline PRISMA 2020

### Etapa 2 — Triagem (Screening)
Remove duplicatas e aplica filtros de período, idioma e palavras-chave.
"""))

cells.append(new_code_cell('''\
# ============================================================
# ETAPA 2 — TRIAGEM (Screening)
# ============================================================
print("=" * 60)
print("  ETAPA 2: TRIAGEM")
print("=" * 60)

df = df_raw.copy()
n0 = len(df)

# 2a. Remover artigos sem título
df = df[df["titulo"].notna() & (df["titulo"].str.strip() != "")]
n_sem_titulo = n0 - len(df)
print(f"  Sem título removidos    : {n_sem_titulo}")

# 2b. Normalizar título para detecção de duplicatas
df["_titulo_norm"] = (
    df["titulo"]
    .str.lower()
    .str.replace(r"[^\\w\\s]", "", regex=True)
    .str.strip()
)

# 2c. Remover duplicatas por título normalizado
n_antes = len(df)
df = df.drop_duplicates(subset=["_titulo_norm"], keep="first")
n_dup_titulo = n_antes - len(df)
print(f"  Duplicatas (título)     : {n_dup_titulo}")

# 2d. Remover duplicatas por DOI
doi_mask = df["doi"].notna() & (df["doi"] != "")
doi_dup  = df[doi_mask].duplicated(subset=["doi"], keep="first")
n_antes  = len(df)
df = df.drop(index=df[doi_mask][doi_dup].index)
n_dup_doi = n_antes - len(df)
print(f"  Duplicatas (DOI)        : {n_dup_doi}")

# 2e. Filtro de período
n_antes = len(df)
df = df[df["ano"].between(CONFIG["ano_min"], CONFIG["ano_max"])]
n_fora_periodo = n_antes - len(df)
print(f"  Fora do período         : {n_fora_periodo}")

# 2f. Filtro de idioma
n_antes = len(df)
df = df[df["idioma"].isin(CONFIG["idiomas_aceitos"] + ["", None])]
n_idioma = n_antes - len(df)
print(f"  Idioma não aceito       : {n_idioma}")

# 2g. Exclusão por palavras-chave
n_excl_kw = 0
if CONFIG["excluir_keywords"]:
    pat = "|".join(re.escape(k) for k in CONFIG["excluir_keywords"])
    mask = (
        df["titulo"].str.contains(pat, case=False, na=False) |
        df["abstract"].str.contains(pat, case=False, na=False)
    )
    n_excl_kw = mask.sum()
    df = df[~mask]
    print(f"  Excluídos por keywords  : {n_excl_kw}")

prisma_meta["triagem_excluidos"] = n0 - len(df)
prisma_meta["apos_triagem"]      = len(df)

print(f"\\n  Após triagem: {len(df)} artigos")
'''))

cells.append(new_markdown_cell("### Etapa 3 — Elegibilidade"))

cells.append(new_code_cell('''\
# ============================================================
# ETAPA 3 — ELEGIBILIDADE
# ============================================================
print("=" * 60)
print("  ETAPA 3: ELEGIBILIDADE")
print("=" * 60)

df_elig = df.copy()

# Score de relevância: conta quantos termos do tema aparecem
termos = [
    t.strip().lower()
    for t in re.sub(r"\\b(AND|OR|NOT)\\b", " ", CONFIG["tema"]).split()
    if len(t.strip()) > 2
]

def score_relevancia(row):
    texto = f"{row.get(\'titulo\', \'\')} {row.get(\'abstract\', \'\')}".lower()
    score = sum(1 for t in termos if t in texto)
    if row.get("abstract", ""):      # bônus por ter abstract
        score += 1
    return score

df_elig["score_relevancia"] = df_elig.apply(score_relevancia, axis=1)

# Critério de inclusão por palavras-chave
if CONFIG["incluir_keywords"]:
    pat_inc = "|".join(re.escape(k) for k in CONFIG["incluir_keywords"])
    mask_in = (
        df_elig["titulo"].str.contains(pat_inc, case=False, na=False) |
        df_elig["abstract"].str.contains(pat_inc, case=False, na=False)
    )
    n_inelig = len(df_elig) - mask_in.sum()
    df_elig  = df_elig[mask_in]
    print(f"  Inelegíveis (critério inclusão): {n_inelig}")
else:
    # Descarta artigos sem nenhum termo relevante
    n_antes  = len(df_elig)
    df_elig  = df_elig[df_elig["score_relevancia"] > 0]
    n_score0 = n_antes - len(df_elig)
    if n_score0:
        print(f"  Score zero removidos           : {n_score0}")

prisma_meta["elegibilidade_excluidos"] = prisma_meta["apos_triagem"] - len(df_elig)
prisma_meta["apos_elegibilidade"]      = len(df_elig)

print(f"  Após elegibilidade: {len(df_elig)} artigos")
'''))

cells.append(new_markdown_cell("### Etapa 4 — Inclusão"))

cells.append(new_code_cell('''\
# ============================================================
# ETAPA 4 — INCLUSÃO (Dataset Final)
# ============================================================
print("=" * 60)
print("  ETAPA 4: INCLUSÃO")
print("=" * 60)

df_final = df_elig.copy()

# Ordenação: score decrescente, depois ano decrescente
df_final = df_final.sort_values(
    ["score_relevancia", "ano"],
    ascending=[False, False]
).reset_index(drop=True)

# Limpeza final
df_final["titulo"]   = df_final["titulo"].str.strip()
df_final["abstract"] = df_final["abstract"].fillna("").str.strip()
df_final["autores"]  = df_final["autores"].fillna("Autor desconhecido")
df_final["journal"]  = df_final["journal"].fillna("Periódico desconhecido")
df_final["doi"]      = df_final["doi"].fillna("")
df_final["ano"]      = df_final["ano"].astype("Int64")  # suporta NaN inteiro

# Remove coluna auxiliar
df_final.drop(columns=["_titulo_norm"], errors="ignore", inplace=True)

prisma_meta["incluidos"] = len(df_final)

print(f"  Total incluído: {len(df_final)} artigos")
print(f"\\n  Por fonte:")
print(df_final["fonte"].value_counts().to_string())
print(f"\\n  Por ano:")
print(df_final["ano"].value_counts().sort_index().to_string())

display(
    df_final[["titulo", "autores", "ano", "journal", "fonte", "score_relevancia"]]
    .head(10)
    .style
    .set_caption("Primeiros 10 artigos incluídos")
    .background_gradient(subset=["score_relevancia"], cmap="Blues")
)
'''))

# ===========================================================
# SECAO 8 — LIMPEZA
# ===========================================================
cells.append(new_markdown_cell("## 8. Limpeza e Tratamento de Dados"))

cells.append(new_code_cell('''\
# ============================================================
# Limpeza e padronização do DataFrame final
# ============================================================

def limpar_texto(texto):
    """Remove espaços extras, caracteres de controle e normaliza."""
    if not isinstance(texto, str):
        return ""
    texto = re.sub(r"[\\x00-\\x1F\\x7F]", " ", texto)  # caracteres de controle
    texto = re.sub(r"\\s+", " ", texto).strip()
    return texto

df_final["titulo"]   = df_final["titulo"].apply(limpar_texto)
df_final["abstract"] = df_final["abstract"].apply(limpar_texto)
df_final["autores"]  = df_final["autores"].apply(limpar_texto)
df_final["journal"]  = df_final["journal"].apply(limpar_texto)

# Padronizar DOI: remove prefixo URL se houver
df_final["doi"] = (
    df_final["doi"]
    .str.replace("https://doi.org/", "", regex=False)
    .str.replace("http://dx.doi.org/", "", regex=False)
    .str.strip()
)

# Estatísticas de cobertura
total = len(df_final)
com_abstract = (df_final["abstract"] != "").sum()
com_doi      = (df_final["doi"] != "").sum()

print("Qualidade do Dataset Final:")
print(f"  Total de artigos       : {total}")
print(f"  Com abstract           : {com_abstract} ({100*com_abstract/total:.1f}%)")
print(f"  Com DOI                : {com_doi} ({100*com_doi/total:.1f}%)")
print(f"  Score médio relevância : {df_final[\'score_relevancia\'].mean():.2f}")
print(f"  Ano médio              : {df_final[\'ano\'].mean():.0f}")
'''))

# ===========================================================
# SECAO 9 — BIBLIOGRAFIA
# ===========================================================
cells.append(new_markdown_cell("""\
## 9. Sugestão de Bibliografia

O programa gera referências automaticamente nos formatos **ABNT NBR 6023:2018** e **APA 7ª edição**,
além de exportar em **BibTeX** para uso em LaTeX/Zotero/Mendeley.
"""))

cells.append(new_code_cell('''\
# ============================================================
# Formatadores de referência bibliográfica
# ============================================================

def fmt_abnt(row):
    """ABNT NBR 6023:2018."""
    autores = row.get("autores", "AUTOR DESCONHECIDO")
    partes  = [a.strip() for a in autores.split(";")]
    if len(partes) > 3:
        ref_autores = partes[0].upper() + " et al."
    else:
        ref_autores = "; ".join(p.upper() for p in partes)

    titulo  = str(row.get("titulo",  "")).strip()
    journal = str(row.get("journal", "")).strip()
    ano     = row.get("ano", "s.d.")
    doi     = row.get("doi",  "")
    url     = row.get("url",  "")

    ref = f"{ref_autores}. {titulo}. <b>{journal}</b>, {ano}."
    if doi:
        ref += f" DOI: {doi}."
    elif url:
        data_acesso = datetime.now().strftime("%d %b. %Y").lower()
        ref += f" Disponível em: &lt;{url}&gt;. Acesso em: {data_acesso}."
    return ref


def fmt_apa(row):
    """APA 7ª edição."""
    autores = row.get("autores", "Unknown Author")
    partes  = [a.strip() for a in autores.split(";")]
    if len(partes) > 20:
        ref_autores = ", ".join(partes[:19]) + " ... " + partes[-1]
    elif len(partes) > 1:
        ref_autores = ", ".join(partes[:-1]) + ", & " + partes[-1]
    else:
        ref_autores = partes[0]

    titulo  = str(row.get("titulo",  "")).strip()
    journal = str(row.get("journal", "")).strip()
    ano     = row.get("ano", "n.d.")
    doi     = row.get("doi",  "")
    url     = row.get("url",  "")

    ref = f"{ref_autores} ({ano}). {titulo}. <i>{journal}</i>."
    if doi:
        ref += f" https://doi.org/{doi}"
    elif url:
        ref += f" {url}"
    return ref


def fmt_bibtex(row, idx):
    """BibTeX."""
    autores = row.get("autores", "Unknown")
    titulo  = row.get("titulo",  "")
    journal = row.get("journal", "")
    ano     = row.get("ano",     0) or 0
    doi     = row.get("doi",     "")

    chave_base = re.sub(r"[^\\w]", "", autores.split(",")[0].split(";")[0].strip())[:10]
    key = f"{chave_base}{ano}_{idx}"

    bib  = f"@article{{{key},\\n"
    bib += f"  author  = {{{autores}}},\\n"
    bib += f"  title   = {{{titulo}}},\\n"
    bib += f"  journal = {{{journal}}},\\n"
    bib += f"  year    = {{{ano}}},\\n"
    if doi:
        bib += f"  doi     = {{{doi}}},\\n"
    bib += "}"
    return bib


# Gerar referências
fmt_fn = fmt_abnt if CONFIG["formato_bib"] == "abnt" else fmt_apa

df_final["referencia"] = [fmt_fn(row) for _, row in df_final.iterrows()]
df_final["bibtex"]     = [fmt_bibtex(row, i+1) for i, (_, row) in enumerate(df_final.iterrows())]

referencias = list(df_final["referencia"])

print(f"Formato: {CONFIG[\'formato_bib\'].upper()}")
print(f"Total de referências geradas: {len(referencias)}")
print("\\n" + "─" * 60)
print("TOP 10 ARTIGOS SUGERIDOS:")
print("─" * 60)
for i, ref in enumerate(referencias[:10], 1):
    display(HTML(f"<p style=\'margin:6px 0; font-size:13px\'><b>{i}.</b> {ref}</p>"))
'''))

# ===========================================================
# SECAO 10 — VISUALIZAÇÕES
# ===========================================================
cells.append(new_markdown_cell("## 10. Visualizações"))

cells.append(new_code_cell('''\
# ============================================================
# 10a. Fluxograma PRISMA 2020
# ============================================================

def desenhar_prisma(meta):
    fig, ax = plt.subplots(figsize=(12, 18))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 22)
    ax.axis("off")
    fig.patch.set_facecolor("#FAFAFA")

    COR = {
        "id":    "#1565C0",
        "tri":   "#E65100",
        "elig":  "#6A1B9A",
        "inc":   "#2E7D32",
        "excl":  "#C62828",
    }

    def caixa(x, y, w, h, texto, cor, fsize=10):
        rect = FancyBboxPatch(
            (x - w/2, y - h/2), w, h,
            boxstyle="round,pad=0.15",
            linewidth=2.5,
            edgecolor=cor,
            facecolor=cor + "18",
        )
        ax.add_patch(rect)
        ax.text(x, y, texto, ha="center", va="center",
                fontsize=fsize, multialignment="center",
                color="#1A1A1A", fontweight="bold", wrap=True)

    def seta(x, y1, y2, cor="#424242"):
        ax.annotate(
            "", xy=(x, y2 + 0.25), xytext=(x, y1 - 0.25),
            arrowprops=dict(arrowstyle="->", color=cor, lw=2.0)
        )

    def seta_lateral(x_src, x_dst, y, cor="#C62828"):
        ax.annotate(
            "", xy=(x_dst, y), xytext=(x_src, y),
            arrowprops=dict(arrowstyle="->", color=cor, lw=1.5)
        )

    # Título
    ax.text(5, 21.3,
            "Fluxograma PRISMA 2020",
            ha="center", va="center", fontsize=15, fontweight="bold")
    ax.text(5, 20.7,
            f"Tema: {CONFIG[\'tema\']}",
            ha="center", va="center", fontsize=9,
            color="#555555", style="italic")

    # Linha de separação
    ax.axhline(20.3, xmin=0.05, xmax=0.95, color="#BDBDBD", lw=1)

    # 1. IDENTIFICAÇÃO
    bases_str = "\\n".join(
        f"{k.title():18s} n={v}"
        for k, v in meta["por_base"].items()
        if v > 0
    )
    caixa(5, 18.8, 7.5, 2.4,
          f"IDENTIFICAÇÃO\\nRegistros identificados\\n{bases_str}\\nTotal: n={meta[\'identificados\']}",
          COR["id"], 10)
    seta(5, 17.6, 16.5)

    # 2. TRIAGEM
    caixa(5, 15.4, 7.5, 2.0,
          f"TRIAGEM\\nApós remoção de duplicatas e filtros\\nn={meta[\'apos_triagem\']}",
          COR["tri"], 10)
    caixa(8.8, 15.4, 2.8, 1.5,
          f"Excluídos\\nn={meta[\'triagem_excluidos\']}",
          COR["excl"], 9)
    seta_lateral(7.2, 7.4, 15.4)
    seta(5, 14.4, 13.4)

    # 3. ELEGIBILIDADE
    caixa(5, 12.3, 7.5, 2.0,
          f"ELEGIBILIDADE\\nAvaliados para elegibilidade\\nn={meta[\'apos_elegibilidade\']}",
          COR["elig"], 10)
    caixa(8.8, 12.3, 2.8, 1.5,
          f"Excluídos\\nn={meta[\'elegibilidade_excluidos\']}",
          COR["excl"], 9)
    seta_lateral(7.2, 7.4, 12.3)
    seta(5, 11.3, 10.3)

    # 4. INCLUSÃO
    caixa(5, 9.2, 7.5, 2.0,
          f"INCLUSÃO\\nEstudos incluídos na revisão\\nn={meta[\'incluidos\']}",
          COR["inc"], 11)

    plt.tight_layout()
    plt.savefig("prisma_flowchart.png", dpi=150, bbox_inches="tight",
                facecolor="#FAFAFA")
    plt.show()
    print("Fluxograma salvo: prisma_flowchart.png")

desenhar_prisma(prisma_meta)
'''))

cells.append(new_code_cell('''\
# ============================================================
# 10b. Publicações por Ano
# ============================================================
fig, ax = plt.subplots(figsize=(12, 5))

ano_counts = df_final["ano"].value_counts().sort_index()
bars = ax.bar(
    ano_counts.index.astype(str),
    ano_counts.values,
    color="#1565C0", edgecolor="white", linewidth=0.8
)
for bar in bars:
    h = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., h + 0.2,
            str(int(h)), ha="center", va="bottom", fontsize=9)

ax.set_title(f"Publicações por Ano\\n{CONFIG[\'tema\']}",
             fontsize=13, fontweight="bold", pad=15)
ax.set_xlabel("Ano",               fontsize=11)
ax.set_ylabel("Número de Artigos", fontsize=11)
ax.set_facecolor("#F8F9FA")
fig.patch.set_facecolor("#FFFFFF")
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig("publicacoes_por_ano.png", dpi=150, bbox_inches="tight")
plt.show()
print("Gráfico salvo: publicacoes_por_ano.png")
'''))

cells.append(new_code_cell('''\
# ============================================================
# 10c. Distribuição por Base de Dados
# ============================================================
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

fonte_counts = df_final["fonte"].value_counts()
cores = ["#1565C0", "#E65100", "#6A1B9A", "#2E7D32", "#C62828"]

# Barras horizontais
bars = axes[0].barh(
    fonte_counts.index, fonte_counts.values,
    color=cores[:len(fonte_counts)], edgecolor="white"
)
for bar in bars:
    w = bar.get_width()
    axes[0].text(w + 0.2, bar.get_y() + bar.get_height()/2.,
                 str(int(w)), va="center", fontsize=9)
axes[0].set_title("Artigos por Base de Dados",
                  fontsize=12, fontweight="bold")
axes[0].set_xlabel("Número de Artigos")
axes[0].set_facecolor("#F8F9FA")

# Gráfico de pizza
wedges, texts, autotexts = axes[1].pie(
    fonte_counts.values,
    labels=fonte_counts.index,
    colors=cores[:len(fonte_counts)],
    autopct="%1.1f%%",
    startangle=90,
    wedgeprops=dict(edgecolor="white", linewidth=2),
)
axes[1].set_title("Distribuição por Base (%)",
                  fontsize=12, fontweight="bold")

fig.patch.set_facecolor("#FFFFFF")
plt.tight_layout()
plt.savefig("distribuicao_fontes.png", dpi=150, bbox_inches="tight")
plt.show()
print("Gráfico salvo: distribuicao_fontes.png")
'''))

cells.append(new_code_cell('''\
# ============================================================
# 10d. Nuvem de Palavras (títulos + abstracts)
# ============================================================
if WORDCLOUD_OK:
    texto_corpus = " ".join(
        f"{r[\'titulo\']} {r[\'abstract\']}"
        for _, r in df_final.iterrows()
    )

    # Stopwords customizadas
    stopwords_custom = {
        "the","a","an","and","or","for","in","on","at","to","of",
        "with","by","from","is","are","was","were","be","been",
        "being","this","that","these","those","it","its","as","we",
        "our","their","has","have","had","not","also","can","may",
        "which","than","more","other","using","used","based","study",
        "data","results","analysis","paper","method","approach",
        "proposed","propose","show","shows","showed","two","one",
        "three","new","high","large","different","such","well",
    }

    wc = WordCloud(
        width=1400, height=700,
        background_color="white",
        colormap="Blues",
        stopwords=stopwords_custom,
        max_words=120,
        min_font_size=10,
        collocations=False,
    ).generate(texto_corpus)

    fig, ax = plt.subplots(figsize=(16, 8))
    ax.imshow(wc, interpolation="bilinear")
    ax.axis("off")
    ax.set_title(f"Nuvem de Palavras — {CONFIG[\'tema\']}",
                 fontsize=14, fontweight="bold", pad=15)
    plt.tight_layout()
    plt.savefig("wordcloud.png", dpi=150, bbox_inches="tight")
    plt.show()
    print("Nuvem de palavras salva: wordcloud.png")
else:
    print("wordcloud não instalado. Execute: pip install wordcloud")
'''))

cells.append(new_code_cell('''\
# ============================================================
# 10e. Top 15 Artigos — Tabela Estilizada
# ============================================================
df_top = df_final[[
    "titulo", "autores", "ano", "journal", "fonte", "score_relevancia"
]].head(15).copy()
df_top.index = range(1, len(df_top) + 1)
df_top["titulo_curto"] = df_top["titulo"].str[:80] + "…"

display(
    df_top[["titulo_curto", "autores", "ano", "journal", "fonte", "score_relevancia"]]
    .rename(columns={
        "titulo_curto":     "Título",
        "autores":          "Autores",
        "ano":              "Ano",
        "journal":          "Periódico",
        "fonte":            "Base",
        "score_relevancia": "Score",
    })
    .style
    .background_gradient(subset=["Score"], cmap="Blues")
    .set_caption(f"Top 15 artigos mais relevantes — {CONFIG[\'tema\']}")
    .set_table_styles([
        {"selector": "th",
         "props": [("background-color", "#1565C0"),
                   ("color", "white"),
                   ("font-weight", "bold"),
                   ("font-size", "12px")]},
        {"selector": "td",
         "props": [("font-size", "11px")]},
    ])
)
'''))

# ===========================================================
# SECAO 11 — EXPORTAÇÃO
# ===========================================================
cells.append(new_markdown_cell("## 11. Exportação dos Resultados"))

cells.append(new_code_cell('''\
# ============================================================
# Exportação: CSV · BibTeX · JSON · HTML
# ============================================================
timestamp  = datetime.now().strftime("%Y%m%d_%H%M%S")
slug       = re.sub(r"[^\\w]", "_", CONFIG["tema"])[:30]
nome_base  = f"prisma_{slug}_{timestamp}"

arquivos_gerados = []

# 1. CSV
csv_path = f"{nome_base}.csv"
df_final.drop(
    columns=["bibtex", "referencia"], errors="ignore"
).to_csv(csv_path, index=False, encoding="utf-8-sig")
arquivos_gerados.append(csv_path)

# 2. BibTeX
bib_path = f"{nome_base}.bib"
with open(bib_path, "w", encoding="utf-8") as f:
    f.write(f"% PRISMA 2020 — {CONFIG[\'tema\']}\\n")
    f.write(f"% Gerado em: {datetime.now().strftime(\'%Y-%m-%d %H:%M\')}\\n\\n")
    f.write("\\n\\n".join(df_final["bibtex"].tolist()))
arquivos_gerados.append(bib_path)

# 3. JSON com metadados PRISMA
json_path = f"{nome_base}_meta.json"
with open(json_path, "w", encoding="utf-8") as f:
    json.dump({
        "tema":          CONFIG["tema"],
        "data_coleta":   datetime.now().isoformat(),
        "periodo":       f"{CONFIG[\'ano_min\']}-{CONFIG[\'ano_max\']}",
        "bases_ativas":  [k for k, v in CONFIG["bases"].items() if v],
        "fluxo_prisma":  prisma_meta,
        "total_incluidos": len(df_final),
    }, f, ensure_ascii=False, indent=2)
arquivos_gerados.append(json_path)

# 4. Relatório HTML
html_path = f"{nome_base}.html"

rows_html = ""
for i, (_, row) in enumerate(df_final.iterrows(), 1):
    rows_html += (
        f"<tr>"
        f"<td>{i}</td>"
        f"<td><a href=\'{row.get(\'url\',\'\')}\' target=\'_blank\'>"
        f"{row.get(\'titulo\',\'\')}</a></td>"
        f"<td>{row.get(\'autores\',\'\')}</td>"
        f"<td>{row.get(\'ano\',\'\')}</td>"
        f"<td>{row.get(\'journal\',\'\')}</td>"
        f"<td>{row.get(\'fonte\',\'\')}</td>"
        f"<td>{row.get(\'score_relevancia\',\'\')}</td>"
        f"</tr>\\n"
    )

refs_html = "\\n".join(
    f"<p class=\'ref\'><b>{i}.</b> {r}</p>"
    for i, r in enumerate(df_final["referencia"].tolist(), 1)
)

html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<title>PRISMA 2020 — {CONFIG[\'tema\']}</title>
<style>
  body     {{ font-family: Arial, sans-serif; max-width: 1200px;
              margin: 0 auto; padding: 20px; color: #212121; }}
  h1       {{ color: #1565C0; }}
  h2       {{ color: #1565C0; border-bottom: 2px solid #1565C0; padding-bottom:4px; }}
  .meta    {{ background:#E3F2FD; padding:15px; border-radius:8px; margin:15px 0; }}
  table    {{ border-collapse:collapse; width:100%; margin:15px 0; }}
  th       {{ background:#1565C0; color:white; padding:8px; text-align:left; }}
  td       {{ border:1px solid #ddd; padding:7px; font-size:13px; }}
  tr:nth-child(even) {{ background:#F5F5F5; }}
  .ref     {{ margin:6px 0; font-size:13px; line-height:1.7; }}
  a        {{ color:#1565C0; }}
  .prisma  {{ display:flex; gap:20px; flex-wrap:wrap; }}
  .pbox    {{ border:2px solid; border-radius:8px; padding:12px;
              min-width:180px; text-align:center; font-size:14px; }}
</style>
</head>
<body>
<h1>Revisão Sistemática — Protocolo PRISMA 2020</h1>
<div class="meta">
  <b>Tema:</b> {CONFIG[\'tema\']}<br>
  <b>Período:</b> {CONFIG[\'ano_min\']} – {CONFIG[\'ano_max\']}<br>
  <b>Bases:</b> {", ".join(k for k,v in CONFIG["bases"].items() if v)}<br>
  <b>Data da coleta:</b> {datetime.now().strftime(\'%d/%m/%Y %H:%M\')}<br>
  <b>Artigos incluídos:</b> {len(df_final)}
</div>

<h2>Fluxo PRISMA 2020</h2>
<div class="prisma">
  <div class="pbox" style="border-color:#1565C0;background:#E3F2FD">
    <b>IDENTIFICAÇÃO</b><br>n={prisma_meta[\'identificados\']}
  </div>
  <div class="pbox" style="border-color:#E65100;background:#FFF3E0">
    <b>TRIAGEM</b><br>n={prisma_meta[\'apos_triagem\']}
  </div>
  <div class="pbox" style="border-color:#6A1B9A;background:#F3E5F5">
    <b>ELEGIBILIDADE</b><br>n={prisma_meta[\'apos_elegibilidade\']}
  </div>
  <div class="pbox" style="border-color:#2E7D32;background:#E8F5E9">
    <b>INCLUSÃO</b><br>n={prisma_meta[\'incluidos\']}
  </div>
</div>

<h2>Artigos Incluídos</h2>
<table>
<tr><th>#</th><th>Título</th><th>Autores</th><th>Ano</th>
    <th>Periódico</th><th>Base</th><th>Score</th></tr>
{rows_html}
</table>

<h2>Referências ({CONFIG[\'formato_bib\'].upper()})</h2>
{refs_html}

<hr>
<p style="font-size:11px;color:#757575">
  Gerado automaticamente por PRISMA 2020 Scraper —
  Disciplina Python e Scraper/Crawler
</p>
</body>
</html>"""

with open(html_path, "w", encoding="utf-8") as f:
    f.write(html)
arquivos_gerados.append(html_path)

print("\\n✅ Exportação concluída!")
for a in arquivos_gerados:
    print(f"   📄 {a}")
'''))

# ===========================================================
# ENCERRAMENTO
# ===========================================================
cells.append(new_markdown_cell("## 12. Encerramento"))

cells.append(new_code_cell('''\
# Encerra o Chrome Headless
if driver:
    driver.quit()
    print("✅ Chrome encerrado.")

print("\\n" + "=" * 55)
print("  REVISÃO SISTEMÁTICA CONCLUÍDA")
print("=" * 55)
print(f"  Tema        : {CONFIG[\'tema\']}")
print(f"  Identificados : {prisma_meta[\'identificados\']}")
print(f"  Após triagem  : {prisma_meta[\'apos_triagem\']}")
print(f"  Após elig.    : {prisma_meta[\'apos_elegibilidade\']}")
print(f"  INCLUÍDOS     : {prisma_meta[\'incluidos\']}")
print("=" * 55)
'''))

# ===========================================================
# MONTA E SALVA O NOTEBOOK
# ===========================================================
nb = new_notebook(cells=cells)
nb.metadata["kernelspec"] = {
    "display_name": "Python 3",
    "language": "python",
    "name": "python3",
}
nb.metadata["language_info"] = {
    "name": "python",
    "version": "3.10.0",
}
nb.metadata["colab"] = {
    "name": "PRISMA_2020_Revisao_Sistematica.ipynb",
    "provenance": [],
}

output_path = "PRISMA_2020_Revisao_Sistematica.ipynb"
with open(output_path, "w", encoding="utf-8") as f:
    nbformat.write(nb, f)

print(f"Notebook gerado: {output_path}")
