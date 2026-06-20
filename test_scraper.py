from curl_cffi import requests

def test_naval_api():
    url_naval = "https://www.naval-group.com/fr/talents/nos-offres"
    print(f"Fetching Naval Group: {url_naval}")
    r_naval = requests.get(url_naval, impersonate="chrome")
    print(f"Status: {r_naval.status_code}")
    print(r_naval.text[:500])

test_naval_api()
