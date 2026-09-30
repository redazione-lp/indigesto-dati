"""Regesto Giurisprudenza - applica correzioni e aggiunte ai dati.

Uso: python3 applica.py <dati-base.json> <cartella-verifiche> <uscita.json> [--solo aggiornamento-AAAA-MM-GG.json ...]
Senza --solo ricostruisce la raccolta dalla v1.0 con tutte le tornate di verifica, in quest'ordine: vincoli, titoli,
stato, abusi, coordinamento; poi aggiunte; poi correzioni finali e seconda lettura.
Con --solo parte dai dati correnti e applica soltanto i file indicati, nel formato degli aggiornamenti periodici
{"aggiunte": [schede nuove, con ag = data di inserimento], "correzioni": [come nei file di correzione]}.
Convenzioni dei file di correzione (LEGGIMI e rapporti delle tornate):
- argomento: argomento principale a cui si riferiscono m e t;
- sposta_a: sposta l'argomento principale (massima e titolo compresi);
- escludi + argomento: toglie quell'argomento principale; se è l'unico, esclude la sentenza;
- aggiungi_argomento: aggiunge l'argomento come principale con m e t;
- m, t per argomento; es, nr, no, lp, lt, ls, c2, se sostituiscono il campo della scheda.
"""
import json, re, sys, collections

ARGS = sys.argv[1:]
SOLO = []
if '--solo' in ARGS:
    i = ARGS.index('--solo'); SOLO = ARGS[i + 1:]; ARGS = ARGS[:i]
    assert SOLO, 'indicare almeno un file dopo --solo'
BASE, DIR, OUT = ARGS[0], ARGS[1].rstrip('/') + '/', ARGS[2]
CORR = ['verifica-vincoli-correzioni.json', 'verifica-titoli-correzioni.json', 'verifica-stato-correzioni.json',
        'verifica-abusi-correzioni.json', 'verifica-vincoli-coordinamento.json']
POST = ['verifica-finale-correzioni.json', 'verifica-seconda-lettura.json']
AGG = ['verifica-titoli-aggiunte.json', 'verifica-stato-aggiunte.json', 'verifica-abusi-aggiunte.json',
       'verifica-finale-aggiunte.json']
SEDI = {'tar_rm': 'Roma', 'tar_na': 'Napoli', 'tar_sa': 'Salerno', 'tar_mi': 'Milano', 'tar_bs': 'Brescia',
        'tar_ve': 'Venezia', 'tar_ba': 'Bari', 'tar_le': 'Lecce', 'tar_pa': 'Palermo', 'tar_ct': 'Catania',
        'tar_ge': 'Genova', 'tar_to': 'Torino', 'tar_fi': 'Firenze', 'tar_bo': 'Bologna'}

rows = json.load(open(BASE))
log = collections.Counter()
touched = collections.defaultdict(list)


def find(x):
    c = [r for r in rows if r['n'] == x['n'] and r['y'] == x['y']]
    if len(c) > 1:
        c = [r for r in c if r['o'] == x['o']]
    if len(c) != 1:
        raise SystemExit(f"scheda non trovata o ambigua: {x['o']} {x['n']}/{x['y']}")
    return c[0]


def applica_file(f, X=None):
    if X is None:
        try:
            X = json.load(open(DIR + f))
        except FileNotFoundError:
            return
    for x in X:
        if x.get('esito_verifica') == 'OK':
            continue
        r = find(x)
        a = x['argomento']
        if x.get('escludi'):
            if a in r['c'] and len(r['c']) > 1:
                r['c'].remove(a); r['m'].pop(a, None); r['t'].pop(a, None); log['argomento tolto'] += 1
            else:
                rows.remove(r); log['sentenza esclusa'] += 1
            continue
        if x.get('aggiungi_argomento') and a not in r['c']:
            r['c'].append(a); log['argomento aggiunto'] += 1
        if a not in r['c']:
            raise SystemExit(f"argomento {a} assente in {r['n']}/{r['y']} ({f})")
        tgt = a
        if x.get('sposta_a'):
            tgt = x['sposta_a']
            r['c'] = list(dict.fromkeys([tgt if c == a else c for c in r['c']]))
            if a in r['m']: r['m'][tgt] = r['m'].pop(a)
            if a in r['t']: r['t'][tgt] = r['t'].pop(a)
            log['argomento spostato'] += 1
        if 'm' in x: r['m'][tgt] = x['m']
        if 't' in x: r['t'][tgt] = x['t']
        for k in ('es', 'nr', 'no', 'lp', 'lt', 'ls', 'c2', 'se', 'z', 'd', 'e'):
            if k in x:
                if k in ('no', 'es', 'nr', 'c2') and any(p != f for p in touched[(r['n'], r['y'], k)]):
                    log[f'campo {k} riscritto da due file'] += 1
                touched[(r['n'], r['y'], k)].append(f)
                r[k] = x[k]
        log['correzioni applicate'] += 1


