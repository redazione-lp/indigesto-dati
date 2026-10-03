"""Controllo dei dati di Indigesto prima della pubblicazione.
Applica le stesse regole con cui la webapp accetta un aggiornamento, più i controlli sul progressivo.
Uso: python3 controlla_dati.py [versione.json pubblicata in precedenza]"""
import json, re, sys, os, hashlib, base64

err = []
def e(m): err.append(m)

txt = open('dati.json', encoding='utf-8').read()
d, v = json.loads(txt), json.load(open('versione.json', encoding='utf-8'))
if v.get('sha256') != hashlib.sha256(txt.encode()).hexdigest(): e('impronta sha256 di dati.json non corrisponde')
if d.get('cifrato') == 1:
    # dati.json è cifrato: senza la chiave (segreto INDIGESTO_CHIAVE del repository) si controllano solo involucro e impronta
    K = os.environ.get('INDIGESTO_CHIAVE')
    if not K:
        if not (d.get('formato') == 1 and d.get('rev') == v.get('rev') and d.get('aggiornata') == v.get('aggiornata') and isinstance(d.get('dati'), str)):
            e('involucro di dati.json non valido')
        print('\n'.join(err) if err else f'involucro valido, progressivo {d.get("rev")} (contenuto non controllato: manca INDIGESTO_CHIAVE)')
        sys.exit(1 if err else 0)
    b = base64.b64decode(d['dati']); s = (int(K) ^ (d['rev'] % 4294967296)) & 0xffffffff or 1; o = bytearray(len(b))
    for i, x in enumerate(b):
        s ^= (s << 13) & 0xffffffff; s ^= s >> 17; s ^= (s << 5) & 0xffffffff; o[i] = x ^ (s & 255)
    d = json.loads(o.decode('utf-8'))
D = re.compile(r'^\d{4}-\d{2}-\d{2}$')
UG = re.compile(r'^https://(mdp|www)\.giustizia-amministrativa\.it/[^\s"\'<>\\]*$')
UC = re.compile(r'^https://www\.cortecostituzionale\.it/[^\s"\'<>\\]*$')
UL = re.compile(r'^https://www\.lavoripubblici\.it/[^\s"\'<>\\]*$')
S = lambda x, n: isinstance(x, str) and len(x) <= n

if d.get('formato') != 1 or v.get('formato') != 1: e('formato diverso da 1')
if d.get('rev') != v.get('rev') or not isinstance(d.get('rev'), int): e('progressivo di dati.json e versione.json diverso')
if d.get('aggiornata') != v.get('aggiornata') or not D.match(str(d.get('aggiornata'))): e('data di aggiornamento non valida')
if not str(d.get('rev', '')).startswith(str(d.get('aggiornata', '')).replace('-', '')): e('il progressivo non comincia con la data')
if v.get('n') != len(d.get('ROWS', [])): e('numero di sentenze in versione.json non corrisponde')
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
if len(sys.argv) > 1:
    prev = json.load(open(sys.argv[1], encoding='utf-8'))
    if d.get('rev', 0) <= prev['rev']: e(f'il progressivo {d.get("rev")} non supera quello pubblicato {prev["rev"]}')
    if len(R) < prev['n'] * 0.95: e(f'le sentenze scendono da {prev["n"]} a {len(R)}')
print('\n'.join(err) if err else f'dati validi, {len(R)} sentenze, progressivo {d.get("rev")}')
sys.exit(1 if err else 0)
