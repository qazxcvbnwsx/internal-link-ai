import re
import unicodedata
from collections import Counter
from urllib.parse import urlparse, unquote

from bs4 import BeautifulSoup


STOPWORDS = {
    "aby",
    "albo",
    "ale",
    "bardzo",
    "bez",
    "bo",
    "by",
    "być",
    "bylo",
    "była",
    "były",
    "był",
    "ci",
    "co",
    "czy",
    "dla",
    "do",
    "gdy",
    "gdzie",
    "ich",
    "ile",
    "i",
    "im",
    "inny",
    "inne",
    "jest",
    "jego",
    "jej",
    "jeśli",
    "już",
    "jak",
    "jako",
    "ją",
    "je",
    "każdy",
    "kiedy",
    "który",
    "która",
    "które",
    "którym",
    "którzy",
    "lub",
    "ma",
    "mają",
    "mi",
    "może",
    "na",
    "nad",
    "nam",
    "nas",
    "nie",
    "nich",
    "niego",
    "niej",
    "niż",
    "o",
    "od",
    "oraz",
    "po",
    "pod",
    "przez",
    "przy",
    "są",
    "się",
    "tak",
    "te",
    "tego",
    "tej",
    "ten",
    "to",
    "tu",
    "tym",
    "tylko",
    "u",
    "w",
    "we",
    "więc",
    "z",
    "za",
    "ze",
    "że",
    "the",
    "and",
    "for",
    "with",
    "from",
    "this",
    "that",
    "your",
    "you",
    "are",
    "was",
    "were",
    "about",
    "into",
    "how",
    "what",
}


IGNORED_URL_WORDS = {
    "www",
    "html",
    "php",
    "asp",
    "aspx",
    "page",
    "pages",
    "strona",
    "strony",
    "blog",
    "artykul",
    "artykuly",
    "article",
    "articles",
    "news",
    "post",
    "posts",
}


def normalize_text(text):
    """
    Normalizuje tekst:
    - małe litery,
    - usuwa polskie znaki diakrytyczne,
    - usuwa znaki specjalne.
    """

    text = text.lower()

    normalized = unicodedata.normalize(
        "NFKD",
        text
    )

    normalized = "".join(
        char
        for char in normalized
        if not unicodedata.combining(char)
    )

    return normalized


def normalize_token(token):
    """
    Normalizuje pojedynczy token.
    """

    token = normalize_text(
        token
    )

    return re.sub(
        r"[^a-z0-9]",
        "",
        token
    )


def tokenize_text(text):
    """
    Dzieli tekst na słowa.
    """

    text = normalize_text(
        text
    )

    raw_tokens = re.findall(
        r"[a-z0-9]+",
        text
    )

    tokens = []

    for token in raw_tokens:

        if len(token) < 4:
            continue

        if token in STOPWORDS:
            continue

        tokens.append(
            token
        )

    return tokens


def extract_article_keywords(
    article_html,
    max_keywords=40
):
    """
    Wyciąga najważniejsze słowa z artykułu.

    Nagłówki otrzymują większą wagę.
    """

    soup = BeautifulSoup(
        article_html,
        "lxml"
    )

    counter = Counter()

    # -------------------------------------------------
    # ZWYKŁA TREŚĆ
    # -------------------------------------------------

    body_text = soup.get_text(
        " ",
        strip=True
    )

    for token in tokenize_text(
        body_text
    ):

        counter[token] += 1

    # -------------------------------------------------
    # NAGŁÓWKI
    # -------------------------------------------------

    for heading in soup.find_all(
        [
            "h1",
            "h2",
            "h3",
            "h4",
        ]
    ):

        heading_text = heading.get_text(
            " ",
            strip=True
        )

        heading_tokens = tokenize_text(
            heading_text
        )

        for token in heading_tokens:

            counter[token] += 8

    return [
        word
        for word, _count
        in counter.most_common(
            max_keywords
        )
    ]


def extract_existing_links(
    article_html
):
    """
    Zwraca URL-e, do których artykuł już linkuje.
    """

    soup = BeautifulSoup(
        article_html,
        "lxml"
    )

    links = []

    for anchor in soup.find_all(
        "a"
    ):

        href = anchor.get(
            "href"
        )

        if not href:
            continue

        href = href.strip()

        if href.startswith(
            "#"
        ):
            continue

        links.append(
            href
        )

    return links


def _url_tokens(url):
    """
    Wyciąga słowa ze ścieżki URL.
    """

    parsed = urlparse(
        unquote(url)
    )

    path = parsed.path

    normalized_path = normalize_text(
        path
    )

    raw_tokens = re.findall(
        r"[a-z0-9]+",
        normalized_path
    )

    tokens = []

    for token in raw_tokens:

        if len(token) < 3:
            continue

        if token in IGNORED_URL_WORDS:
            continue

        tokens.append(
            token
        )

    return tokens


