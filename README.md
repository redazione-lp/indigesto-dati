# Indigesto – dati della raccolta

Questo repository contiene i dati che la webapp **Indigesto**, la raccolta delle sentenze amministrative e delle pronunce della Corte costituzionale su edilizia e urbanistica a cura di Ing. Gianluca Oreto (Grafill), legge per aggiornarsi senza che l’utente debba scaricare una nuova versione.

La webapp controlla `versione.json` all’apertura, al massimo una volta al giorno, oppure quando si preme il pulsante di aggiornamento. Se il progressivo `rev` è più alto di quello che ha già, scarica `dati.json`, lo verifica con le stesse regole di `controlla_dati.py` e lo conserva sul computer, così le sentenze nuove restano disponibili anche senza connessione. I dati che non superano il controllo vengono ignorati e la webapp continua a mostrare quelli che ha.

## Come si pubblica un aggiornamento

Ogni aggiornamento arriva come richiesta di modifica (pull request) con le schede nuove descritte nel testo. Il controllo automatico «Controllo dati» verifica formato, collegamenti, progressivo e impronta. La pubblicazione avviene solo quando il direttore approva e unisce la richiesta nel ramo `main`; da quel momento, entro pochi minuti, le webapp degli utenti ricevono le novità.

Per correggere una pubblicazione sbagliata non si torna indietro con il progressivo, si pubblica una nuova versione con `rev` più alto.

## File

- `versione.json`, il file piccolo che la webapp legge per sapere se ci sono novità
- `dati.json`, le sentenze amministrative con massime, note, argomenti e collegamenti
- `dati-cost.json`, le pronunce della Corte costituzionale, lette soltanto dalla webapp dalla versione 1.17 con progressivo e impronta propri nel blocco `cost` di `versione.json`
- `testi/AAAA.json`, i testi integrali delle sentenze ripuliti e senza nomi di persone e Comuni, un archivio per anno, che la webapp dalla 1.17 usa per la ricerca nel testo e scarica soltanto quando cambia il blocco `testi` di `versione.json`
- `controlla_dati.py`, il controllo eseguito su ogni richiesta di modifica, che verifica anche le pronunce della Corte e gli archivi dei testi

Le copie della webapp fino alla 1.16.1 leggono soltanto `versione.json` e `dati.json` e continuano ad aggiornarsi sulle sentenze amministrative.

I numeri, le date e gli identificativi delle pronunce della Corte costituzionale provengono da dati.cortecostituzionale.it (licenza CC BY-SA 3.0); le massime della raccolta sono scritte dalla redazione e non riproducono le massime ufficiali.

© 2026 Grafill S.r.l. – Tutti i diritti riservati. I dati sono destinati alla webapp Indigesto e non possono essere riprodotti o riutilizzati senza autorizzazione.