def aggiungi(A, f):
    for x in A:
        if any(r['n'] == x['n'] and r['y'] == x['y'] and r['o'] == x['o'] or r['e'] == x.get('e') for r in rows):
            raise SystemExit(f"aggiunta già presente: {x['o']} {x['n']}/{x['y']} ({f})")
        x = {k: v for k, v in x.items() if not k.startswith('_')}
        rows.append(x); log['sentenze aggiunte'] += 1


if SOLO:
    for f in SOLO:
        U = json.load(open(DIR + f))
        assert isinstance(U, dict) and set(U) <= {'aggiunte', 'correzioni'}, f'formato non valido: {f}'
        for x in U.get('aggiunte', []):
            assert re.fullmatch(r'\d{4}-\d{2}-\d{2}', x.get('ag', '')), f"manca la data di inserimento ag: {x.get('n')}/{x.get('y')}"
        aggiungi(U.get('aggiunte', []), f)
        applica_file(f, U.get('correzioni', []))
else:
    for f in CORR:
        applica_file(f)
    for f in AGG:
        try:
            aggiungi(json.load(open(DIR + f)), f)
        except FileNotFoundError:
            continue
    # correzioni sulle sentenze aggiunte e seconda lettura (tornata 6 e successive)
    for f in POST:
        applica_file(f)

# normalizzazioni
TXT = ('m', 't')
INTERNE = [r'\s*Pubblicata solo in PDF; letta con estrazione del testo\.', r',? già in raccolta', r' \(non in raccolta\)']


def tipo(s):
    s = re.sub(r"(\w)'(\w)", '\\1\u2019\\2', s)          # apostrofo tra lettere
    s = re.sub(r"(^|[\s(«])'(\d\d)\b", '\\1\u2019\\2', s)  # ante '67
    return s


def nkey(n):
    return re.sub(r'[\s,]+', ' ', n.replace('codice civile', 'c.c.')).strip().lower()


for r in rows:
    for k in TXT:
        r[k] = {c: tipo(v) for c, v in r[k].items()}
    for k in ('es', 'no', 'lt'):
        if r.get(k):
            v = r[k]
            if k == 'no':
                for p in INTERNE: v = re.sub(p, '', v)
                v = v.strip()
            r[k] = tipo(v)
        if k in r and not r[k]:
            del r[k]
    # norme: formato, doppioni, generiche assorbite da quelle con comma
    nr = []
    for n in r.get('nr', []):
        n = re.sub(r'^(art\. [\w-]+), (d\.P\.R\.|D\.Lgs\.|Legge|c\.p\.a\.)', r'\1 \2', n).replace('codice civile', 'c.c.')
        if nkey(n) not in [nkey(z) for z in nr]: nr.append(n)
    out = []
    for n in nr:
        m = re.match(r'^(art\. [\w-]+) (.+)$', n)
        if m and any(z != n and z.startswith(m.group(1) + ',') and z.endswith(m.group(2)) for z in nr):
            log['norma generica assorbita'] += 1; continue
        out.append(n)
    r['nr'] = out
    if r['o'].startswith('TAR') and not r.get('se'):
        s = re.search(r'schema=(\w+)', r['u'])
        if s and s.group(1) in SEDI: r['se'] = SEDI[s.group(1)]; log['sede completata'] += 1
    if r['o'] == 'CGARS': r['z'] = ''
    r.setdefault('se', '')
    r['c2'] = [c for c in dict.fromkeys(r.get('c2', [])) if c not in r['c']]

rows.sort(key=lambda r: (r['d'], r['o'], r['n']), reverse=True)
json.dump(rows, open(OUT, 'w'), ensure_ascii=False, indent=1)
for k, v in sorted(log.items()): print(f'{k}: {v}')
print('sentenze:', len(rows))