def _tokens_are_similar(
    token_a,
    token_b
):
    """
    Sprawdza proste podobieństwo słów.

    Dzięki temu np.
        okular
        okulary
        okularach

    mogą zostać potraktowane jako
    potencjalnie powiązane.

    Nie jest to pełna analiza językowa.
    """

    if token_a == token_b:
        return True

    if len(token_a) < 5 or len(token_b) < 5:
        return False

    shorter, longer = sorted(
        [
            token_a,
            token_b
        ],
        key=len
    )

    return longer.startswith(
        shorter[:5]
    )


def _score_url(
    url,
    keyword_weights
):
    """
    Oblicza wstępne dopasowanie URL
    do tematu artykułu.
    """

    url_tokens = _url_tokens(
        url
    )

    if not url_tokens:
        return 0

    score = 0

    for url_token in set(
        url_tokens
    ):

        best_match_score = 0

        for keyword, weight in keyword_weights.items():

            if url_token == keyword:

                best_match_score = max(
                    best_match_score,
                    weight * 3
                )

            elif _tokens_are_similar(
                url_token,
                keyword
            ):

                best_match_score = max(
                    best_match_score,
                    weight
                )

        score += best_match_score

    # Premia za krótszy, konkretniejszy URL.
    if len(url_tokens) <= 2:
        score += 2

    elif len(url_tokens) == 3:
        score += 1

    return score


def _normalize_url(
    url
):
    """
    Ujednolica URL do porównań.
    """

    return (
        url
        .strip()
        .rstrip("/")
        .lower()
    )


def filter_existing_links(
    urls,
    article_html
):
    """
    Usuwa URL-e, które są już podlinkowane
    w analizowanym artykule.

    Obsługuje:
    - pełne URL-e,
    - względne URL-e.
    """

    existing_links = (
        extract_existing_links(
            article_html
        )
    )

    if not existing_links:
        return (
            urls,
            0
        )

    normalized_existing = set()

    for link in existing_links:

        normalized_existing.add(
            _normalize_url(
                link
            )
        )

    filtered = []
    removed = 0

    for url in urls:

        normalized_url = _normalize_url(
            url
        )

        if normalized_url in normalized_existing:

            removed += 1
            continue

        filtered.append(
            url
        )

    return (
        filtered,
        removed
    )


def select_candidate_urls(
    article_html,
    urls,
    limit=30
):
    """
    Wybiera najbardziej prawdopodobne URL-e
    do dalszej analizy.

    NIE odwiedza żadnego URL-a.

    Analizuje wyłącznie:
        - treść artykułu,
        - listę URL-i z sitemap.

    Zwraca:
        selected_urls
        diagnostics
    """

    if not urls:

        return (
            [],
            {
                "total_urls": 0,
                "eligible_urls": 0,
                "matched_urls": 0,
                "selected_urls": 0,
                "removed_existing_links": 0,
                "keywords": [],
            }
        )

    # -------------------------------------------------
    # USUNIĘCIE JUŻ ISTNIEJĄCYCH LINKÓW
    # -------------------------------------------------

    (
        eligible_urls,
        removed_existing_links
    ) = filter_existing_links(
        urls,
        article_html
    )

    # -------------------------------------------------
    # SŁOWA KLUCZOWE
    # -------------------------------------------------

    keywords = extract_article_keywords(
        article_html,
        max_keywords=40
    )

    keyword_weights = {}

    for position, keyword in enumerate(
        keywords
    ):

        weight = max(
            1,
            40 - position
        )

        keyword_weights[
            keyword
        ] = weight

    # -------------------------------------------------
    # OCENA URL-I
    # -------------------------------------------------

    scored_urls = []

    for index, url in enumerate(
        eligible_urls
    ):

        score = _score_url(
            url,
            keyword_weights
        )

        scored_urls.append(
            (
                score,
                index,
                url
            )
        )

    # Najpierw najwyższy wynik,
    # przy remisie zachowujemy kolejność sitemap.
    scored_urls.sort(
        key=lambda item: (
            -item[0],
            item[1]
        )
    )

    matched_urls = [
        item
        for item in scored_urls
        if item[0] > 0
    ]

    selected = (
        matched_urls[:limit]
    )

    # Jeżeli dopasowanych URL-i jest mniej niż 30,
    # dokładamy kolejne URL-e z sitemap.
    if len(selected) < limit:

        selected_ids = {
            item[1]
            for item in selected
        }

        for item in scored_urls:

            if len(selected) >= limit:
                break

            if item[1] in selected_ids:
                continue

            selected.append(
                item
            )

            selected_ids.add(
                item[1]
            )

    selected_urls = [
        item[2]
        for item in selected
    ]

    diagnostics = {
        "total_urls": len(urls),
        "eligible_urls": len(
            eligible_urls
        ),
        "matched_urls": len(
            matched_urls
        ),
        "selected_urls": len(
            selected_urls
        ),
        "removed_existing_links": (
            removed_existing_links
        ),
        "keywords": keywords,
    }

    return (
        selected_urls,
        diagnostics
    )
