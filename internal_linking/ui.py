import streamlit as st
import html
from urllib.parse import urlparse

from .extractor import extract_article_content
from .sitemap import get_sitemap_urls


def get_domain(url):

    parsed = urlparse(url)

    return parsed.netloc.lower().replace(
        "www.",
        ""
    )


def show_internal_linking():

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

    # =====================================================
    # ŹRÓDŁO ARTYKUŁU
    # =====================================================

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

    # =====================================================
    # SITEMAP
    # =====================================================

    sitemap_url = st.text_input(
        "URL sitemap",
        placeholder="https://twojastrona.pl/sitemap.xml"
    )

    # =====================================================
    # ANALIZA
    # =====================================================

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

    # =====================================================
    # POWRÓT
    # =====================================================

    st.markdown("---")

    if st.button(
        "← Wróć do narzędzi"
    ):

        st.session_state["page"] = "home"

        st.rerun()
