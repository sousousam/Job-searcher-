import cloudscraper

def test_naval_html():
    scraper = cloudscraper.create_scraper()
    url_naval = "https://www.naval-group.com/fr/nous-rejoindre"
    r_naval = scraper.get(url_naval)
    print(r_naval.text[:2000])

test_naval_html()
