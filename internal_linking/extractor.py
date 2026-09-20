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
# ELEMENTY, KTÓRE NIE SĄ TREŚCIĄ ARTYKUŁU
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
        ".cookies",
    ]

    for selector in selectors:

        for element in soup.select(selector):

            element.decompose()


# =========================================================
# ZNALEZIENIE GŁÓWNEJ TREŚCI
# =========================================================

def find_main_content(soup):

    selectors = [

        # WordPress
        "article .entry-content",
        "article .post-content",
        "article .page-content",
        "article .article-content",

        # Elementor
        ".elementor-widget-theme-post-content",
        ".elementor-widget-text-editor",

        # Gutenberg
        ".wp-block-post-content",

        # Popularne klasy
        ".entry-content",
        ".post-content",
        ".page-content",
        ".article-content",
        ".single-content",

        # Ogólne
        "article",
        "main",
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
    # WYBIERAMY NAJBARDZIEJ PRAWDOPODOBNY KONTENER
    # =====================================================

    # Nie zawsze największy element jest najlepszy,
    # dlatego preferujemy bardziej szczegółowe selektory.

    for selector in selectors:

        for element in candidates:

            if element in soup.select(selector):

                return element

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
# CZYSZCZENIE KONTENERA
# =========================================================

def clean_content(container):

    # Tworzymy niezależną kopię
    content = BeautifulSoup(
        str(container),
        "html.parser"
    )

    remove_unwanted_elements(
        content
    )

    # =====================================================
    # USUWAMY ELEMENTY, KTÓRE MOGĄ BYĆ WEWNĄTRZ ARTYKUŁU
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
        "breadcrumbs",
    ]

    for class_name in unwanted_classes:

        for element in content.select(
            f".{class_name}"
        ):

            element.decompose()

    # =====================================================
    # CZYŚCIMY TEKST
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

        # Usuwamy zawartość HTML wewnątrz elementu,
        # ale zachowujemy sam element, np. H3.
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
    # ZNALEZIENIE TREŚCI
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
    # OCZYSZCZENIE TREŚCI
    # =====================================================

    content = clean_content(
        main_content
    )

    # =====================================================
    # TEKST DO WALIDACJI
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
