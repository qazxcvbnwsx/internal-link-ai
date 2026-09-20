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
    - usuwa polskie znaki diakrytyczne.
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
    Normalizuje pojedyncze słowo.
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
    Zwraca znormalizowane słowa.
    """

    normalized = normalize_text(
        text
    )

    raw_tokens = re.findall(
        r"[a-z0-9]+",
        normalized
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


def tokenize_with_surface(text):
    """
    Zwraca pary:
        (znormalizowane_słowo, oryginalne_słowo)
    """

    raw_tokens = re.findall(
        r"[A-Za-zĄąĆćĘęŁłŃńÓóŚśŹźŻż0-9]+",
        text
    )

    result = []

    for raw_token in raw_tokens:

        normalized = normalize_token(
            raw_token
        )

        if len(normalized) < 4:
            continue

        if normalized in STOPWORDS:
            continue

        result.append(
            (
                normalized,
                raw_token
            )
        )

    return result


def tokens_are_similar(
    token_a,
    token_b
):
    """
    Proste sprawdzenie podobieństwa słów.

    Pozwala traktować np.:
        okular
        okulary
        okularach

    jako potencjalnie powiązane.
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


def _extract_phrase_candidates(
    soup
):
    """
    Tworzy listę potencjalnych fraz z artykułu.

    Największą wagę mają:
        - H1
        - H2
        - H3
        - H4

    Następnie wykorzystywane są również
    naturalne frazy 2- i 3-wyrazowe
    z treści.
    """

    phrases = []

    # -------------------------------------------------
    # FRAZY Z NAGŁÓWKÓW
    # -------------------------------------------------

    for heading in soup.find_all(
        [
            "h1",
            "h2",
            "h3",
            "h4",
        ]
    ):

        heading_text = " ".join(
            heading.get_text(
                " ",
                strip=True
            ).split()
        )

        tokens = tokenize_with_surface(
            heading_text
        )

        if not tokens:
            continue

        normalized_tokens = [
            item[0]
            for item in tokens
        ]

        surface_tokens = [
            item[1]
            for item in tokens
        ]

        # Cały nagłówek jako fraza
        if len(surface_tokens) >= 2:

            phrases.append(
                {
                    "text": " ".join(
                        surface_tokens
                    ),
                    "tokens": normalized_tokens,
                    "weight": 10,
                }
            )

        # 2-gramy
        for i in range(
            len(tokens) - 1
        ):

            phrase_tokens = [
                tokens[i],
                tokens[i + 1]
            ]

            phrases.append(
                {
                    "text": " ".join(
                        item[1]
                        for item in phrase_tokens
                    ),
                    "tokens": [
                        item[0]
                        for item in phrase_tokens
                    ],
                    "weight": 8,
                }
            )

        # 3-gramy
        for i in range(
            len(tokens) - 2
        ):

            phrase_tokens = [
                tokens[i],
                tokens[i + 1],
                tokens[i + 2]
            ]

            phrases.append(
                {
                    "text": " ".join(
                        item[1]
                        for item in phrase_tokens
                    ),
                    "tokens": [
                        item[0]
                        for item in phrase_tokens
                    ],
                    "weight": 9,
                }
            )

    # -------------------------------------------------
    # FRAZY Z TREŚCI
    # -------------------------------------------------

    paragraphs = soup.find_all(
        [
            "p",
            "li",
            "blockquote",
        ]
    )

    body_counter = Counter()

    body_phrases = {}

    for paragraph in paragraphs:

        paragraph_text = " ".join(
            paragraph.get_text(
                " ",
                strip=True
            ).split()
        )

        tokens = tokenize_with_surface(
            paragraph_text
        )

        if not tokens:
            continue

        normalized_tokens = [
            item[0]
            for item in tokens
        ]

        surface_tokens = [
            item[1]
            for item in tokens
        ]

        # 2-gramy
        for i in range(
            len(tokens) - 1
        ):

            phrase_tokens = [
                tokens[i],
                tokens[i + 1]
            ]

            normalized_phrase = tuple(
                item[0]
                for item in phrase_tokens
            )

            surface_phrase = " ".join(
                item[1]
                for item in phrase_tokens
            )

            body_counter[
                normalized_phrase
            ] += 1

            body_phrases[
                normalized_phrase
            ] = surface_phrase

        # 3-gramy
        for i in range(
            len(tokens) - 2
        ):

            phrase_tokens = [
                tokens[i],
                tokens[i + 1],
                tokens[i + 2]
            ]

            normalized_phrase = tuple(
                item[0]
                for item in phrase_tokens
            )

            surface_phrase = " ".join(
                item[1]
                for item in phrase_tokens
            )

            body_counter[
                normalized_phrase
            ] += 1

            body_phrases[
                normalized_phrase
            ] = surface_phrase

    for phrase_tokens, count in body_counter.most_common(
        80
    ):

        if count < 1:
            continue

        phrases.append(
            {
                "text": body_phrases[
                    phrase_tokens
                ],
                "tokens": list(
                    phrase_tokens
                ),
                "weight": min(
                    6,
                    2 + count
                ),
            }
        )

    return phrases


def _remove_duplicate_phrases(
    phrases
):
    """
    Usuwa identyczne frazy.
    """

    result = []
    seen = set()

    for phrase in phrases:

        key = normalize_text(
            phrase["text"]
        )

        if key in seen:
            continue

        seen.add(
            key
        )

        result.append(
            phrase
        )

    return result


