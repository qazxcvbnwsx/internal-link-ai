import streamlit as st
from internal_linking.ui import show_internal_linking


st.set_page_config(
    page_title="SEO Tools AI",
    page_icon="🔗",
    layout="wide"
)


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

    .article-preview a {
        color: #2563eb;
        text-decoration: underline;
        font-weight: 500;
    }

    .candidate-table-wrapper {
        width: 100%;
        overflow-x: auto;
        margin-top: 15px;
        margin-bottom: 25px;
    }

    .candidate-table {
        width: 100%;
        border-collapse: collapse;
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        overflow: hidden;
        font-size: 14px;
    }

    .candidate-table th {
        text-align: left;
        padding: 14px 16px;
        background: #f9fafb;
        border-bottom: 1px solid #e5e7eb;
        color: #111827;
        font-weight: 600;
    }

    .candidate-table td {
        padding: 14px 16px;
        border-bottom: 1px solid #e5e7eb;
        vertical-align: top;
        line-height: 1.7;
    }

    .candidate-table tr:last-child td {
        border-bottom: none;
    }

    .phrase-cell {
        width: 42%;
        color: #111827;
    }

    .url-cell {
        width: 58%;
        word-break: break-word;
    }

    .url-cell a {
        color: #2563eb;
        text-decoration: none;
    }

    .url-cell a:hover {
        text-decoration: underline;
    }

    .no-match {
        color: #9ca3af;
        font-style: italic;
    }

    </style>
    """,
    unsafe_allow_html=True
)


if "page" not in st.session_state:

    st.session_state["page"] = "home"


if st.session_state["page"] == "internal_links":

    show_internal_linking()

    st.stop()


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


col1, col2, col3 = st.columns(3)


with col1:

    with st.container(
        border=True
    ):

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

            st.session_state[
                "page"
            ] = "internal_links"

            st.rerun()


with col2:

    with st.container(
        border=True
    ):

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

    with st.container(
        border=True
    ):

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
