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
    "comments",
    "comment",
    "breadcrumb",
    "breadcrumbs",
    "pagination",
    "advert",
    "ads",
    "newsletter",
    "login",
    "register",
}


def detect_cms(html):
    """
    Próbuje rozpoznać CMS.
    Jest to tylko informacja pomocnicza.
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

    if "shoper" in html_lower:
        return "shoper"

    if (
        "cdn.shopify.com" in html_lower
        or "shopify" in html_lower
    ):
        return "shopify"

    if "joomla" in html_lower:
        return "joomla"

    if (
        "webflow.css" in html_lower
        or "webflow.js" in html_lower
    ):
        return "webflow"

    return "unknown"


def _clean_text(element):
    """
    Zwraca oczyszczony tekst elementu.
    """

    return " ".join(
        element.get_text(
            " ",
            strip=True
        ).split()
    )


def _identifier_matches(element):
    """
    Sprawdza class i id danego elementu.

    Ważne:
    sprawdzamy tylko konkretny element,
    a nie wszystkich jego rodziców.
    """

    classes = element.get("class", [])
    element_id = element.get("id", "")

    if isinstance(classes, list):
        values = classes[:]
    else:
        values = [str(classes)]

    if element_id:
        values.append(str(element_id))

    text = " ".join(values).lower()

    for keyword in EXCLUDED_KEYWORDS:

        if keyword in text:
            return True

    return False


def _is_excluded(element):
    """
    Sprawdza, czy sam element znajduje się w oczywiście
    wykluczonym miejscu.

    Nie sprawdzamy wszystkich rodziców pod kątem klas,
    ponieważ mogłoby to wyciąć cały artykuł.
    """

    current = element

    while current is not None:

        tag_name = getattr(
            current,
            "name",
            None
        )

        if tag_name in EXCLUDED_TAGS:
            return True

        current = current.parent

    # Dopiero na samym elemencie sprawdzamy class/id.
    if _identifier_matches(element):
        return True

    return False


def _is_valid_block(element):
    """
    Sprawdza, czy element jest wartościowym fragmentem
    tekstu.
    """

    if element.name not in CONTENT_TAGS:
        return False

    if _is_excluded(element):
        return False

    text = _clean_text(element)

    if not text:
        return False

    # Nagłówki mogą być krótkie.
    if element.name in {
        "h1",
        "h2",
        "h3",
        "h4",
    }:
        return len(text) >= 3

    # Dla zwykłego tekstu wymagamy minimum znaków.
    return len(text) >= 20


def _get_content_blocks(soup):
    """
    Pobiera wszystkie elementy treści z całej strony.

    Nie wybieramy jednego kontenera.
    """

    blocks = []

    for element in soup.find_all(CONTENT_TAGS):

        if not _is_valid_block(element):
            continue

        # Jeżeli P znajduje się w LI,
        # nie dodajemy go drugi raz.
        if element.name == "p":

            if element.find_parent("li") is not None:
                continue

        blocks.append(element)

    return blocks


def _remove_duplicates(blocks):
    """
    Usuwa powtarzające się elementy.
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


def _calculate_content_score(blocks):
    """
    Oblicza, czy znalezione bloki wyglądają jak
    rzeczywista treść strony.
    """

    if not blocks:
        return 0

    score = 0

    for block in blocks:

        text = _clean_text(block)

        if block.name == "h1":
            score += 20

        elif block.name == "h2":
            score += 10

        elif block.name == "h3":
            score += 8

        elif block.name == "h4":
            score += 6

        elif block.name == "p":
            score += 3

        elif block.name == "li":
            score += 1

        if len(text) > 200:
            score += 2

    return score


def extract_content_blocks(html):
    """
    Główna funkcja ekstrakcji.

    Zwraca:

        cms
        blocks
    """

    soup = BeautifulSoup(
        html,
        "lxml"
    )

    cms = detect_cms(html)

    blocks = _get_content_blocks(soup)

    blocks = _remove_duplicates(blocks)

    score = _calculate_content_score(blocks)

    if not blocks or score < 10:
        return cms, []

    return cms, blocks
