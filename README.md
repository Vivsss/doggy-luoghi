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

## Pagine pubbliche dell'app (GitHub Pages)

- `apri/`: la pagina "ponte" che apre i link di Doggy mandati su WhatsApp, SMS ed email.
- `smarrito/`: la pagina di un **cane smarrito** (`smarrito/#t=<codice>`), da condividere anche con chi non ha Doggy: foto, dati, dove si è perso, "Chiama la famiglia" se ha scelto di mostrare il telefono, e "L'ho visto" per mandare una segnalazione. Usa solo le due funzioni del database pensate per chi non ha un account (`lost_dog_public`, `lost_sighting_public`) con la chiave pubblica dell'app.
- `vicini/`: la pagina per chi riceve l'invito di un vicino ("Invita chi ha un cane qui vicino" nell'app): cos'è Doggy e, per chi ce l'ha già, il pulsante per aprirla.

Prima del lancio queste pagine passano sul dominio `doggy-app.it`.

## Licenza dei dati

© OpenStreetMap contributors, licenza ODbL: vedi [LICENZA-DATI.md](LICENZA-DATI.md).
