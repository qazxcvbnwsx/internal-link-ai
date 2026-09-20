import streamlit as st

# --------------------------------------------------
# KONFIGURACJA
# --------------------------------------------------

st.set_page_config(
    page_title="SEO Tools AI",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --------------------------------------------------
# CSS
# --------------------------------------------------

st.markdown("""
<style>

    /* Główne tło */
    .stApp {
        background: #f7f8fa;
    }

    /* Ukrycie domyślnego menu Streamlit */
    #MainMenu {
        visibility: hidden;
    }

    footer {
        visibility: hidden;
    }

    header {
        visibility: hidden;
    }

    /* Główny kontener */
    .main .block-container {
        max-width: 1200px;
        padding-top: 60px;
        padding-bottom: 60px;
    }

    /* Nagłówek */
    .hero {
        text-align: center;
        margin-bottom: 55px;
    }

    .hero-title {
        font-size: 46px;
        font-weight: 700;
        letter-spacing: -1.5px;
        color: #111827;
        margin-bottom: 12px;
    }

    .hero-subtitle {
        font-size: 18px;
        color: #6b7280;
    }

    /* Kafelek */
    .tool-card {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 18px;
        padding: 30px;
        min-height: 250px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.04);
        transition: all 0.2s ease;
        margin-bottom: 20px;
    }

    .tool-card:hover {
        border-color: #cbd5e1;
        box-shadow: 0 8px 25px rgba(0,0,0,0.08);
        transform: translateY(-2px);
    }

    .tool-icon {
        font-size: 38px;
        margin-bottom: 18px;
    }

    .tool-title {
        font-size: 23px;
        font-weight: 650;
        color: #111827;
        margin-bottom: 10px;
    }

    .tool-description {
        font-size: 15px;
        line-height: 1.6;
        color: #6b7280;
        margin-bottom: 18px;
    }

    .available {
        display: inline-block;
        font-size: 12px;
        font-weight: 600;
        color: #047857;
        background: #ecfdf5;
        padding: 5px 10px;
        border-radius: 20px;
    }

    .coming-soon {
        display: inline-block;
        font-size: 12px;
        font-weight: 600;
        color: #6b7280;
        background: #f3f4f6;
        padding: 5px 10px;
        border-radius: 20px;
    }

    /* Przycisk */
    .stButton > button {
        width: 100%;
        border-radius: 10px;
        border: 1px solid #d1d5db;
        background: white;
        color: #111827;
        font-weight: 600;
        padding: 10px 15px;
    }

    .stButton > button:hover {
        border-color: #111827;
        color: #111827;
    }

</style>
""", unsafe_allow_html=True)


# --------------------------------------------------
# NAGŁÓWEK
# --------------------------------------------------

st.markdown("""
<div class="hero">

    <div class="hero-title">
        SEO Tools AI
    </div>

    <div class="hero-subtitle">
        Proste narzędzia SEO wspierane przez sztuczną inteligencję
    </div>

</div>
""", unsafe_allow_html=True)


# --------------------------------------------------
# NARZĘDZIA
# --------------------------------------------------

col1, col2 = st.columns(2)


# --------------------------------------------------
# LINKOWANIE WEWNĘTRZNE
# --------------------------------------------------

with col1:

    st.markdown("""
    <div class="tool-card">

        <div class="tool-icon">🔗</div>

        <div class="tool-title">
            Linkowanie wewnętrzne
        </div>

        <div class="tool-description">
            Znajdź naturalne miejsca w artykule,
            w których warto dodać linki do innych
            stron w Twoim serwisie.
        </div>

        <span class="available">
            DOSTĘPNE
        </span>

    </div>
    """, unsafe_allow_html=True)

    if st.button(
        "Otwórz narzędzie →",
        key="internal_links"
    ):
        st.session_state["page"] = "internal_links"
        st.rerun()


# --------------------------------------------------
# AUDYT SEO
# --------------------------------------------------

with col2:

    st.markdown("""
    <div class="tool-card">

        <div class="tool-icon">🔍</div>

        <div class="tool-title">
            Audyt SEO
        </div>

        <div class="tool-description">
            Sprawdź najważniejsze elementy techniczne
            i on-page swojej strony.
        </div>

        <span class="coming-soon">
            WKRÓTCE
        </span>

    </div>
    """, unsafe_allow_html=True)


# --------------------------------------------------
# ANALIZA TREŚCI
# --------------------------------------------------

col3, col4 = st.columns(2)


with col3:

    st.markdown("""
    <div class="tool-card">

        <div class="tool-icon">📝</div>

        <div class="tool-title">
            Analiza treści
        </div>

        <div class="tool-description">
            Analizuj treść pod kątem tematów,
            nagłówków, semantyki i potencjału SEO.
        </div>

        <span class="coming-soon">
            WKRÓTCE
        </span>

    </div>
    """, unsafe_allow_html=True)


with col4:

    st.markdown("""
    <div class="tool-card">

        <div class="tool-icon">📊</div>

        <div class="tool-title">
            Analiza strony
        </div>

        <div class="tool-description">
            Zbierz najważniejsze informacje o stronie
            i znajdź elementy wymagające optymalizacji.
        </div>

        <span class="coming-soon">
            WKRÓTCE
        </span>

    </div>
    """, unsafe_allow_html=True)
