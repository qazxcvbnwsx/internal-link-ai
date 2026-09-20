import streamlit as st
import html
import time

from .extractor import extract_article_content

from .sitemap import (
    get_sitemap_urls,
    find_sitemap_in_robots,
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

    # -------------------------------------------------
    # ŹRÓDŁO TEKSTU
    # -------------------------------------------------

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

    # -------------------------------------------------
    # SITEMAP
    # -------------------------------------------------

    sitemap_url = st.text_input(
        "URL sitemap",
        placeholder="https://twojastrona.pl/sitemap.xml",
        help=(
            "Możesz wpisać sitemapę ręcznie albo "
            "znaleźć ją automatycznie przez robots.txt."
        )
    )

    # -------------------------------------------------
    # ZNAJDŹ SITEMAPĘ
    # -------------------------------------------------

    if mode == "Mam już artykuł na stronie":

        if st.button(
            "🔍 Znajdź sitemapę",
            use_container_width=True
        ):

            if not article_url.strip():

                st.error(
                    "Najpierw podaj URL artykułu."
                )

            else:

                with st.spinner(
                    "Sprawdzam robots.txt..."
                ):

                    robots_result = find_sitemap_in_robots(
                        article_url.strip()
                    )

                if robots_result["status"] == "found":

                    st.session_state[
                        "detected_sitemap"
                    ] = robots_result["sitemap_url"]

                    st.success(
                        "Znaleziono sitemapę."
                    )

                elif robots_result["status"] == "missing":

                    st.session_state[
                        "detected_sitemap"
                    ] = ""

                    st.warning(
                        "Nie znaleziono robots.txt. "
                        "Wklej URL sitemap ręcznie."
                    )

                elif robots_result["status"] == "not_listed":

                    st.session_state[
                        "detected_sitemap"
                    ] = ""

                    st.warning(
                        "Robots.txt istnieje, ale nie zawiera "
                        "adresu sitemap. Wklej URL sitemap ręcznie."
                    )

                else:

                    st.session_state[
                        "detected_sitemap"
                    ] = ""

                    st.warning(
                        "Nie udało się sprawdzić robots.txt. "
                        "Wklej URL sitemap ręcznie."
                    )

    # -------------------------------------------------
    # POKAŻ ZNALEZIONĄ SITEMAPĘ
    # -------------------------------------------------

    detected_sitemap = st.session_state.get(
        "detected_sitemap",
        ""
    )

    if detected_sitemap:

        st.markdown(
            "**Znaleziony adres sitemap:**"
        )

        st.code(
            detected_sitemap,
            language="text"
        )

    effective_sitemap_url = (
        sitemap_url.strip()
        or detected_sitemap
    )

    # -------------------------------------------------
    # WYKLUCZENIA URL
    # -------------------------------------------------

    exclude_input = st.text_area(
        "Wyklucz URL-e zawierające",
        placeholder=(
            "/pl/p/\n"
            "/produkt/\n"
            "/tag/\n"
            "/autor/"
        ),
        height=100,
        help=(
            "Wpisz fragmenty URL-i, które mają zostać "
            "pominięte podczas analizy. "
            "Każdy fragment wpisz w osobnej linii."
        )
    )

    exclude_fragments = [
        line.strip()
        for line in exclude_input.splitlines()
        if line.strip()
    ]

    # -------------------------------------------------
    # ANALIZUJ
    # -------------------------------------------------

    analyze = st.button(
        "🔍 Analizuj",
        type="primary",
        use_container_width=True
    )

    if analyze:

        # -------------------------------------------------
        # WALIDACJA ARTYKUŁU
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

        # -------------------------------------------------
        # WALIDACJA SITEMAP
        # -------------------------------------------------

        if not effective_sitemap_url:

            if mode == "Mam już artykuł na stronie":

                st.error(
                    "Nie znaleziono sitemap. "
                    "Wpisz jej adres ręcznie lub użyj "
                    "przycisku „Znajdź sitemapę”."
                )

            else:

                st.error(
                    "Przy wklejonej treści artykułu "
                    "podaj URL sitemap ręcznie."
                )

            st.stop()

        # -------------------------------------------------
        # POBRANIE ARTYKUŁU
        # -------------------------------------------------

        if mode == "Mam już artykuł na stronie":

            try:

                with st.spinner(
                    "Pobieram i analizuję artykuł..."
                ):

                    article_html, stats = (
                        extract_article_content(
                            article_url
                        )
                    )

                st.success(
                    "Strona artykułu została pobrana."
                )

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
                        f"H4: {stats['h4']}"
                    )

                    st.write(
                        f"Listy: {stats['lists']}"
                    )

                    st.write(
                        f"Znaki: {stats['characters']}"
                    )

                    st.write(
                        f"CMS: {stats['cms']}"
                    )

                    st.write(
                        f"Metoda ekstrakcji: "
                        f"{stats['method']}"
                    )

            except Exception as e:

                st.error(
                    f"Nie udało się pobrać artykułu: {e}"
                )

                st.stop()

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

        # -------------------------------------------------
        # PODGLĄD ARTYKUŁU
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

        st.markdown(
            "<div style='height: 50px;'></div>",
            unsafe_allow_html=True
        )

        # -------------------------------------------------
        # ODCZYT SITEMAP
        # -------------------------------------------------

        try:

            sitemap_start = time.perf_counter()

            with st.spinner(
                "Odczytuję sitemapę..."
            ):

                (
                    sitemap_urls,
                    total_sitemap_urls,
                    excluded_count
                ) = get_sitemap_urls(
                    effective_sitemap_url,
                    exclude_fragments=exclude_fragments
                )

            sitemap_time = (
                time.perf_counter()
                - sitemap_start
            )

            if not sitemap_urls:

                st.warning(
                    "Nie znaleziono żadnych URL-i "
                    "w sitemapie po zastosowaniu wykluczeń."
                )

                st.stop()

            # -------------------------------------------------
            # USUNIĘCIE AKTUALNEGO ARTYKUŁU
            # -------------------------------------------------

            removed_current_article = 0

            if mode == "Mam już artykuł na stronie":

                current_url = (
                    article_url
                    .strip()
                    .rstrip("/")
                    .lower()
                )

                original_count = len(
                    sitemap_urls
                )

                sitemap_urls = [
                    url
                    for url in sitemap_urls
                    if url
                    .strip()
                    .rstrip("/")
                    .lower()
                    != current_url
                ]

                if len(sitemap_urls) < original_count:

                    removed_current_article = 1

            # -------------------------------------------------
            # PODSUMOWANIE
            # -------------------------------------------------

            st.success(
                f"Sitemap została odczytana."
            )

            col1, col2, col3 = st.columns(3)

            with col1:

                st.metric(
                    "URL-i w sitemap",
                    total_sitemap_urls
                )

            with col2:

                st.metric(
                    "Wykluczonych",
                    excluded_count
                )

            with col3:

                st.metric(
                    "Pozostałych",
                    len(sitemap_urls)
                )

            if removed_current_article:

                st.caption(
                    "Pominięto również URL aktualnie "
                    "analizowanego artykułu."
                )

            st.caption(
                f"Czas odczytu sitemap: "
                f"{sitemap_time:.2f} s"
            )

            st.info(
                "ℹ️ Z sitemap pobierane są wyłącznie "
                "adresy URL. Narzędzie nie odwiedza "
                "stron znajdujących się pod tymi adresami."
            )

        except Exception as e:

            st.error(
                f"Nie udało się odczytać sitemap: {e}"
            )

    # -------------------------------------------------
    # POWRÓT
    # -------------------------------------------------

    st.markdown("---")

    if st.button(
        "← Wróć do narzędzi"
    ):

        st.session_state["page"] = "home"

        st.rerun()
