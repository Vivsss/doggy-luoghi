# doggy-luoghi

Luoghi utili per chi ha un cane (aree cani, parchi, veterinari, toelettature, negozi, pensioni,
addestramento, canili, fontanelle, sacchetti), estratti ogni settimana da OpenStreetMap per l'app **Doggy**.

## Come funziona

1. Ogni lunedì alle 02:00 UTC l'automazione **Aggiorna luoghi** (GitHub Actions) scarica da
   [Geofabrik](https://download.geofabrik.de/europe/italy.html) il file OpenStreetMap della zona.
2. Lo script `scripts/aggiorna.py` ritaglia il rettangolo di ogni zona e tiene solo i luoghi che interessano,
   con [osmium](https://osmcode.org/osmium-tool/).
3. Il risultato (es. `roma.json`) viene pubblicato sul ramo **`dati`**, sempre con un solo commit.
4. Il database di Doggy (Supabase) lo scarica il lunedì mattina e aggiorna la tabella dei luoghi.

Le zone sono in `aree.json`: nome, file da produrre, file Geofabrik di partenza e rettangolo
`[ovest, sud, est, nord]`. Per ora c'è solo **Roma**.

Il formato dei file è lo stesso delle risposte di Overpass: `{"elements": [{"type", "id", "lat", "lon", "tags"}]}`.

## Lanciarlo a mano

GitHub → **Actions** → **Aggiorna luoghi** → **Run workflow**.

## Licenza dei dati

© OpenStreetMap contributors, licenza ODbL: vedi [LICENZA-DATI.md](LICENZA-DATI.md).
