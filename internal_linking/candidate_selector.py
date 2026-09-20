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


# -------------------------------------------------
# SŁOWA OGÓLNE / MAŁO PRZYDATNE JAKO FRAZY
# -------------------------------------------------

GENERIC_WORDS = {
    "powinno",
    "powinien",
    "powinna",
    "powinni",
    "powinny",
    "mieć",
    "miec",
    "można",
    "mozna",
    "może",
    "moze",
    "warto",
    "wartości",
    "wartosc",
    "ważne",
    "wazne",
    "ważny",
    "wazny",
    "ważna",
    "wazna",
    "ważne",
    "wazne",
    "dobrze",
    "dobry",
    "dobra",
    "dobre",
    "większy",
    "wiekszy",
    "większa",
    "wieksza",
    "większe",
    "wieksze",
    "większego",
    "wiekszego",
    "mniejszy",
    "mniejsza",
    "mniejsze",
    "najlepiej",
    "najważniejsze",
    "najwazniejsze",
    "istotne",
    "istotny",
    "istotna",
    "kwestia",
    "kwestii",
    "sposób",
    "sposob",
    "sposoby",
    "sprawa",
    "sprawie",
    "rzeczy",
    "osoba",
    "osoby",
    "osób",
    "osob",
    "czasu",
    "czas",
    "miejsca",
    "miejsce",
    "przypadku",
    "przypadek",
    "znaczenie",
    "znaczenia",
    "informacje",
    "informacja",
    "temat",
    "tematu",
    "tematy",
    "często",
    "czesto",
    "zwykle",
    "zazwyczaj",
    "wtedy",
    "dlatego",
    "jednak",
    "również",
    "rowniez",
    "także",
    "takze",
    "natomiast",
    "ponieważ",
    "poniewaz",
    "czyli",
    "dzięki",
    "dzieki",
    "przede",
    "wszystkim",
    "właśnie",
    "wlasnie",
    "tutaj",
    "tam",
    "swoim",
    "swojej",
    "swoje",
    "swoich",
    "naszym",
    "nasza",
    "nasze",
    "naszych",
    "twoim",
    "twoja",
    "twoje",
    "twoich",
    "ich",
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
    "kategorii",
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
    - usuwa polskie znaki.
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
    Pobiera słowa znaczące.
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

        if token in GENERIC_WORDS:
            continue

        tokens.append(
            token
        )

    return tokens


def extract_surface_words(text):
    """
    Pobiera wszystkie słowa z zachowaniem
    oryginalnej formy.

    Tutaj NIE usuwamy stopwords, ponieważ
    fraza musi pozostać identyczna z tekstem.
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


def is_topic_word(token):
    """
    Określa, czy słowo może być słowem
    tematycznym frazy.

    Odrzucamy:
        - stopwords,
        - bardzo ogólne czasowniki/sformułowania,
        - bardzo krótkie słowa.
    """

    if len(token) < 5:
        return False

    if token in STOPWORDS:
        return False

    if token in GENERIC_WORDS:
        return False

    return True


def tokens_are_similar(
    token_a,
    token_b
):
    """
    Proste sprawdzenie podobieństwa słów.

    Przykłady:
        okular
        okulary
        okularach

    mogą być traktowane jako powiązane.
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
    Tworzy wyłącznie rzeczywiste frazy
    występujące w tekście.

    Fraza:
        - ma 2-5 słów,
        - ma minimum 2 słowa tematyczne,
        - nie składa się z ogólnych sformułowań.
    """

    words = extract_surface_words(
        text
    )

    phrases = []

    if len(words) < 2:
        return phrases

    for phrase_length in range(
        2,
        6
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

            topic_tokens = [
                token
                for token in normalized_tokens
                if is_topic_word(
                    token
                )
            ]

            # -------------------------------------------------
            # MINIMUM 2 SŁOWA TEMATYCZNE
            # -------------------------------------------------

            if len(topic_tokens) < 2:
                continue

            # -------------------------------------------------
            # NIE TWORZYMY FRAZ Z SAMYCH OGÓLNIKÓW
            # -------------------------------------------------

            generic_count = sum(
                1
                for token
                in normalized_tokens
                if token in GENERIC_WORDS
            )

            if generic_count >= 2:
                continue

            # -------------------------------------------------
            # FRAZA NIE MOŻE BYĆ CAŁYM DŁUGIM ZDANIEM
            # -------------------------------------------------

            if len(display_text) > 70:
                continue

            phrases.append(
                {
                    "text": display_text,
                    "tokens": normalized_tokens,
                    "topic_tokens": topic_tokens,
                    "weight": source_weight,
                }
            )

    return phrases


def _extract_heading_phrases(
    soup
):
    """
    Pobiera rzeczywiste frazy z nagłówków.
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

        heading_phrases = (
            _extract_exact_phrases_from_text(
                heading_text,
                source_weight=10
            )
        )

        phrases.extend(
            heading_phrases
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
    Tworzy listę rzeczywistych,
    tematycznych fraz z artykułu.
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
    tematyczne z artykułu.
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
    Pobiera wszystkie słowa ze ścieżki URL.
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

        if token in IGNORED_URL_WORDS:
            continue

        tokens.append(
            token
        )

    return tokens


def _url_topic_tokens(url):
    """
    Usuwa techniczne/generyczne elementy URL.
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
    Sprawdza, czy cała fraza występuje
    w URL jako ciąg kolejnych słów.
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

        if (
            url_tokens[
                start:start + phrase_length
            ]
            == phrase_tokens
        ):

            return True

    return False


def _matched_topic_tokens(
    phrase,
    url_tokens
):
    """
    Liczy dopasowane słowa tematyczne.
    """

    matched = []

    for phrase_token in phrase[
        "topic_tokens"
    ]:

        for url_token in url_tokens:

            if tokens_are_similar(
                phrase_token,
                url_token
            ):

                matched.append(
                    phrase_token
                )

                break

    return matched


def _score_phrase(
    phrase,
    url_tokens
):
    """
    Ocenia pojedynczą rzeczywistą frazę.
    """

    phrase_tokens = phrase[
        "tokens"
    ]

    topic_tokens = phrase[
        "topic_tokens"
    ]

    if len(topic_tokens) < 2:
        return (
            0,
            False,
            []
        )

    # -------------------------------------------------
    # DOKŁADNA FRAZA W URL
    # -------------------------------------------------

    if _contains_exact_sequence(
        phrase_tokens,
        url_tokens
    ):

        score = (
            5000
            + len(phrase_tokens) * 500
            + phrase["weight"] * 20
        )

        return (
            score,
            True,
            topic_tokens
        )

    # -------------------------------------------------
    # DOPASOWANIE TEMATYCZNYCH SŁÓW
    # -------------------------------------------------

    matched_topics = (
        _matched_topic_tokens(
            phrase,
            url_tokens
        )
    )

    if len(matched_topics) < 2:
        return (
            0,
            False,
            []
        )

    # Wszystkie słowa tematyczne frazy
    # powinny najlepiej znaleźć się w URL.
    if len(matched_topics) < len(
        topic_tokens
    ):
        return (
            0,
            False,
            []
        )

    score = (
        500
        + len(matched_topics) * 200
        + len(topic_tokens) * 100
        + phrase["weight"] * 20
    )

    return (
        score,
        False,
        matched_topics
    )


def _score_url(
    url,
    phrases
):
    """
    Oblicza wynik URL oraz jego
    najlepsze frazy.
    """

    url_tokens = _url_topic_tokens(
        url
    )

    if not url_tokens:

        return (
            0,
            []
        )

    phrase_matches = []

    for phrase in phrases:

        (
            phrase_score,
            exact_match,
            matched_topics
        ) = _score_phrase(
            phrase,
            url_tokens
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

        phrase_copy[
            "matched_topics"
        ] = matched_topics

        phrase_matches.append(
            phrase_copy
        )

    if not phrase_matches:

        return (
            0,
            []
        )

    # Najpierw dokładne frazy,
    # później częściowe.
    phrase_matches.sort(
        key=lambda item: (
            not item["exact_match"],
            -item["score"],
            -len(
                item["topic_tokens"]
            )
        )
    )

    best_phrase = phrase_matches[
        0
    ]

    url_score = best_phrase[
        "score"
    ]

    # Delikatna premia za dodatkowe
    # sensowne frazy.
    for extra_phrase in phrase_matches[
        1:3
    ]:

        url_score += (
            extra_phrase["score"]
            * 0.1
        )

    return (
        url_score,
        phrase_matches
    )


def _normalize_url(
    url
):
    """
    Ujednolica URL.
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

        if (
            _normalize_url(url)
            in normalized_existing
        ):

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

    Frazy:
        - pochodzą dokładnie z artykułu,
        - są tematyczne,
        - muszą być powiązane z URL,
        - każda fraza może zostać użyta tylko raz.

    Nie odwiedza żadnego URL-a.
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

        (
            score,
            matched_phrases
        ) = _score_url(
            url,
            phrases
        )

        if score <= 0:
            continue

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

    matched_urls = list(
        scored_urls
    )

    # -------------------------------------------------
    # KAŻDA FRAZA TYLKO RAZ
    # -------------------------------------------------

    used_phrases = set()

    selected = []

    for item in matched_urls:

        available_phrases = []

        for phrase in item[
            "matched_phrases"
        ]:

            phrase_key = normalize_text(
                phrase["text"]
            )

            if phrase_key in used_phrases:
                continue

            available_phrases.append(
                phrase
            )

        if not available_phrases:
            continue

        # Maksymalnie 3 najlepsze
        # rzeczywiste frazy dla URL.
        available_phrases = (
            available_phrases[:3]
        )

        item_copy = item.copy()

        item_copy[
            "matched_phrases"
        ] = available_phrases

        selected.append(
            item_copy
        )

        for phrase in available_phrases:

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
