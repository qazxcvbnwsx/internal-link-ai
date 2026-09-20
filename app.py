import streamlit as st
import requests
from bs4 import BeautifulSoup


# --------------------------------------------------
# KONFIGURACJA
# --------------------------------------------------

st.set_page_config(
    page_title="SEO Tools AI",
    page_icon="🔗",
    layout="wide",
    initial_sidebar_state="collapsed"
)


# --------------------------------------------------
# CSS
# --------------------------------------------------

st.markdown(
    """
    <style>

    .stApp {
        background-color: #f7f8fa;
    }

    #MainMenu {
        visibility: hidden;
    }

    footer {
        visibility: hidden;
    }

    header {
        visibility: hidden;
    }

    .block-container {
        max-width: 1100px;
        padding-top: 60px;
        padding-bottom: 60px;
    }

    .hero-title {
        font-size: 44px;
        font-weight: 700;
        color: #111827;
        text-align: center;
        margin-bottom: 10px;
    }

    .hero-subtitle {
        font-size: 18px;
        color: #6b7280;
        text-align: center;
        margin-bottom: 50px;
    }

    .page-title {
        font-size: 38px;
        font-weight: 700;
        color: #111827;
        margin-bottom: 8px;
    }

    .page-description {
        font-size: 17px;
        color: #6b7280;
        margin-bottom: 40px;
    }

    .section-title {
        font-size: 20px;
        font-weight: 650;
        color: #111827;
        margin-top: 25px;
        margin-bottom: 15px;
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
        font-size: 32px;
        line-height: 1.25;
        margin-top: 0;
        margin-bottom: 25px;
        color: #111827;
    }

    .article-preview h2 {
        font-size: 24px;
        line-height: 1.35;
        margin-top: 35px;
        margin-bottom: 15px;
        color: #111827;
    }

    .article-preview h3 {
        font-size: 20px;
        line-height: 1.4;
        margin-top: 28px;
        margin-bottom: 12px;
        color: #111827;
    }

    .article-preview h4 {
        font-size: 18px;
        line-height: 1.4;
        margin-top: 24px;
        margin-bottom: 10px;
        color: #111827;
    }

    .article-preview p {
        margin-bottom: 18px;
    }

    .article-preview ul,
    .article-preview ol {
        margin-bottom: 20px;
        padding-left: 28px;
    }

    .article-preview li {
        margin-bottom: 8px;
    }

    .article-preview strong {
        font-weight: 700;
    }

    .article-preview a {
        color: #2563eb;
        text-decoration: underline;
    }

    .stButton > button {
        width: 100%;
        border-radius: 10px;
        min-height: 42px;
        font-weight: 600;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# --------------------------------------------------
# NAWIGACJA
# --------------------------------------------------

if "page" not in st.session_state:
    st.session_state["page"] = "home"


# --------------------------------------------------
# FUNKCJA: POBIERANIE TREŚCI
# --------------------------------------------------

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

    # --------------------------------------------------
    # USUWAMY ELEMENTY TECHNICZNE
    # --------------------------------------------------

    for tag in soup.find_all([
        "script",
        "style",
        "noscript",
        "template",
        "svg",
        "iframe",
        "form",
        "nav",
        "footer",
        "header"
    ]):
        tag.decompose()

    # --------------------------------------------------
    # SZUKAMY GŁÓWNEGO OBSZARU TREŚCI
    # --------------------------------------------------

    content = None

    # Najpierw próbujemy znaleźć semantyczne elementy
    # najczęściej wykorzystywane dla głównej treści.

    selectors = [
        "main",
        "article",
        "[role='main']"
    ]

    for selector in selectors:

        candidate = soup.select_one(selector)

        if candidate:

            # Sprawdzamy, czy element rzeczywiście
            # zawiera sensowną ilość tekstu.

            text_length = len(
                candidate.get_text(
                    " ",
                    strip=True
                )
            )

            if text_length > 300:

                content = candidate
                break

    # --------------------------------------------------
    # JEŻELI NIE ZNALEŹLIŚMY MAIN/ARTICLE
    # --------------------------------------------------

    if content is None:

        # Szukamy elementu zawierającego H1.

        h1 = soup.find("h1")

        if h1:

            # Próbujemy znaleźć jego sensowny kontener.

            candidate = h1.parent

            while candidate and candidate.name not in [
                "body",
                "html"
            ]:

                text_length = len(
                    candidate.get_text(
                        " ",
                        strip=True
                    )
                )

                if text_length > 500:

                    content = candidate

                    # Nie idziemy za wysoko.
                    # Jeżeli rodzic jest bardzo duży,
                    # zatrzymujemy się.

                    if text_length > 20000:
                        break

                candidate = candidate.parent

    # --------------------------------------------------
    # OSTATECZNY FALLBACK
    # --------------------------------------------------

    if content is None:

        content = soup.body

    if content is None:

        raise ValueError(
            "Nie udało się znaleźć treści strony."
        )

    # --------------------------------------------------
    # USUWAMY ELEMENTY WEWNĄTRZ GŁÓWNEGO KONTENERA
    # --------------------------------------------------

    for tag in content.find_all([
        "script",
        "style",
        "noscript",
        "template",
        "svg",
        "iframe",
        "form",
        "nav",
        "footer",
        "header"
    ]):
        tag.decompose()

    # --------------------------------------------------
    # USUWAMY META I TITLE
    # --------------------------------------------------

    for tag in content.find_all([
        "title",
        "meta"
    ]):
        tag.decompose()

    # --------------------------------------------------
    # WYBIERAMY TYLKO ELEMENTY TREŚCIOWE
    # --------------------------------------------------

    allowed_tags = [
        "h1",
        "h2",
        "h3",
        "h4",
        "p",
        "ul",
        "ol"
    ]

    elements = content.find_all(
        allowed_tags
    )

    # --------------------------------------------------
    # BUDUJEMY CZYSTY HTML ARTYKUŁU
    # --------------------------------------------------

    article_html = ""

    for element in elements:

        # ----------------------------------------------
        # NAGŁÓWKI
        # ----------------------------------------------

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

        # ----------------------------------------------
        # AKAPITY
        # ----------------------------------------------

        elif element.name == "p":

            text = element.get_text(
                " ",
                strip=True
            )

            if text:

                article_html += (
                    f"<p>{text}</p>"
                )

        # ----------------------------------------------
        # LISTY
        # ----------------------------------------------

        elif element.name in [
            "ul",
            "ol"
        ]:

            # Tworzymy listę od nowa,
            # żeby nie pobierać śmieciowego HTML.

            list_html = ""

            for li in element.find_all(
                "li",
                recursive=False
            ):

                text = li.get_text(
                    " ",
                    strip=True
                )

                if text:

                    list_html += (
                        f"<li>{text}</li>"
                    )

            if list_html:

                article_html += (
                    f"<{element.name}>"
                    f"{list_html}"
                    f"</{element.name}>"
                )

    # --------------------------------------------------
    # SPRAWDZENIE WYNIKU
    # --------------------------------------------------

    clean_text = BeautifulSoup(
        article_html,
        "html.parser"
    ).get_text(
        " ",
        strip=True
    )

    if len(clean_text) < 200:

        raise ValueError(
            "Nie udało się znaleźć wystarczającej ilości "
            "treści artykułu."
        )

    return article_html


# --------------------------------------------------
# STRONA: LINKOWANIE WEWNĘTRZNE
# --------------------------------------------------

if st.session_state["page"] == "internal_links":

    if st.button("← Wróć do narzędzi"):

        st.session_state["page"] = "home"
        st.rerun()

    st.markdown(
        '<div class="page-title">'
        '🔗 Linkowanie wewnętrzne'
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

    st.markdown(
        '<div class="section-title">'
        '1. Tekst do analizy'
        '</div>',
        unsafe_allow_html=True
    )

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
            placeholder=(
                "https://twojastrona.pl/blog/artykul/"
            )
        )

    else:

        article_text = st.text_area(
            "Wklej cały tekst artykułu",
            height=350,
            placeholder=(
                "Wklej tutaj treść artykułu..."
            )
        )

    st.markdown(
        '<div class="section-title">'
        '2. Sitemap'
        '</div>',
        unsafe_allow_html=True
    )

    sitemap_url = st.text_input(
        "URL sitemap",
        placeholder=(
            "https://twojastrona.pl/sitemap.xml"
        )
    )

    st.markdown("")

    if st.button(
        "🔍 Analizuj linkowanie",
        type="primary",
        use_container_width=True
    ):

        if (
            mode == "Mam już artykuł na stronie"
            and not article_url
        ):

            st.error(
                "Podaj URL artykułu."
            )

        elif (
            mode == "Artykuł nie jest jeszcze opublikowany"
            and not article_text
        ):

            st.error(
                "Wklej treść artykułu."
            )

        elif not sitemap_url:

            st.error(
                "Podaj adres sitemap."
            )

        else:

            # ------------------------------------------
            # POBIERANIE ARTYKUŁU Z URL
            # ------------------------------------------

            if mode == "Mam już artykuł na stronie":

                try:

                    article_html = extract_article_content(
                        article_url
                    )

                    st.success(
                        "Strona została pobrana."
                    )

                    st.markdown(
                        "### Podgląd treści artykułu"
                    )

                    st.markdown(
                        f'<div class="article-preview">'
                        f'{article_html}'
                        f'</div>',
                        unsafe_allow_html=True
                    )

                except requests.RequestException as e:

                    st.error(
                        f"Nie udało się pobrać strony: {e}"
                    )

                except Exception as e:

                    st.error(
                        f"Wystąpił błąd podczas analizy: {e}"
                    )

            # ------------------------------------------
            # ARTYKUŁ WKLEJONY RĘCZNIE
            # ------------------------------------------

            else:

                st.success(
                    "Treść została przyjęta."
                )

                st.markdown(
                    "### Podgląd treści artykułu"
                )

                formatted_text = (
                    article_text
                    .replace("\n\n", "</p><p>")
                    .replace("\n", "<br>")
                )

                st.markdown(
                    '<div class="article-preview">'
                    f'<p>{formatted_text}</p>'
                    '</div>',
                    unsafe_allow_html=True
                )

    st.stop()


# --------------------------------------------------
# STRONA GŁÓWNA
# --------------------------------------------------

st.markdown(
    '<div class="hero-title">'
    'SEO Tools AI'
    '</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="hero-subtitle">'
    'Proste narzędzia SEO wspierane przez sztuczną inteligencję'
    '</div>',
    unsafe_allow_html=True
)


# --------------------------------------------------
# PIERWSZY RZĄD
# --------------------------------------------------

col1, col2 = st.columns(2)


# --------------------------------------------------
# LINKOWANIE WEWNĘTRZNE
# --------------------------------------------------

with col1:

    with st.container(border=True):

        st.markdown(
            "## 🔗 Linkowanie wewnętrzne"
        )

        st.write(
            "Znajdź naturalne miejsca w artykule, "
            "w których warto dodać linki do innych "
            "stron w Twoim serwisie."
        )

        st.success(
            "DOSTĘPNE"
        )

        if st.button(
            "Otwórz narzędzie →",
            key="internal_links",
            use_container_width=True
        ):

            st.session_state["page"] = "internal_links"
            st.rerun()


# --------------------------------------------------
# AUDYT SEO
# --------------------------------------------------

with col2:

    with st.container(border=True):

        st.markdown(
            "## 🔍 Audyt SEO"
        )

        st.write(
            "Sprawdź najważniejsze elementy techniczne "
            "i on-page swojej strony."
        )

        st.info(
            "WKRÓTCE"
        )


# --------------------------------------------------
# DRUGI RZĄD
# --------------------------------------------------

col3, col4 = st.columns(2)


# --------------------------------------------------
# ANALIZA TREŚCI
# --------------------------------------------------

with col3:

    with st.container(border=True):

        st.markdown(
            "## 📝 Analiza treści"
        )

        st.write(
            "Analizuj treść pod kątem tematów, "
            "nagłówków, semantyki i potencjału SEO."
        )

        st.info(
            "WKRÓTCE"
        )


# --------------------------------------------------
# ANALIZA STRONY
# --------------------------------------------------

with col4:

    with st.container(border=True):

        st.markdown(
            "## 📊 Analiza strony"
        )

        st.write(
            "Zbierz najważniejsze informacje o stronie "
            "i znajdź elementy wymagające optymalizacji."
        )

        st.info(
            "WKRÓTCE"
        )
