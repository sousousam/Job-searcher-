"""
====================================================================
 CONFIGURATION — c'est ICI que tu ajoutes / modifies tes recherches.
 Rien d'autre à toucher dans les autres fichiers.
====================================================================

Chaque source = un couple (site + catégorie). Le même site peut apparaître
plusieurs fois avec des filtres différents (ex. Airbus en CDI et en VIE).

Le champ "categorie" (CDI / VIE / CDD / Stage…) range toutes les offres de
la source dans cette catégorie (colonne Contrat). Pour Naval Group, il sert
aussi à ne garder QUE les offres de ce type.
"""

# Optionnel : décris en une phrase le poste que tu cherches (tri par Claude).
PROFIL = "Jeune diplômé ingénieur, intéressé par un VIE ou un CDI à l'international en aéronautique/spatial/naval."

SOURCES = [

    # ======================== CDI ========================

    # ---- Airbus CDI (Workday) — réunit tes deux jeux de lieux ----
    {
        "name": "Airbus CDI",
        "type": "workday",
        "categorie": "CDI",
        "host": "ag.wd3.myworkdayjobs.com",
        "tenant": "ag",
        "site": "Airbus",
        "page_url": "https://ag.wd3.myworkdayjobs.com/fr-FR/Airbus",
        "applied_facets": {
            "FullPartTime": ["70a157281071017ad8c0ee4170448100"],
            "locationCountry": ["54c5b6971ffb4bf0b116fe7651ec789a"],
            "locations": [
                "f5811cef9cb501b257d6346b4c0acb4b",
                "f5811cef9cb501ede9109d684c0afc42",
                "f5811cef9cb50162c7b52c6b4c0aad4b",
                "f5811cef9cb5010f2f8c386b4c0ada4b",
                "c1ced8e17e4b010192c72e68dddf0000",
                "f5811cef9cb501aefccc5c6a4c0af648",
                "f5811cef9cb501ab3690c9684c0aa643",
                "f5811cef9cb501304da2d76a4c0a814a",
                "f5811cef9cb501cd0ac3406a4c0a9248",
                "f5811cef9cb501de472dae6a4c0a044a",
                "9b650d88307001466b3ad56730591326",
                "f5811cef9cb50126818a01694c0a5f44",
            ],
        },
    },

    # ---- Safran CDI (HTML) — France / Occitanie / CDI ----
    {
        "name": "Safran CDI",
        "type": "safran",
        "categorie": "CDI",
        "url": "https://www.safran-group.com/fr/offres?countries%5B0%5D=1002-france&regions_states%5B0%5D=51-occitanie&contracts%5B0%5D=9-cdi",
        "max_pages": 20,
    },

    # ---- Naval Group CDI (HTML) ----
    # Astuce : pour réduire le nombre de pages, applique le filtre
    # "Type de contrat = Durée indéterminée" (+ une ville si tu veux) sur le
    # site, puis colle l'URL filtrée ici. Le filtrage CDI est de toute façon
    # fait automatiquement.
    {
        "name": "Naval Group",
        "type": "naval",
        "categorie": "CDI",
        "villes": ["Toulon", "Ollioules", "Saint-Tropez"],   # ne garder que ces villes
        "url": "https://www.naval-group.com/fr/nous-rejoindre",
        "max_pages": 60,
    },

    # ======================== VIE ========================

    # ---- VIE / Business France (Civiweb – API) ----
    {
        "name": "VIE",
        "type": "civiweb",
        "categorie": "VIE",
        "body": {
            "limit": 200,
            "skip": 0,
            "query": None,
            "geographicZones": ["2", "4", "8"],
            "teletravail": ["0"],
            "porteEnv": ["0"],
            "activitySectorId": [],
            "missionsTypesIds": [],
            "missionsDurations": [],
            "countriesIds": [],
            "studiesLevelId": [],
            "companiesSizes": [],
            "specializationsIds": [],
            "entreprisesIds": [0],
            "missionStartDate": None,
        },
    },

    # ---- Airbus VIE (Workday) — filtre workerSubType = VIE ----
    {
        "name": "Airbus VIE",
        "type": "workday",
        "categorie": "VIE",
        "host": "ag.wd3.myworkdayjobs.com",
        "tenant": "ag",
        "site": "Airbus",
        "page_url": "https://ag.wd3.myworkdayjobs.com/fr-FR/Airbus",
        "applied_facets": {
            "workerSubType": ["f5811cef9cb5016cb7041bb2470a8418"],
        },
    },

    # ---- Safran VIE (HTML) ----
    {
        "name": "Safran VIE",
        "type": "safran",
        "categorie": "VIE",
        "url": "https://www.safran-group.com/fr/offres?contracts%5B0%5D=87-vie",
        "max_pages": 20,
    },
]