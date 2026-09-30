"""Indigesto - costruzione della webapp.
Uso: python3 build.py dati.json modello.html uscita.html VERSIONE "data di aggiornamento" [--rev N] [--repo proprietario/nome]
Il modello contiene logo, icone e foglio di stile, con i segnaposto /*DATA*/, {{VER}}, {{AGG}}, {{NLP}},
{{AGGISO}}, {{REV}} e {{URL}}. --repo indica il repository GitHub da cui la webapp scarica gli aggiornamenti;
senza --repo la webapp non cerca aggiornamenti e il pulsante non compare.
--rev è il numero progressivo dei dati (AAAAMMGGnn); di default è la data di aggiornamento con nn = 01.
prepara() e i dizionari GROUPS e LABEL sono usati anche da pubblica.py."""
import json, sys, re, os

GROUPS = [
    ("Titoli edilizi", ["pdc", "silenzio-assenso", "silenzio-rigetto", "edilizia-libera", "cila", "scia", "scia-alternativa", "agibilita"]),
    ("Stato legittimo e interventi", ["stato-legittimo", "ante67", "ristrutturazione", "pertinenze", "destinazione-uso", "distanze", "tolleranze"]),
    ("Abusi e sanatoria", ["abusi-demolizione", "acquisizione", "fiscalizzazione", "sanatoria-36", "sanatoria-36bis", "condono"]),
    ("Vincoli, oneri e pianificazione", ["paesaggio", "oneri", "pianificazione", "lottizzazione"]),
    ("Autotutela e tutela dei terzi", ["autotutela", "terzi"]),
]
LABEL = {
    "stato-legittimo": "Stato legittimo", "ante67": "Immobili ante ’67", "pdc": "Permesso di costruire",
    "silenzio-assenso": "Silenzio assenso", "silenzio-rigetto": "Silenzio rigetto e inadempimento",
    "edilizia-libera": "Edilizia libera", "cila": "CILA e CILAS", "scia": "SCIA", "scia-alternativa": "SCIA alternativa",
    "agibilita": "Agibilità e abitabilità", "abusi-demolizione": "Abusi edilizi e demolizione", "acquisizione": "Inottemperanza e acquisizione",
    "fiscalizzazione": "Fiscalizzazione", "sanatoria-36": "Accertamento di conformità (art. 36)",
    "sanatoria-36bis": "Sanatoria Salva Casa (art. 36-bis)", "condono": "Condono edilizio", "tolleranze": "Tolleranze costruttive",
    "ristrutturazione": "Ristrutturazione e demolizione-ricostruzione", "pertinenze": "Pertinenze, volumi tecnici e verande",
    "destinazione-uso": "Mutamento di destinazione d’uso", "distanze": "Distanze tra fabbricati", "paesaggio": "Vincolo paesaggistico",
    "oneri": "Contributo di costruzione", "autotutela": "Annullamento d’ufficio dei titoli", "terzi": "Impugnazione da parte dei terzi",
    "pianificazione": "Pianificazione urbanistica", "lottizzazione": "Lottizzazione abusiva",
}
ORDER = [c for g in GROUPS for c in g[1]]
assert set(ORDER) == set(LABEL)
MESI = ['gennaio', 'febbraio', 'marzo', 'aprile', 'maggio', 'giugno', 'luglio', 'agosto', 'settembre', 'ottobre', 'novembre', 'dicembre']
FORMATO = 1
# chiave della cifratura leggera di dati.json: non protegge da chi possiede la webapp, che la contiene,
# ma rende il file illeggibile e non ricercabile su GitHub. Deve coincidere in build.py e pubblica.py.
CHIAVE = int(os.environ['INDIGESTO_CHIAVE'])


def flusso(n, rev):
    s = (CHIAVE ^ (rev % 4294967296)) & 0xffffffff or 1
    out = bytearray(n)
    for i in range(n):
        s ^= (s << 13) & 0xffffffff; s ^= s >> 17; s ^= (s << 5) & 0xffffffff
        out[i] = s & 255
    return out


def cifra(txt, rev):
    import base64
    b = txt.encode('utf-8'); k = flusso(len(b), rev)
    return base64.b64encode(bytes(x ^ y for x, y in zip(b, k))).decode()


def prepara(rows):
    """Ordina argomenti e sentenze e toglie i campi vuoti, come nella webapp."""
    for r in rows:
        r['c'] = sorted(r['c'], key=ORDER.index)
        r['c2'] = [c for c in sorted(r.get('c2', []), key=ORDER.index) if c not in r['c']]
        for f in ('lp', 'lt', 'ls', 'no', 'ag'):
            if f in r and not r[f]:
                del r[f]
    rows.sort(key=lambda r: (r['d'], r['o'], r['n']), reverse=True)
    return rows


def data_iso(agg):
    """«30 settembre 2026» → «2026-09-30»."""
    m = re.fullmatch(r'(\d{1,2})º? (\w+) (\d{4})', agg.strip())
    if not m or m.group(2) not in MESI:
        raise SystemExit('data di aggiornamento non riconosciuta: ' + agg)
    return f'{m.group(3)}-{MESI.index(m.group(2)) + 1:02d}-{int(m.group(1)):02d}'


def data_it(iso):
    y, m, d = iso.split('-')
    return f'{int(d)} {MESI[int(m) - 1]} {y}'


def url_dati(repo):
    """Indirizzi da cui la webapp legge versione.json e dati.json: prima GitHub, poi la copia jsDelivr."""
    if not repo:
        return None
    if not re.fullmatch(r'[A-Za-z0-9-]{1,39}/[A-Za-z0-9._-]{1,100}', repo):
        raise SystemExit('repository non valido: ' + repo)
    return [f'https://raw.githubusercontent.com/{repo}/main/', f'https://cdn.jsdelivr.net/gh/{repo}@main/']


if __name__ == '__main__':
    args = sys.argv[1:]
    opt = {}
    for k in ('--rev', '--repo'):
        if k in args:
            i = args.index(k); opt[k] = args[i + 1]; del args[i:i + 2]
    DATI, MOD, OUT, VER, AGG = args[:5]
    iso = data_iso(AGG)
    rev = int(opt.get('--rev') or iso.replace('-', '') + '01')
    assert str(rev).startswith(iso.replace('-', '')), 'il progressivo deve cominciare con la data di aggiornamento'
    rows = prepara(json.load(open(DATI)))
    data = ('var ROWS=' + json.dumps(rows, ensure_ascii=False, separators=(',', ':')) + ';\nvar LABEL=' +
            json.dumps(LABEL, ensure_ascii=False, separators=(',', ':')) + ';\nvar GROUPS=' +
            json.dumps(GROUPS, ensure_ascii=False, separators=(',', ':')) + ';\n').replace('</', '<\\/')
    t = open(MOD).read()
    assert t.count('/*DATA*/') == 1
    t = t.replace('/*DATA*/', data).replace('{{VER}}', VER).replace('{{AGG}}', AGG)
    t = t.replace('{{AGGISO}}', iso).replace('{{REV}}', str(rev)).replace('{{CHIAVE}}', str(CHIAVE))
    t = t.replace('{{URL}}', json.dumps(url_dati(opt.get('--repo'))))
    t = t.replace('{{NLP}}', str(sum(1 for r in rows if r.get('lp'))))
    assert '{{' not in t
    open(OUT, 'w').write(t)
    print('sentenze', len(rows), 'commentate LP', sum(1 for r in rows if r.get('lp')), 'progressivo', rev,
          'aggiornamenti', opt.get('--repo') or 'disattivati', 'byte', len(t.encode()))
