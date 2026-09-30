# Indigesto – dati della raccolta

Questo repository contiene i dati che la webapp **Indigesto**, la raccolta delle sentenze amministrative su edilizia e urbanistica a cura di Ing. Gianluca Oreto (Grafill), legge per aggiornarsi senza che l’utente debba scaricare una nuova versione.

La webapp controlla `versione.json` all’apertura, al massimo una volta al giorno, oppure quando si preme il pulsante di aggiornamento. Se il progressivo `rev` è più alto di quello che ha già, scarica `dati.json`, lo verifica con le stesse regole di `controlla_dati.py` e lo conserva sul computer, così le sentenze nuove restano disponibili anche senza connessione. I dati che non superano il controllo vengono ignorati e la webapp continua a mostrare quelli che ha.

## Come si pubblica un aggiornamento

Ogni aggiornamento viene preparato dalla redazione, controllato con `controlla_dati.py` e pubblicato dal direttore sostituendo `dati.json` e `versione.json` nel ramo `main`. Da quel momento, entro pochi minuti, le webapp degli utenti ricevono le novità.

Per correggere una pubblicazione sbagliata non si torna indietro con il progressivo, si pubblica una nuova versione con `rev` più alto.

## File

- `versione.json`, il file piccolo che la webapp legge per sapere se ci sono novità
- `dati.json`, le sentenze con massime, note, argomenti e collegamenti
- `controlla_dati.py`, il controllo dei dati prima della pubblicazione
- `apri.py`, `applica.py`, `controlla.py`, `pubblica.py` e `build.py`, gli strumenti con cui la redazione prepara gli aggiornamenti; la chiave di cifratura non è nel repository e va fornita con la variabile INDIGESTO_CHIAVE

© 2026 Grafill S.r.l. – Tutti i diritti riservati. I dati sono destinati alla webapp Indigesto e non possono essere riprodotti o riutilizzati senza autorizzazione.
