import re
import html

import trafilatura
from bs4 import BeautifulSoup

from .crawler import download_page


# =========================================================
# CZYSZCZENIE TEKSTU
# =========================================================

def clean_text(text):

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# =========================================================
# USUWANIE NIEPOTRZEBNYCH ELEMENTÓW
# =========================================================

def remove_unwanted_elements(soup):

    for element in soup.find_all(
        [
            "script",
            "style",
            "svg",
            "noscript",
            "iframe",
            "form"
        ]
    ):

        element.decompose()


# =========================================================
# ZNALEZIENIE GŁÓWNEGO KONTENERA
# =========================================================

def find_main_content(soup):

    # Najczęstsze kontenery WordPress
    selectors = [
        "article",
        "main",
        ".entry-content",
        ".post-content",
        ".article-content",
        ".single-content",
        ".page-content",
        ".content-area",
        ".elementor-widget-theme-post-content",
        ".wp-block-post-content"
    ]

    candidates = []

    for selector in selectors:

        elements = soup.select(selector)

        for element in elements:

            text = element.get_text(
                " ",
                strip=True
            )

            if len(text) >= 200:

                candidates.append(
                    element
                )

    if candidates:

        # Wybieramy najdłuższy sensowny kontener
        return max(
            candidates,
            key=lambda element: len(
                element.get_text(
                    " ",
                    strip=True
                )
            )
        )

    return None


# =========================================================
# OCZYSZCZANIE GŁÓWNEJ TREŚCI
# =========================================================

def clean_content_container(container):

    # Kopia, żeby nie modyfikować przypadkiem
    # oryginalnego dokumentu
    content = BeautifulSoup(
        str(container),
        "html.parser"
    )

    remove_unwanted_elements(
        content
    )

    # Usuwamy typowe elementy nawigacyjne
    for selector in [
        "nav",
        "header",
        "footer",
        ".sidebar",
        ".widget",
        ".comments",
        ".comment",
        ".related-posts",
        ".share-buttons"
    ]:

        for element in content.select(
            selector
        ):

            element.decompose()

    # =====================================================
    # CZYSZCZENIE TEKSTU W ELEMENTACH
    # =====================================================

    for element in content.find_all(
        [
            "h1",
            "h2",
            "h3",
            "h4",
            "p",
            "li"
        ]
    ):

        text = element.get_text(
            " ",
            strip=True
        )

        text = clean_text(
            text
        )

        # Usuwamy puste elementy
        if not text:

            element.decompose()

            continue

        # Czyścimy tekst z nadmiarowych spacji
        element.clear()

        element.append(
            text
        )

    return content


# =========================================================
# GŁÓWNA FUNKCJA
# =========================================================

def extract_article_content(url):

    raw_html = download_page(
        url
    )

    # =====================================================
    # ORYGINALNY HTML
    # =====================================================

    original_soup = BeautifulSoup(
        raw_html,
        "html.parser"
    )

    remove_unwanted_elements(
        original_soup
    )

    # =====================================================
    # PRÓBA ZNALEZIENIA GŁÓWNEJ TREŚCI
    # =====================================================

    main_content = find_main_content(
        original_soup
    )

    # =====================================================
    # JEŚLI ZNALEZIONO KONTENER
    # =====================================================

    if main_content:

        content = clean_content_container(
            main_content
        )

    # =====================================================
    # FALLBACK — TRAFILATURA
    # =====================================================

    else:

        extracted_html = trafilatura.extract(
            raw_html,
            output_format="html",
            include_links=False,
            include_images=False,
            include_tables=True,
            include_formatting=True,
            favor_precision=False,
            favor_recall=True
        )

        if not extracted_html:

            raise ValueError(
                "Nie udało się wyodrębnić głównej "
                "treści strony."
            )

        content = BeautifulSoup(
            extracted_html,
            "html.parser"
        )

        remove_unwanted_elements(
            content
        )

    # =====================================================
    # SPRAWDZENIE TREŚCI
    # =====================================================

    clean_article_text = content.get_text(
        " ",
        strip=True
    )

    if len(clean_article_text) < 200:

        raise ValueError(
            "Znaleziono zbyt mało tekstu "
            "w głównej treści strony."
        )

    # =====================================================
    # STATYSTYKI
    # =====================================================

    stats = {

        "h1": len(
            content.find_all("h1")
        ),

        "h2": len(
            content.find_all("h2")
        ),

        "h3": len(
            content.find_all("h3")
        ),

        "h4": len(
            content.find_all("h4")
        ),

        "paragraphs": len(
            content.find_all("p")
        ),

        "lists": len(
            content.find_all(
                ["ul", "ol"]
            )
        ),

        "characters": len(
            clean_article_text
        )
    }

    # =====================================================
    # HTML DO PODGLĄDU
    # =====================================================

    article_html = str(
        content
    )

    return article_html, stats
