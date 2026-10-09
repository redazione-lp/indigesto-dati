"""Controllo dei dati di Indigesto prima della pubblicazione.
Applica le stesse regole con cui la webapp accetta un aggiornamento, più i controlli sul progressivo.
Uso: python3 controlla_dati.py [versione.json pubblicata in precedenza]
v1.8: controlla anche dati-cost.json (sentenze della Corte costituzionale) e gli archivi dei testi integrali testi/AAAA.json,
quando versione.json li dichiara."""
import json, re, sys, os, hashlib, base64

err = []
def e(m): err.append(m)

K = os.environ.get('INDIGESTO_CHIAVE')
def decifra(b, rev):
    s = (int(K) ^ (rev % 4294967296)) & 0xffffffff or 1; o = bytearray(len(b))
    for i, x in enumerate(b):
        s ^= (s << 13) & 0xffffffff; s ^= s >> 17; s ^= (s << 5) & 0xffffffff; o[i] = x ^ (s & 255)
    return bytes(o)
v = json.load(open('versione.json', encoding='utf-8'))
prev_v = json.load(open(sys.argv[1], encoding='utf-8')) if len(sys.argv) > 1 and os.path.getsize(sys.argv[1]) else {}


def controlla_dati(nome, attesi, corte):
    """attesi: blocco di versione.json con rev, aggiornata, n, sha256. Restituisce l'elenco delle schede o None."""
    if not os.path.exists(nome): e(f'{nome} dichiarato in versione.json ma assente'); return None
    txt = open(nome, encoding='utf-8').read()
    d = json.loads(txt)
    if attesi.get('sha256') != hashlib.sha256(txt.encode()).hexdigest(): e(f'impronta sha256 di {nome} non corrisponde')
    if not (d.get('formato') == 1 and d.get('rev') == attesi.get('rev') and d.get('aggiornata') == attesi.get('aggiornata') and isinstance(d.get('dati'), str) and d.get('cifrato') == 1):
        e(f'involucro di {nome} non valido'); return None
    if not K: return None
    d = json.loads(decifra(base64.b64decode(d['dati']), d['rev']).decode('utf-8'))
    return controlla_contenuto(nome, d, attesi, corte)


