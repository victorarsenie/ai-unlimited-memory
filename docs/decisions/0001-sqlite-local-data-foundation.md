# ADR-0001: SQLite ca bază canonică locală inițială

## Stare

Acceptată pentru primul increment de implementare.

## Data

2026-10-01

## Context

Aplicațiile Windows și Android sunt proiectate să păstreze baze locale complete, sincronizate bidirecțional. Prima implementare trebuie să funcționeze local pe Windows, să păstreze fișierele importate byte-cu-byte, să țină datele personale în afara Git și să modeleze surse, conversații, mesaje, atașamente, datele knowledge graph și proveniența. Arhiva primită a fost inspectată local; parserul concret trebuie să urmeze structura observată și să păstreze payload-urile necunoscute legate de RAW.

Mediul inspectat include Python 3.12 și SQLite cu FTS5 disponibil. FastAPI și Uvicorn nu sunt instalate. Primul increment nu trebuie să depindă de descărcarea unor pachete sau de pornirea unui serviciu de rețea.

## Decizie

Folosim SQLite pentru baza canonică inițială de metadate și biblioteca standard Python pentru inițializare și migrații SQL versionate. Baza de date se află în `INDEX/`; directoarele `RAW/`, `INDEX/`, `DERIVED/` și `backups/` se creează într-o locație de date per utilizator, în afara clonării Git. Locația Windows implicită este `%LOCALAPPDATA%\PersonalMemory`; se poate schimba prin `PERSONAL_MEMORY_HOME` sau `--data-dir`.

Octeții originali se păstrează în RAW ca obiecte adresate prin conținut, identificate cu SHA-256. Baza de date păstrează metadatele și legăturile către aceste obiecte. Textul extras, OCR-ul, miniaturile, embeddings și alte artefacte reconstruibile stau în DERIVED sau în indexuri regenerabile. Fișierele de migrare nu se modifică după aplicare; inițializatorul le verifică amprenta SHA-256.

## Alternative analizate

### PostgreSQL

- Oferă concurență multi-utilizator și model server.
- Adaugă instalare și operare care nu sunt necesare pentru primul increment cu un singur PC.
- Reevaluăm dacă măsurătorile de concurență sau accesul de la distanță cer un server de baze de date separat.

### Bază de date documentară sau un singur fișier JSON

- Oferă flexibilitate pentru formate de intrare necunoscute.
- Slăbește integritatea relațională pentru proveniență, atașamente și legături din graful de cunoștințe; migrațiile și interogările ar fi mai greu de auditat.
- Nu o folosim pentru stratul canonic; payload-urile necunoscute rămân intacte în RAW și pot fi descrise în metadate JSON.

### Instalarea imediată a FastAPI și a unui ORM

- Ar putea accelera dezvoltarea API-ului și a modelelor aplicației.
- Niciuna dintre dependențe nu este prezentă în runtime-ul inspectat, iar contractul API nu este încă implementat.
- Amânăm alegerea până la incrementul API, când vom selecta și documenta runtime-ul și dependențele.

## Consecințe

- Primul increment funcționează local, fără dependențe externe, și este simplu de copiat pentru backup.
- SQLite oferă proveniență relațională; FTS5 este disponibil pentru incrementul ulterior de căutare lexicală.
- Baza de date are un singur scriitor; replica Android și protocolul de sincronizare necesită o decizie separată.
- Migrațiile SQL și validarea aplicației trebuie să evolueze fără rescrierea migrațiilor deja aplicate.
- Această decizie nu stabilește framework-ul API, providerul de embeddings sau tehnologia clientului Android.
