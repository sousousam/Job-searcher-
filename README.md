# Veille emploi automatique

Un bot qui visite chaque jour tes pages carrières, repère les **nouvelles**
offres, et te les présente sur ton propre site (deux onglets : un flux à trier,
et un tableau de suivi de tes candidatures).

Sources déjà branchées : **Safran**, **Airbus** (Workday), **VIE** (Business France).

---

## Les fichiers

```
job-watcher/
├── config.py          ← tes sites + filtres (le seul fichier à éditer)
├── sources.py         ← comment lire chaque site
├── watcher.py         ← le bot : récupère et détecte les nouveautés
├── offres.html        ← TON SITE (2 onglets : nouvelles offres + tableau)
├── requirements.txt
├── README.md
├── data/
│   └── offers.js      ← écrit par le bot, lu par le site
└── .github/
    └── workflows/
        └── daily.yml  ← lance le bot tout seul chaque jour
```

---

## 1. Essai sur ton ordi

```bash
pip install -r requirements.txt
python watcher.py
```

Puis ouvre **offres.html** dans ton navigateur.

> Le **1er passage** n'affiche aucune nouveauté : il enregistre l'état actuel
> comme référence. Les vraies nouvelles offres arrivent dès le 2e passage.

---

## 2. Le faire tourner tout seul (gratuit, sans laisser le PC allumé)

Avec **GitHub Actions** :

1. Crée un dépôt GitHub et pousses-y ce dossier.
2. `.github/workflows/daily.yml` est déjà prêt : il lance le bot chaque matin
   et réécrit `data/` dans le dépôt. L'horaire se règle sur la ligne `cron:`.
3. (Option) Active **GitHub Pages** → ton `offres.html` est en ligne et se met
   à jour tout seul, consultable depuis ton téléphone.
4. (Option) Tri par Claude : ajoute ta clé dans *Settings → Secrets → Actions*
   sous le nom `ANTHROPIC_API_KEY`, et décommente `anthropic` dans
   `requirements.txt`.

---

## 3. Comment marche le site (offres.html)

- **Onglet « Nouvelles offres »** : le flux à trier (filtrable par site).
  👍 = garder (l'offre passe dans le tableau) · 👎 = masquer.
- **Onglet « Mes offres »** : ton tableau de suivi. Colonnes Titre, Société,
  Localisation, Continent, Contrat, Lien, Statut. Le continent et le contrat
  sont devinés automatiquement et modifiables ; le statut est éditable
  (À postuler / Candidature envoyée / Entretien prévu / Refusé).

Tes choix et statuts sont enregistrés dans le navigateur. Une offre gardée reste
dans le tableau même quand elle n'est plus « nouvelle ».

---

## 4. Ajouter / modifier des recherches

Tout est dans **`config.py`**. Pour Safran, colle ton URL de recherche (avec tes
filtres) ; le bot gère la pagination. Pour une autre entreprise en Workday,
copie le bloc Airbus et change `host` / `tenant` / `site`.

---

## 5. Ajuster un champ d'API (si Airbus ou VIE renvoie 0 ou une erreur)

Leurs filtres passent par des API internes dont les noms de champs peuvent
varier. Pour récupérer la requête exacte, en 30 secondes :

1. Ouvre la page carrière dans Chrome, applique **tes** filtres.
2. `F12` → onglet **Réseau (Network)** → filtre **Fetch/XHR**.
3. Repère l'appel `jobs` (Workday) ou `Offers/search` (VIE), clique dessus.
4. Onglet **Payload / Charge utile** : recopie le contenu dans `config.py`
   (`applied_facets` pour Workday, `body` pour VIE).

Astuce debug : ajoute `print(data)` au début de l'adapteur dans `sources.py`
pour voir la réponse brute.

---

## Note

Le bot ne passe qu'**une fois par jour** et s'identifie normalement : c'est une
consultation respectueuse de pages publiques. Garde cette fréquence basse.
