import requests


USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/153.0.0.0 Safari/537.36"
)


def download_page(url):
    response = requests.get(
        url,
        timeout=30,
        headers={
            "User-Agent": USER_AGENT
        }
    )

    response.raise_for_status()

    return response.text
