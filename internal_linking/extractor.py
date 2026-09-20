import re
import html

import trafilatura
from bs4 import BeautifulSoup

from .crawler import download_page


def clean_text(text):
    """
    Czyści tekst z nadmiarowych spacji
    i prostych elementów Markdown.
    """

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


def extract_article_content(url):

    raw_html = download_page(url)

    # =====================================================
    # PRÓBA WYODRĘBNIENIA GŁÓWNEJ TREŚCI
    # =====================================================

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

    # =====================================================
    # PARSOWANIE HTML
    # =====================================================

    soup = BeautifulSoup(
        extracted_html,
        "html.parser"
    )

    # =====================================================
    # USUWANIE ŚMIECI
    # =====================================================

    for element in soup.find_all(
        ["script", "style", "svg", "noscript"]
    ):

        element.decompose()

    # =====================================================
    # NAGŁÓWKI
    # =====================================================

    headings = soup.find_all(
        ["h1", "h2", "h3", "h4"]
    )

    # =====================================================
    # AKAPITY
    # =====================================================

    paragraphs = soup.find_all("p")

    # =====================================================
    # LISTY
    # =====================================================

    lists = soup.find_all(
        ["ul", "ol"]
    )

    # =====================================================
    # CZYSZCZENIE TEKSTU
    # =====================================================

    for element in soup.find_all(True):

        if element.name in [
            "h1",
            "h2",
            "h3",
            "h4",
            "p",
            "li"
        ]:

            text = element.get_text(
                " ",
                strip=True
            )

            text = clean_text(text)

            element.clear()

            if text:
                element.append(
                    text
                )

    # =====================================================
    # TEKST CAŁEGO ARTYKUŁU
    # =====================================================

    clean_article_text = soup.get_text(
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
            soup.find_all("h1")
        ),

        "h2": len(
            soup.find_all("h2")
        ),

        "h3": len(
            soup.find_all("h3")
        ),

        "h4": len(
            soup.find_all("h4")
        ),

        "paragraphs": len(
            soup.find_all("p")
        ),

        "lists": len(
            soup.find_all(
                ["ul", "ol"]
            )
        ),

        "characters": len(
            clean_article_text
        )
    }

    return str(soup), stats
