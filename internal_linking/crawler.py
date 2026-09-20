import requests
from concurrent.futures import ThreadPoolExecutor, as_completed


USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/153.0.0.0 Safari/537.36"
)


def download_page(url):
    """
    Pobiera pojedynczą stronę.
    """

    response = requests.get(
        url,
        timeout=30,
        headers={
            "User-Agent": USER_AGENT
        }
    )

    response.raise_for_status()

    return response.text


def download_pages(
    urls,
    max_workers=10
):
    """
    Pobiera wiele stron równocześnie.

    Zwraca:
        pages - lista słowników:
            {
                "url": "...",
                "html": "...",
                "error": None
            }

    albo przy błędzie:
            {
                "url": "...",
                "html": None,
                "error": "..."
            }
    """

    pages = []

    def fetch(url):

        try:

            html = download_page(
                url
            )

            return {
                "url": url,
                "html": html,
                "error": None,
            }

        except Exception as e:

            return {
                "url": url,
                "html": None,
                "error": str(e),
            }

    with ThreadPoolExecutor(
        max_workers=max_workers
    ) as executor:

        futures = {
            executor.submit(
                fetch,
                url
            ): url
            for url in urls
        }

        for future in as_completed(
            futures
        ):

            result = future.result()

            pages.append(
                result
            )

    return pages
