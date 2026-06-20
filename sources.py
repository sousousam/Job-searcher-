"""
Adapteurs : un par type de site. Chacun renvoie une liste d'offres
normalisées sous la forme :

    {
        "id":       "identifiant stable et unique de l'offre",
        "title":    "intitulé du poste",
        "url":      "lien direct vers l'offre",
        "company":  "...",
        "location": "...",
        "contract": "...",
        "date":     "...",     # peut être vide
    }

Le seul champ vraiment indispensable est "id" : c'est lui qui sert à
détecter ce qui est NOUVEAU d'un jour à l'autre.
"""

import re
import time
import unicodedata
import requests
import cloudscraper
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode

HEADERS = {
    # On se présente comme un vrai navigateur (Safran refuse les User-Agent "robots").
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,"
              "image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
    "Upgrade-Insecure-Requests": "1",
}
TIMEOUT = 25


# ------------------------------------------------------------------ SAFRAN
def fetch_safran(cfg):
    from bs4 import BeautifulSoup
    offers, seen_ids = [], set()
    # Motif d'un lien d'offre : /fr/offres/<pays>/<ville>/<slug>-<id>
    pat = re.compile(r"/fr/offres/[^/]+/[^/]+/.+-(\d+)$")

    for page in range(cfg.get("max_pages", 20)):
        url = _with_query(cfg["url"], {"page": page})
        scraper = cloudscraper.create_scraper()
        r = scraper.get(url, timeout=TIMEOUT)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        found_on_page = 0
        for a in soup.find_all("a", href=True):
            m = pat.search(a["href"].split("?")[0])
            if not m:
                continue
            job_id = m.group(1)
            if job_id in seen_ids:
                continue
            seen_ids.add(job_id)
            found_on_page += 1
            title = a.get_text(" ", strip=True)
            if not title:
                continue
            offers.append({
                "id": job_id,
                "title": title,
                "url": a["href"] if a["href"].startswith("http") else "https://www.safran-group.com" + a["href"],
                "company": "Safran",
                "location": "",
                "contract": "",
                "date": "",
            })
        if found_on_page == 0:        # plus d'offres → on arrête
            break
    return offers


# ------------------------------------------------------------------ WORKDAY (Airbus)
def fetch_workday(cfg):
    endpoint = f"https://{cfg['host']}/wday/cxs/{cfg['tenant']}/{cfg['site']}/jobs"
    offers, offset, limit = [], 0, 20
    page_url = cfg["page_url"].rstrip("/")

    while True:
        payload = {
            "appliedFacets": cfg.get("applied_facets", {}),
            "limit": limit,
            "offset": offset,
            "searchText": cfg.get("search_text", ""),
        }
        r = requests.post(endpoint, json=payload, headers={**HEADERS, "Accept": "application/json"}, timeout=TIMEOUT)
        r.raise_for_status()
        data = r.json()
        postings = data.get("jobPostings", [])
        if not postings:
            break
        for p in postings:
            ext = p.get("externalPath", "")
            job_id = ext or p.get("bulletFields", [""])[0]
            offers.append({
                "id": str(job_id),
                "title": p.get("title", "").strip(),
                "url": page_url + ext if ext else page_url,
                "company": "Airbus",
                "location": p.get("locationsText", ""),
                "contract": "",
                "date": p.get("postedOn", ""),
            })
        offset += limit
        if offset >= data.get("total", 0) or offset > 2000:
            break
    return offers


# ------------------------------------------------------------------ CIVIWEB (VIE)
def fetch_civiweb(cfg):
    endpoint = "https://civiweb-api-prd.azurewebsites.net/api/Offers/search"
    body = dict(cfg.get("body", {}))
    headers = {**HEADERS, "Accept": "application/json",
               "Origin": "https://mon-vie-via.businessfrance.fr",
               "Referer": "https://mon-vie-via.businessfrance.fr/"}
    r = requests.post(endpoint, json=body, headers=headers, timeout=TIMEOUT)
    if r.status_code >= 300:
        raise RuntimeError(f"{r.status_code} — réponse de l'API : {r.text[:300]}")
    data = r.json()

    # La réponse peut être une liste, ou un objet {result:[...]} / {data:[...]} / {items:[...]}
    items = data if isinstance(data, list) else (
        data.get("result") or data.get("data") or data.get("offers")
        or data.get("items") or data.get("value") or []
    )

    offers = []
    for o in items:
        if not isinstance(o, dict):
            continue
        job_id = o.get("id") or o.get("offerId") or o.get("idOffre") or o.get("missionId")
        if job_id is None:
            continue
        title = (o.get("missionTitle") or o.get("title") or o.get("jobTitle")
                 or o.get("intitule") or o.get("organizationName") or "Offre VIE")
        company = o.get("organizationName") or o.get("companyName") or o.get("entreprise") or ""
        city = o.get("cityName") or o.get("city") or o.get("ville") or ""
        country = o.get("countryName") or o.get("country") or o.get("pays") or ""
        offers.append({
            "id": str(job_id),
            "title": title,
            "url": f"https://mon-vie-via.businessfrance.fr/offre/{job_id}",
            "company": company,
            "location": ", ".join(x for x in [city, country] if x),
            "contract": "VIE",
            "date": o.get("publicationDate") or o.get("datePublication") or o.get("creationDate") or "",
        })

    # Indice si la réponse a des noms de champs inattendus (titres tous vides)
    if items and offers and all(of["title"] == "Offre VIE" for of in offers):
        print("   [VIE] (info) champs reçus dans la réponse :", list(items[0].keys())[:20])

    return offers


