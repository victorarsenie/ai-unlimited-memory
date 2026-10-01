# Checklist — Personal Memory

Planul detaliat este în [`plan.md`](plan.md). Comparația inițială a produselor este în [`existing-solutions-comparison.md`](../docs/research/existing-solutions-comparison.md). Utilizatorul a aprobat direcția de a construi nucleul propriu unde soluțiile existente nu acoperă cerințele.

## Pregătire

- [x] Confirmă repo-ul și specificația existentă.
- [x] Compară documentația produselor existente și consemnează golurile față de cerințe.
- [x] Utilizatorul a confirmat dezvoltarea proprie dacă nu există soluție completă; se reutilizează UI/adaptoare unde au sens.

## Etapa 0 — Evaluare produse existente

- [x] Compară Khoj, Open WebUI, AnythingLLM, Memos, Mem0 și Letta cu cerințele prioritare.
- [ ] Prototip manual cu date fictive pentru candidații cei mai potriviți.
- [x] Recomandă nucleu propriu interoperabil; evaluează produse existente drept UI/clienți/adaptoare.
- [x] Direcția proprie aprobată de utilizator la 2026-10-01.

## Etapa 1 — Fundație și contracte

- [ ] Inspectează runtime-ul disponibil și instrucțiunile repo-ului.
- [ ] Definește contractele RAW / INDEX / DERIVED și regulile de păstrare RAW.
- [ ] Definește schema inițială și migrațiile versionate.
- [ ] Documentează inițializarea și backup-ul local.
- [ ] Revizuire manuală de acceptare.

## Etapa 2 — API și căutare lexicală

- [ ] API local versionat.
- [ ] Index FTS5 și provenance în rezultate.
- [ ] Import generic documentat, fără ipoteze despre exportul ChatGPT.
- [ ] Walkthrough manual cu date sintetice.

## Etapa 3 — Import ChatGPT (când arhiva este disponibilă)

- [ ] Inspectează arhiva și inventariază formatele reale.
- [ ] Implementează adaptorul pe baza formatului observat.
- [ ] Păstrează RAW și asigură import repetabil cu raport de rezultate.
- [ ] Verifică manual pe copii ale arhivei.

## Etapa 4 — UI și Android în LAN

- [ ] UI de căutare, explorare și provenance.
- [ ] Hartă a entităților și relațiilor.
- [ ] Acces local de pe Android și mesaj când PC-ul nu e disponibil.
- [ ] Walkthrough manual PC + Android.

## Etapa 5 — Căutare semantică

- [ ] Provider embeddings interschimbabil și metadate de versiune.
- [ ] Integrare cu runtime local disponibil.
- [ ] Căutare combinată FTS + semantică.
- [ ] Walkthrough manual sau documentarea dependenței locale absente.

## Etapa 6 — MCP și adaptoare

- [ ] MCP bridge read-only inițial.
- [ ] Adaptoare pentru clienții confirmați: ChatGPT, OpenCode, Hermes.
- [ ] Validare și jurnalizare înainte de orice operație de scriere.
- [ ] Conectare manuală în fiecare client suportat.

## Etapa 7 — Sincronizare și recuperare

- [ ] Proiectează replicarea PC-authoritative și tratarea conflictelor.
- [ ] Documentează accesul LAN și backup/restaurare.
- [ ] Walkthrough manual de restaurare.



