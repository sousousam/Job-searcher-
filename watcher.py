"""
watcher.py — le cerveau.

À chaque exécution :
  1. interroge chaque source de config.py
  2. compare avec ce qui avait déjà été vu (data/seen.json)
  3. garde uniquement les NOUVELLES offres
  4. (optionnel) demande à Claude de noter leur pertinence
  5. écrit data/offers.js, que la page review.html lit pour t'afficher tout ça

Lancer :  python watcher.py
"""

import os
import json
import datetime
from pathlib import Path

import config
from sources import ADAPTERS

DATA = Path(__file__).parent / "data"
DATA.mkdir(exist_ok=True)
SEEN_FILE = DATA / "seen.json"
OUT_FILE = DATA / "offers.js"


def load_seen():
    if SEEN_FILE.exists():
        return json.loads(SEEN_FILE.read_text(encoding="utf-8"))
    return {}


def save_seen(seen):
    SEEN_FILE.write_text(json.dumps(seen, ensure_ascii=False, indent=2), encoding="utf-8")


def collect():
    """Interroge toutes les sources. Renvoie {nom_source: [offres]}."""
    results = {}
    for src in config.SOURCES:
        name = src["name"]
        adapter = ADAPTERS.get(src["type"])
        if not adapter:
            print(f"  [!] type inconnu pour {name}: {src['type']}")
            continue
        try:
            offers = adapter(src)
            # Catégorie par site : si la source en déclare une, on l'applique
            # aux offres qui n'ont pas déjà un type plus précis.
            categorie = src.get("categorie")
            if categorie:
                for o in offers:
                    if not o.get("contract"):
                        o["contract"] = categorie
            print(f"  [{name}] {len(offers)} offre(s) trouvée(s)")
            results[name] = offers
        except Exception as e:
            # Une source qui plante ne doit pas casser tout le reste.
            print(f"  [{name}] ERREUR : {e}")
            results[name] = []
    return results


def diff(results, seen):
    """Sépare le nouveau de l'ancien et met à jour `seen`.

    Une source jamais vue auparavant (ex. que tu viens d'ajouter) sert de
    référence : ses offres sont enregistrées mais PAS signalées comme nouvelles.
    Ainsi, ajouter un site ne fait pas remonter des centaines d'offres d'un coup.
    """
    new_offers = []
    global_first = len(seen) == 0
    for name, offers in results.items():
        source_known = name in seen          # déjà suivie lors d'un passage précédent ?
        known = set(seen.get(name, []))
        current_ids = []
        for o in offers:
            current_ids.append(o["id"])
            if source_known and o["id"] not in known:
                o["source"] = name
                o["is_new"] = True
                new_offers.append(o)
            else:
                o["source"] = name
        seen[name] = current_ids
    return new_offers, global_first


def score_with_claude(offers):
    """Optionnel : note 0-100 la pertinence vs config.PROFIL.
    Activé seulement si la variable d'environnement ANTHROPIC_API_KEY existe."""
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key or not offers:
        return
    try:
        import anthropic
    except ImportError:
        print("  [Claude] paquet 'anthropic' non installé, tri ignoré.")
        return

    client = anthropic.Anthropic(api_key=key)
    listing = "\n".join(f'{i}. {o["title"]} — {o["company"]} — {o["location"]}'
                        for i, o in enumerate(offers))
    prompt = (
        f"Profil recherché : {config.PROFIL}\n\n"
        f"Voici des offres numérotées :\n{listing}\n\n"
        "Pour CHAQUE numéro, donne un score de pertinence 0-100. "
        'Réponds UNIQUEMENT en JSON : {"scores": {"0": 80, "1": 25, ...}}'
    )
    try:
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}],
        )
        txt = "".join(b.text for b in msg.content if b.type == "text")
        txt = txt.replace("```json", "").replace("```", "").strip()
        scores = json.loads(txt).get("scores", {})
        for i, o in enumerate(offers):
            o["score"] = scores.get(str(i))
    except Exception as e:
        print(f"  [Claude] tri ignoré : {e}")


def write_output(new_offers, all_results, first_run):
    payload = {
        "generatedAt": datetime.datetime.now().isoformat(timespec="minutes"),
        "firstRun": first_run,
        "new": new_offers,
        "counts": {name: len(o) for name, o in all_results.items()},
    }
    OUT_FILE.write_text(
        "window.OFFERS = " + json.dumps(payload, ensure_ascii=False, indent=2) + ";",
        encoding="utf-8",
    )


def main():
    print("Veille emploi —", datetime.datetime.now().strftime("%d/%m %H:%M"))
    seen = load_seen()
    results = collect()
    new_offers, first_run = diff(results, seen)
    score_with_claude(new_offers)
    # Les mieux notées d'abord (les non notées tombent à la fin).
    new_offers.sort(key=lambda o: o.get("score") or -1, reverse=True)
    save_seen(seen)
    write_output(new_offers, results, first_run)

    if first_run:
        print(f"Premier passage : {sum(len(v) for v in results.values())} offres "
              "enregistrées comme référence. Les nouveautés apparaîtront dès demain.")
    else:
        print(f"{len(new_offers)} NOUVELLE(S) offre(s) depuis le dernier passage.")


if __name__ == "__main__":
    main()