def controlla_contenuto(nome, d, v, corte):
    D = re.compile(r'^\d{4}-\d{2}-\d{2}$')
    UG = re.compile(r'^https://(mdp|www)\.giustizia-amministrativa\.it/[^\s"\'<>\\]*$')
    UC = re.compile(r'^https://www\.cortecostituzionale\.it/[^\s"\'<>\\]*$')
    UL = re.compile(r'^https://www\.lavoripubblici\.it/[^\s"\'<>\\]*$')
    S = lambda x, n: isinstance(x, str) and len(x) <= n

    if d.get('formato') != 1 or v.get('formato', 1) != 1: e(f'formato di {nome} diverso da 1')
    if d.get('rev') != v.get('rev') or not isinstance(d.get('rev'), int): e(f'progressivo di {nome} e versione.json diverso')
    if d.get('aggiornata') != v.get('aggiornata') or not D.match(str(d.get('aggiornata'))): e('data di aggiornamento non valida')
    if not str(d.get('rev', '')).startswith(str(d.get('aggiornata', '')).replace('-', '')): e('il progressivo non comincia con la data')
    if v.get('n') != len(d.get('ROWS', [])): e(f'numero di sentenze di {nome} non corrisponde a versione.json')
    L, G, R = d.get('LABEL', {}), d.get('GROUPS', []), d.get('ROWS', [])
    if not isinstance(L, dict) or not L or len(L) > 200: e('argomenti assenti o più di 200')
    if not isinstance(G, list) or not G or len(G) > 30 or any(not (isinstance(g, list) and len(g) == 2 and S(g[0], 80) and g[0] and isinstance(g[1], list) and g[1]) for g in G): e('gruppi non validi (al massimo 30, ciascuno con nome e argomenti)')
    if not isinstance(R, list) or not R or len(R) > 20000: e('elenco delle sentenze assente o oltre 20000')
    for k, x in L.items():
        if not re.match(r'^[a-z0-9-]{1,40}$', k) or not S(x, 80) or not x: e('argomento non valido ' + k)
    seen = [c for g in G for c in g[1]]
    if sorted(seen) != sorted(L) or len(seen) != len(set(seen)): e('gruppi e argomenti non coincidono')
    ecli = set()
    for i, r in enumerate(R):
        w = r.get('e', f'riga {i}')
        ok = (S(r.get('o'), 120) and r.get('o') and re.match(r'^\d{1,6}$', str(r.get('n'))) and re.match(r'^\d{4}$', str(r.get('y')))
              and D.match(str(r.get('d'))) and S(r.get('es'), 800) and r.get('es') and S(w, 80) and re.match(r'^ECLI:IT:[A-Z0-9:.]+$', w)
              and S(r.get('u'), 600) and (UG.match(r['u']) or UC.match(r['u'])))
        if not ok: e('campi obbligatori non validi ' + w); continue
        if w in ecli: e('ECLI duplicato ' + w)
        ecli.add(w)
        c = r.get('c') or []
        if not c or len(c) > 12 or any(x not in L for x in c) or len(set(c)) != len(c): e('argomenti non validi ' + w)
        c2 = r.get('c2', [])
        if not isinstance(c2, list) or len(c2) > 30 or any(x not in L for x in c2) or len(set(c2)) != len(c2): e('vedi anche non valido ' + w)
        if 'se' in r and not S(r['se'], 80): e('sede troppo lunga ' + w)
        if 'z' in r and not S(r['z'], 40): e('sezione troppo lunga ' + w)
        if 'lt' in r and not S(r['lt'], 400): e('titolo del commento troppo lungo ' + w)
        if 'nr' in r and not (isinstance(r['nr'], list) and len(r['nr']) <= 80 and all(S(x, 400) for x in r['nr'])): e('norme non valide (al massimo 80, ciascuna entro 400 caratteri) ' + w)
        for x in c:
            if not (S(r.get('m', {}).get(x), 4000) and r['m'][x] and S(r.get('t', {}).get(x), 400) and r['t'][x]): e(f'massima o titolo mancante {w} {x}')
        for f in ('lp', 'ls'):
            if f in r and not (S(r[f], 600) and UL.match(r[f])): e(f'collegamento {f} non valido ' + w)
        if 'ag' in r and not D.match(str(r['ag'])): e('data di inserimento non valida ' + w)
        if 'no' in r and not S(r['no'], 6000): e('nota troppo lunga ' + w)
        # i limiti replicano idgValida della webapp: un campo che la webapp rifiuta scarterebbe l'intero aggiornamento
        # dalla v1.6 (regola allineata a indigesto.py pubblica nella v1.7): tipi della nota e orientamento non uniforme (la webapp 1.6 rifiuta l'intero aggiornamento se non sono validi)
        if 'nt' in r and not (isinstance(r['nt'], list) and len(r['nt']) <= 3 and len(set(r['nt'])) == len(r['nt']) and all(t in ('aggiornamento', 'collegate', 'contrasto') for t in r['nt'])): e('nt non valido ' + w)
        if 'kon' in r and not isinstance(r['kon'], bool): e('kon non booleano ' + w)
        if 'nt' in r and 'kon' in r and r['kon'] != ('contrasto' in r['nt']): e('kon e nt non coincidono ' + w)
        if r.get('no') and ('nt' not in r or 'kon' not in r): e('nota senza nt o kon ' + w)
        if not r.get('no') and ('nt' in r or 'kon' in r): e('nt o kon su una scheda senza nota ' + w)
        if corte:
            # v1.8: regole proprie delle schede della Corte costituzionale
            if r.get('o') != 'Corte costituzionale' or r.get('gz') not in ('incidentale', 'principale', 'conflitto') or r.get('tp') not in ('S', 'O'):
                e('scheda della Corte con organo, gz o tp non validi ' + w)
            if r.get('e') != f"ECLI:IT:COST:{r.get('y')}:{r.get('n')}" or r.get('u') != f"https://www.cortecostituzionale.it/scheda-pronuncia/{r.get('y')}/{r.get('n')}":
                e('ECLI o indirizzo della scheda della Corte non coerenti ' + w)
        elif r.get('o') == 'Corte costituzionale':
            e('scheda della Corte dentro dati.json ' + w)
    return R


