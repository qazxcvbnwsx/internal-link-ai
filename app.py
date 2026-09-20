import streamlit as st

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

    /* Przyciski */
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
# NAGŁÓWEK
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

        st.markdown("## 🔗 Linkowanie wewnętrzne")

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
    st.switch_page("pages/internal_links.py")


# --------------------------------------------------
# AUDYT SEO
# --------------------------------------------------

with col2:

    with st.container(border=True):

        st.markdown("## 🔍 Audyt SEO")

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

        st.markdown("## 📝 Analiza treści")

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

        st.markdown("## 📊 Analiza strony")

        st.write(
            "Zbierz najważniejsze informacje o stronie "
            "i znajdź elementy wymagające optymalizacji."
        )

        st.info("WKRÓTCE")
