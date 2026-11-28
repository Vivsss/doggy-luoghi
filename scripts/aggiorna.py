"""Prepara i luoghi di dogtown dai dati di OpenStreetMap.

Per ogni zona in aree.json:
  1. scarica il file di Geofabrik (una volta sola se più zone usano lo stesso file);
  2. ritaglia il rettangolo della zona e tiene solo i luoghi che interessano a dogtown (osmium);
  3. scrive uscita/<file>.json nello stesso formato di Overpass ({"elements": [...]}),
     così il database lo legge con lo stesso codice.

Uso: python3 scripts/aggiorna.py   (serve osmium-tool installato)
"""

import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LAVORO = os.path.join(ROOT, "lavoro")
USCITA = os.path.join(ROOT, "uscita")

# Cosa cerchiamo in OpenStreetMap (come la query Overpass della migrazione 013)
FILTRI = [
    "nwr/leisure=dog_park,park",
    "nwr/amenity=veterinary,animal_boarding,animal_training,animal_shelter,animal_breeding,drinking_water",
    "nwr/shop=pet,pet_grooming",
    "nwr/vending=excrement_bags",
    "nwr/waste",
]

# I tag che servono al database: il resto lo togliamo per tenere il file piccolo
TAG_UTILI = {
    "name", "leisure", "amenity", "shop", "vending", "waste",
    "addr:street", "addr:housenumber", "opening_hours",
    "phone", "contact:phone", "website", "contact:website", "dog", "animal_breeding",
}

# 27/11: in OpenStreetMap molte colonie feline sono segnate come rifugi per animali (amenity=animal_shelter).
# In un'app per proprietari di cani non servono: si tolgono i rifugi che per i tag non accolgono cani (solo gatti o
# altre specie) e, senza tag sugli animali, quelli che dal nome sono solo per gatti. Un rifugio con il cane (anche
# insieme ai gatti) o senza indicazioni resta.
PAROLE_GATTI = re.compile(r"gatt|felin|\bcats?\b|\bkitten|\bmici\b|\bmicio\b", re.IGNORECASE)
PAROLE_CANI = re.compile(r"\bcan[ei]\b|canil|\bdogs?\b|cagnolin|cucciol", re.IGNORECASE)
CHIAVI_ANIMALI = ("animal", "animal_shelter", "animal_shelter:animal", "species")


def motivo_solo_gatti(t):
    """Perché il rifugio è solo per gatti ('tag: ...' oppure 'nome/sito'), o None se non lo è."""
    if t.get("amenity") != "animal_shelter":
        return None
    animali = ";".join(t.get(k, "") for k in CHIAVI_ANIMALI).lower()
    # un tag generico ("yes") non dice niente sugli animali
    specie = [x.strip() for x in re.split(r"[;,]", animali) if x.strip() and x.strip() not in ("yes", "designated")]
    if specie:
        # i tag dicono quali animali accoglie il rifugio: resta solo se c'è il cane (o un'indicazione generica che lo
        # può comprendere); un rifugio di soli gatti o di altre specie (es. un'oasi con capre e conigli) si toglie
        if any(re.search(r"dog|can[ei]\b|canin|animal|\ball\b|\bany\b|\bpets?\b|stray|randag|domestic|abandon|mammal", x) for x in specie):
            return None
        return f"tag: senza cani ({';'.join(specie)})"
    testo = " ".join(t.get(k, "") for k in ("name", "website", "contact:website"))
    if PAROLE_GATTI.search(testo) and not PAROLE_CANI.search(testo):
        return "nome/sito"
    return None


def solo_gatti(t):
    """True se il rifugio è chiaramente solo per gatti (tag degli animali, nome o sito)."""
    return motivo_solo_gatti(t) is not None


def tipo(t):
    """Stessa logica di place_kind() nel database: None = non ci interessa."""
    if t.get("leisure") == "dog_park":
        return "area_cani"
    if t.get("amenity") == "veterinary":
        return "veterinario"
    if t.get("shop") == "pet_grooming":
        return "toelettatura"
    if t.get("shop") == "pet":
        return "negozio"
    if t.get("amenity") == "animal_boarding":
        return "pensione"
    if t.get("amenity") == "animal_training":
        return "addestramento"
    if t.get("amenity") == "animal_shelter":
        return "canile"
    # 25/11: allevamenti di cani (solo con il cane tra gli animali allevati; senza nome si chiamano "Allevamento")
    if t.get("amenity") == "animal_breeding" and "dog" in [x.strip() for x in t.get("animal_breeding", "").split(";")]:
        return "allevamento"
    if t.get("amenity") == "drinking_water":
        return "fontanella"
    if t.get("vending") == "excrement_bags" or "dog_excrement" in t.get("waste", ""):
        return "sacchetti"
    if t.get("leisure") == "park" and t.get("name"):
        return "parco"
    return None


def centro(geometry):
    """Un punto per ogni luogo: il punto stesso, o la media dei vertici del contorno."""
    g = geometry["type"]
    c = geometry["coordinates"]
    if g == "Point":
        return c[1], c[0]
    if g == "LineString":
        punti = c
    elif g == "Polygon":
        punti = c[0]
    elif g == "MultiPolygon":
        punti = [p for poligono in c for p in poligono[0]]
    else:
        return None
    if not punti:
        return None
    lat = sum(p[1] for p in punti) / len(punti)
    lon = sum(p[0] for p in punti) / len(punti)
    return lat, lon


def run(*args):
    print("$", " ".join(args), flush=True)
    subprocess.run(args, check=True)


