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

    /* Tło aplikacji */
    .stApp {
        background-color: #f7f8fa;
    }

    /* Ukrycie elementów Streamlit */
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
    .block-container {
        max-width: 1100px;
        padding-top: 60px;
        padding-bottom: 60px;
    }

    /* Nagłówek */
    .hero {
        text-align: center;
        margin-bottom: 50px;
    }

    .hero-title {
        font-size: 44px;
        font-weight: 700;
        color: #111827;
        margin-bottom: 12px;
    }

    .hero-subtitle {
        font-size: 18px;
        color: #6b7280;
    }

    /* Kafelki */
    .tool-card {
        background-color: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 18px;
        padding: 30px;
        min-height: 220px;
        margin-bottom: 20px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.04);
    }

    .tool-icon {
        font-size: 36px;
        margin-bottom: 15px;
    }

    .tool-title {
        font-size: 22px;
        font-weight: 700;
        color: #111827;
        margin-bottom: 10px;
    }

    .tool-description {
        font-size: 15px;
        line-height: 1.6;
        color: #6b7280;
        margin-bottom: 18px;
    }

    .status-available {
        display: inline-block;
        padding: 5px 10px;
        border-radius: 20px;
        background-color: #ecfdf5;
        color: #047857;
        font-size: 12px;
        font-weight: 600;
    }

    .status-soon {
        display: inline-block;
        padding: 5px 10px;
        border-radius: 20px;
        background-color: #f3f4f6;
        color: #6b7280;
        font-size: 12px;
        font-weight: 600;
    }

    /* Przyciski */
    .stButton > button {
        width: 100%;
        border-radius: 10px;
        border: 1px solid #d1d5db;
        background-color: #ffffff;
        color: #111827;
        font-weight: 600;
        min-height: 42px;
    }

    .stButton > button:hover {
        border-color: #111827;
        color: #111827;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# --------------------------------------------------
# NAGŁÓWEK
# --------------------------------------------------

st.markdown(
    """
    <div class="hero">
        <div class="hero-title">SEO Tools AI</div>
        <div class="hero-subtitle">
            Proste narzędzia SEO wspierane przez sztuczną inteligencję
        </div>
    </div>
    """,
    unsafe_allow_html=True
)


# --------------------------------------------------
# PIERWSZY RZĄD KAFELKÓW
# --------------------------------------------------

col1, col2 = st.columns(2)


# --------------------------------------------------
# KAFEL 1 — LINKOWANIE
# --------------------------------------------------

with col1:

    st.markdown(
        """
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

            <span class="status-available">
                DOSTĘPNE
            </span>
        </div>
        """,
        unsafe_allow_html=True
    )

    if st.button(
        "Otwórz narzędzie →",
        key="internal_links"
    ):
        st.session_state["page"] = "internal_links"
        st.rerun()


# --------------------------------------------------
# KAFEL 2 — AUDYT
# --------------------------------------------------

with col2:

    st.markdown(
        """
        <div class="tool-card">
            <div class="tool-icon">🔍</div>

            <div class="tool-title">
                Audyt SEO
            </div>

            <div class="tool-description">
                Sprawdź najważniejsze elementy techniczne
                i on-page swojej strony.
            </div>

            <span class="status-soon">
                WKRÓTCE
            </span>
        </div>
        """,
        unsafe_allow_html=True
    )


# --------------------------------------------------
# DRUGI RZĄD
# --------------------------------------------------

col3, col4 = st.columns(2)


# --------------------------------------------------
# KAFEL 3 — ANALIZA TREŚCI
# --------------------------------------------------

with col3:

    st.markdown(
        """
        <div class="tool-card">
            <div class="tool-icon">📝</div>

            <div class="tool-title">
                Analiza treści
            </div>

            <div class="tool-description">
                Analizuj treść pod kątem tematów,
                nagłówków, semantyki i potencjału SEO.
            </div>

            <span class="status-soon">
                WKRÓTCE
            </span>
        </div>
        """,
        unsafe_allow_html=True
    )


# --------------------------------------------------
# KAFEL 4 — ANALIZA STRONY
# --------------------------------------------------

with col4:

    st.markdown(
        """
        <div class="tool-card">
            <div class="tool-icon">📊</div>

            <div class="tool-title">
                Analiza strony
            </div>

            <div class="tool-description">
                Zbierz najważniejsze informacje o stronie
                i znajdź elementy wymagające optymalizacji.
            </div>

            <span class="status-soon">
                WKRÓTCE
            </span>
        </div>
        """,
        unsafe_allow_html=True
    )
