import streamlit as st
import requests
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

    </style>
    """,
    unsafe_allow_html=True
)


# =========================================================
# FUNKCJA POMOCNICZA
# =========================================================

def clean_container(container):
    """
    Usuwa z kontenera elementy techniczne, nawigacyjne
    i elementy, które nie są właściwą treścią.
    """

    # Usuwamy elementy, których nie chcemy analizować
    for tag in container.find_all([
        "script",
        "style",
        "noscript",
        "template",
        "svg",
        "iframe",
        "canvas",
        "form",
        "nav",
        "footer",
        "header",
        "aside"
    ]):
        tag.decompose()

    # Usuwamy elementy ukryte
    for tag in container.find_all(
        style=lambda value: value and (
            "display:none" in value.replace(" ", "").lower()
            or "visibility:hidden" in value.replace(" ", "").lower()
        )
    ):
        tag.decompose()

    # Usuwamy elementy typu title/meta
    for tag in container.find_all([
        "title",
        "meta",
        "link"
    ]):
        tag.decompose()

    return container


# =========================================================
# WYBÓR NAJLEPSZEGO KONTENERA TREŚCI
# =========================================================

def find_best_content_container(soup):

    # Najpierw czyścimy dokument z oczywistych śmieci
    for tag in soup.find_all([
        "script",
        "style",
        "noscript",
        "template",
        "svg",
        "iframe",
        "canvas",
        "form",
        "nav",
        "footer",
        "header",
        "aside"
    ]):
        tag.decompose()

    candidates = []

    # -----------------------------------------------------
    # 1. Semantyczne kontenery
    # -----------------------------------------------------

    for selector in [
        "article",
        "main",
        "[role='main']"
    ]:

        for element in soup.select(selector):

            text = element.get_text(
                " ",
                strip=True
            )

            paragraphs = element.find_all("p")

            headings = element.find_all([
                "h1",
                "h2",
                "h3",
                "h4"
            ])

            if len(text) >= 300:

                candidates.append({
                    "element": element,
                    "text_length": len(text),
                    "paragraphs": len(paragraphs),
                    "headings": len(headings),
                    "score": (
                        len(text)
                        + len(paragraphs) * 300
                        + len(headings) * 100
                    )
                })

    # -----------------------------------------------------
    # 2. Szukamy kontenera zawierającego H1
    # -----------------------------------------------------

    h1 = soup.find("h1")

    if h1:

        parent = h1.parent

        levels_checked = 0

        while parent and parent.name not in [
            "body",
            "html"
        ] and levels_checked < 8:

            text = parent.get_text(
                " ",
                strip=True
            )

            paragraphs = parent.find_all("p")

            headings = parent.find_all([
                "h1",
                "h2",
                "h3",
                "h4"
            ])

            if (
                len(text) >= 500
                and len(paragraphs) >= 2
            ):

                candidates.append({
                    "element": parent,
                    "text_length": len(text),
                    "paragraphs": len(paragraphs),
                    "headings": len(headings),
                    "score": (
                        len(text)
                        + len(paragraphs) * 300
                        + len(headings) * 100
                    )
                })

            parent = parent.parent
            levels_checked += 1

    # -----------------------------------------------------
    # 3. Jeżeli mamy kandydatów, wybieramy najlepszego
    # -----------------------------------------------------

    if candidates:

        # Sortujemy po wyniku
        candidates.sort(
            key=lambda item: item["score"],
            reverse=True
        )

        return candidates[0]["element"]

    # -----------------------------------------------------
    # 4. Ostateczny fallback
    # -----------------------------------------------------

    if soup.body:
        return soup.body

    return soup


# =========================================================
# POBIERANIE ARTYKUŁU
# =========================================================

@st.cache_data(ttl=3600)
def extract_article_content(url):

    response = requests.get(
        url,
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
        response.text,
        "html.parser"
    )

    # Znajdujemy właściwy kontener
    content = find_best_content_container(
        soup
    )

    # Czyścimy go
    content = clean_container(
        content
    )

    # -----------------------------------------------------
    # BUDOWANIE CZYSTEJ WERSJI HTML
    # -----------------------------------------------------

    article_html = ""

    # Przechodzimy po elementach w kolejności,
    # w której występują w artykule.
    #
    # Dzięki temu nie tracimy relacji:
    # H2 -> P -> P -> H2 -> P itd.

    for element in content.find_all([
        "h1",
        "h2",
        "h3",
        "h4",
        "p",
        "ul",
        "ol"
    ]):

        # -----------------------------------------------
        # NAGŁÓWKI
        # -----------------------------------------------

        if element.name in [
            "h1",
            "h2",
            "h3",
            "h4"
        ]:

            text = element.get_text(
                " ",
                strip=True
            )

            if text:

                article_html += (
                    f"<{element.name}>"
                    f"{text}"
                    f"</{element.name}>"
                )

        # -----------------------------------------------
        # AKAPITY
        # -----------------------------------------------

        elif element.name == "p":

            text = element.get_text(
                " ",
                strip=True
            )

            if text:

                article_html += (
                    f"<p>{text}</p>"
                )

        # -----------------------------------------------
        # LISTY
        # -----------------------------------------------

        elif element.name in [
            "ul",
            "ol"
        ]:

            list_items = []

            for li in element.find_all(
                "li",
                recursive=False
            ):

                text = li.get_text(
                    " ",
                    strip=True
                )

                if text:

                    list_items.append(
                        f"<li>{text}</li>"
                    )

            if list_items:

                article_html += (
                    f"<{element.name}>"
                    + "".join(list_items)
                    + f"</{element.name}>"
                )

    # -----------------------------------------------------
    # SPRAWDZENIE REZULTATU
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
            "Nie udało się znaleźć "
            "wystarczającej ilości treści artykułu."
        )

    return article_html


# =========================================================
# POBIERANIE SITEMAPY
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
# INTERNAL LINKING
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

        # -------------------------------------------------
        # WALIDACJA
        # -------------------------------------------------

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

        # -------------------------------------------------
        # ARTYKUŁ Z URL
        # -------------------------------------------------

        if mode == "Mam już artykuł na stronie":

            try:

                with st.spinner(
                    "Pobieram artykuł..."
                ):

                    article_html = extract_article_content(
                        article_url
                    )

                st.success(
                    "Strona została pobrana."
                )

            except Exception as e:

                st.error(
                    f"Nie udało się pobrać artykułu: {e}"
                )

                st.stop()

        # -------------------------------------------------
        # ARTYKUŁ WKLEJONY
        # -------------------------------------------------

        else:

            paragraphs = article_text.split(
                "\n"
            )

            article_html = ""

            for paragraph in paragraphs:

                paragraph = paragraph.strip()

                if paragraph:

                    article_html += (
                        f"<p>{paragraph}</p>"
                    )

            st.success(
                "Tekst został wczytany."
            )

        # -------------------------------------------------
        # PODGLĄD
        # -------------------------------------------------

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

        # -------------------------------------------------
        # SITEMAP
        # -------------------------------------------------

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


# =========================================================
# INTERNAL LINKING
# =========================================================

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

            st.session_state["page"] = "internal_links"

            st.rerun()


# =========================================================
# SEO AUDIT
# =========================================================

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


# =========================================================
# CONTENT ANALYSIS
# =========================================================

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
