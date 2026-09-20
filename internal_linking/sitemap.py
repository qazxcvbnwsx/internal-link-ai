import requests
from bs4 import BeautifulSoup

from .crawler import USER_AGENT


def _filter_urls(urls, exclude_fragments=None):
    """
    Usuwa URL-e zawierające podane fragmenty.
    Wielkość liter nie ma znaczenia.
    """

    if not exclude_fragments:
        return list(dict.fromkeys(urls))

    fragments = [
        fragment.strip().lower()
        for fragment in exclude_fragments
        if fragment.strip()
    ]

    if not fragments:
        return list(dict.fromkeys(urls))

    filtered = []

    for url in urls:

        url_lower = url.lower()

        if any(
            fragment in url_lower
            for fragment in fragments
        ):
            continue

        filtered.append(url)

    return list(dict.fromkeys(filtered))


def get_sitemap_urls(
    sitemap_url,
    exclude_fragments=None
):
    """
    Pobiera sitemapę lub sitemap index.

    Zwraca adresy URL po zastosowaniu
    opcjonalnych wykluczeń.
    """

    response = requests.get(
        sitemap_url,
        timeout=30,
        headers={
            "User-Agent": USER_AGENT
        }
    )

    response.raise_for_status()

    soup = BeautifulSoup(
        response.content,
        "xml"
    )

    # -------------------------------------------------
    # SITEMAP INDEX
    # -------------------------------------------------

    sitemap_tags = soup.find_all(
        "sitemap"
    )

    if sitemap_tags:

        sitemap_links = []

        for sitemap in sitemap_tags:

            loc = sitemap.find(
                "loc"
            )

            if loc:

                url = loc.get_text(
                    strip=True
                )

                if url:
                    sitemap_links.append(
                        url
                    )

        all_urls = []

        for child_sitemap in sitemap_links:

            try:

                child_response = requests.get(
                    child_sitemap,
                    timeout=30,
                    headers={
                        "User-Agent": USER_AGENT
                    }
                )

                child_response.raise_for_status()

                child_soup = BeautifulSoup(
                    child_response.content,
                    "xml"
                )

                for url_tag in child_soup.find_all(
                    "url"
                ):

                    loc = url_tag.find(
                        "loc"
                    )

                    if loc:

                        url = loc.get_text(
                            strip=True
                        )

                        if url:
                            all_urls.append(
                                url
                            )

            except Exception:
                continue

        return _filter_urls(
            all_urls,
            exclude_fragments
        )

    # -------------------------------------------------
    # ZWYKŁA SITEMAPA
    # -------------------------------------------------

    urls = []

    for url_tag in soup.find_all(
        "url"
    ):

        loc = url_tag.find(
            "loc"
        )

        if loc:

            url = loc.get_text(
                strip=True
            )

            if url:
                urls.append(
                    url
                )

    return _filter_urls(
        urls,
        exclude_fragments
    )
