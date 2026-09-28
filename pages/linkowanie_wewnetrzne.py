import os
import json
import re
import time
import urllib.request
import xml.etree.ElementTree as ET
from urllib.parse import urlparse, urlunparse

import pandas as pd
import streamlit as st
import trafilatura

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


# ============================================================
# KONFIGURACJA
# ============================================================

st.set_page_config(
    page_title="Linkowanie Wewnętrzne AI",
    layout="wide"
)

if "article_text" not in st.session_state:
    st.session_state.article_text = ""

if "article_url" not in st.session_state:
    st.session_state.article_url = ""

if "sitemap_url" not in st.session_state:
    st.session_state.sitemap_url = ""

if "analysis_results" not in st.session_state:
    st.session_state.analysis_results = None

if "selected_anchors" not in st.session_state:
    st.session_state.selected_anchors = []

if "candidate_urls" not in st.session_state:
    st.session_state.candidate_urls = []

if "final_results" not in st.session_state:
    st.session_state.final_results = None

if "searched_anchors" not in st.session_state:
    st.session_state.searched_anchors = set()


IGNORED_EXTENSIONS = (
    ".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".bmp", ".ico",
    ".pdf", ".zip", ".rar", ".doc", ".docx", ".xls", ".xlsx",
    ".mp3", ".mp4", ".avi", ".mov", ".webm"
)

GENERIC_ANCHORS = {
    "kliknij",
    "tutaj",
    "więcej",
    "czytaj więcej",
    "dowiedz się więcej",
    "sprawdź",
    "zobacz",
    "strona",
    "oferta",
    "nasza oferta",
    "więcej informacji",
    "sprawdź tutaj",
    "kliknij tutaj",
    "dowiedz się",
    "czytaj",
}

STOP_WORDS = {
    "i", "a", "o", "u", "w", "z", "na", "do", "od", "po", "dla",
    "ze", "za", "pod", "nad", "przy", "czy", "jak", "co", "to",
    "ten", "ta", "te", "jest", "są", "być", "się", "nie", "tak",
    "oraz", "lub", "ale", "jego", "jej", "ich", "który", "która",
    "które", "których", "którym", "może", "mogą", "bardzo", "już",
    "też", "tym", "tych", "czyli", "więc", "przez", "bez", "nad",
    "między", "ze", "we", "tym", "ten", "tej", "tego"
}


# ============================================================
# POMOCNICZE
# ============================================================

def normalize_url(url):
    """Normalizuje URL do porównań."""
    if not url:
        return ""

    url = url.strip()

    try:
        parsed = urlparse(url)

        scheme = parsed.scheme.lower()
        netloc = parsed.netloc.lower()

        if netloc.startswith("www."):
            netloc = netloc[4:]

        path = parsed.path or "/"
        path = re.sub(r"/+", "/", path)

        if path != "/" and path.endswith("/"):
            path = path[:-1]

        return urlunparse((
            scheme,
            netloc,
            path,
            "",
            "",
            ""
        ))
    except Exception:
        return url.rstrip("/").lower()


def same_url(url1, url2):
    return normalize_url(url1) == normalize_url(url2)


def tokenize(text):
    """Dzieli tekst na sensowne słowa."""
    return re.findall(r"[A-Za-zĄĆĘŁŃÓŚŹŻąćęłńóśźż0-9]+", text.lower())


def clean_anchor(anchor):
    anchor = re.sub(r"\s+", " ", anchor or "").strip()
    anchor = anchor.strip(".,;:!?()[]{}\"'")
    return anchor


def is_useful_anchor(anchor):
    """Podstawowy filtr jakości anchorów."""
    anchor = clean_anchor(anchor)
    words = tokenize(anchor)

    if not anchor or not words:
        return False

    if anchor.lower() in GENERIC_ANCHORS:
        return False

    if len(words) == 1 and len(words[0]) < 4:
        return False

    # Odrzucamy bardzo długie fragmenty, które raczej nie są anchorami.
    if len(words) > 8:
        return False

    # Fraza składająca się prawie wyłącznie ze stop words nie jest dobrym anchorem.
    meaningful = [w for w in words if w not in STOP_WORDS]
    if not meaningful:
        return False

    return True


