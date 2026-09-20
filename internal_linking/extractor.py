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
        ".cookies",
        ".breadcrumbs",
        ".breadcrumb"
    ]

    for selector in selectors:

        for element in soup.select(selector):

            element.decompose()


# =========================================================
# ZNALEZIENIE GŁÓWNEGO OBSZARU STRONY
# =========================================================

def find_main_content(soup):

    selectors = [

        # Najbardziej typowe dla WordPressa
        "article",
        "main",

        # WordPress
        ".entry-content",
        ".post-content",
        ".page-content",
        ".article-content",
        ".single-content",

        # Elementor
        ".elementor-widget-theme-post-content",

        # Gutenberg
        ".wp-block-post-content"
    ]

    candidates = []

    for selector in selectors:

        for element in soup.select(selector):

            text_length = len(
                element.get_text(
                    " ",
                    strip=True
                )
            )

            if text_length >= 300:

                candidates.append(
                    (
                        element,
                        text_length
                    )
                )

    if not candidates:
        return None

    # =====================================================
    # WYBIERAMY NAJWIĘKSZY KONTENER
    # =====================================================

    # Ważne:
    # nie wybieramy pierwszego pasującego elementu.
    #
    # Przy Elementorze treść może być podzielona
    # na kilka kolumn. Największy kontener nadrzędny
    # daje większą szansę na zachowanie całego artykułu.

    candidates.sort(
        key=lambda item: item[1],
        reverse=True
    )

    return candidates[0][0]


# =========================================================
# CZYSZCZENIE GŁÓWNEJ TREŚCI
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
    # USUWANIE ELEMENTÓW NIEBĘDĄCYCH TREŚCIĄ
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
    # USUWANIE PUSTYCH ELEMENTOROWYCH KONTENERÓW
    # =====================================================

    for element in content.find_all(
        ["div", "section"]
    ):

        text = element.get_text(
            " ",
            strip=True
        )

        if not text:

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

        # Zachowujemy element HTML
        # np. H2/H3/P
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
    # PARSOWANIE ORYGINALNEGO HTML
    # =====================================================

    soup = BeautifulSoup(
        raw_html,
        "html.parser"
    )

    # =====================================================
    # USUWANIE ŚMIECI PRZED SZUKANIEM TREŚCI
    # =====================================================

    remove_unwanted_elements(
        soup
    )

    # =====================================================
    # GŁÓWNY KONTENER
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
    # CZYSZCZENIE
    # =====================================================

    content = clean_content(
        main_content
    )

    # =====================================================
    # TEKST
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
