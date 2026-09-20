import streamlit as st
import requests
import re
import html
import trafilatura
from bs4 import BeautifulSoup
from urllib.parse import urlparse


# =========================================================
# KONFIGURACJA
# =========================================================

st.set_page_config(
    page_title="SEO Tools AI",
    page_icon="🔗",
    layout="wide"
)


# =========================================================
# CSS
# =========================================================

st.markdown(
    """
    <style>

    .main {
        background: #f7f8fa;
    }

    .hero {
        padding: 45px 0 35px 0;
    }

    .hero h1 {
        font-size: 42px;
        font-weight: 700;
        margin-bottom: 10px;
        color: #111827;
    }

    .hero p {
        font-size: 18px;
        color: #6b7280;
        margin-top: 0;
    }

    .page-title {
        font-size: 32px;
        font-weight: 700;
        color: #111827;
        margin-bottom: 8px;
    }

    .page-description {
        color: #6b7280;
        font-size: 16px;
        margin-bottom: 30px;
    }

    .article-preview {
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 30px 40px;
        margin-top: 20px;
        color: #1f2937;
        line-height: 1.75;
        font-size: 16px;
        height: 520px;
        overflow-y: auto;
        scroll-behavior: smooth;
    }

    .article-preview h1 {
        font-size: 30px;
        margin-top: 0;
        margin-bottom: 20px;
        color: #111827;
    }

    .article-preview h2 {
        font-size: 24px;
        margin-top: 30px;
        margin-bottom: 12px;
        color: #111827;
    }

    .article-preview h3 {
        font-size: 20px;
        margin-top: 25px;
        margin-bottom: 10px;
        color: #111827;
    }

    .article-preview h4 {
        font-size: 18px;
        margin-top: 20px;
        margin-bottom: 8px;
        color: #111827;
    }

    .article-preview p {
        margin-bottom: 16px;
    }

    .article-preview ul,
    .article-preview ol {
        margin-bottom: 18px;
        padding-left: 25px;
    }

    .diagnostic {
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 10px;
        padding: 15px 20px;
        margin-top: 15px;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# =========================================================
# POBIERANIE HTML STRONY
# =========================================================

@st.cache_data(ttl=3600)
def download_page(url):

    response = requests.get(
        url,
        timeout=30,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/153.0.0.0 Safari/537.36"
            )
        }
    )

    response.raise_for_status()

    return response.text


# =========================================================
# CZYSZCZENIE TEKSTU MARKDOWN
# =========================================================

def clean_markdown_text(text):

    # Usuwamy obrazki Markdown
    text = re.sub(
        r"!\[[^\]]*\]\([^)]+\)",
        "",
        text
    )

    # Zamieniamy link Markdown na sam tekst
    text = re.sub(
        r"\[([^\]]+)\]\([^)]+\)",
        r"\1",
        text
    )

    # Usuwamy ewentualne HTML
    text = re.sub(
        r"<[^>]+>",
        "",
        text
    )

    # Usuwamy nadmiarowe gwiazdki pogrubienia
    text = re.sub(
        r"\*\*(.*?)\*\*",
        r"\1",
        text
    )

    # Usuwamy pojedyncze gwiazdki kursywy
    text = re.sub(
        r"\*(.*?)\*",
        r"\1",
        text
    )

    return text.strip()


# =========================================================
# KONWERSJA MARKDOWN → HTML
# =========================================================

def markdown_to_article_html(markdown_text):

    lines = markdown_text.splitlines()

    output = []

    paragraph_buffer = []

    in_list = False
    list_type = None

    def flush_paragraph():

        nonlocal paragraph_buffer

        if not paragraph_buffer:
            return

        text = " ".join(
            x.strip()
            for x in paragraph_buffer
            if x.strip()
        )

        paragraph_buffer = []

        if not text:
            return

        text = clean_markdown_text(text)

        if text:
            output.append(
                f"<p>{html.escape(text)}</p>"
            )

    def close_list():

        nonlocal in_list
        nonlocal list_type

        if in_list:

            output.append(
                f"</{list_type}>"
            )

            in_list = False
            list_type = None

    for raw_line in lines:

        line = raw_line.strip()

        # -------------------------------------------------
        # PUSTA LINIA
        # -------------------------------------------------

        if not line:

            flush_paragraph()

            continue

        # -------------------------------------------------
        # NAGŁÓWKI MARKDOWN
        # -------------------------------------------------

        heading_match = re.match(
            r"^\s*(#{1,6})\s+(.+?)\s*$",
            line
        )

        if heading_match:

            flush_paragraph()
            close_list()

            level = len(
                heading_match.group(1)
            )

            # W naszym podglądzie obsługujemy H1-H4.
            # H5/H6 traktujemy jako H4.
            if level > 4:
                level = 4

            heading_text = heading_match.group(2)

            heading_text = clean_markdown_text(
                heading_text
            )

            if heading_text:

                output.append(
                    f"<h{level}>"
                    f"{html.escape(heading_text)}"
                    f"</h{level}>"
                )

            continue

        # -------------------------------------------------
        # NAGŁÓWKI, KTÓRE TRAFILATURA MOŻE ZWRÓCIĆ
        # Z DODATKOWYM ZNAKIEM #
        # -------------------------------------------------

        heading_match = re.match(
            r"^#{1,6}(.+?)$",
            line
        )

        if heading_match and not line.startswith(
            ("#",)
        ):

            flush_paragraph()
            close_list()

            continue

        # -------------------------------------------------
        # LISTA NIEUPORZĄDKOWANA
        # -------------------------------------------------

        unordered_match = re.match(
            r"^[-*+]\s+(.+)$",
            line
        )

        # -------------------------------------------------
        # LISTA UPORZĄDKOWANA
        # -------------------------------------------------

        ordered_match = re.match(
            r"^\d+[.)]\s+(.+)$",
            line
        )

        if unordered_match or ordered_match:

            flush_paragraph()

            current_type = (
                "ul"
                if unordered_match
                else "ol"
            )

            item_text = (
                unordered_match.group(1)
                if unordered_match
                else ordered_match.group(1)
            )

            if not in_list:

                in_list = True
                list_type = current_type

                output.append(
                    f"<{list_type}>"
                )

            elif list_type != current_type:

                close_list()

                in_list = True
                list_type = current_type

                output.append(
                    f"<{list_type}>"
                )

            item_text = clean_markdown_text(
                item_text
            )

            output.append(
                f"<li>{html.escape(item_text)}</li>"
            )

            continue

        # -------------------------------------------------
        # ZWYKŁY TEKST
        # -------------------------------------------------

        close_list()

        paragraph_buffer.append(
            line
        )

    # -----------------------------------------------------
    # DOMKNIĘCIE
    # -----------------------------------------------------

    flush_paragraph()
    close_list()

    return "".join(output)


# =========================================================
# EKSTRAKCJA ARTYKUŁU
# =========================================================

@st.cache_data(ttl=3600)
def extract_article_content(url):

    raw_html = download_page(
        url
    )

    # -----------------------------------------------------
    # TRAFILATURA
    # -----------------------------------------------------

    extracted = trafilatura.extract(
        raw_html,
        output_format="markdown",
        include_links=False,
        include_images=False,
        include_tables=True,
        include_formatting=True,
        favor_precision=False,
        favor_recall=True
    )

    if not extracted:

        raise ValueError(
            "Nie udało się wyodrębnić głównej "
            "treści strony."
        )

    # -----------------------------------------------------
    # USUWAMY ŚMIECI
    # -----------------------------------------------------

    extracted = re.sub(
        r"\[svg\]\([^)]+\)",
        "",
        extracted,
        flags=re.IGNORECASE
    )

    extracted = re.sub(
        r"\[image[^\]]*\]\([^)]+\)",
        "",
        extracted,
        flags=re.IGNORECASE
    )

    # -----------------------------------------------------
    # MARKDOWN → HTML
    # -----------------------------------------------------

    article_html = markdown_to_article_html(
        extracted
    )

    # -----------------------------------------------------
    # WALIDACJA
    # -----------------------------------------------------

    clean_text = BeautifulSoup(
        article_html,
        "html.parser"
    ).get_text(
        " ",
        strip=True
    )

    if len(clean_text) < 200:

        raise ValueError(
            "Znaleziono zbyt mało tekstu "
            "w głównej treści strony."
        )

    # -----------------------------------------------------
    # STATYSTYKI
    # -----------------------------------------------------

    soup = BeautifulSoup(
        article_html,
        "html.parser"
    )

    stats = {
        "h1": len(
            soup.find_all("h1")
        ),
        "h2": len(
            soup.find_all("h2")
        ),
        "h3": len(
            soup.find_all("h3")
        ),
        "h4": len(
            soup.find_all("h4")
        ),
        "paragraphs": len(
            soup.find_all("p")
        ),
        "lists": len(
            soup.find_all(["ul", "ol"])
        ),
        "characters": len(
            clean_text
        )
    }

    return article_html, stats


# =========================================================
# SITEMAP
# =========================================================

@st.cache_data(ttl=3600)
def get_sitemap_urls(sitemap_url):

    response = requests.get(
        sitemap_url,
        timeout=20,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/153.0.0.0 Safari/537.36"
            )
        }
    )

    response.raise_for_status()

    soup = BeautifulSoup(
        response.content,
        "xml"
    )

    # -----------------------------------------------------
    # SITEMAP INDEX
    # -----------------------------------------------------

    sitemap_tags = soup.find_all(
        "sitemap"
    )

    if sitemap_tags:

        sitemap_links = []

        for sitemap in sitemap_tags:

            loc = sitemap.find("loc")

            if loc:

                url = loc.get_text(
                    strip=True
                )

                if url:

                    sitemap_links.append(
                        url
                    )

        all_urls = []

        for child_sitemap in sitemap_links:

            try:

                child_response = requests.get(
                    child_sitemap,
                    timeout=20,
                    headers={
                        "User-Agent": (
                            "Mozilla/5.0 "
                            "(Windows NT 10.0; Win64; x64) "
                            "AppleWebKit/537.36 "
                            "(KHTML, like Gecko) "
                            "Chrome/153.0.0.0 "
                            "Safari/537.36"
                        )
                    }
                )

                child_response.raise_for_status()

                child_soup = BeautifulSoup(
                    child_response.content,
                    "xml"
                )

                for url_tag in child_soup.find_all(
                    "url"
                ):

                    loc = url_tag.find("loc")

                    if loc:

                        url = loc.get_text(
                            strip=True
                        )

                        if url:

                            all_urls.append(
                                url
                            )

            except Exception:

                continue

        return list(
            dict.fromkeys(all_urls)
        )

    # -----------------------------------------------------
    # ZWYKŁA SITEMAPA
    # -----------------------------------------------------

    urls = []

    for url_tag in soup.find_all(
        "url"
    ):

        loc = url_tag.find("loc")

        if loc:

            url = loc.get_text(
                strip=True
            )

            if url:

                urls.append(
                    url
                )

    return list(
        dict.fromkeys(urls)
    )


# =========================================================
# DOMENA
# =========================================================

def get_domain(url):

    parsed = urlparse(url)

    return parsed.netloc.lower().replace(
        "www.",
        ""
    )


# =========================================================
# NAWIGACJA
# =========================================================

if "page" not in st.session_state:

    st.session_state["page"] = "home"


# =========================================================
# STRONA INTERNAL LINKING
# =========================================================

if st.session_state["page"] == "internal_links":

    st.markdown(
        '<div class="page-title">'
        '🔗 Internal Linking AI'
        '</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="page-description">'
        'Znajdź naturalne miejsca na linki wewnętrzne '
        'w swoim artykule.'
        '</div>',
        unsafe_allow_html=True
    )

    # -----------------------------------------------------
    # ŹRÓDŁO ARTYKUŁU
    # -----------------------------------------------------

    mode = st.radio(
        "Wybierz źródło tekstu:",
        [
            "Mam już artykuł na stronie",
            "Artykuł nie jest jeszcze opublikowany"
        ],
        horizontal=True
    )

    article_url = ""
    article_text = ""

    if mode == "Mam już artykuł na stronie":

        article_url = st.text_input(
            "URL artykułu",
            placeholder="https://twojastrona.pl/artykul/"
        )

    else:

        article_text = st.text_area(
            "Wklej treść artykułu",
            height=250,
            placeholder="Wklej tutaj cały tekst artykułu..."
        )

    # -----------------------------------------------------
    # SITEMAP
    # -----------------------------------------------------

    sitemap_url = st.text_input(
        "URL sitemap",
        placeholder="https://twojastrona.pl/sitemap.xml"
    )

    # -----------------------------------------------------
    # ANALIZA
    # -----------------------------------------------------

    analyze = st.button(
        "🔍 Analizuj",
        type="primary",
        use_container_width=True
    )

    if analyze:

        # =================================================
        # WALIDACJA
        # =================================================

        if mode == "Mam już artykuł na stronie":

            if not article_url.strip():

                st.error(
                    "Podaj URL artykułu."
                )

                st.stop()

        else:

            if not article_text.strip():

                st.error(
                    "Wklej treść artykułu."
                )

                st.stop()

        if not sitemap_url.strip():

            st.error(
                "Podaj URL sitemap."
            )

            st.stop()

        # =================================================
        # ARTYKUŁ Z URL
        # =================================================

        if mode == "Mam już artykuł na stronie":

            try:

                with st.spinner(
                    "Pobieram i oczyszczam artykuł..."
                ):

                    article_html, stats = (
                        extract_article_content(
                            article_url
                        )
                    )

                st.success(
                    "Strona została pobrana."
                )

                # -----------------------------------------
                # DIAGNOSTYKA
                # -----------------------------------------

                with st.expander(
                    "Diagnostyka pobranej treści"
                ):

                    col1, col2, col3, col4 = (
                        st.columns(4)
                    )

                    with col1:
                        st.metric(
                            "H1",
                            stats["h1"]
                        )

                    with col2:
                        st.metric(
                            "H2",
                            stats["h2"]
                        )

                    with col3:
                        st.metric(
                            "H3",
                            stats["h3"]
                        )

                    with col4:
                        st.metric(
                            "Akapity",
                            stats["paragraphs"]
                        )

                    st.write(
                        f"Znaki: {stats['characters']}"
                    )

            except Exception as e:

                st.error(
                    f"Nie udało się pobrać artykułu: {e}"
                )

                st.stop()

        # =================================================
        # TEKST WKLEJONY
        # =================================================

        else:

            paragraphs = article_text.split(
                "\n"
            )

            article_html = ""

            for paragraph in paragraphs:

                paragraph = paragraph.strip()

                if paragraph:

                    article_html += (
                        f"<p>{html.escape(paragraph)}</p>"
                    )

            st.success(
                "Tekst został wczytany."
            )

        # =================================================
        # PODGLĄD
        # =================================================

        st.markdown(
            "### Podgląd treści artykułu"
        )

        st.markdown(
            f"""
            <div class="article-preview">
                {article_html}
            </div>
            """,
            unsafe_allow_html=True
        )

        # =================================================
        # SITEMAP
        # =================================================

        try:

            with st.spinner(
                "Analizuję sitemapę..."
            ):

                sitemap_urls = get_sitemap_urls(
                    sitemap_url
                )

            if not sitemap_urls:

                st.warning(
                    "Nie znaleziono żadnych URL-i w sitemapie."
                )

            else:

                st.success(
                    f"Znaleziono {len(sitemap_urls)} adresów URL."
                )

                sitemap_domain = get_domain(
                    sitemap_url
                )

                st.markdown(
                    "### Znalezione podstrony"
                )

                st.caption(
                    f"Domena: {sitemap_domain}"
                )

                display_urls = sitemap_urls[:100]

                for index, url in enumerate(
                    display_urls,
                    start=1
                ):

                    st.markdown(
                        f"**{index}.** {url}"
                    )

                if len(sitemap_urls) > 100:

                    st.info(
                        f"Wyświetlam pierwsze 100 z "
                        f"{len(sitemap_urls)} znalezionych URL-i."
                    )

        except Exception as e:

            st.error(
                f"Nie udało się pobrać sitemap: {e}"
            )

    # -----------------------------------------------------
    # POWRÓT
    # -----------------------------------------------------

    st.markdown("---")

    if st.button(
        "← Wróć do narzędzi"
    ):

        st.session_state["page"] = "home"

        st.rerun()

    st.stop()


# =========================================================
# STRONA GŁÓWNA
# =========================================================

st.markdown(
    """
    <div class="hero">
        <h1>SEO Tools AI</h1>
        <p>
            Proste narzędzia SEO wykorzystujące AI
            do codziennej pracy.
        </p>
    </div>
    """,
    unsafe_allow_html=True
)


# =========================================================
# KAFELKI
# =========================================================

col1, col2, col3 = st.columns(3)


with col1:

    with st.container(border=True):

        st.markdown(
            "### 🔗 Internal Linking AI"
        )

        st.write(
            "Znajdź naturalne miejsca na "
            "linki wewnętrzne w artykule."
        )

        st.caption(
            "Analiza treści + sitemap + AI"
        )

        if st.button(
            "Otwórz narzędzie",
            key="internal_links_button",
            use_container_width=True
        ):

            st.session_state["page"] = (
                "internal_links"
            )

            st.rerun()


with col2:

    with st.container(border=True):

        st.markdown(
            "### 🔎 SEO Audit"
        )

        st.write(
            "Szybka analiza podstawowych "
            "elementów SEO strony."
        )

        st.caption(
            "Wkrótce"
        )

        st.info(
            "Narzędzie będzie dostępne wkrótce."
        )


with col3:

    with st.container(border=True):

        st.markdown(
            "### ✍️ Content Analysis"
        )

        st.write(
            "Analiza treści pod kątem SEO, "
            "struktury i tematów."
        )

        st.caption(
            "Wkrótce"
        )

        st.info(
            "Narzędzie będzie dostępne wkrótce."
        )
