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

Le zone sono in `aree.json`: nome, file da produrre, file Geofabrik di partenza e, per una città, il rettangolo
`[ovest, sud, est, nord]`. **Dal 4/11 tutta Italia**, in 5 file che non si sovrappongono, uno per ogni parte di Geofabrik:
`italia-centro.json`, `italia-nord-ovest.json`, `italia-nord-est.json`, `italia-sud.json`, `italia-isole.json`.
Resta anche `roma.json` (il ritaglio di Roma), finché il database di prova non passa alle 5 parti (migrazione 069 di doggy-app).

Il formato dei file è lo stesso delle risposte di Overpass: `{"elements": [{"type", "id", "lat", "lon", "tags"}]}`.

## Lanciarlo a mano

GitHub → **Actions** → **Aggiorna luoghi** → **Run workflow**.

## Pagine pubbliche dell'app (GitHub Pages)

- `apri/`: la pagina "ponte" che apre i link di Doggy mandati su WhatsApp, SMS ed email.
- `smarrito/`: la pagina di un **cane smarrito** (`smarrito/#t=<codice>`), da condividere anche con chi non ha Doggy: foto, dati, dove si è perso, "Chiama la famiglia" se ha scelto di mostrare il telefono, e "L'ho visto" per mandare una segnalazione. Usa solo le due funzioni del database pensate per chi non ha un account (`lost_dog_public`, `lost_sighting_public`) con la chiave pubblica dell'app.
- `vicini/`: la pagina per chi riceve l'invito di un vicino ("Invita chi ha un cane qui vicino" nell'app): cos'è Doggy e, per chi ce l'ha già, il pulsante per aprirla.

- `beta/`: la pagina per **diventare tester** (4/11), un solo link da mandare su WhatsApp: per Android il gruppo Google dei tester e il link del test di Google Play, per iPhone TestFlight. I link veri vanno al posto dei `#DA_...` quando ci sono gli account degli store.

- pagina iniziale (`index.html`), `privacy/` e `condizioni/` (5/11): le ultime due si generano dai documenti di doggy-app con `python3 scripts/pagine-legali.py ../doggy-app`, da rilanciare a ogni modifica della privacy policy o delle condizioni d'uso.
- `img/`: il logo per le email di Doggy.

**Dominio `doggy-app.it` (5/11):** le pagine passano su https://doggy-app.it con GitHub Pages. Servono i record DNS su OVH (4 record A verso GitHub, un CNAME `www` → `vivsss.github.io`, il TXT di verifica del dominio per l'account GitHub), poi il file `CNAME` in questo repository. I link interni delle pagine sono relativi, quindi funzionano sia qui sia sul dominio.

## Licenza dei dati

© OpenStreetMap contributors, licenza ODbL: vedi [LICENZA-DATI.md](LICENZA-DATI.md).
