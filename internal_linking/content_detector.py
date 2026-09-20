from bs4 import BeautifulSoup


CONTENT_TAGS = {
    "h1",
    "h2",
    "h3",
    "h4",
    "p",
    "li",
    "blockquote",
}


EXCLUDED_TAGS = {
    "script",
    "style",
    "noscript",
    "svg",
    "nav",
    "header",
    "footer",
    "aside",
    "form",
    "iframe",
    "canvas",
}


EXCLUDED_KEYWORDS = {
    "menu",
    "navigation",
    "nav",
    "header",
    "footer",
    "sidebar",
    "widget",
    "cookie",
    "consent",
    "popup",
    "modal",
    "social",
    "share",
    "sharing",
    "related",
    "recommend",
    "comments",
    "comment",
    "breadcrumb",
    "breadcrumbs",
    "pagination",
    "advert",
    "ads",
    "banner",
    "newsletter",
    "login",
    "register",
}


def detect_cms(html):
    """
    Próbuje rozpoznać CMS.
    CMS jest tylko informacją pomocniczą.
    Ekstrakcja treści nie zależy od konkretnego CMS-a.
    """

    html_lower = html.lower()

    if (
        "wp-content" in html_lower
        or "wp-includes" in html_lower
        or "wordpress" in html_lower
    ):
        return "wordpress"

    if "prestashop" in html_lower:
        return "prestashop"

    if (
        "shoper" in html_lower
        or "shoparena" in html_lower
    ):
        return "shoper"

    if (
        "cdn.shopify.com" in html_lower
        or "shopify" in html_lower
    ):
        return "shopify"

    if (
        "/media/system/" in html_lower
        or "joomla" in html_lower
    ):
        return "joomla"

    if (
        "webflow.css" in html_lower
        or "webflow.js" in html_lower
    ):
        return "webflow"

    return "unknown"


def _identifier(element):
    """
    Łączy class i id elementu.
    """

    classes = element.get("class", [])
    element_id = element.get("id", "")

    if isinstance(classes, list):
        classes = " ".join(classes)

    return f"{classes} {element_id}".lower()


def _is_excluded(element):
    """
    Sprawdza element oraz jego rodziców.
    """

    current = element

    while current is not None:

        if getattr(current, "name", None) in EXCLUDED_TAGS:
            return True

        identifier = _identifier(current)

        for keyword in EXCLUDED_KEYWORDS:
            if keyword in identifier:
                return True

        current = current.parent

    return False


def _clean_text(element):
    """
    Pobiera czysty tekst elementu.
    """

    return " ".join(
        element.get_text(
            " ",
            strip=True
        ).split()
    )


def _is_valid_block(element):
    """
    Sprawdza, czy element może być fragmentem
    głównej treści.
    """

    if element.name not in CONTENT_TAGS:
        return False

    if _is_excluded(element):
        return False

    text = _clean_text(element)

    if not text:
        return False

    # Bardzo krótkie elementy zwykle nie są
    # właściwą treścią artykułu.
    if len(text) < 20:
        return False

    return True


def _get_blocks(soup):
    """
    Pobiera wszystkie potencjalne bloki treści
    z całego dokumentu.

    Nie wybiera jednego kontenera.
    """

    blocks = []

    for element in soup.find_all(CONTENT_TAGS):

        if not _is_valid_block(element):
            continue

        # Jeżeli LI zawiera P, nie chcemy pobierać
        # P osobno, ponieważ powstałby duplikat.
        if element.name == "p":
            parent_li = element.find_parent("li")

            if parent_li is not None:
                continue

        blocks.append(element)

    return blocks


def _block_score(element):
    """
    Ocenia pojedynczy blok tekstu.

    Wyższy wynik oznacza większe prawdopodobieństwo,
    że jest częścią właściwego artykułu.
    """

    score = 0

    text = _clean_text(element)

    if element.name == "h1":
        score += 15

    elif element.name == "h2":
        score += 12

    elif element.name == "h3":
        score += 10

    elif element.name == "h4":
        score += 8

    elif element.name == "p":
        score += 5

    elif element.name == "li":
        score += 3

    elif element.name == "blockquote":
        score += 5

    # Dłuższe fragmenty są częściej właściwą treścią.
    if len(text) >= 100:
        score += 5

    if len(text) >= 250:
        score += 5

    if len(text) >= 500:
        score += 5

    # Element znajdujący się wewnątrz article/main
    # dostaje dodatkowy sygnał.
    parent = element.parent

    while parent is not None:

        if getattr(parent, "name", None) == "article":
            score += 15
            break

        if getattr(parent, "name", None) == "main":
            score += 15
            break

        parent = parent.parent

    return score


def _remove_duplicates(blocks):
    """
    Usuwa identyczne fragmenty tekstu.
    """

    result = []
    seen = set()

    for block in blocks:

        text = _clean_text(block)

        key = (
            block.name,
            text
        )

        if key in seen:
            continue

        seen.add(key)
        result.append(block)

    return result


def _find_content_region(blocks):
    """
    Próbuje określić, które fragmenty należą do głównej
    treści bez wybierania jednego kontenera.

    Wykorzystujemy sąsiedztwo bloków oraz obecność nagłówków.
    """

    if not blocks:
        return []

    scores = [
        _block_score(block)
        for block in blocks
    ]

    # Minimalny próg.
    valid = []

    for block, score in zip(blocks, scores):

        if score >= 5:
            valid.append(block)

    if not valid:
        return blocks

    # Jeżeli mamy dużo prawidłowych bloków,
    # zachowujemy ich kolejność z dokumentu.
    return valid


def extract_content_blocks(html):
    """
    Główna funkcja.

    Zwraca:

        cms
        blocks

    blocks zawiera elementy:

        H1
        H2
        H3
        H4
        P
        LI
        BLOCKQUOTE
    """

    soup = BeautifulSoup(
        html,
        "lxml"
    )

    cms = detect_cms(html)

    blocks = _get_blocks(soup)

    blocks = _find_content_region(blocks)

    blocks = _remove_duplicates(blocks)

    return cms, blocks
