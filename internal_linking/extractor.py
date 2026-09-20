from bs4 import BeautifulSoup
import trafilatura

from .crawler import download_page
from .content_detector import extract_content_blocks


CONTENT_TAGS = [
    "h1",
    "h2",
    "h3",
    "h4",
    "p",
    "li",
    "blockquote",
]


def _extract_with_trafilatura(html):
    """
    Drugi, awaryjny mechanizm ekstrakcji treści.
    Używany, gdy standardowy ekstraktor nie znalazł treści.
    """

    extracted = trafilatura.extract(
        html,
        output_format="html",
        include_formatting=True,
        include_links=True,
    )

    if not extracted:
        return []


    soup = BeautifulSoup(
        extracted,
        "lxml"
    )

    blocks = []

    for element in soup.find_all(CONTENT_TAGS):

        text = " ".join(
            element.get_text(
                " ",
                strip=True
            ).split()
        )

        if not text:
            continue

        if element.name in {
            "h1",
            "h2",
            "h3",
            "h4",
        }:
            if len(text) < 1:
                continue

        else:
            if len(text) < 20:
                continue

        blocks.append(element)

    return blocks


def _build_article_html(blocks):
    """
    Buduje HTML podglądu z listy elementów.
    """

    output = []

    for block in blocks:

        tag = block.name

        text = " ".join(
            block.get_text(
                " ",
                strip=True
            ).split()
        )

        if not text:
            continue

        if tag == "h1":
            output.append(
                f"<h1>{text}</h1>"
            )

        elif tag == "h2":
            output.append(
                f"<h2>{text}</h2>"
            )

        elif tag == "h3":
            output.append(
                f"<h3>{text}</h3>"
            )

        elif tag == "h4":
            output.append(
                f"<h4>{text}</h4>"
            )

        elif tag == "p":
            output.append(
                f"<p>{text}</p>"
            )

        elif tag == "li":
            output.append(
                f"<li>{text}</li>"
            )

        elif tag == "blockquote":
            output.append(
                f"<blockquote>{text}</blockquote>"
            )

    return "\n".join(output)


def _build_stats(blocks, cms, method):
    """
    Tworzy statystyki ekstrakcji.
    """

    stats = {
        "h1": 0,
        "h2": 0,
        "h3": 0,
        "h4": 0,
        "paragraphs": 0,
        "lists": 0,
        "characters": 0,
        "cms": cms,
        "method": method,
    }

    text_parts = []

    for block in blocks:

        text = " ".join(
            block.get_text(
                " ",
                strip=True
            ).split()
        )

        if not text:
            continue

        text_parts.append(text)

        if block.name == "h1":
            stats["h1"] += 1

        elif block.name == "h2":
            stats["h2"] += 1

        elif block.name == "h3":
            stats["h3"] += 1

        elif block.name == "h4":
            stats["h4"] += 1

        elif block.name == "p":
            stats["paragraphs"] += 1

        elif block.name == "li":
            stats["lists"] += 1

    stats["characters"] = len(
        " ".join(text_parts)
    )

    return stats


def extract_article_content(url):
    """
    Pobiera stronę i wyciąga główną treść artykułu.

    Najpierw używany jest własny ekstraktor DOM.
    Jeżeli nie znajdzie treści, uruchamiany jest
    fallback oparty o Trafilaturę.

    Zwraca:
        article_html
        stats
    """

    html = download_page(url)

    cms, blocks = extract_content_blocks(html)

    method = "standard"

    # -------------------------------------------------
    # FALLBACK
    # -------------------------------------------------

    if not blocks:

        blocks = _extract_with_trafilatura(
            html
        )

        method = "trafilatura"

    if not blocks:
        raise ValueError(
            "Nie udało się znaleźć głównej treści artykułu."
        )

    article_html = _build_article_html(
        blocks
    )

    stats = _build_stats(
        blocks,
        cms,
        method
    )

    return article_html, stats