def extract_article_keywords(
    article_html,
    max_keywords=40
):
    """
    Zwraca najważniejsze słowa artykułu.
    """

    soup = BeautifulSoup(
        article_html,
        "lxml"
    )

    counter = Counter()

    body_text = soup.get_text(
        " ",
        strip=True
    )

    for token in tokenize_text(
        body_text
    ):

        counter[token] += 1

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

        for token in tokenize_text(
            heading_text
        ):

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
    Pobiera istniejące linki z artykułu.
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

    normalized_path = normalize_text(
        parsed.path
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


def _phrase_matches_url(
    phrase,
    url_tokens
):
    """
    Sprawdza, ile słów z frazy
    pasuje do słów URL.
    """

    phrase_tokens = phrase[
        "tokens"
    ]

    if not phrase_tokens:
        return 0

    matched = 0

    for phrase_token in phrase_tokens:

        for url_token in url_tokens:

            if tokens_are_similar(
                phrase_token,
                url_token
            ):

                matched += 1
                break

    return matched


def _score_url_and_phrases(
    url,
    phrases,
    keyword_weights
):
    """
    Oblicza wynik URL oraz zwraca
    pasujące frazy z artykułu.
    """

    url_tokens = _url_tokens(
        url
    )

    if not url_tokens:

        return 0, []

    score = 0

    matched_phrases = []

    # -------------------------------------------------
    # DOPASOWANIE FRAZ
    # -------------------------------------------------

    for phrase in phrases:

        matched_count = _phrase_matches_url(
            phrase,
            url_tokens
        )

        if matched_count == 0:
            continue

        phrase_length = len(
            phrase["tokens"]
        )

        # Pełne dopasowanie frazy
        if (
            phrase_length >= 2
            and matched_count == phrase_length
        ):

            phrase_score = (
                phrase["weight"]
                * matched_count
                * 2
            )

        else:

            phrase_score = (
                phrase["weight"]
                * matched_count
            )

        score += phrase_score

        matched_phrases.append(
            {
                "text": phrase["text"],
                "score": phrase_score,
            }
        )

    # -------------------------------------------------
    # DODATKOWE DOPASOWANIE SŁÓW
    # -------------------------------------------------

    for url_token in set(
        url_tokens
    ):

        best_word_score = 0

        for keyword, weight in keyword_weights.items():

            if url_token == keyword:

                best_word_score = max(
                    best_word_score,
                    weight * 3
                )

            elif tokens_are_similar(
                url_token,
                keyword
            ):

                best_word_score = max(
                    best_word_score,
                    weight
                )

        score += best_word_score

    # -------------------------------------------------
    # USUNIĘCIE POWTARZAJĄCYCH SIĘ FRAZ
    # -------------------------------------------------

    unique_phrases = []
    seen = set()

    for phrase in sorted(
        matched_phrases,
        key=lambda item: -item["score"]
    ):

        key = normalize_text(
            phrase["text"]
        )

        if key in seen:
            continue

        seen.add(
            key
        )

        unique_phrases.append(
            phrase
        )

    return score, unique_phrases


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
    Wybiera 30 najbardziej pasujących URL-i.

    Nie odwiedza żadnego URL-a.

    Analizuje wyłącznie:
        - artykuł,
        - URL-e z sitemap.
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
    # USUNIĘCIE ISTNIEJĄCYCH LINKÓW
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
    # FRAZY
    # -------------------------------------------------

    soup = BeautifulSoup(
        article_html,
        "lxml"
    )

    phrases = _extract_phrase_candidates(
        soup
    )

    phrases = _remove_duplicate_phrases(
        phrases
    )

    # -------------------------------------------------
    # OCENA URL-I
    # -------------------------------------------------

    scored_urls = []

    for index, url in enumerate(
        eligible_urls
    ):

        score, matched_phrases = (
            _score_url_and_phrases(
                url,
                phrases,
                keyword_weights
            )
        )

        scored_urls.append(
            {
                "score": score,
                "index": index,
                "url": url,
                "matched_phrases": matched_phrases,
            }
        )

    # -------------------------------------------------
    # SORTOWANIE
    # -------------------------------------------------

    scored_urls.sort(
        key=lambda item: (
            -item["score"],
            item["index"]
        )
    )

    matched_urls = [
        item
        for item in scored_urls
        if item["score"] > 0
    ]

    selected = matched_urls[
        :limit
    ]

    # Jeżeli mamy mniej niż 30
    # dopasowanych URL-i, uzupełniamy listę.
    if len(selected) < limit:

        selected_ids = {
            item["index"]
            for item in selected
        }

        for item in scored_urls:

            if len(selected) >= limit:
                break

            if item["index"] in selected_ids:
                continue

            selected.append(
                item
            )

            selected_ids.add(
                item["index"]
            )

    selected_urls = [
        item["url"]
        for item in selected
    ]

    candidate_matches = [
        {
            "url": item["url"],
            "matched_phrases": [
                phrase["text"]
                for phrase
                in item["matched_phrases"][:6]
            ],
            "score": item["score"],
        }
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
        "candidate_matches": candidate_matches,
    }

    return (
        selected_urls,
        diagnostics
    )
