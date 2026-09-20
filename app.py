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
# CZYSZCZENIE DOKUMENTU
# =========================================================

def remove_unwanted_elements(soup):
    """
    Usuwa elementy, które nie są właściwą treścią strony.
    """

    unwanted = [
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
    ]

    for tag in soup.find_all(unwanted):
        tag.decompose()

    return soup


# =========================================================
# SZUKANIE GŁÓWNEGO OBSZARU TREŚCI
# =========================================================

def find_content_area(soup):
    """
    Szuka najbardziej prawdopodobnego obszaru głównej treści.
    Nie wybiera automatycznie pierwszego <main>.
    """

    candidates = []

    # Najpierw elementy semantyczne
    selectors = [
        "article",
        "main",
        "[role='main']"
    ]

    for selector in selectors:

        for element in soup.select(selector):

            paragraphs = element.find_all("p")
            headings = element.find_all(
                ["h1", "h2", "h3", "h4"]
            )

            text = element.get_text(
                " ",
                strip=True
            )

            if len(text) < 300:
                continue

            score = (
                len(paragraphs) * 1000
                + len(headings) * 500
                + min(len(text), 30000)
            )

            candidates.append(
                (score, element)
            )

    # Jeżeli mamy kandydatów, wybieramy ten,
    # który ma najwięcej rzeczywistej treści.
    if candidates:

        candidates.sort(
            key=lambda item: item[0],
            reverse=True
        )

        return candidates[0][1]

    # Fallback
    return soup.body


# =========================================================
# WYDOBYCIE ELEMENTÓW ARTYKUŁU
# =========================================================

def extract_article_elements(content):
    """
    Pobiera H1-H4, P oraz listy w kolejności
    występowania w dokumencie.
    """

    elements = []

    # Szukamy wszystkich elementów treści.
    # Nie przechodzimy osobno po nagłówkach i akapitach,
    # dzięki czemu zachowujemy ich kolejność.

    for element in content.find_all(
        ["h1", "h2", "h3", "h4", "p", "ul", "ol"]
    ):

        # ---------------------------------------------
        # NAGŁÓWKI
        # ---------------------------------------------

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

            if not text:
                continue

            elements.append({
                "type": element.name,
                "text": text
            })

        # ---------------------------------------------
        # AKAPITY
        # ---------------------------------------------

        elif element.name == "p":

            text = element.get_text(
                " ",
                strip=True
            )

            if not text:
                continue

            # Pomijamy bardzo krótkie elementy,
            # które często są np. podpisami lub
            # elementami technicznymi.
            if len(text) < 20:
                continue

            elements.append({
                "type": "p",
                "text": text
            })

        # ---------------------------------------------
        # LISTY
        # ---------------------------------------------

        elif element.name in [
            "ul",
            "ol"
        ]:

            items = []

            for li in element.find_all(
                "li",
                recursive=False
            ):

                text = li.get_text(
                    " ",
                    strip=True
                )

                if text:

                    items.append(
                        text
                    )

            if items:

                elements.append({
                    "type": element.name,
                    "items": items
                })

    return elements


# =========================================================
# BUDOWANIE HTML PODGLĄDU
# =========================================================

def elements_to_html(elements):

    html = ""

    for element in elements:

        element_type = element["type"]

        # Nagłówki
        if element_type in [
            "h1",
            "h2",
            "h3",
            "h4"
        ]:

            text = element["text"]

            html += (
                f"<{element_type}>"
                f"{text}"
                f"</{element_type}>"
            )

        # Akapit
        elif element_type == "p":

            html += (
                f"<p>{element['text']}</p>"
            )

        # Lista numerowana / punktowana
        elif element_type in [
            "ul",
            "ol"
        ]:

            html += f"<{element_type}>"

            for item in element["items"]:

                html += (
                    f"<li>{item}</li>"
                )

            html += f"</{element_type}>"

    return html


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

    # -----------------------------------------------------
    # USUWAMY ELEMENTY TECHNICZNE
    # -----------------------------------------------------

    soup = remove_unwanted_elements(
        soup
    )

    # -----------------------------------------------------
    # SZUKAMY OBSZARU TREŚCI
    # -----------------------------------------------------

    content = find_content_area(
        soup
    )

    if content is None:

        raise ValueError(
            "Nie udało się znaleźć głównego "
            "obszaru treści."
        )

    # -----------------------------------------------------
    # WYDOBYWAMY ELEMENTY
    # -----------------------------------------------------

    elements = extract_article_elements(
        content
    )

    if not elements:

        raise ValueError(
            "Nie znaleziono elementów tekstowych "
            "w głównej treści strony."
        )

    # -----------------------------------------------------
    # HTML
    # -----------------------------------------------------

    article_html = elements_to_html(
        elements
    )

    # -----------------------------------------------------
    # TEKST DO WALIDACJI
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

    stats = {
        "h1": sum(
            1 for x in elements
            if x["type"] == "h1"
        ),
        "h2": sum(
            1 for x in elements
            if x["type"] == "h2"
        ),
        "h3": sum(
            1 for x in elements
            if x["type"] == "h3"
        ),
        "h4": sum(
            1 for x in elements
            if x["type"] == "h4"
        ),
        "paragraphs": sum(
            1 for x in elements
            if x["type"] == "p"
        ),
        "lists": sum(
            1 for x in elements
            if x["type"] in ["ul", "ol"]
        ),
        "characters": len(clean_text)
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
    # ŹRÓDŁO TEKSTU
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
    # PRZYCISK
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
        # POBIERANIE ARTYKUŁU
        # =================================================

        if mode == "Mam już artykuł na stronie":

            try:

                with st.spinner(
                    "Pobieram artykuł..."
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
                        f"<p>{paragraph}</p>"
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

            st.session_state["page"] = (
                "internal_links"
            )

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
