import requests
from bs4 import BeautifulSoup

def test_counts():
    url_all = "https://dcns-recrute.talent-soft.com/offre-de-emploi/liste-offres.aspx"
    url_toulon = "https://dcns-recrute.talent-soft.com/offre-de-emploi/liste-offres.aspx?Location=Toulon"
    
    for url in [url_all, url_toulon]:
        r = requests.get(url)
        soup = BeautifulSoup(r.text, 'html.parser')
        
        # TalentSoft usually puts the count in an element with class ts-offer-list-count or similar
        count_elem = soup.find(id='ts-results-count') or soup.find(class_='offerlist-count')
        if not count_elem:
            # Let's just find any strong tag that has "offres" in it
            strongs = soup.find_all('strong')
            for s in strongs:
                if 'offre' in s.text.lower():
                    print("Count:", s.text)
                    break
        else:
            print("Count:", count_elem.text)

test_counts()
