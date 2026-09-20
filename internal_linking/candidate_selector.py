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


GENERIC_URL_WORDS = {
    "c",
    "kategoria",
    "kategorie",
    "category",
    "categories",
    "produkt",
    "produkty",
    "product",
    "products",
    "page",
    "pages",
    "blog",
    "news",
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
    Pobiera słowa znaczące z tekstu.
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
    Pobiera wszystkie słowa z zachowaniem
    oryginalnej formy.

    Stopwords NIE są tutaj usuwane,
    ponieważ musimy zachować rzeczywiste
    frazy z tekstu.
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
    Sprawdza, czy słowo jest znaczące.
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

    Uwzględnia podstawowe odmiany.
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
    source_weight=4
):
    """
    Tworzy rzeczywiste frazy występujące
    w tekście jako ciąg kolejnych słów.

    Nie usuwa stopwords.

    Przykład:

        Książki o lesbijkach

    pozostaje dokładnie:

        Książki o lesbijkach
    """

    words = extract_surface_words(
        text
    )

    phrases = []

    if len(words) < 2:
        return phrases

    # Frazy 2-6 wyrazowe.
    for phrase_length in range(
        2,
        7
    ):

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

            # Fraza musi zawierać co najmniej
            # dwa znaczące słowa.
            if len(meaningful_tokens) < 2:
                continue

            if len(display_text) < 8:
                continue

            phrases.append(
                {
                    "text": display_text,
                    "tokens": normalized_tokens,
                    "meaningful_tokens": (
                        meaningful_tokens
                    ),
                    "weight": source_weight,
                }
            )

    return phrases