def extract_existing_links(markdown_text):
    """
    Wyciąga linki Markdown:
    [anchor](https://example.com)
    """
    pattern = re.compile(
        r"\[([^\]]+)\]\((https?://[^)\s]+)\)",
        re.IGNORECASE
    )

    links = []

    for match in pattern.finditer(markdown_text or ""):
        links.append({
            "anchor": clean_anchor(match.group(1)),
            "url": match.group(2).strip()
        })

    return links


def anchor_is_already_linked(anchor, existing_links):
    anchor_norm = re.sub(r"\s+", " ", anchor.lower()).strip()

    for link in existing_links:
        existing_norm = re.sub(
            r"\s+",
            " ",
            link["anchor"].lower()
        ).strip()

        if anchor_norm == existing_norm:
            return link["url"]

    return None


# ============================================================
# POBIERANIE TREŚCI
# ============================================================

def extract_structured_text_from_url(url):
    try:
        downloaded = trafilatura.fetch_url(url)

        if not downloaded:
            return None

        text = trafilatura.extract(
            downloaded,
            output_format="markdown",
            include_formatting=True,
            include_links=True
        )

        return text if text else None

    except Exception as e:
        st.error(f"Błąd podczas pobierania treści z URL: {e}")
        return None


# ============================================================
# SITEMAP
# ============================================================

def get_sitemap_from_robots(url_or_domain):
    try:
        parsed = urlparse(url_or_domain)

        scheme = parsed.scheme if parsed.scheme else "https"
        netloc = (
            parsed.netloc
            if parsed.netloc
            else parsed.path.split("/")[0]
        )

        if not netloc:
            return None

        robots_url = f"{scheme}://{netloc}/robots.txt"

        req = urllib.request.Request(
            robots_url,
            headers={"User-Agent": "Mozilla/5.0"}
        )

        with urllib.request.urlopen(req, timeout=8) as response:
            content = response.read().decode(
                "utf-8",
                errors="ignore"
            )

        for line in content.splitlines():
            if line.strip().lower().startswith("sitemap:"):
                return line.split(":", 1)[1].strip()

        return None

    except Exception:
        return None


