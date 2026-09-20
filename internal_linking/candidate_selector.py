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
    Zwraca znormalizowane słowa
    bez stopwords.
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


def extract_surface_words(text):
    """
    Pobiera słowa z zachowaniem ich
    oryginalnej formy i kolejności.

    Przykład:

        "Książki o lesbijkach"

    daje:

        [
            ("ksiazki", "Książki"),
            ("o", "o"),
            ("lesbijkach", "lesbijkach")
        ]

    """

    raw_words = re.findall(
        r"[A-Za-zĄąĆćĘęŁłŃńÓóŚśŹźŻż0-9]+",
        text
    )

    result = []

    for word in raw_words:

        normalized = normalize_token(
            word
        )

        if not normalized:
            continue

        result.append(
            (
                normalized,
                word
            )
        )

    return result


def is_meaningful_token(
    token
):
    """
    Sprawdza, czy słowo ma znaczenie
    przy dopasowaniu tematycznym.
    """

    if len(token) < 4:
        return False

    if token in STOPWORDS:
        return False

    return True


def tokens_are_similar(
    token_a,
    token_b
):
    """
    Proste sprawdzenie podobieństwa słów.

    Pozwala uwzględnić podstawowe odmiany,
    np.:
        okular
        okulary
        okularach
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


def _extract_exact_phrases_from_text(
    text,
    source_weight=2
):
    """
    Tworzy wyłącznie rzeczywiste frazy
    występujące jako ciąg kolejnych słów
    w tekście.

    Nie usuwa stopwords przed budowaniem frazy.

    Dzięki temu:

        "Książki o lesbijkach"

    pozostaje:

        "Książki o lesbijkach"

    a nie:

        "Książki lesbijkach"

    """

    words = extract_surface_words(
        text
    )

    phrases = []

    if len(words) < 2:
        return phrases

    # Frazy 2-, 3- i 4-wyrazowe.
    for phrase_length in [
        2,
        3,
        4,
    ]:

        for start in range(
            len(words) - phrase_length + 1
        ):

            phrase_words = words[
                start:start + phrase_length
            ]

            display_text = " ".join(
                word[1]
                for word in phrase_words
            )

            normalized_tokens = [
                word[0]
                for word in phrase_words
            ]

            meaningful_tokens = [
                token
                for token in normalized_tokens
                if is_meaningful_token(
                    token
                )
            ]

            # Fraza musi mieć przynajmniej
            # dwa znaczące słowa.
            if len(meaningful_tokens) < 2:
                continue

            # Odrzucamy bardzo krótkie frazy
            # składające się tylko z przypadkowych słów.
            if len(display_text) < 8:
                continue

            phrases.append(
                {
                    "text": display_text,
                    "tokens": normalized_tokens,
                    "meaningful_tokens": meaningful_tokens,
                    "weight": source_weight,
                }
            )

    return phrases


def _extract_heading_phrases(
    soup
):
    """
    Pobiera rzeczywiste frazy z nagłówków.

    Zachowujemy dokładne słowa występujące
    w nagłówku.
    """

    phrases = []

    headings = soup.find_all(
        [
            "h1",
            "h2",
            "h3",
            "h4",
        ]
    )

    for heading in headings:

        text = " ".join(
            heading.get_text(
                " ",
                strip=True
            ).split()
        )

        if not text:
            continue

        # Cały nagłówek, jeżeli nie jest
        # przesadnie długi.
        heading_words = extract_surface_words(
            text
        )

        if (
            2 <= len(heading_words) <= 8
        ):

            meaningful_tokens = [
                token
                for token, _surface
                in heading_words
                if is_meaningful_token(
                    token
                )
            ]

            if len(meaningful_tokens) >= 2:

                phrases.append(
                    {
                        "text": " ".join(
                            word[1]
                            for word in heading_words
                        ),
                        "tokens": [
                            word[0]
                            for word in heading_words
                        ],
                        "meaningful_tokens": (
                            meaningful_tokens
                        ),
                        "weight": 10,
                    }
                )

        # Dodatkowo krótsze dokładne frazy
        # występujące wewnątrz nagłówka.
        phrases.extend(
            _extract_exact_phrases_from_text(
                text,
                source_weight=8
            )
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


def _extract_article_phrases(
    article_html
):
    """
    Tworzy listę rzeczywistych fraz
    występujących w artykule.

    Frazy są budowane:
        - z nagłówków,
        - z akapitów,
        - z list,
        - z blockquote.

    Zawsze zachowują rzeczywistą
    kolejność słów z tekstu.
    """

    soup = BeautifulSoup(
        article_html,
        "lxml"
    )

    phrases = []

    # -------------------------------------------------
    # NAGŁÓWKI
    # -------------------------------------------------

    phrases.extend(
        _extract_heading_phrases(
            soup
        )
    )

    # -------------------------------------------------
    # TREŚĆ
    # -------------------------------------------------

    content_elements = soup.find_all(
        [
            "p",
            "li",
            "blockquote",
        ]
    )

    for element in content_elements:

        text = " ".join(
            element.get_text(
                " ",
                strip=True
            ).split()
        )

        if not text:
            continue

        phrases.extend(
            _extract_exact_phrases_from_text(
                text,
                source_weight=4
            )
        )

    return _remove_duplicate_phrases(
        phrases
    )


def extract_article_keywords(
    article_html,
    max_keywords=40
):
    """
    Wyciąga najważniejsze słowa
    z artykułu.
    """

    soup = BeautifulSoup(
        article_html,
        "lxml"
    )

    counter = Counter()

    # Zwykły tekst
    body_text = soup.get_text(
        " ",
        strip=True
    )

    for token in tokenize_text(
        body_text
    ):

        counter[token] += 1

    # Nagłówki mają większą wagę
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
    Sprawdza dopasowanie znaczących słów
    z rzeczywistej frazy do URL.

    Wszystkie znaczące słowa frazy muszą
    znaleźć dopasowanie w URL.

    Dzięki temu np.:

        "Książki o lesbijkach"

    może pasować do:

        /ksiazki-o-lesbijkach/

    ale:

        "Kategorii książki lesbijkach"

    nie zostanie utworzone, jeśli taki
    ciąg nie istnieje w artykule.
    """

    meaningful_tokens = phrase[
        "meaningful_tokens"
    ]

    if not meaningful_tokens:
        return 0

    matched = 0

    for phrase_token in meaningful_tokens:

        token_found = False

        for url_token in url_tokens:

            if tokens_are_similar(
                phrase_token,
                url_token
            ):

                token_found = True
                break

        if token_found:

            matched += 1

        else:

            return 0

    return matched


