import pytest


@pytest.fixture(autouse=True, scope="module")
def scraper_headers():
    return {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6)'
                      ' AppleWebKit/603.3.8 (KHTML, like Gecko) '
                      'Version/10.1.2 Safari/603.3.8',
        'Host': 'bitcointalk.org',
        'Origin': 'https://bitcointalk.org',
        'Referer': 'https://bitcointalk.org'
    }
