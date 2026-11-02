# PRISMA 2020 — Revisão Sistemática da Literatura
### Projeto Final — Disciplina Python e Scraper/Crawler

> **Disciplina:** Sistemas de Informação  
> **Professor:** Guilherme de Cleva Farto  
> **Curso:** Python e Scraper/Crawler — 2º Semestre  
> **Aluno:** Arthur Naoto Miura — RA 2311600029

---

## Sobre o Projeto

Este notebook implementa o **Protocolo PRISMA 2020** (*Preferred Reporting Items
for Systematic Reviews and Meta-Analyses*) de forma automatizada, aplicando as
técnicas de Web Scraping estudadas em sala de aula para coleta e análise de
artigos científicos.

### O que é PRISMA 2020?

PRISMA é um protocolo internacional para condução de revisões sistemáticas da
literatura. Define um fluxo de 4 etapas:

```
IDENTIFICAÇÃO → TRIAGEM → ELEGIBILIDADE → INCLUSÃO
```

Este notebook automatiza cada etapa, desde a busca até a geração do relatório final.

---

## Bases de Dados Suportadas

| Base | Tecnologia | Cobertura |
|---|---|---|
| **PubMed** | Selenium + BeautifulSoup + Entrez API | Biomédica |
| **arXiv** | BeautifulSoup (XML) | CS, Física, Matemática |
| **Semantic Scholar** | REST API | Multidisciplinar |
| **OpenAlex** | REST API | +200 milhões de artigos |

---

## Tecnologias Utilizadas

| Tecnologia | Uso |
|---|---|
| **Selenium** | Navegação automatizada no PubMed, paginação dinâmica |
| **BeautifulSoup** | Parsing de HTML (PubMed) e XML (arXiv) |
| **requests** | Chamadas às APIs REST |
| **pandas** | Estruturação, limpeza e tratamento dos dados |
| **matplotlib / plotly** | Gráficos e fluxograma PRISMA |
| **wordcloud** | Nuvem de palavras dos títulos/abstracts |
| **Biopython (Entrez)** | Coleta de metadados completos do PubMed |

---

## Como Usar

### Opção 1 — Google Colab (recomendado)

1. Acesse [Google Colab](https://colab.research.google.com)
2. `Arquivo → Abrir notebook → GitHub` e cole a URL deste repositório
3. Abra `PRISMA_2020_Revisao_Sistematica.ipynb`
4. Na **Célula 3 (Configuração)**, edite:
   - `"tema"`: sua pergunta de pesquisa
   - `"bases"`: ative/desative as bases
   - `"ano_min"` / `"ano_max"`: período de interesse
5. Execute tudo: `Runtime → Run all`

### Opção 2 — Local (Jupyter Lab)

```bash
# 1. Clone o repositório
git clone https://github.com/<seu-usuario>/prisma-scraper.git
cd prisma-scraper

# 2. Instale as dependências
pip install -r requirements.txt

# 3. Inicie o Jupyter Lab
jupyter lab

# 4. Abra PRISMA_2020_Revisao_Sistematica.ipynb
```

> **Pré-requisito local:** [Google Chrome](https://www.google.com/chrome/) instalado.
> O `webdriver-manager` baixa o ChromeDriver automaticamente.

---

## Configuração Rápida

Edite apenas a **Célula 3** do notebook:

```python
CONFIG = {
    "tema": "machine learning AND healthcare",  # ← MUDE AQUI
    "bases": {
        "pubmed":           True,
        "arxiv":            True,
        "semantic_scholar": True,
        "openalex":         True,
    },
    "ano_min": 2019,
    "ano_max":  2024,
    "max_por_base": 50,
    "formato_bib": "abnt",  # "abnt" ou "apa"
}
```

### Exemplos de Temas

```python
# Tecnologia
"tema": "blockchain AND supply chain management"
"tema": "deep learning AND object detection"
"tema": "natural language processing AND sentiment analysis"

# Saúde
"tema": "artificial intelligence AND cancer diagnosis"
"tema": "telemedicine AND patient outcomes"

# Ciências Sociais
"tema": "social media AND mental health"
"tema": "machine learning AND education"
```

---

## Saídas Geradas

Após a execução completa, o notebook gera:

| Arquivo | Descrição |
|---|---|
| `prisma_*.csv` | Dataset completo dos artigos incluídos |
| `prisma_*.bib` | Referências em formato BibTeX |
| `prisma_*_meta.json` | Metadados do fluxo PRISMA |
| `prisma_*.html` | Relatório HTML completo |
| `prisma_flowchart.png` | Fluxograma PRISMA 2020 |
| `publicacoes_por_ano.png` | Gráfico de publicações por ano |
| `distribuicao_fontes.png` | Distribuição por base de dados |
| `wordcloud.png` | Nuvem de palavras |

---

## Estrutura do Repositório

```
prisma-scraper/
├── PRISMA_2020_Revisao_Sistematica.ipynb  # Notebook principal
├── requirements.txt                        # Dependências Python
├── README.md                               # Esta documentação
├── .gitignore                              # Arquivos ignorados
└── create_notebook.py                      # Script gerador do notebook
```

---

## Referências

- PAGE, M. J. et al. The PRISMA 2020 statement: an updated guideline for reporting
  systematic reviews. **BMJ**, v. 372, n. 71, 2021. DOI: 10.1136/bmj.n71

- NCBI E-utilities. **Entrez Programming Utilities Help**. Disponível em:
  https://www.ncbi.nlm.nih.gov/books/NBK25499/

- OpenAlex. **OpenAlex API Documentation**. Disponível em: https://docs.openalex.org

- Semantic Scholar. **Academic Graph API**. Disponível em:
  https://api.semanticscholar.org/graph/v1

---

*Projeto desenvolvido para a disciplina Python e Scraper/Crawler — Sistema de Informação*
