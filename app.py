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
# STRONA: LINKOWANIE WEWNĘTRZNE
# --------------------------------------------------

if st.session_state["page"] == "internal_links":

    if st.button("← Wróć do narzędzi"):
        st.session_state["page"] = "home"
        st.rerun()

    st.markdown(
        '<div class="page-title">🔗 Linkowanie wewnętrzne</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="page-description">'
        'Znajdź naturalne miejsca na linki wewnętrzne w swoim artykule.'
        '</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="section-title">1. Tekst do analizy</div>',
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
            placeholder="https://twojastrona.pl/blog/artykul/"
        )

    else:

        article_text = st.text_area(
            "Wklej cały tekst artykułu",
            height=350,
            placeholder="Wklej tutaj treść artykułu..."
        )

    st.markdown(
        '<div class="section-title">2. Sitemap</div>',
        unsafe_allow_html=True
    )

    sitemap_url = st.text_input(
        "URL sitemap",
        placeholder="https://twojastrona.pl/sitemap.xml"
    )

    st.markdown("")

    if st.button(
        "🔍 Analizuj linkowanie",
        type="primary",
        use_container_width=True
    ):

        if mode == "Mam już artykuł na stronie" and not article_url:

            st.error("Podaj URL artykułu.")

        elif mode == "Artykuł nie jest jeszcze opublikowany" and not article_text:

            st.error("Wklej treść artykułu.")

        elif not sitemap_url:

            st.error("Podaj adres sitemap.")

        else:

            try:

                response = requests.get(
                    article_url,
                    timeout=15,
                    headers={
                        "User-Agent": "Mozilla/5.0"
                    }
                )

                response.raise_for_status()

                soup = BeautifulSoup(
                    response.text,
                    "html.parser"
                )

                # Usuwamy elementy, które nie są treścią artykułu
                for element in soup(
                    [
                        "script",
                        "style",
                        "nav",
                        "footer",
                        "header",
                        "aside"
                    ]
                ):
                    element.decompose()

                # Szukamy głównej treści strony
                main = soup.find("main")

                if main:

                    content = main.get_text(
                        separator=" ",
                        strip=True
                    )

                else:

                    content = soup.get_text(
                        separator=" ",
                        strip=True
                    )

                st.success(
                    "Strona została pobrana."
                )

                st.markdown(
                    "### Pobrana treść"
                )

                st.text_area(
                    "Tekst znaleziony na stronie:",
                    content,
                    height=500
                )

            except requests.RequestException as e:

                st.error(
                    f"Nie udało się pobrać strony: {e}"
                )

            except Exception as e:

                st.error(
                    f"Wystąpił błąd podczas analizy: {e}"
                )

    st.stop()


# --------------------------------------------------
# STRONA GŁÓWNA
# --------------------------------------------------

st.markdown(
    '<div class="hero-title">SEO Tools AI</div>',
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

        st.success("DOSTĘPNE")

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

        st.info("WKRÓTCE")


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

        st.info("WKRÓTCE")


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

        st.info("WKRÓTCE")