def fetch_and_parse_xml(url):
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/xml,text/xml;q=0.9,*/*;q=0.8"
    }

    req = urllib.request.Request(
        url,
        headers=headers
    )

    with urllib.request.urlopen(req, timeout=15) as response:
        xml_data = response.read()

    return ET.fromstring(xml_data)


def get_urls_from_sitemap(
    url,
    progress_callback=None,
    visited=None,
    total_state=None
):
    """
    Obsługuje:
    - zwykłą sitemapę URL-i,
    - sitemap index,
    - zagnieżdżone sitemap-y.
    """

    if visited is None:
        visited = set()

    if total_state is None:
        total_state = {"count": 0}

    if url in visited:
        return []

    visited.add(url)

    urls = []

    try:
        root = fetch_and_parse_xml(url)
    except Exception:
        return urls

    sub_sitemaps = []
    page_urls = []

    for elem in root.iter():
        if not elem.tag.endswith("loc") or not elem.text:
            continue

        loc = elem.text.strip()
        loc_lower = loc.lower()

        if loc_lower.endswith(IGNORED_EXTENSIONS):
            continue

        if (
            loc_lower.endswith(".xml")
            or "sitemap" in loc_lower
        ):
            if (
                "image" not in loc_lower
                and "photo" not in loc_lower
            ):
                sub_sitemaps.append(loc)
        else:
            page_urls.append(loc)

    urls.extend(page_urls)

    total_state["count"] += len(page_urls)

    if progress_callback:
        progress_callback(
            f"Pobrano {total_state['count']} URL-i..."
        )

    for sub_url in sub_sitemaps:
        if sub_url not in visited:
            urls.extend(
                get_urls_from_sitemap(
                    sub_url,
                    progress_callback,
                    visited,
                    total_state
                )
            )

    # Zachowujemy kolejność i usuwamy duplikaty.
    unique = []
    seen = set()

    for item in urls:
        norm = normalize_url(item)

        if norm not in seen:
            seen.add(norm)
            unique.append(item)

    return unique


# ============================================================
# WSTĘPNY RANKING URL-I — BEZ AI
# ============================================================

def url_path_tokens(url):
    parsed = urlparse(url)

    text = (
        parsed.path.replace("-", " ")
        .replace("_", " ")
        .replace("/", " ")
    )

    return set(tokenize(text))


def score_url_for_anchor(anchor, url):
    """
    Wstępny, deterministyczny ranking URL-i.
    AI dostaje później tylko najlepszych kandydatów.
    """

    anchor_tokens = [
        w for w in tokenize(anchor)
        if w not in STOP_WORDS
    ]

    if not anchor_tokens:
        return 0

    url_tokens = url_path_tokens(url)

    score = 0

    # Dokładne słowa z anchoru w URL.
    for token in anchor_tokens:
        if token in url_tokens:
            score += 15

    # Bardzo mocny sygnał, jeśli cała fraza występuje w ścieżce.
    path = urlparse(url).path.lower()

    anchor_slug = "-".join(anchor_tokens)

    if anchor_slug and anchor_slug in path:
        score += 45

    # Wszystkie znaczące słowa anchoru znajdują się w URL.
    if all(token in url_tokens for token in anchor_tokens):
        score += 35

    # Preferuj krótsze i bardziej konkretne ścieżki.
    path_parts = [
        part for part in urlparse(url).path.split("/")
        if part
    ]

    if len(path_parts) <= 2:
        score += 5
    elif len(path_parts) >= 5:
        score -= 5

    return score


def rank_candidate_urls(anchor, urls, max_candidates=30):
    scored = []

    for url in urls:
        score = score_url_for_anchor(anchor, url)

        if score > 0:
            scored.append((score, url))

    scored.sort(
        key=lambda x: (-x[0], len(x[1]))
    )

    return [
        {
            "url": url,
            "score": score
        }
        for score, url in scored[:max_candidates]
    ]


# ============================================================
# POBIERANIE DANYCH STRONY DO OCENY AI
# ============================================================

def fetch_page_metadata(url):
    """
    Pobiera title i H1.
    Nie pobieramy całej treści wszystkich URL-i,
    bo byłoby to bardzo wolne.
    """

    try:
        downloaded = trafilatura.fetch_url(url)

        if not downloaded:
            return {
                "url": url,
                "title": "",
                "h1": ""
            }

        from bs4 import BeautifulSoup

        soup = BeautifulSoup(
            downloaded,
            "html.parser"
        )

        title = ""
        if soup.title:
            title = soup.title.get_text(
                " ",
                strip=True
            )

        h1 = ""
        h1_tag = soup.find("h1")

        if h1_tag:
            h1 = h1_tag.get_text(
                " ",
                strip=True
            )

        return {
            "url": url,
            "title": title[:300],
            "h1": h1[:300]
        }

    except Exception:
        return {
            "url": url,
            "title": "",
            "h1": ""
        }


# ============================================================
# AI — WYKRYWANIE ANCHORÓW
# ============================================================

def extract_keywords_with_ai(api_key, article_text):
    if not OPENAI_AVAILABLE:
        raise RuntimeError(
            "Biblioteka openai nie jest zainstalowana."
        )

    client = OpenAI(api_key=api_key)

    prompt = f"""
Przeanalizuj tekst artykułu pod kątem linkowania wewnętrznego.

Znajdź maksymalnie 25 konkretnych fraz, które naturalnie
występują w tekście i mogą być dobrymi anchorami do linków
wewnętrznych.

WAŻNE:
- wybieraj frazy tematyczne i konkretne,
- preferuj nazwy usług, kategorii, produktów, zagadnień,
  miejsc, problemów lub konkretnych pojęć,
- nie wybieraj "kliknij tutaj", "więcej", "sprawdź",
  "nasza oferta", "czytaj więcej" itp.,
- nie wymyślaj fraz, których nie ma w tekście,
- nie wybieraj całych zdań,
- preferuj 1–5 słów,
- jeśli fraza jest już częścią istniejącego linku Markdown,
  oznacz ją jako już zalinkowaną,
- jedna fraza może wystąpić w tekście wiele razy,
  ale zwróć ją tylko raz.

Dla każdej frazy zwróć:
- anchor
- status: "brak linku" albo pełny istniejący URL
- occurrence_count: liczbę wystąpień frazy w tekście

Zwróć WYŁĄCZNIE JSON:
{{
  "items": [
    {{
      "anchor": "dokładna fraza",
      "status": "brak linku",
      "occurrence_count": 2
    }}
  ]
}}

TEKST:
{article_text[:20000]}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "Jesteś ekspertem SEO od architektury "
                    "informacji i linkowania wewnętrznego. "
                    "Zwracasz wyłącznie poprawny JSON."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        response_format={"type": "json_object"},
        temperature=0.1
    )

    content = response.choices[0].message.content
    data = json.loads(content)

    items = data.get("items", [])

    existing_links = extract_existing_links(
        article_text
    )

    rows = []

    for item in items:
        if not isinstance(item, dict):
            continue

        anchor = clean_anchor(
            item.get("anchor", "")
        )

        if not is_useful_anchor(anchor):
            continue

        linked_url = anchor_is_already_linked(
            anchor,
            existing_links
        )

        if linked_url:
            status = linked_url
        else:
            status = "brak linku"

        try:
            occurrence_count = int(
                item.get("occurrence_count", 0)
            )
        except Exception:
            occurrence_count = 0

        rows.append({
            "Fraza / Anchor": anchor,
            "Status linkowania": status,
            "Wystąpienia": occurrence_count
        })

    # Usunięcie duplikatów anchorów.
    unique_rows = []
    seen = set()

    for row in rows:
        key = row["Fraza / Anchor"].lower()

        if key not in seen:
            seen.add(key)
            unique_rows.append(row)

    return pd.DataFrame(unique_rows)


# ============================================================
# AI — WYBÓR NAJLEPSZEGO URL-A
# ============================================================

def match_anchor_to_candidates(
    api_key,
    anchor,
    article_context,
    candidates,
    is_ecommerce
):
    if not candidates:
        return None

    if not OPENAI_AVAILABLE:
        raise RuntimeError(
            "Biblioteka openai nie jest zainstalowana."
        )

    client = OpenAI(api_key=api_key)

    ecommerce_instruction = ""

    if is_ecommerce:
        ecommerce_instruction = """
Dla sklepu internetowego preferuj:
- kategorie,
- podkategorie,
- strony zbiorcze.

Unikaj pojedynczego produktu, jeżeli istnieje
odpowiednia kategoria lub strona zbiorcza.
"""

    candidate_lines = []

    for item in candidates:
        candidate_lines.append(
            f"URL: {item['url']}\n"
            f"Wstępny scoring URL: {item['score']}\n"
            f"TITLE: {item.get('title', '')}\n"
            f"H1: {item.get('h1', '')}"
        )

    candidates_text = "\n\n".join(
        candidate_lines
    )

    prompt = f"""
Wybierz najlepszą stronę docelową dla linku
wewnętrznego z anchoru:

ANCHOR:
{anchor}

KONTEKST ARTYKUŁU:
{article_context[:5000]}

KANDYDACI:
{candidates_text}

{ecommerce_instruction}

Zasady:
1. URL musi być rzeczywiście tematycznie związany z anchorem.
2. Nie wybieraj URL tylko dlatego, że zawiera podobne słowo.
3. TITLE i H1 są ważniejsze niż przypadkowa zgodność słów w URL.
4. Jeśli żaden kandydat nie jest wystarczająco dobry,
   zwróć "no_match".
5. Nie wymyślaj URL.
6. Nie wybieraj strony źródłowej, jeśli pojawi się na liście.
7. Uzasadnienie ma być krótkie i konkretne.

Zwróć WYŁĄCZNIE JSON:
{{
  "url": "pełny URL albo no_match",
  "confidence": "wysoka|średnia|niska",
  "reason": "krótkie uzasadnienie"
}}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "Jesteś ekspertem SEO. "
                    "Oceniasz wyłącznie przedstawione URL-e. "
                    "Nie wymyślasz adresów."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        response_format={"type": "json_object"},
        temperature=0.0
    )

    content = response.choices[0].message.content
    result = json.loads(content)

    return result


# ============================================================
# UI
# ============================================================

st.markdown(
    "<h1>Linkowanie Wewnętrzne AI</h1>",
    unsafe_allow_html=True
)

st.caption(
    "Analiza anchorów i rekomendacja docelowych URL-i. "
    "Linki nie są automatycznie wstawiane do tekstu."
)


# ============================================================
# API KEY
# ============================================================

secret_key = (
    st.secrets.get("OPENAI_API_KEY")
    or os.environ.get("OPENAI_API_KEY")
)

if secret_key:
    api_key_input = secret_key
else:
    api_key_input = st.sidebar.text_input(
        "Klucz OpenAI API:",
        type="password"
    )


# ============================================================
# KROK 1
# ============================================================

st.markdown("---")
st.subheader("1. Treść artykułu")

input_type = st.radio(
    "Sposób wprowadzania artykułu:",
    [
        "Wklej tekst ręcznie",
        "Pobierz z adresu URL"
    ],
    horizontal=True
)

current_text = ""

if input_type == "Wklej tekst ręcznie":

    current_text = st.text_area(
        "Wklej tutaj tekst artykułu:",
        height=260
    )

else:

    article_url = st.text_input(
        "Adres URL artykułu:",
        placeholder="https://twojadomena.pl/moj-artykul"
    )

    if article_url:

        st.session_state.article_url = article_url

        with st.spinner(
            "Pobieranie treści wraz z istniejącymi linkami..."
        ):
            fetched_text = extract_structured_text_from_url(
                article_url
            )

        if fetched_text:

            current_text = fetched_text

            st.success(
                f"Pobrano treść ({len(current_text)} znaków)."
            )

        else:

            st.error(
                "Nie udało się pobrać treści z URL."
            )


if current_text:

    st.write("**Podgląd treści:**")

    with st.container(height=320):
        st.markdown(current_text)


analyze_btn = st.button(
    "Krok 1: Analizuj tekst i wykryj anchory",
    type="primary"
)


if analyze_btn:

    if not api_key_input:

        st.error(
            "Wprowadź Klucz OpenAI API."
        )

    elif not current_text.strip():

        st.error(
            "Podaj treść artykułu lub URL."
        )

    else:

        start_time = time.time()

        try:

            with st.spinner(
                "AI analizuje tekst i wykrywa potencjalne anchory..."
            ):

                results = extract_keywords_with_ai(
                    api_key_input,
                    current_text
                )

            st.session_state.article_text = current_text
            st.session_state.analysis_results = results
            st.session_state.selected_anchors = []
            st.session_state.final_results = None
            st.session_state.searched_anchors = set()

            elapsed = time.time() - start_time

            st.success(
                f"Analiza zakończona w {elapsed:.1f} s."
            )

            st.rerun()

        except Exception as e:

            st.error(
                f"Błąd analizy tekstu: {e}"
            )


# ============================================================
# KROK 2
# ============================================================

if st.session_state.analysis_results is not None:

    st.markdown("---")
    st.subheader("2. Wybierz frazy do linkowania")

    if st.session_state.final_results is not None:
        st.info(
            "Możesz wrócić do tej listy w dowolnym momencie, "
            "zaznaczyć kolejne frazy i ponownie uruchomić wyszukiwanie. "
            "Wcześniejsze rekomendacje zostaną zachowane."
        )

    df = st.session_state.analysis_results

    if df.empty:

        st.warning(
            "Nie znaleziono odpowiednich anchorów."
        )

    else:

        st.write(
            "Zaznacz tylko te frazy, dla których chcesz "
            "otrzymać propozycję strony docelowej."
        )

        selected = []

        for idx, row in df.iterrows():

            anchor = row["Fraza / Anchor"]
            status = row["Status linkowania"]
            occurrences = row["Wystąpienia"]

            col1, col2, col3, col4 = st.columns(
                [0.7, 4, 3, 1]
            )

            checked = col1.checkbox(
                "",
                key=f"anchor_{idx}"
            )

            col2.write(anchor)

            if anchor.lower() in {
                a.lower() for a in st.session_state.searched_anchors
            }:
                col2.caption("✓ już przeszukana")

            if status.startswith("http"):

                col3.markdown(
                    f"[Już zalinkowane]({status})"
                )

            else:

                col3.write("Brak linku")

            col4.write(
                str(occurrences)
            )

            if checked:
                selected.append(anchor)

        st.session_state.selected_anchors = selected

        st.info(
            f"Wybrano: {len(selected)} fraz."
        )


# ============================================================
# KROK 3 — SITEMAP
# ============================================================

if (
    st.session_state.analysis_results is not None
    and len(st.session_state.selected_anchors) > 0
):

    st.markdown("---")
    st.subheader("3. Sitemapa i filtrowanie URL-i")

    is_ecommerce_site = st.checkbox(
        "Mam sklep internetowy — preferuj kategorie "
        "i strony zbiorcze zamiast pojedynczych produktów",
        value=False
    )

    fetch_robots_btn = st.button(
        "Pobierz automatycznie sitemapę z robots.txt"
    )

    if fetch_robots_btn:

        target = st.session_state.article_url

        if not target:

            st.warning(
                "Automatyczne pobranie z robots.txt wymaga "
                "podania URL artykułu w Kroku 1."
            )

        else:

            with st.spinner(
                "Sprawdzanie robots.txt..."
            ):

                found = get_sitemap_from_robots(
                    target
                )

            if found:

                st.session_state.sitemap_url = found

                st.success(
                    f"Znaleziono sitemapę: {found}"
                )

            else:

                st.error(
                    "Nie znaleziono sitemapy w robots.txt."
                )


    sitemap_input = st.text_input(
        "Adres sitemapy XML:",
        value=st.session_state.sitemap_url,
        placeholder="https://twojadomena.pl/sitemap.xml"
    )


    col_inc, col_exc = st.columns(2)

    with col_inc:

        include_filter = st.text_input(
            "Musi zawierać w URL:",
            placeholder="/c/, /kategoria/"
        )

    with col_exc:

        exclude_filter = st.text_input(
            "Wyklucz z URL:",
            placeholder="/p/, /tag/, /autor/"
        )


    source_url = st.session_state.article_url

    already_searched = st.session_state.searched_anchors.intersection(
        set(st.session_state.selected_anchors)
    )

    new_selected = [
        anchor
        for anchor in st.session_state.selected_anchors
        if anchor not in st.session_state.searched_anchors
    ]

    if st.session_state.final_results is not None:
        st.caption(
            f"Nowo wybrane frazy: {len(new_selected)} | "
            f"Wcześniej przeszukane: {len(already_searched)}"
        )
        match_button_label = "Ponownie przeszukaj zaznaczone frazy"
    else:
        match_button_label = (
            "Krok 3: Znajdź najlepsze URL-e dla wybranych fraz"
        )

    match_btn = st.button(
        match_button_label,
        type="primary",
        use_container_width=True
    )


    if match_btn:

        anchors_to_search = [
            anchor
            for anchor in st.session_state.selected_anchors
            if anchor not in st.session_state.searched_anchors
        ]

        if not anchors_to_search:
            st.warning(
                "Nie wybrano nowych fraz do wyszukania. "
                "Zaznacz nową frazę na liście powyżej."
            )
            st.stop()

        if not sitemap_input:

            st.error(
                "Wprowadź adres sitemapy XML."
            )

        else:

            try:

                progress = st.progress(0)
                status = st.empty()

                status.write(
                    "Pobieranie i parsowanie sitemapy..."
                )

                raw_urls = get_urls_from_sitemap(
                    sitemap_input
                )

                progress.progress(25)

                if not raw_urls:

                    st.error(
                        "Nie udało się pobrać URL-i z sitemapy."
                    )

                    st.stop()


                filtered_urls = raw_urls[:]


                # ------------------------------------------------
                # FILTR INCLUDE
                # ------------------------------------------------

                if include_filter.strip():

                    patterns = [
                        p.strip().lower()
                        for p in include_filter.split(",")
                        if p.strip()
                    ]

                    filtered_urls = [
                        url
                        for url in filtered_urls
                        if any(
                            p in url.lower()
                            for p in patterns
                        )
                    ]


                # ------------------------------------------------
                # FILTR EXCLUDE
                # ------------------------------------------------

                if exclude_filter.strip():

                    patterns = [
                        p.strip().lower()
                        for p in exclude_filter.split(",")
                        if p.strip()
                    ]

                    filtered_urls = [
                        url
                        for url in filtered_urls
                        if not any(
                            p in url.lower()
                            for p in patterns
                        )
                    ]


                # ------------------------------------------------
                # NIE LINKUJEMY DO TEJ SAMEJ STRONY
                # ------------------------------------------------

                if source_url:

                    filtered_urls = [
                        url
                        for url in filtered_urls
                        if not same_url(
                            url,
                            source_url
                        )
                    ]


                progress.progress(35)

                st.info(
                    f"Sitemap zawiera {len(raw_urls)} URL-i. "
                    f"Po filtrach pozostało {len(filtered_urls)}."
                )


                # ------------------------------------------------
                # RANKING PROGRAMISTYCZNY
                # ------------------------------------------------

                status.write(
                    "Tworzenie wstępnego rankingu kandydatów..."
                )

                candidates_by_anchor = {}

                for anchor in anchors_to_search:

                    candidates = rank_candidate_urls(
                        anchor,
                        filtered_urls,
                        max_candidates=20
                    )

                    candidates_by_anchor[anchor] = candidates


                progress.progress(50)


                # ------------------------------------------------
                # POBIERANIE TITLE + H1 TYLKO DLA KANDYDATÓW
                # ------------------------------------------------

                unique_candidate_urls = []

                for candidates in candidates_by_anchor.values():

                    for item in candidates:

                        if item["url"] not in unique_candidate_urls:

                            unique_candidate_urls.append(
                                item["url"]
                            )


                metadata_cache = {}

                status.write(
                    f"Sprawdzanie Title/H1 dla "
                    f"{len(unique_candidate_urls)} kandydatów..."
                )


                # Maksymalnie 100 stron w jednym uruchomieniu.
                unique_candidate_urls = (
                    unique_candidate_urls[:100]
                )


                for i, url in enumerate(
                    unique_candidate_urls
                ):

                    metadata_cache[url] = (
                        fetch_page_metadata(url)
                    )

                    progress.progress(
                        50 + int(
                            ((i + 1) /
                             max(1, len(unique_candidate_urls)))
                            * 20
                        )
                    )


                # ------------------------------------------------
                # AI FINALNE DOPASOWANIE
                # ------------------------------------------------

                status.write(
                    "AI ocenia najlepsze dopasowania..."
                )

                final_rows = []

                article_context = (
                    st.session_state.article_text
                )

                for index, anchor in enumerate(
                    anchors_to_search
                ):

                    candidates = candidates_by_anchor.get(
                        anchor,
                        []
                    )

                    enriched_candidates = []

                    for item in candidates:

                        metadata = metadata_cache.get(
                            item["url"],
                            {}
                        )

                        enriched_candidates.append({
                            "url": item["url"],
                            "score": item["score"],
                            "title": metadata.get(
                                "title",
                                ""
                            ),
                            "h1": metadata.get(
                                "h1",
                                ""
                            )
                        })


                    result = match_anchor_to_candidates(
                        api_key_input,
                        anchor,
                        article_context,
                        enriched_candidates,
                        is_ecommerce_site
                    )


                    if not result:
                        continue


                    selected_url = result.get(
                        "url",
                        ""
                    )


                    if selected_url == "no_match":

                        final_rows.append({
                            "Anchor": anchor,
                            "Rekomendowany URL": "",
                            "Dopasowanie": "Brak odpowiedniego URL",
                            "Uzasadnienie": (
                                result.get(
                                    "reason",
                                    "Brak wystarczająco dobrego dopasowania."
                                )
                            )
                        })

                    else:

                        # Bezpieczeństwo:
                        # AI może wybrać tylko URL znajdujący
                        # się wśród przedstawionych kandydatów.
                        valid_urls = {
                            item["url"]
                            for item in enriched_candidates
                        }

                        if selected_url not in valid_urls:

                            final_rows.append({
                                "Anchor": anchor,
                                "Rekomendowany URL": "",
                                "Dopasowanie": "Brak odpowiedniego URL",
                                "Uzasadnienie": (
                                    "AI zwróciło URL spoza listy "
                                    "zweryfikowanych kandydatów."
                                )
                            })

                        else:

                            final_rows.append({
                                "Anchor": anchor,
                                "Rekomendowany URL": selected_url,
                                "Dopasowanie": result.get(
                                    "confidence",
                                    "nieokreślone"
                                ),
                                "Uzasadnienie": result.get(
                                    "reason",
                                    ""
                                )
                            })


                    progress.progress(
                        70 + int(
                            ((index + 1) /
                             max(
                                 1,
                                 len(anchors_to_search)
                             ))
                            * 30
                        )
                    )


                progress.progress(100)

                status.success(
                    "Gotowe. Linki nie zostały automatycznie "
                    "wstawione do tekstu."
                )


                final_df = pd.DataFrame(
                    final_rows
                )

                # Zapamiętujemy, które anchory zostały już przeszukane.
                st.session_state.searched_anchors.update(
                    anchors_to_search
                )

                # Nie kasujemy wcześniejszych wyników.
                # Nowe rekomendacje są dokładane do istniejącego raportu.
                if (
                    st.session_state.final_results is not None
                    and not st.session_state.final_results.empty
                ):
                    previous_df = st.session_state.final_results

                    combined_df = pd.concat(
                        [previous_df, final_df],
                        ignore_index=True
                    )

                    # Ten sam anchor może pojawić się tylko raz w raporcie.
                    combined_df = combined_df.drop_duplicates(
                        subset=["Anchor"],
                        keep="last"
                    )

                    st.session_state.final_results = combined_df

                else:
                    st.session_state.final_results = final_df

                st.rerun()


            except Exception as e:

                st.error(
                    f"Błąd podczas analizy sitemapy: {e}"
                )


# ============================================================
# WYNIKI
# ============================================================

if st.session_state.final_results is not None:

    st.markdown("---")
    st.subheader(
        "4. Rekomendowane linkowanie"
    )

    st.write(
        "Poniżej znajdują się propozycje. "
        "Narzędzie **nie modyfikuje artykułu** — "
        "linki należy dodać ręcznie."
    )

    result_df = st.session_state.final_results.copy()


    if result_df.empty:

        st.warning(
            "Nie znaleziono rekomendacji."
        )

    else:

        st.dataframe(
            result_df,
            use_container_width=True,
            column_config={
                "Rekomendowany URL": st.column_config.LinkColumn(
                    "Rekomendowany URL",
                    help=(
                        "Kliknij, aby otworzyć stronę "
                        "docelową."
                    )
                )
            },
            hide_index=True
        )


        # -----------------------------------------------
        # PODSUMOWANIE
        # -----------------------------------------------

        valid_count = int(
            (
                result_df["Rekomendowany URL"]
                .fillna("")
                .astype(str)
                .str.strip()
                != ""
            ).sum()
        )

        no_match_count = len(result_df) - valid_count


        c1, c2 = st.columns(2)

        c1.metric(
            "Znalezione dopasowania",
            valid_count
        )

        c2.metric(
            "Brak odpowiedniego URL",
            no_match_count
        )


        # -----------------------------------------------
        # CSV
        # -----------------------------------------------

        csv_data = result_df.to_csv(
            index=False
        ).encode("utf-8-sig")

        st.download_button(
            label="Pobierz raport CSV",
            data=csv_data,
            file_name="linkowanie_wewnetrzne.csv",
            mime="text/csv"
        )


        st.info(
            "Linki nie są automatycznie wstawiane do artykułu. "
            "Możesz teraz ręcznie dodać wybrane linki albo wrócić "
            "do listy anchorów powyżej, zaznaczyć kolejne frazy "
            "i kliknąć „Ponownie przeszukaj zaznaczone frazy”. "
            "Wcześniejsze rekomendacje pozostaną w raporcie."
        )
