import re

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
# ELEMENTY, KTÓRE NIE SĄ TREŚCIĄ
# =========================================================

def remove_unwanted_elements(soup):

    selectors = [
        "script",
        "style",
        "svg",
        "noscript",
        "iframe",
        "nav",
        "header",
        "footer",
        "form",
        ".sidebar",
        ".widget",
        ".comments",
        ".comment",
        ".related-posts",
        ".share-buttons",
        ".cookie",
        ".cookies"
    ]

    for selector in selectors:

        for element in soup.select(selector):

            element.decompose()


# =========================================================
# ZNALEZIENIE GŁÓWNEGO KONTENERA
# =========================================================

def find_main_content(soup):

    selectors = [

        # WordPress
        ".entry-content",
        ".post-content",
        ".page-content",
        ".article-content",
        ".single-content",

        # Elementor
        ".elementor-widget-theme-post-content",

        # Gutenberg
        ".wp-block-post-content",

        # Ogólne
        "article",
        "main"
    ]

    candidates = []

    for selector in selectors:

        elements = soup.select(
            selector
        )

        for element in elements:

            text = element.get_text(
                " ",
                strip=True
            )

            if len(text) >= 300:

                candidates.append(
                    element
                )

    if not candidates:

        return None

    # =====================================================
    # WYBIERAMY NAJWIĘKSZY KONTENER
    # =====================================================

    return max(
        candidates,
        key=lambda element: len(
            element.get_text(
                " ",
                strip=True
            )
        )
    )


# =========================================================
# CZYSZCZENIE TREŚCI
# =========================================================

def clean_content(container):

    content = BeautifulSoup(
        str(container),
        "html.parser"
    )

    remove_unwanted_elements(
        content
    )

    # =====================================================
    # USUWANIE ELEMENTÓW POMOCNICZYCH
    # =====================================================

    unwanted_classes = [
        "share",
        "social",
        "related",
        "author",
        "comments",
        "comment",
        "newsletter",
        "breadcrumb",
        "breadcrumbs"
    ]

    for class_name in unwanted_classes:

        for element in content.select(
            f".{class_name}"
        ):

            element.decompose()

    # =====================================================
    # CZYSZCZENIE TEKSTU
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

        if not text:

            element.decompose()

            continue

        # Zachowujemy strukturę HTML:
        # H1, H2, H3, H4, P, LI

        element.clear()

        element.append(
            text
        )

    return content


# =========================================================
# GŁÓWNA FUNKCJA
# =========================================================

def extract_article_content(url):

    # =====================================================
    # POBRANIE STRONY
    # =====================================================

    raw_html = download_page(
        url
    )

    # =====================================================
    # PARSOWANIE ORYGINALNEGO HTML
    # =====================================================

    soup = BeautifulSoup(
        raw_html,
        "html.parser"
    )

    # =====================================================
    # NAJPIERW SZUKAMY TREŚCI
    #
    # WAŻNE:
    # nie usuwamy jeszcze header/footer/nav,
    # ponieważ mogą znajdować się w strukturze
    # kontenera potrzebnego do znalezienia artykułu.
    # =====================================================

    main_content = find_main_content(
        soup
    )

    if main_content is None:

        raise ValueError(
            "Nie udało się znaleźć głównej "
            "treści artykułu."
        )

    # =====================================================
    # DOPIERO TERAZ CZYŚCIMY TREŚĆ
    # =====================================================

    content = clean_content(
        main_content
    )

    # =====================================================
    # TEKST ARTYKUŁU
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
