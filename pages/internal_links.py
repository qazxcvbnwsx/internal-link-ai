import streamlit as st


# --------------------------------------------------
# KONFIGURACJA
# --------------------------------------------------

st.set_page_config(
    page_title="Linkowanie wewnętrzne | SEO Tools AI",
    page_icon="🔗",
    layout="wide"
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

    .block-container {
        max-width: 1000px;
        padding-top: 50px;
        padding-bottom: 60px;
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

    </style>
    """,
    unsafe_allow_html=True
)


# --------------------------------------------------
# POWRÓT
# --------------------------------------------------

if st.button("← Wróć do narzędzi"):

    st.switch_page("../app.py")


# --------------------------------------------------
# NAGŁÓWEK
# --------------------------------------------------

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


# --------------------------------------------------
# ŹRÓDŁO ARTYKUŁU
# --------------------------------------------------

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


# --------------------------------------------------
# SITEMAP
# --------------------------------------------------

st.markdown(
    '<div class="section-title">2. Sitemap</div>',
    unsafe_allow_html=True
)

sitemap_url = st.text_input(
    "URL sitemap",
    placeholder="https://twojastrona.pl/sitemap.xml"
)


# --------------------------------------------------
# ANALIZA
# --------------------------------------------------

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

        st.success(
            "Dane są poprawne. W kolejnym kroku uruchomimy właściwą analizę."
        )
