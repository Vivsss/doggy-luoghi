"""Pagine pubbliche della privacy policy e delle condizioni d'uso di Doggy (5/11).

Le scrive da docs/PRIVACY-POLICY.md e docs/CONDIZIONI-USO.md del repository doggy-app, togliendo le note per il
team (citazioni iniziali, sezioni "da verificare con il legale"). Da rilanciare a ogni modifica dei due documenti:

    python3 scripts/pagine-legali.py ../doggy-app
"""
import html
import os
import re
import sys

import markdown

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

STYLE = """
  :root { --prato:#1F6B4F; --foglia:#DDEBDF; --sabbia:#F4F0E6; --bosco:#1E2A24; --muted:#4A564F; --card:#fff; --linea:#D9D3C4; }
  @media (prefers-color-scheme: dark) {
    :root { --prato:#72C69D; --foglia:#1F3A2C; --sabbia:#121915; --bosco:#EDE8DC; --muted:#B2BAB3; --card:#1C2520; --linea:#2E3A33; }
  }
  * { box-sizing: border-box; }
  body { margin:0; background:var(--sabbia); color:var(--bosco); font-family:-apple-system, system-ui, "Segoe UI", Roboto, sans-serif;
         line-height:1.55; padding:24px 16px 48px; }
  main { max-width:760px; margin:0 auto; background:var(--card); border-radius:20px; padding:28px 24px 36px;
         box-shadow:0 4px 24px rgba(30,42,36,.08); }
  header { display:flex; align-items:center; gap:10px; margin-bottom:8px; }
  header a { display:flex; align-items:center; gap:10px; text-decoration:none; }
  .mark { width:40px; height:40px; border-radius:50%; background:var(--foglia); border:2px solid var(--prato);
          display:flex; align-items:center; justify-content:center; }
  .word { font-size:28px; font-weight:800; letter-spacing:-.5px; color:var(--prato); }
  h1 { font-size:26px; line-height:1.2; margin:16px 0 6px; }
  h2 { font-size:20px; margin:32px 0 8px; color:var(--prato); }
  h3 { font-size:17px; margin:24px 0 6px; }
  p, li { color:var(--bosco); }
  a { color:var(--prato); }
  .meta { color:var(--muted); font-size:14px; margin:0 0 8px; }
  .nota { background:var(--foglia); border-radius:12px; padding:12px 14px; font-size:14px; color:var(--bosco); }
  .tab { overflow-x:auto; margin:12px 0; }
  table { border-collapse:collapse; width:100%; font-size:14px; }
  th, td { text-align:left; vertical-align:top; padding:8px 10px; border-bottom:1px solid var(--linea); }
  th { background:var(--foglia); }
  footer { max-width:760px; margin:16px auto 0; color:var(--muted); font-size:13px; text-align:center; }
"""

PAW = ('<svg width="22" height="22" viewBox="0 0 32 32" fill="currentColor" style="color:var(--prato)" aria-hidden="true">'
       '<ellipse cx="7" cy="13" rx="3" ry="4"/><ellipse cx="12.5" cy="7" rx="3" ry="4"/><ellipse cx="19.5" cy="7" rx="3" ry="4"/>'
       '<ellipse cx="25" cy="13" rx="3" ry="4"/><path d="M16 14c-5 0-9 5-9 9 0 3 2.5 4 5 4 1.6 0 2.6-.8 4-.8s2.4.8 4 .8c2.5 0 5-1 5-4 0-4-4-9-9-9z"/></svg>')


def pagina(titolo, intro, corpo_md):
    corpo = markdown.markdown(corpo_md, extensions=["tables"])
    corpo = corpo.replace("<table>", '<div class="tab"><table>').replace("</table>", "</table></div>")
    return f"""<!doctype html>
<html lang="it">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(titolo)} · Doggy</title>
<meta name="description" content="{html.escape(titolo)} dell'app Doggy, la community dei cani di quartiere.">
<style>{STYLE}</style>
</head>
<body>
<main>
  <header><a href="../" aria-label="Doggy, pagina iniziale"><span class="mark">{PAW}</span><span class="word">doggy</span></a></header>
  <h1>{html.escape(titolo)}</h1>
  {intro}
  {corpo}
</main>
<footer>Doggy · <a href="../privacy/">Privacy</a> · <a href="../condizioni/">Condizioni d'uso</a> · <a href="mailto:ciao@doggy-app.it">ciao@doggy-app.it</a><br>
<!-- generata da scripts/pagine-legali.py: non modificare a mano --></footer>
</body>
</html>
"""


def senza_note(md):
    # via le citazioni per il team (righe che iniziano con "> ")
    return "\n".join(r for r in md.split("\n") if not r.startswith("> "))


def sezioni(md, da=None, fino=None):
    if da:
        md = md[md.index(da):]
    if fino and fino in md:
        md = md[:md.index(fino)]
    return md.strip() + "\n"


def main():
    app = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "..", "doggy-app")
    privacy = open(os.path.join(app, "docs/PRIVACY-POLICY.md"), encoding="utf-8").read()
    privacy = sezioni(senza_note(privacy), da="## Chi siamo", fino="### Da verificare con il legale")
    # la bozza ha la data nel testo ("Bozza del 29/10/2026 ...")
    intro_p = ('<p class="meta">Versione per la prova dell\'app (beta). Va rivista da un legale prima dell\'uscita '
               'pubblica sugli store.</p>')
    with open(os.path.join(ROOT, "privacy/index.html"), "w", encoding="utf-8") as f:
        f.write(pagina("Privacy policy", intro_p, privacy))

    cond = open(os.path.join(app, "docs/CONDIZIONI-USO.md"), encoding="utf-8").read()
    cond = sezioni(senza_note(cond), da="## Chi può iscriversi", fino="## Da decidere e da verificare con il legale")
    intro_c = ('<p class="meta">Versione per la prova dell\'app (beta). Va rivista da un legale prima dell\'uscita '
               'pubblica sugli store.</p>'
               '<p>Queste sono le regole che accetti quando ti iscrivi a Doggy. Chi crea il profilo di un cane ne accetta '
               'in più gli impegni del referente. Come trattiamo i tuoi dati lo spiega la <a href="../privacy/">privacy '
               'policy</a>.</p>')
    with open(os.path.join(ROOT, "condizioni/index.html"), "w", encoding="utf-8") as f:
        f.write(pagina("Condizioni d'uso", intro_c, cond))
    print("privacy/index.html e condizioni/index.html aggiornate")


if __name__ == "__main__":
    main()
