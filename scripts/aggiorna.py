"""Prepara i luoghi di Doggy dai dati di OpenStreetMap.

Per ogni zona in aree.json:
  1. scarica il file di Geofabrik (una volta sola se più zone usano lo stesso file);
  2. ritaglia il rettangolo della zona e tiene solo i luoghi che interessano a Doggy (osmium);
  3. scrive uscita/<file>.json nello stesso formato di Overpass ({"elements": [...]}),
     così il database lo legge con lo stesso codice.

Uso: python3 scripts/aggiorna.py   (serve osmium-tool installato)
"""

import json
import os
import subprocess
import sys
import urllib.request
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LAVORO = os.path.join(ROOT, "lavoro")
USCITA = os.path.join(ROOT, "uscita")

# Cosa cerchiamo in OpenStreetMap (come la query Overpass della migrazione 013)
FILTRI = [
    "nwr/leisure=dog_park,park",
    "nwr/amenity=veterinary,animal_boarding,animal_training,animal_shelter,drinking_water",
    "nwr/shop=pet,pet_grooming",
    "nwr/vending=excrement_bags",
    "nwr/waste",
]

# I tag che servono al database: il resto lo togliamo per tenere il file piccolo
TAG_UTILI = {
    "name", "leisure", "amenity", "shop", "vending", "waste",
    "addr:street", "addr:housenumber", "opening_hours",
    "phone", "contact:phone", "website", "contact:website", "dog",
}


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
    if not os.path.exists(destinazione):
        print(f"Scarico {url}", flush=True)
        richiesta = urllib.request.Request(url, headers={"User-Agent": "DoggyApp/0.1 (luoghi per proprietari di cani)"})
        with urllib.request.urlopen(richiesta) as risposta, open(destinazione, "wb") as f:
            while True:
                blocco = risposta.read(1 << 20)
                if not blocco:
                    break
                f.write(blocco)
    return destinazione


def prepara(area):
    pbf = scarica(area["fonte"])
    base = os.path.join(LAVORO, area["file"].replace(".json", ""))
    ritaglio = base + "-ritaglio.osm.pbf"
    filtrato = base + "-filtrato.osm.pbf"
    geojson = base + ".geojsonseq"
    w, s, e, n = area["bbox"]

    run("osmium", "extract", "--bbox", f"{w},{s},{e},{n}", "--strategy", "smart", "--overwrite", "-o", ritaglio, pbf)
    run("osmium", "tags-filter", "--overwrite", "-o", filtrato, ritaglio, *FILTRI)
    run("osmium", "export", "--overwrite", "-f", "geojsonseq", "-a", "type,id", "-o", geojson, filtrato)

    elementi = {}
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
