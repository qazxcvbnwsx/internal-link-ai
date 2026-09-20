from bs4 import BeautifulSoup


# Elementy, które z dużym prawdopodobieństwem nie należą
# do głównej treści strony.
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


# Słowa często występujące w klasach i ID elementów,
# które nie są główną treścią artykułu.
EXCLUDED_KEYWORDS = {
    "menu",
    "nav",
    "navigation",
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


CONTENT_TAGS = {
    "h1",
    "h2",
    "h3",
    "h4",
    "p",
    "li",
    "blockquote",
}


def detect_cms(html):
    """
    Próbuje rozpoznać CMS na podstawie charakterystycznych
    elementów znajdujących się w kodzie HTML.

    Rozpoznanie CMS jest tylko wskazówką.
    Ekstrakcja treści nie będzie od niego zależna.
    """

    html_lower = html.lower()

    # WordPress
    if (
        "wp-content" in html_lower
        or "wp-includes" in html_lower
        or 'name="generator" content="wordpress' in html_lower
    ):
        return "wordpress"

    # PrestaShop
    if (
        "prestashop" in html_lower
        or "prestashop" in html_lower
    ):
        return "prestashop"

    # Shoper
    if (
        "shoper" in html_lower
        or "shoparena" in html_lower
    ):
        return "shoper"

    # Shopify
    if (
        "cdn.shopify.com" in html_lower
        or "shopify" in html_lower
    ):
        return "shopify"

    # Joomla
    if (
        "/media/system/" in html_lower
        or "joomla" in html_lower
    ):
        return "joomla"

    # Webflow
    if (
        "webflow.css" in html_lower
        or "webflow.js" in html_lower
        or "webflow" in html_lower
    ):
        return "webflow"

    return "unknown"


def _get_element_identifier(element):
    """
    Zwraca połączoną wartość class + id elementu.
    """

    classes = element.get("class", [])
    element_id = element.get("id", "")

    if isinstance(classes, list):
        classes_text = " ".join(classes)
    else:
        classes_text = str(classes)

    return f"{classes_text} {element_id}".lower()


def _is_excluded(element):
    """
    Sprawdza, czy element lub jego rodzic znajduje się
    w obszarze, którego nie chcemy analizować.
    """

    current = element

    while current is not None and getattr(current, "name", None):
        if current.name in EXCLUDED_TAGS:
            return True

        identifier = _get_element_identifier(current)

        for keyword in EXCLUDED_KEYWORDS:
            if keyword in identifier:
                return True

        current = current.parent

    return False


def _get_text_length(element):
    """
    Zwraca długość tekstu znajdującego się w elemencie.
    """

    return len(
        element.get_text(" ", strip=True)
    )


def _get_link_text_length(element):
    """
    Zwraca długość tekstu znajdującego się wewnątrz linków.
    """

    length = 0

    for link in element.find_all("a"):
        length += len(
            link.get_text(" ", strip=True)
        )

    return length


def _get_semantic_blocks(element):
    """
    Pobiera wszystkie znaczące elementy treści
    znajdujące się wewnątrz danego kontenera.
    """

    blocks = []

    for child in element.find_all(CONTENT_TAGS):

        if _is_excluded(child):
            continue

        text = child.get_text(" ", strip=True)

        if not text:
            continue

        # Pomijamy bardzo krótkie elementy,
        # które zazwyczaj są przyciskami lub pojedynczymi etykietami.
        if len(text) < 20:
            continue

        blocks.append(child)

    return blocks


def _score_container(element):
    """
    Oblicza wynik dla potencjalnego kontenera głównej treści.
    Im wyższy wynik, tym bardziej element przypomina główną
    część artykułu.
    """

    if _is_excluded(element):
        return -999999

    blocks = _get_semantic_blocks(element)

    if not blocks:
        return -999999

    text_length = sum(
        _get_text_length(block)
        for block in blocks
    )

    headings = sum(
        1
        for block in blocks
        if block.name in {"h1", "h2", "h3", "h4"}
    )

    paragraphs = sum(
        1
        for block in blocks
        if block.name in {"p", "li", "blockquote"}
    )

    link_text_length = _get_link_text_length(element)

    if text_length == 0:
        return -999999

    link_ratio = link_text_length / text_length

    score = 0

    # Duża ilość treści jest dobrym sygnałem.
    score += min(text_length / 100, 100)

    # Większa liczba bloków tekstowych zwiększa wynik.
    score += min(len(blocks) * 3, 100)

    # Nagłówki są mocnym sygnałem artykułu.
    score += headings * 15

    # Paragrafy również.
    score += min(paragraphs * 2, 60)

    # Duża ilość tekstu będącego linkami sugeruje menu/sidebar.
    if link_ratio > 0.7:
        score -= 100

    elif link_ratio > 0.5:
        score -= 50

    return score


def find_content_containers(soup):
    """
    Znajduje potencjalne kontenery głównej treści.

    Nie zakładamy konkretnego CMS-a.
    """

    candidates = []

    # Najpierw sprawdzamy semantyczne elementy HTML.
    for tag_name in ["article", "main"]:
        for element in soup.find_all(tag_name):
            score = _score_container(element)

            if score > 0:
                candidates.append(
                    (score, element)
                )

    # Następnie sprawdzamy section/div.
    for tag_name in ["section", "div"]:
        for element in soup.find_all(tag_name):

            # Bardzo małe elementy nie mają sensu jako
            # główny kontener artykułu.
            if _get_text_length(element) < 200:
                continue

            score = _score_container(element)

            if score > 0:
                candidates.append(
                    (score, element)
                )

    candidates.sort(
        key=lambda item: item[0],
        reverse=True
    )

    return candidates


def extract_content_blocks(html):
    """
    Główna funkcja modułu.

    Zwraca:
        cms
        blocks

    blocks zawiera elementy H1-H4, P, LI i BLOCKQUOTE
    w kolejności występowania w kodzie strony.
    """

    soup = BeautifulSoup(
        html,
        "lxml"
    )

    cms = detect_cms(html)

    candidates = find_content_containers(soup)

    if not candidates:
        return cms, []

    # Najlepszy znaleziony kontener.
    best_container = candidates[0][1]

    blocks = _get_semantic_blocks(
        best_container
    )

    # Usuwamy duplikaty.
    unique_blocks = []
    seen = set()

    for block in blocks:

        text = block.get_text(
            " ",
            strip=True
        )

        key = (
            block.name,
            text
        )

        if key in seen:
            continue

        seen.add(key)
        unique_blocks.append(block)

    return cms, unique_blocks
