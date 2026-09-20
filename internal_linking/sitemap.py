import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

from .crawler import USER_AGENT


def _filter_urls(
    urls,
    filter_mode="exclude",
    filter_fragments=None
):
    """
    Filtruje URL-e na podstawie fragmentów.

    filter_mode:
        exclude = wyklucz URL-e zawierające fragment
        include = zostaw tylko URL-e zawierające fragment

    Zwraca:
        filtered_urls
        filtered_out_count
    """

    unique_urls = list(
        dict.fromkeys(
            urls
        )
    )

    if not filter_fragments:

        return (
            unique_urls,
            0
        )

    fragments = [
        fragment.strip().lower()
        for fragment in filter_fragments
        if fragment.strip()
    ]

    if not fragments:

        return (
            unique_urls,
            0
        )

    filtered = []
    filtered_out_count = 0

    for url in unique_urls:

        url_lower = url.lower()

        contains_fragment = any(
            fragment in url_lower
            for fragment in fragments
        )

        # ---------------------------------------------
        # WYKLUCZ
        # ---------------------------------------------

        if filter_mode == "exclude":

            if contains_fragment:

                filtered_out_count += 1
                continue

            filtered.append(
                url
            )

        # ---------------------------------------------
        # TYLKO TE URL-E
        # ---------------------------------------------

        elif filter_mode == "include":

            if contains_fragment:

                filtered.append(
                    url
                )

            else:

                filtered_out_count += 1

        # ---------------------------------------------
        # BEZPIECZNY DOMYŚLNY TRYB
        # ---------------------------------------------

        else:

            filtered.append(
                url
            )

    return (
        filtered,
        filtered_out_count
    )


def find_sitemap_in_robots(page_url):
    """
    Sprawdza robots.txt domeny i szuka wpisu Sitemap:.
    """

    parsed = urlparse(
        page_url
    )

    if not parsed.scheme or not parsed.netloc:

        return {
            "status": "error",
            "sitemap_url": None,
            "robots_url": "",
        }

    robots_url = (
        f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    )

    try:

        response = requests.get(
            robots_url,
            timeout=15,
            headers={
                "User-Agent": USER_AGENT
            },
            allow_redirects=True,
        )

    except requests.RequestException:

        return {
            "status": "error",
            "sitemap_url": None,
            "robots_url": robots_url,
        }

    if response.status_code == 404:

        return {
            "status": "missing",
            "sitemap_url": None,
            "robots_url": robots_url,
        }

    if response.status_code != 200:

        return {
            "status": "error",
            "sitemap_url": None,
            "robots_url": robots_url,
        }

    sitemap_urls = []

    for line in response.text.splitlines():

        line = line.strip()

        if not line:
            continue

        if line.startswith("#"):
            continue

        if ":" not in line:
            continue

        directive, value = line.split(
            ":",
            1
        )

        if directive.strip().lower() != "sitemap":
            continue

        sitemap_url = value.strip()

        if sitemap_url:

            sitemap_urls.append(
                sitemap_url
            )

    sitemap_urls = list(
        dict.fromkeys(
            sitemap_urls
        )
    )

    if not sitemap_urls:

        return {
            "status": "not_listed",
            "sitemap_url": None,
            "robots_url": robots_url,
        }

    return {
        "status": "found",
        "sitemap_url": sitemap_urls[0],
        "robots_url": robots_url,
    }


def get_sitemap_urls(
    sitemap_url,
    filter_fragments=None,
    filter_mode="exclude",
    progress_callback=None
):
    """
    Pobiera sitemapę lub sitemap index.

    filter_mode:
        exclude = wyklucz URL-e
        include = zostaw tylko pasujące URL-e

    Zwraca:

        sitemap_urls
        total_urls
        filtered_out_count
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

        total_sitemaps = len(
            sitemap_links
        )

        completed_sitemaps = 0

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

                pass

            completed_sitemaps += 1

            if progress_callback:

                progress_callback(
                    completed_sitemaps,
                    total_sitemaps
                )

        unique_urls = list(
            dict.fromkeys(
                all_urls
            )
        )

        total_urls = len(
            unique_urls
        )

        (
            filtered_urls,
            filtered_out_count
        ) = _filter_urls(
            unique_urls,
            filter_mode=filter_mode,
            filter_fragments=filter_fragments
        )

        return (
            filtered_urls,
            total_urls,
            filtered_out_count
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

    if progress_callback:

        progress_callback(
            1,
            1
        )

    unique_urls = list(
        dict.fromkeys(
            urls
        )
    )

    total_urls = len(
        unique_urls
    )

    (
        filtered_urls,
        filtered_out_count
    ) = _filter_urls(
        unique_urls,
        filter_mode=filter_mode,
        filter_fragments=filter_fragments
    )

    return (
        filtered_urls,
        total_urls,
        filtered_out_count
    )