def scarica(url):
    os.makedirs(LAVORO, exist_ok=True)
    destinazione = os.path.join(LAVORO, os.path.basename(url))
    if os.path.exists(destinazione):
        return destinazione
    # 21/11: il 16/11 il download è fallito per un errore di rete passeggero ("Network is unreachable"):
    # si riprova fino a 8 volte, aspettando sempre di più (27/11: di nuovo "Network is unreachable")
    for tentativo in range(1, 9):
        try:
            print(f"Scarico {url} (tentativo {tentativo})", flush=True)
            richiesta = urllib.request.Request(
                url, headers={"User-Agent": "DoggyApp/0.1 (luoghi per proprietari di cani)"}
            )
            with urllib.request.urlopen(richiesta, timeout=120) as risposta, open(destinazione, "wb") as f:
                while True:
                    blocco = risposta.read(1 << 20)
                    if not blocco:
                        break
                    f.write(blocco)
            return destinazione
        except (OSError, urllib.error.URLError) as errore:
            print(f"Download non riuscito: {errore}", flush=True)
            if os.path.exists(destinazione):
                os.remove(destinazione)
            # 27/11: "Network is unreachable" può essere la rete IPv6 del server: ripiego con curl solo su IPv4
            try:
                print("Riprovo con curl su IPv4", flush=True)
                subprocess.run(
                    ["curl", "-4", "-L", "--fail", "--silent", "--show-error", "--connect-timeout", "30",
                     "--retry", "2", "-A", "DoggyApp/0.1 (luoghi per proprietari di cani)", "-o", destinazione, url],
                    check=True,
                    timeout=1800,
                )
                return destinazione
            except (subprocess.SubprocessError, OSError) as e2:
                print(f"Anche curl non è riuscito: {e2}", flush=True)
                if os.path.exists(destinazione):
                    os.remove(destinazione)
            if tentativo == 8:
                raise
            time.sleep(min(30 * tentativo, 120))


def prepara(area):
    pbf = scarica(area["fonte"])
    base = os.path.join(LAVORO, area["file"].replace(".json", ""))
    ritaglio = base + "-ritaglio.osm.pbf"
    filtrato = base + "-filtrato.osm.pbf"
    geojson = base + ".geojsonseq"
    if area.get("bbox"):
        # una città: si ritaglia il suo rettangolo
        w, s, e, n = area["bbox"]
        run("osmium", "extract", "--bbox", f"{w},{s},{e},{n}", "--strategy", "smart", "--overwrite", "-o", ritaglio, pbf)
        sorgente = ritaglio
    else:
        # 4/11: tutta la zona del file di Geofabrik (le 5 parti dell'Italia, che non si sovrappongono)
        sorgente = pbf
    run("osmium", "tags-filter", "--overwrite", "-o", filtrato, sorgente, *FILTRI)
    run("osmium", "export", "--overwrite", "-f", "geojsonseq", "-a", "type,id", "-o", geojson, filtrato)

    elementi = {}
    tolti_gatti = []
    with open(geojson, encoding="utf-8") as f:
        for riga in f:
            riga = riga.strip().lstrip("\x1e")
            if not riga:
                continue
            feature = json.loads(riga)
            props = feature.get("properties") or {}
            tags = {k: v for k, v in props.items() if not k.startswith("@")}
            if tipo(tags) is None:
                continue
            motivo = motivo_solo_gatti(tags)
            if motivo:
                tolti_gatti.append(f"{tags.get('name') or tags.get('website') or '(senza nome)'}  [{motivo}]")
                continue
            punto = centro(feature["geometry"])
            if punto is None:
                continue
            osm_type = props.get("@type")
            osm_id = props.get("@id")
            if osm_type not in ("node", "way", "relation") or osm_id is None:
                continue
            # Le aree chiuse diventano "area" in osmium: risalgo al tipo originale
            elementi[(osm_type, osm_id)] = {
                "type": osm_type,
                "id": int(osm_id),
                "lat": round(punto[0], 6),
                "lon": round(punto[1], 6),
                "tags": {k: v for k, v in tags.items() if k in TAG_UTILI},
            }

    risultato = {
        "zona": area["nome"],
        "generato": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "fonte": area["fonte"],
        "licenza": "Dati © OpenStreetMap contributors, licenza ODbL (https://www.openstreetmap.org/copyright)",
        "elements": sorted(elementi.values(), key=lambda x: (x["type"], x["id"])),
    }
    os.makedirs(USCITA, exist_ok=True)
    with open(os.path.join(USCITA, area["file"]), "w", encoding="utf-8") as f:
        json.dump(risultato, f, ensure_ascii=False, separators=(",", ":"))
    conteggio = {}
    for el in risultato["elements"]:
        k = tipo(el["tags"])
        conteggio[k] = conteggio.get(k, 0) + 1
    print(f"{area['nome']}: {len(risultato['elements'])} luoghi {conteggio}", flush=True)
    if tolti_gatti:
        print(f"Rifugi senza cani tolti: {len(tolti_gatti)}", flush=True)
        for nome in sorted(tolti_gatti)[:150]:
            print(f"  - {nome}", flush=True)
    return len(risultato["elements"])


def main():
    with open(os.path.join(ROOT, "aree.json"), encoding="utf-8") as f:
        aree = json.load(f)
    totale = 0
    for area in aree:
        n = prepara(area)
        if n == 0:
            print(f"ERRORE: nessun luogo per {area['nome']}", file=sys.stderr)
            sys.exit(1)
        totale += n
    print(f"Totale: {totale} luoghi")


if __name__ == "__main__":
    main()
