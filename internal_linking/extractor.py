from .crawler import download_page
from .content_detector import extract_content_blocks


def extract_article_content(url):
    """
    Pobiera stronę i wyciąga główną treść artykułu.

    Zwraca:
        article_html
        stats
    """

    html = download_page(url)

    cms, blocks = extract_content_blocks(html)

    if not blocks:
        raise ValueError(
            "Nie udało się znaleźć głównej treści artykułu."
        )

    output = []

    stats = {
        "h1": 0,
        "h2": 0,
        "h3": 0,
        "h4": 0,
        "paragraphs": 0,
        "lists": 0,
        "characters": 0,
        "cms": cms,
    }

    for block in blocks:

        tag = block.name

        text = block.get_text(
            " ",
            strip=True
        )

        if not text:
            continue

        # Nagłówki
        if tag == "h1":
            output.append(
                f"<h1>{text}</h1>"
            )
            stats["h1"] += 1

        elif tag == "h2":
            output.append(
                f"<h2>{text}</h2>"
            )
            stats["h2"] += 1

        elif tag == "h3":
            output.append(
                f"<h3>{text}</h3>"
            )
            stats["h3"] += 1

        elif tag == "h4":
            output.append(
                f"<h4>{text}</h4>"
            )
            stats["h4"] += 1

        # Paragrafy
        elif tag == "p":
            output.append(
                f"<p>{text}</p>"
            )
            stats["paragraphs"] += 1

        # Listy
        elif tag == "li":
            output.append(
                f"<li>{text}</li>"
            )
            stats["lists"] += 1

        # Cytaty
        elif tag == "blockquote":
            output.append(
                f"<blockquote>{text}</blockquote>"
            )

    article_html = "\n".join(output)

    stats["characters"] = len(
        " ".join(
            block.get_text(
                " ",
                strip=True
            )
            for block in blocks
        )
    )

    return article_html, stats
