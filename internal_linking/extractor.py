import re
import html

import trafilatura
from bs4 import BeautifulSoup

from .crawler import download_page


def clean_markdown_text(text):

    # Obrazki Markdown
    text = re.sub(
        r"!\[[^\]]*\]\([^)]+\)",
        "",
        text
    )

    # Linki Markdown → sam tekst
    text = re.sub(
        r"\[([^\]]+)\]\([^)]+\)",
        r"\1",
        text
    )

    # HTML
    text = re.sub(
        r"<[^>]+>",
        "",
        text
    )

    # Pogrubienie
    text = re.sub(
        r"\*\*(.*?)\*\*",
        r"\1",
        text
    )

    # Kursywa
    text = re.sub(
        r"\*(.*?)\*",
        r"\1",
        text
    )

    return text.strip()


def markdown_to_article_html(markdown_text):

    lines = markdown_text.splitlines()

    output = []

    paragraph_buffer = []

    in_list = False
    list_type = None

    def flush_paragraph():

        nonlocal paragraph_buffer

        if not paragraph_buffer:
            return

        text = " ".join(
            x.strip()
            for x in paragraph_buffer
            if x.strip()
        )

        paragraph_buffer = []

        if not text:
            return

        text = clean_markdown_text(text)

        if text:

            output.append(
                f"<p>{html.escape(text)}</p>"
            )

    def close_list():

        nonlocal in_list
        nonlocal list_type

        if in_list:

            output.append(
                f"</{list_type}>"
            )

            in_list = False
            list_type = None

    for raw_line in lines:

        line = raw_line.strip()

        # =================================================
        # PUSTA LINIA
        # =================================================

        if not line:

            flush_paragraph()

            continue

        # =================================================
        # NAGŁÓWEK
        # =================================================

        heading_match = re.match(
            r"^#{1,6}\s+(.+?)\s*$",
            line
        )

        if heading_match:

            flush_paragraph()
            close_list()

            level = len(
                re.match(
                    r"^#{1,6}",
                    line
                ).group(0)
            )

            if level > 4:
                level = 4

            heading_text = heading_match.group(1)

            heading_text = clean_markdown_text(
                heading_text
            )

            if heading_text:

                output.append(
                    f"<h{level}>"
                    f"{html.escape(heading_text)}"
                    f"</h{level}>"
                )

            continue

        # =================================================
        # LISTA NIEUPORZĄDKOWANA
        # =================================================

        unordered_match = re.match(
            r"^[-*+]\s+(.+)$",
            line
        )

        # =================================================
        # LISTA UPORZĄDKOWANA
        # =================================================

        ordered_match = re.match(
            r"^\d+[.)]\s+(.+)$",
            line
        )

        if unordered_match or ordered_match:

            flush_paragraph()

            current_type = (
                "ul"
                if unordered_match
                else "ol"
            )

            item_text = (
                unordered_match.group(1)
                if unordered_match
                else ordered_match.group(1)
            )

            if not in_list:

                in_list = True
                list_type = current_type

                output.append(
                    f"<{list_type}>"
                )

            elif list_type != current_type:

                close_list()

                in_list = True
                list_type = current_type

                output.append(
                    f"<{list_type}>"
                )

            item_text = clean_markdown_text(
                item_text
            )

            output.append(
                f"<li>{html.escape(item_text)}</li>"
            )

            continue

        # =================================================
        # ZWYKŁY TEKST
        # =================================================

        close_list()

        paragraph_buffer.append(
            line
        )

    flush_paragraph()
    close_list()

    return "".join(output)


def extract_article_content(url):

    raw_html = download_page(url)

    extracted = trafilatura.extract(
        raw_html,
        output_format="markdown",
        include_links=False,
        include_images=False,
        include_tables=True,
        include_formatting=True,
        favor_precision=False,
        favor_recall=True
    )

    if not extracted:

        raise ValueError(
            "Nie udało się wyodrębnić głównej "
            "treści strony."
        )

    # =====================================================
    # USUWANIE ŚMIECI
    # =====================================================

    extracted = re.sub(
        r"\[svg\]\([^)]+\)",
        "",
        extracted,
        flags=re.IGNORECASE
    )

    extracted = re.sub(
        r"\[image[^\]]*\]\([^)]+\)",
        "",
        extracted,
        flags=re.IGNORECASE
    )

    # =====================================================
    # MARKDOWN → HTML
    # =====================================================

    article_html = markdown_to_article_html(
        extracted
    )

    # =====================================================
    # WALIDACJA
    # =====================================================

    soup = BeautifulSoup(
        article_html,
        "html.parser"
    )

    clean_text = soup.get_text(
        " ",
        strip=True
    )

    if len(clean_text) < 200:

        raise ValueError(
            "Znaleziono zbyt mało tekstu "
            "w głównej treści strony."
        )

    # =====================================================
    # STATYSTYKI
    # =====================================================

    stats = {
        "h1": len(soup.find_all("h1")),
        "h2": len(soup.find_all("h2")),
        "h3": len(soup.find_all("h3")),
        "h4": len(soup.find_all("h4")),
        "paragraphs": len(soup.find_all("p")),
        "lists": len(
            soup.find_all(["ul", "ol"])
        ),
        "characters": len(clean_text)
    }

    return article_html, stats