def _extract_heading_phrases(
    soup
):
    """
    Pobiera dokładne frazy z nagłówków.
    """

    phrases = []

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

        if not heading_text:
            continue

        phrases.extend(
            _extract_exact_phrases_from_text(
                heading_text,
                source_weight=10
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
    Wyciąga najważniejsze słowa artykułu.
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
    Pobiera wszystkie słowa ze ścieżki URL.

    Ważne:
    zachowujemy również krótkie słowa,
    np. "o", ponieważ mogą być częścią
    dokładnej frazy.
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

        if token in IGNORED_URL_WORDS:
            continue

        tokens.append(
            token
        )

    return tokens


def _url_tokens_for_comparison(
    url
):
    """
    Pobiera URL bez generycznych segmentów,
    np. /c/, /category/, /produkt/.

    Dzięki temu:

        /c/ksiazki-o-lesbijkach/

    może zostać dokładnie porównane
    z:

        Książki o lesbijkach
    """

    tokens = _url_tokens(
        url
    )

    return [
        token
        for token in tokens
        if token not in GENERIC_URL_WORDS
    ]


def _contains_exact_sequence(
    phrase_tokens,
    url_tokens
):
    """
    Sprawdza, czy dokładna sekwencja
    słów frazy występuje w URL.
    """

    if not phrase_tokens:
        return False

    if not url_tokens:
        return False

    phrase_length = len(
        phrase_tokens
    )

    url_length = len(
        url_tokens
    )

    if phrase_length > url_length:
        return False

    for start in range(
        url_length - phrase_length + 1
    ):

        sequence = url_tokens[
            start:start + phrase_length
        ]

        if sequence == phrase_tokens:

            return True

    return False


def _matched_word_count(
    phrase_tokens,
    url_tokens
):
    """
    Liczy ile znaczących słów frazy
    pasuje do URL.
    """

    meaningful_tokens = [
        token
        for token in phrase_tokens
        if is_meaningful_token(
            token
        )
    ]

    if not meaningful_tokens:
        return 0

    matched = 0

    for phrase_token in meaningful_tokens:

        for url_token in url_tokens:

            if tokens_are_similar(
                phrase_token,
                url_token
            ):

                matched += 1
                break

    return matched


def _score_phrase(
    phrase,
    url_tokens
):
    """
    Ocenia pojedynczą frazę względem URL.

    Najwyżej oceniane są dokładne,
    ciągłe dopasowania.
    """

    phrase_tokens = phrase[
        "tokens"
    ]

    meaningful_tokens = phrase[
        "meaningful_tokens"
    ]

    if not meaningful_tokens:
        return 0, False

    # -------------------------------------------------
    # DOKŁADNE DOPASOWANIE CAŁEJ FRAZY
    # -------------------------------------------------

    if _contains_exact_sequence(
        phrase_tokens,
        url_tokens
    ):

        phrase_length = len(
            phrase_tokens
        )

        score = (
            1000
            + phrase_length * 150
            + phrase["weight"] * 20
        )

        return (
            score,
            True
        )

    # -------------------------------------------------
    # CZĘŚCIOWE DOPASOWANIE
    # -------------------------------------------------

    matched_count = _matched_word_count(
        phrase_tokens,
        url_tokens
    )

    if matched_count == 0:
        return 0, False

    meaningful_count = len(
        meaningful_tokens
    )

    if matched_count < meaningful_count:
        return 0, False

    score = (
        50
        + matched_count * 20
        + phrase["weight"] * 5
    )

    return (
        score,
        False
    )


def _score_url(
    url,
    phrases
):
    """
    Oblicza wynik URL oraz wybiera
    najlepsze rzeczywiste frazy.
    """

    url_tokens = _url_tokens_for_comparison(
        url
    )

    if not url_tokens:

        return (
            0,
            []
        )

    phrase_matches = []

    for phrase in phrases:

        phrase_score, exact_match = (
            _score_phrase(
                phrase,
                url_tokens
            )
        )

        if phrase_score <= 0:
            continue

        phrase_copy = phrase.copy()

        phrase_copy[
            "score"
        ] = phrase_score

        phrase_copy[
            "exact_match"
        ] = exact_match

        phrase_matches.append(
            phrase_copy
        )

    if not phrase_matches:

        return (
            0,
            []
        )

    # -------------------------------------------------
    # SORTOWANIE FRAZ
    # -------------------------------------------------

    phrase_matches.sort(
        key=lambda item: (
            not item["exact_match"],
            -item["score"],
            -len(item["tokens"])
        )
    )

    # Najlepsza fraza decyduje głównie
    # o pozycji URL-u.
    best_phrase = phrase_matches[
        0
    ]

    url_score = best_phrase[
        "score"
    ]

    # Dodatkowe sensowne frazy zwiększają
    # wynik, ale dużo mniej niż pierwsza.
    for extra_phrase in phrase_matches[
        1:4
    ]:

        url_score += (
            extra_phrase["score"] * 0.15
        )

    # Jeżeli istnieje dokładne dopasowanie,
    # wyraźnie premiujemy taki URL.
    if best_phrase[
        "exact_match"
    ]:

        url_score += 500

    return (
        url_score,
        phrase_matches
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
    Usuwa URL-e już podlinkowane
    w artykule.
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

    Frazy pochodzą wyłącznie z rzeczywistych
    ciągów słów występujących w artykule.

    Szczególnie wysoko oceniane są frazy,
    które dokładnie występują w URL.

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
    # ISTNIEJĄCE LINKI
    # -------------------------------------------------

    (
        eligible_urls,
        removed_existing_links
    ) = filter_existing_links(
        urls,
        article_html
    )

    # -------------------------------------------------
    # SŁOWA
    # -------------------------------------------------

    keywords = extract_article_keywords(
        article_html,
        max_keywords=40
    )

    keyword_weights = {}

    for position, keyword in enumerate(
        keywords
    ):

        keyword_weights[
            keyword
        ] = max(
            1,
            40 - position
        )

    # -------------------------------------------------
    # FRAZY
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
            _score_url(
                url,
                phrases
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
    # SORTOWANIE URL-I
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

        # Pokazujemy maksymalnie 3 najlepsze
        # frazy dla jednego URL-a.
        unique_phrases = (
            unique_phrases[:3]
        )

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
    # WYNIK
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