R = controlla_dati('dati.json', v, False)
if prev_v:
    if v.get('rev', 0) < prev_v.get('rev', 0) or (v.get('rev') == prev_v.get('rev') and v.get('sha256') != prev_v.get('sha256')):
        e(f'il progressivo {v.get("rev")} non supera quello pubblicato {prev_v.get("rev")}')
    if v.get('n', 0) < prev_v.get('n', 0) * 0.95: e(f'le sentenze scendono da {prev_v.get("n")} a {v.get("n")}')
    # i blocchi già pubblicati non possono sparire
    for k in ('cost', 'testi'):
        if k in prev_v and k not in v: e(f'versione.json ha perso il blocco {k} (pubblicare con indigesto.py 1.8 o successivo)')
RC, ecli = None, set()
if 'cost' in v:
    c = v['cost']
    RC = controlla_dati('dati-cost.json', c, True)
    pc = prev_v.get('cost', {})
    if pc:
        if c.get('rev', 0) < pc.get('rev', 0) or (c.get('rev') == pc.get('rev') and c.get('sha256') != pc.get('sha256')): e('progressivo dei dati della Corte non cresce')
        if c.get('n', 0) < pc.get('n', 0) * 0.95: e(f'le sentenze della Corte scendono da {pc.get("n")} a {c.get("n")}')
    if c.get('ultima') and not re.match(r'^\d{4}/\d{1,4}$', c['ultima']): e('cost.ultima non valida')
elif os.path.exists('dati-cost.json'):
    e('dati-cost.json presente ma non dichiarato in versione.json')
for x in (R or []) + (RC or []): ecli.add(x.get('e'))
if 'testi' in v:
    import gzip
    if not isinstance(v['testi'], dict): e('blocco testi non valido')
    for anno, b in sorted(v['testi'].items()):
        f = os.path.join('testi', f'{anno}.json')
        if not re.match(r'^\d{4}$', anno) or not os.path.exists(f): e(f'archivio dei testi {anno} dichiarato ma assente'); continue
        txt = open(f, encoding='utf-8').read()
        if len(txt) > 15000000: e(f'archivio dei testi {anno} oltre 15 MB')
        if b.get('sha256') != hashlib.sha256(txt.encode()).hexdigest(): e(f'impronta dei testi {anno} non corrisponde')
        a = json.loads(txt)
        if not (a.get('formato') == 1 and a.get('anno') == anno and a.get('rev') == b.get('rev') and a.get('cifrato') == 1 and a.get('gzip') == 1 and isinstance(a.get('dati'), str)):
            e(f'involucro dei testi {anno} non valido'); continue
        pb = prev_v.get('testi', {}).get(anno)
        if pb and (b.get('rev', 0) < pb.get('rev', 0) or (b.get('rev') == pb.get('rev') and b.get('sha256') != pb.get('sha256'))): e(f'progressivo dei testi {anno} non cresce')
        if K:
            try: T = json.loads(gzip.decompress(decifra(base64.b64decode(a['dati']), a['rev'])).decode('utf-8'))
            except Exception: e(f'archivio dei testi {anno} illeggibile'); continue
            if not isinstance(T, dict) or len(T) != b.get('n'): e(f'numero di testi {anno} non corrisponde'); continue
            for k2, t in T.items():
                if not (isinstance(t, str) and 200 <= len(t) <= 400000) or '<' in t.replace('<<', ''): e(f'testo non valido {k2}')
                if k2.split(':')[3:4] != [anno]: e(f'testo {k2} nell\'archivio dell\'anno sbagliato')
                if ecli and k2 not in ecli: e(f'testo {k2} senza scheda in raccolta')
for f in (os.listdir('testi') if os.path.isdir('testi') else []):
    if f.endswith('.json') and f[:-5] not in v.get('testi', {}): e(f'testi/{f} presente ma non dichiarato in versione.json')
if err: print('\n'.join(err))
elif not K: print(f'involucri validi, progressivo {v.get("rev")} (contenuto non controllato: manca INDIGESTO_CHIAVE)')
else: print(f'dati validi, {len(R)} sentenze amministrative' + (f', {len(RC)} della Corte' if RC is not None else '') + (f', testi in {len(v["testi"])} archivi' if 'testi' in v else '') + f', progressivo {v.get("rev")}')
sys.exit(1 if err else 0)