def _score_url_and_phrases(
    url,
    phrases,
    keyword_weights
):
    """
    Oblicza dopasowanie URL do rzeczywistych
    fraz występujących w artykule.
    """

    url_tokens = _url_tokens(
        url
    )

    if not url_tokens:

        return (
            0,
            []
        )

    score = 0

    matched_phrases = []

    # -------------------------------------------------
    # FRAZY
    # -------------------------------------------------

    for phrase in phrases:

        matched_count = _phrase_matches_url(
            phrase,
            url_tokens
        )

        if matched_count == 0:
            continue

        phrase_length = len(
            phrase["meaningful_tokens"]
        )

        # Im więcej pełnych znaczących słów
        # frazy pasuje do URL, tym większy wynik.
        phrase_score = (
            phrase["weight"]
            * matched_count
            * matched_count
        )

        # Dodatkowa premia za frazę wielowyrazową.
        if phrase_length >= 2:

            phrase_score += (
                phrase_length * 4
            )

        score += phrase_score

        matched_phrases.append(
            {
                "text": phrase["text"],
                "score": phrase_score,
            }
        )

    # -------------------------------------------------
    # POJEDYNCZE SŁOWA
    # -------------------------------------------------

    for url_token in set(
        url_tokens
    ):

        best_word_score = 0

        for keyword, weight in (
            keyword_weights.items()
        ):

            if url_token == keyword:

                best_word_score = max(
                    best_word_score,
                    weight * 2
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
    # USUŃ DUPLIKATY FRAZ DLA TEGO URL
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

    return (
        score,
        unique_phrases
    )


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
    Wybiera najbardziej pasujące URL-e.

    Każda fraza występująca w artykule
    może zostać przypisana tylko do
    jednego URL-a.

    Żaden URL nie jest odwiedzany.
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
                "candidate_matches": [],
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
    # RZECZYWISTE FRAZY Z ARTYKUŁU
    # -------------------------------------------------

    phrases = _extract_article_phrases(
        article_html
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
                "matched_phrases": (
                    matched_phrases
                ),
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

    # -------------------------------------------------
    # KAŻDA FRAZA TYLKO RAZ
    # -------------------------------------------------

    used_phrases = set()

    selected = []

    for item in matched_urls:

        unique_phrases = []

        for phrase in item[
            "matched_phrases"
        ]:

            phrase_key = normalize_text(
                phrase["text"]
            )

            if phrase_key in used_phrases:
                continue

            unique_phrases.append(
                phrase
            )

        if not unique_phrases:
            continue

        item_copy = item.copy()

        item_copy[
            "matched_phrases"
        ] = unique_phrases

        selected.append(
            item_copy
        )

        for phrase in unique_phrases:

            used_phrases.add(
                normalize_text(
                    phrase["text"]
                )
            )

        if len(selected) >= limit:
            break

    # -------------------------------------------------
    # JEŻELI NIE MA 30 DOPASOWANYCH URL-I
    # NIE TWORZYMY SZTUCZNYCH FRAZ
    # -------------------------------------------------

    selected_urls = [
        item["url"]
        for item in selected
    ]

    candidate_matches = []

    for item in selected:

        candidate_matches.append(
            {
                "url": item["url"],
                "matched_phrases": [
                    phrase["text"]
                    for phrase
                    in item[
                        "matched_phrases"
                    ]
                ],
                "score": item["score"],
            }
        )

    diagnostics = {
        "total_urls": len(
            urls
        ),
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
        "candidate_matches": (
            candidate_matches
        ),
    }

    return (
        selected_urls,
        diagnostics
    )