# ------------------------------------------------------------------ NAVAL GROUP (HTML)
NAVAL_CONTRACTS = {
    "durée indéterminée": "CDI",
    "durée déterminée": "CDD",
    "stagiaire": "Stage",
    "contrat d'alternance": "Alternance",
    "alternance": "Alternance",
    "cifre": "CIFRE",
    "intérimaire": "Intérim",
    "manager de transition": "Autre",
    "vie": "VIE",
}


def _naval_contract(title, text):
    s = (title + " " + text).lower()
    # 1) libellés exacts présents dans la fiche
    for label, cat in NAVAL_CONTRACTS.items():
        if label in s:
            return cat
    # 2) préfixe du titre ("CDI - ...", "Stage - ...")
    head = title.lower()
    for kw, cat in [("cdi", "CDI"), ("cdd", "CDD"), ("stage", "Stage"),
                    ("alternance", "Alternance"), ("vie", "VIE")]:
        if head.startswith(kw):
            return cat
    return ""


def _norm(s):
    """minuscule + sans accents + tirets→espaces, pour comparer des villes."""
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s.lower().replace("-", " ").strip()


def _naval_location(detail_html):
    """Extrait l'« Implantation géographique » de la FICHE offre.

    On se limite au conteneur #contenu-ficheoffre pour ne pas attraper le
    même libellé présent dans le filtre latéral (un <select> de toutes les
    zones). La valeur est un chemin du type
    « Europe, France, Provence-Cote d'Azur, Saint-Tropez ».
    """
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(detail_html, "html.parser")
    box = soup.find(id="contenu-ficheoffre")
    if box is None:
        return ""
    for h in box.find_all(["h3", "h2", "span", "strong", "dt", "label"]):
        if "implantation geographique" in _norm(h.get_text()):
            p = h.find_next("p")
            if p is not None:
                return p.get_text(" ", strip=True)
    return ""


def fetch_naval(cfg):
    from bs4 import BeautifulSoup
    offers, seen_ids = [], set()
    pat = re.compile(r"/offre-de-emploi/emploi-.+?_(\d+)\.aspx")
    target = (cfg.get("categorie") or "").strip()

    # On utilise TalentSoft (site officiel ATS) pour contourner DataDome
    base_url = "https://dcns-recrute.talent-soft.com/offre-de-emploi/liste-offres.aspx"

    for page in range(1, cfg.get("max_pages", 60) + 1):
        url = _with_query(base_url, {"page": page})
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        found = 0
        for a in soup.find_all("a", href=True):
            m = pat.search(a["href"])
            if not m:
                continue
            job_id = m.group(1)
            if job_id in seen_ids:
                continue
            seen_ids.add(job_id)
            found += 1

            # remonter jusqu'au conteneur de l'offre
            box = a
            for _ in range(5):
                if box.parent is not None:
                    box = box.parent
                if box.name == "li":
                    break
            
            title = a.get_text(" ", strip=True)
            text = box.get_text(" ", strip=True)

            offers.append({
                "id": job_id,
                "title": title,
                "url": "https://dcns-recrute.talent-soft.com" + a["href"].split("?")[0],
                "company": "Naval Group",
                "location": "", # La ville n'est pas exposée dans la liste TalentSoft
                "contract": _naval_contract(title, text),
                "date": "",
            })

        if found == 0:        # plus d'offres → fin de la pagination
            break
        time.sleep(0.4)       # on reste poli entre les pages

    # ne garder que la catégorie voulue (ex : "CDI")
    # — fait AVANT d'ouvrir les fiches pour réduire le nombre de requêtes.
    if target:
        offers = [o for o in offers if o["contract"] == target]

    # filtre par ville : la ville n'est PAS dans la liste, seulement dans la
    # fiche. On ouvre donc chaque fiche (1 requête/offre) pour lire
    # « Implantation géographique », puis on garde les villes voulues.
    villes = cfg.get("villes") or []
    villes_norm = {_norm(v) for v in villes}
    if not villes_norm:
        return offers

    kept = []
    for o in offers:
        try:
            rd = requests.get(o["url"], headers=HEADERS, timeout=TIMEOUT)
            rd.raise_for_status()
            loc = _naval_location(rd.text)
        except requests.RequestException:
            loc = ""
        o["location"] = loc
        segs = {_norm(s) for s in loc.split(",")}
        if villes_norm & segs:
            kept.append(o)
        time.sleep(0.4)       # politesse entre les fiches (anti-DataDome)
    return kept


# ------------------------------------------------------------------ utilitaires
def _with_query(url, extra):
    """Renvoie l'URL avec les paramètres `extra` ajoutés/remplacés."""
    parts = urlparse(url)
    q = dict(parse_qsl(parts.query, keep_blank_values=True))
    q.update({k: str(v) for k, v in extra.items()})
    return urlunparse(parts._replace(query=urlencode(q)))


ADAPTERS = {
    "safran": fetch_safran,
    "workday": fetch_workday,
    "civiweb": fetch_civiweb,
    "naval": fetch_naval,
}