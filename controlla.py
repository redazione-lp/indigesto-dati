"""Controlli automatici sui dati del Regesto Giurisprudenza. Uso: python3 controlla.py dati.json"""
import json, re, sys, collections
SLUG = ["pdc","silenzio-assenso","silenzio-rigetto","edilizia-libera","cila","scia","scia-alternativa","agibilita","stato-legittimo","ante67","ristrutturazione","pertinenze","destinazione-uso","distanze","tolleranze","abusi-demolizione","acquisizione","fiscalizzazione","sanatoria-36","sanatoria-36bis","condono","paesaggio","oneri","pianificazione","lottizzazione","autotutela","terzi"]
rows = json.load(open(sys.argv[1]))
E, W = [], collections.Counter()
seen = set()
for r in rows:
    id_ = f"{r['o']} {r['n']}/{r['y']}"
    k = (r['o'], r['se'], r['n'], r['y'])
    if k in seen: E.append(f'{id_}: sentenza doppia')
    seen.add(k)
    for f in ('o','n','y','d','e','u','c','m','t','es'):
        if not r.get(f): E.append(f'{id_}: campo {f} vuoto')
    if not re.match(r'^\d{4}-\d\d-\d\d$', r['d']): E.append(f'{id_}: data {r["d"]}')
    if r['o'] != 'Adunanza Plenaria' and r['d'][:4] != r['y']: W['anno diverso dalla data'] += 1
    if not re.match(r'^ECLI:IT:(CDS|CGARS|TAR[A-Z]+):\d{4}:\d+[A-Z]+$', r['e']): E.append(f'{id_}: ECLI {r["e"]}')
    if not r['u'].startswith('https://mdp.giustizia-amministrativa.it/'): E.append(f'{id_}: indirizzo del portale')
    for f in ('lp','ls'):
        if r.get(f) and not r[f].startswith('https://www.lavoripubblici.it/'): E.append(f'{id_}: indirizzo {f}')
    if r['o'].startswith('TAR') and not r['se']: E.append(f'{id_}: sede TAR mancante')
    for c in r['c'] + r['c2']:
        if c not in SLUG: E.append(f'{id_}: argomento {c} inesistente')
    if set(r['m']) != set(r['c']) or set(r['t']) != set(r['c']): E.append(f'{id_}: massime e argomenti non allineati')
    for c, m in r['m'].items():
        if ':' in m: E.append(f'{id_} [{c}]: due punti nella massima')
        if re.search(r'\bconcret|\bchiar[oaie]\b|\bchiarezz', m, re.I): E.append(f'{id_} [{c}]: parola vietata')
        if "'" in m: W['apostrofo diritto'] += 1
        if len(m) > 450: W['massime oltre 450 caratteri'] += 1
        if len(m) > 600: E.append(f'{id_} [{c}]: massima oltre 600 caratteri ({len(m)})')
        if len(m) < 200: W['massime sotto 200 caratteri'] += 1
    for t in r['t'].values():
        if ':' in t: E.append(f'{id_}: due punti nel titolo')
    if r.get('no') and re.search(r'già in raccolta|letta con estrazione', r['no']): E.append(f'{id_}: annotazione interna nella nota')
    if len({re.sub(r'\W+',' ',n).lower() for n in r['nr']}) != len(r['nr']): E.append(f'{id_}: norme ripetute')
cnt = collections.Counter(c for r in rows for c in r['c'])
print('sentenze', len(rows), 'massime', sum(len(r['c']) for r in rows))
print('per argomento', {s: cnt[s] for s in SLUG})
print('sotto dieci', [s for s in SLUG if cnt[s] < 10])
print('avvisi', dict(W))
print('errori', len(E)); print('\n'.join(E[:60]))
sys.exit(1 if E else 0)
