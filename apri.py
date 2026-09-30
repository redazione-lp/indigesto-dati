"""Indigesto - apre il dati.json pubblicato (cifrato) e scrive l'elenco delle sentenze in chiaro.
Uso: INDIGESTO_CHIAVE=... python3 apri.py dati.json dati-correnti.json"""
import json, sys, base64
from build import CHIAVE, flusso
d = json.load(open(sys.argv[1], encoding='utf-8'))
if d.get('cifrato') == 1:
    b = base64.b64decode(d['dati']); k = flusso(len(b), d['rev'])
    d = json.loads(bytes(x ^ y for x, y in zip(b, k)).decode('utf-8'))
json.dump(d['ROWS'], open(sys.argv[2], 'w', encoding='utf-8'), ensure_ascii=False)
print('sentenze', len(d['ROWS']), 'progressivo', d['rev'], 'aggiornata', d['aggiornata'])
