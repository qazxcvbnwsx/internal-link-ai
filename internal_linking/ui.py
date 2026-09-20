import streamlit as st
import html
import time

from .extractor import extract_article_content

from .sitemap import (
    get_sitemap_urls,
    find_sitemap_in_robots,
)

from .candidate_selector import (
    select_candidate_urls,
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
    # FILTROWANIE URL
    # -------------------------------------------------

    st.markdown(
        "### Filtrowanie adresów URL"
    )

    filter_mode_label = st.radio(
        "Wybierz sposób filtrowania:",
        [
            "Wyklucz adresy zawierające",
            "Szukaj tylko adresów zawierających",
        ],
        horizontal=True
    )

    if (
        filter_mode_label
        == "Wyklucz adresy zawierające"
    ):

        filter_mode = "exclude"

        filter_label = (
            "Wyklucz URL-e zawierające"
        )

        filter_help = (
            "Wpisz fragmenty URL-i, które mają "
            "zostać pominięte. Każdy fragment "
            "w osobnej linii."
        )

        filter_placeholder = (
            "/pl/p/\n"
            "/produkt/\n"
            "/tag/\n"
            "/autor/"
        )

    else:

        filter_mode = "include"

        filter_label = (
            "Szukaj tylko adresów zawierających"
        )

        filter_help = (
            "Wpisz fragmenty URL-i, które mają "
            "zostać znalezione. Zostaną zachowane "
            "tylko URL-e zawierające przynajmniej "
            "jeden z podanych fragmentów."
        )

        filter_placeholder = (
            "category\n"
            "/c/\n"
            "/blog/"
        )

    filter_input = st.text_area(
        filter_label,
        placeholder=filter_placeholder,
        height=100,
        help=filter_help
    )

    filter_fragments = [
        line.strip()
        for line in filter_input.splitlines()
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

            sitemap_progress_text = st.empty()

            sitemap_progress_bar = st.progress(
                0
            )

            def update_sitemap_progress(
                completed,
                total
            ):

                if total <= 0:
                    return

                elapsed = (
                    time.perf_counter()
                    - sitemap_start
                )

                sitemap_progress_text.markdown(
                    f"**Pobieranie sitemap:** "
                    f"{completed} / {total} "
                    f"• **Czas:** "
                    f"{elapsed:.1f} s"
                )

                sitemap_progress_bar.progress(
                    completed / total
                )

            (
                sitemap_urls,
                total_sitemap_urls,
                filtered_out_count
            ) = get_sitemap_urls(
                effective_sitemap_url,
                filter_fragments=filter_fragments,
                filter_mode=filter_mode,
                progress_callback=(
                    update_sitemap_progress
                )
            )

            sitemap_time = (
                time.perf_counter()
                - sitemap_start
            )

            sitemap_progress_bar.progress(
                1.0
            )

            sitemap_progress_text.success(
                f"Sitemap została odczytana "
                f"w {sitemap_time:.2f} s."
            )

            if not sitemap_urls:

                st.warning(
                    "Nie znaleziono żadnych URL-i "
                    "spełniających ustawione filtry."
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
                "Sitemap została odczytana."
            )

            col1, col2, col3 = st.columns(3)

            with col1:

                st.metric(
                    "URL-i w sitemap",
                    total_sitemap_urls
                )

            with col2:

                st.metric(
                    "Odfiltrowanych",
                    filtered_out_count
                )

            with col3:

                st.metric(
                    "URL-i po filtrach",
                    len(sitemap_urls)
                )

            if removed_current_article:

                st.caption(
                    "Aktualny artykuł został pominięty "
                    "w dalszej analizie."
                )

            st.info(
                "ℹ️ Z sitemap pobierane są wyłącznie "
                "adresy URL. Strony znajdujące się "
                "pod tymi adresami nie są odwiedzane."
            )

            # -------------------------------------------------
            # WYBÓR KANDYDATÓW
            # -------------------------------------------------

            with st.spinner(
                "Dobieram najbardziej pasujące "
                "URL-e do treści artykułu..."
            ):

                (
                    candidate_urls,
                    candidate_info
                ) = select_candidate_urls(
                    article_html,
                    sitemap_urls,
                    limit=30
                )

            st.markdown(
                "### 30 kandydatów do linkowania"
            )

            st.caption(
                "Każda fraza jest przypisywana "
                "tylko do jednego URL-a."
            )

            # -------------------------------------------------
            # TABELA
            # -------------------------------------------------

            table_rows = []

            for candidate in candidate_info[
                "candidate_matches"
            ]:

                phrases = candidate[
                    "matched_phrases"
                ]

                if phrases:

                    phrases_html = "<br>".join(
                        html.escape(
                            phrase
                        )
                        for phrase in phrases
                    )

                else:

                    phrases_html = (
                        '<span class="no-match">'
                        "brak unikalnej frazy"
                        "</span>"
                    )

                url = candidate[
                    "url"
                ]

                escaped_url = html.escape(
                    url,
                    quote=True
                )

                table_rows.append(
                    f"""
                    <tr>

                        <td class="phrase-cell">
                            {phrases_html}
                        </td>

                        <td class="url-cell">

                            <a
                                href="{escaped_url}"
                                target="_blank"
                                rel="noopener noreferrer"
                            >
                                {escaped_url}
                            </a>

                        </td>

                    </tr>
                    """
                )

            if table_rows:

                table_html = f"""
                <div class="candidate-table-wrapper">

                    <table class="candidate-table">

                        <thead>

                            <tr>

                                <th>
                                    Dopasowane frazy z artykułu
                                </th>

                                <th>
                                    URL
                                </th>

                            </tr>

                        </thead>

                        <tbody>
                            {"".join(table_rows)}
                        </tbody>

                    </table>

                </div>
                """

                st.html(
                    table_html
                )

            else:

                st.warning(
                    "Nie znaleziono URL-i z odpowiednimi "
                    "frazami w artykule."
                )

            # -------------------------------------------------
            # SZCZEGÓŁY SELEKCJI
            # -------------------------------------------------

            with st.expander(
                "Szczegóły selekcji"
            ):

                st.write(
                    f"URL-i po filtrach: "
                    f"{candidate_info['total_urls']}"
                )

                st.write(
                    f"URL-i dostępnych do selekcji: "
                    f"{candidate_info['eligible_urls']}"
                )

                st.write(
                    f"URL-i z dopasowaniem: "
                    f"{candidate_info['matched_urls']}"
                )

                st.write(
                    f"Wybranych kandydatów: "
                    f"{candidate_info['selected_urls']}"
                )

                st.write(
                    f"Już istniejące linki pominięte: "
                    f"{candidate_info['removed_existing_links']}"
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
