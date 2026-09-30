"""Indigesto - file per l'aggiornamento a distanza.
Uso: python3 pubblica.py dati.json cartella-repository "data di aggiornamento" [--rev N] [--app-min 1.3] [--app-ultima 1.3] [--download URL]
Scrive nella cartella del repository dati.json (tutte le sentenze, con argomenti e gruppi, con la cifratura leggera
di build.py) e versione.json
(il file piccolo che la webapp legge per sapere se ci sono novità). Il progressivo deve crescere a ogni
pubblicazione: di default è AAAAMMGG01, e per una seconda pubblicazione nello stesso giorno si passa --rev AAAAMMGG02.
Lo script si ferma se il progressivo non supera quello già pubblicato o se le sentenze diminuiscono di molto."""
import json, os, sys, hashlib
from build import prepara, LABEL, GROUPS, FORMATO, data_iso, cifra

args = sys.argv[1:]
opt = {'--rev': None, '--app-min': '1.3', '--app-ultima': '1.3', '--download': 'https://www.grafill.it/home/8992-2068-regolarita-edilizia-catastale-compravendite-immobiliari.html'}
for k in list(opt):
    if k in args:
        i = args.index(k); opt[k] = args[i + 1]; del args[i:i + 2]
DATI, REPO, AGG = args[:3]
iso = data_iso(AGG)
rev = int(opt['--rev'] or iso.replace('-', '') + '01')
assert str(rev).startswith(iso.replace('-', '')) and len(str(rev)) == 10, 'progressivo non valido'

rows = prepara(json.load(open(DATI)))
ecli = [r['e'] for r in rows]
assert len(ecli) == len(set(ecli)), 'ECLI duplicati'
for r in rows:
    assert r['u'].startswith(('https://mdp.giustizia-amministrativa.it/', 'https://www.giustizia-amministrativa.it/', 'https://www.cortecostituzionale.it/')), r['e']
    for f in ('lp', 'ls'):
        assert f not in r or r[f].startswith('https://www.lavoripubblici.it/'), (r['e'], f)

vfile = os.path.join(REPO, 'versione.json')
if os.path.exists(vfile):
    prev = json.load(open(vfile))
    assert rev > prev['rev'], f'il progressivo {rev} deve superare quello pubblicato {prev["rev"]}'
    assert len(rows) >= prev['n'] * 0.95, f'le sentenze scendono da {prev["n"]} a {len(rows)}: controllare prima di pubblicare'

dati = {'formato': FORMATO, 'rev': rev, 'aggiornata': iso, 'app_min': opt['--app-min'],
        'ROWS': rows, 'LABEL': LABEL, 'GROUPS': GROUPS}
chiaro = json.dumps(dati, ensure_ascii=False, separators=(',', ':'))
txt = json.dumps({'formato': FORMATO, 'rev': rev, 'aggiornata': iso, 'cifrato': 1, 'dati': cifra(chiaro, rev)}, separators=(',', ':'))
os.makedirs(REPO, exist_ok=True)
open(os.path.join(REPO, 'dati.json'), 'w').write(txt)
ver = {'formato': FORMATO, 'rev': rev, 'aggiornata': iso, 'n': len(rows),
       'nuove': sum(1 for r in rows if r.get('ag') == iso),
       'app_min': opt['--app-min'], 'app_ultima': opt['--app-ultima'], 'download': opt['--download'],
       'sha256': hashlib.sha256(txt.encode()).hexdigest()}
open(vfile, 'w').write(json.dumps(ver, ensure_ascii=False, indent=1) + '\n')
print('pubblicato', rev, 'sentenze', len(rows), 'byte', len(txt.encode()))
