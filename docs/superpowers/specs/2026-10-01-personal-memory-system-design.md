# Sistem personal de memorie — design

**Stare:** direcția confirmată de utilizator la 2026-10-01
**Data:** 2026-10-01

## Scop

**Obiectivul central este păstrarea contextului util al conversațiilor în timp.** Arhiva istorică ChatGPT se importă integral ca backfill. Pentru conversațiile curente și viitoare, sistemul salvează checkpoint-uri periodice detaliate și structurate; acestea pot comprima repetițiile, păstrând deciziile/motivația, faptele, preferințele/corectările, acțiunile/starea/termenele, întrebările deschise, schimbările și trimiterile la surse. Un checkpoint este derivat, nu transcript verbatim. Transcripturile brute accesibile rămân intacte în RAW. Metoda și acoperirea capturii trebuie afișate și validate.

Construim incremental un sistem personal de memorie accesibil de pe Windows și Android. Aplicațiile păstrează fiecare o copie locală completă și sincronizează modificările bidirecțional când sunt în aceeași rețea locală sau la cererea utilizatorului; fiecare poate căuta și citi datele local când celălalt dispozitiv este oprit. Accesul din afara casei poate fi adăugat ulterior printr-o rețea privată precum Tailscale.

Sistemul trebuie să păstreze sursele intacte, inclusiv imaginile și fișierele atașate, să arate proveniența fiecărei informații și să poată alimenta ulterior modele locale precum Qwen, gpt-oss-20b și Gemma 4, precum și agenți/harness-uri ca OpenCode și Hermes. Integrarea ChatGPT este o țintă separată și opțională. La 2026-10-01, documentația OpenAI spune că aplicațiile MCP sunt web-only, nu mobile; ChatGPT se conectează la servere MCP remote, iar un server dintr-o rețea privată poate necesita Secure MCP Tunnel. Accesul și acțiunile disponibile depind de plan/client. Aplicația proprie Android rămâne calea mobilă directă. [Sursa OpenAI](https://help.openai.com/en/articles/12584461-developer-mode-and-full-mcp-connectors-in-chatgpt).

Cerințele complete, scenariile, criteriile și justificarea de portofoliu sunt în [documentul de cerințe](../../project/requirements-and-scope.md). Comparația produselor existente este în [evaluarea soluțiilor](../../research/existing-solutions-comparison.md).

## Arhitectură propusă

- **Aplicația Windows:** păstrează o bază locală completă și oferă API local pentru sincronizare/căutare; serviciul ascultă numai pe rețeaua locală configurată, iar dispozitivele asociate sunt autorizate. Nu se configurează redirecționare de porturi.
- **Android:** aplicație proprie instalabilă, cu baza locală completă, captură prin Share și coadă de sincronizare offline. Se distribuie prin Google Play după testare și review.
- **Sincronizare:** protocolul transferă modificări identificabile, cu versiuni și proveniență, între două replici complete. Schimbările conflictuale nu se suprascriu în tăcere; se păstrează ambele variante și se marchează pentru rezolvare.
- **Clienți AI:** API-ul este contractul comun pentru aplicațiile proprii. Un adaptor MCP separat expune operații limitate de căutare/citire și, ulterior, scriere controlată. Integrarea ChatGPT se activează doar pe suprafețele și planurile care o suportă.

## Separarea datelor

- **RAW:** arhivele și binarele originale primite/importate, inclusiv imagini și atașamente, păstrate byte-cu-byte și identificate prin hash. Nicio normalizare sau editare nu le modifică.
- **INDEX:** date normalizate pentru căutare și sincronizare, cu referințe către fișierele și înregistrările RAW de origine.
- **DERIVED:** text extras, miniaturi, OCR, fragmente, embeddings, entități, relații, rezumate și afirmații deduse. Acestea pot fi reconstruite sau marcate ca revizuite fără a modifica RAW; procesarea vizuală este opțională și preferabil locală.

Schema canonică inițială folosește SQLite și migrații SQL versionate, conform [ADR-0001](../../decisions/0001-sqlite-local-data-foundation.md). Migrațiile 001/002 modelează surse/importuri, capturi cu acoperire, conversații, mesaje/ramuri, segmente multimodale, obiecte brute și atașamente, documente, entități, afirmații, relații și provenance. Fragmentele de căutare și evenimentele de sincronizare se adaugă în etapele lor. Faptele extrase păstrează referința la sursa justificativă și starea lor (derivat, confirmat sau contestat).

## Delimitarea datelor personale și GitHub

The GitHub repository and portfolio use synthetic data only. The user's real conversations and ChatGPT archive are used only in the local Personal Memory instance. Keep RAW, INDEX, DERIVED, backups, ingestion logs, and outputs derived from private data outside tracked Git content. Configure exclusions before importing the real archive. Synthetic demo data is generated independently, not by anonymizing the user's conversations. Importer validation against a copy of the actual archive may happen locally; its content and outputs are not published.

## Backfill istoric ChatGPT și capturarea continuă

Importul arhivei este necesar pentru recuperarea istoricului existent: după primire, inspectăm structura reală, păstrăm ZIP-ul original în RAW și importăm toate conversațiile, mesajele și segmentele conținute. Importer-ul nu presupune schema înainte de inspecție; păstrează ramuri/variante și payload-uri necunoscute prin locator către RAW, iar raportul indică acoperirea, erorile și elementele neinterpretate. Conversațiile șterse sau absente din export nu pot fi reconstruite.

Pe lângă backfill, utilizatorul trebuie să poată salva conversația ChatGPT curentă și conversațiile ulterioare ca transcripturi complete. O captură explicită inițiată de utilizator este acceptabilă dacă platforma nu oferă captură automată. Validăm metoda înainte să o numim automată și facem vizibile conversațiile/mesajele/segmentele necapturate. Exportul ChatGPT documentat oficial este solicitat de utilizator și furnizat ca arhivă ZIP; documentația consultată nu descrie sincronizarea automată per mesaj către depozitul local.

## Căutare și knowledge graph

Prima etapă de căutare folosește full-text și filtre după sursă, dată și entități. Căutarea semantică folosește embeddings generate local, printr-un adaptor de model configurabil; indexul vectorial este derivat și regenerabil. Graful de cunoștințe păstrează entități, relații și afirmații împreună cu proveniența lor. Extracția automată nu devine fapt verificat fără confirmare.

## Interfață

Interfața Windows/Android oferă capturarea explicită și raportarea conversației ChatGPT curente, căutare, rezultate cu surse, vizualizarea conversațiilor/documentelor și a imaginilor/fișierelor atașate, explorarea entităților și relațiilor, stare de sincronizare și inspectarea provenienței. Editările și validarea afirmațiilor sunt acțiuni explicite. Interfața de pe Android folosește aceeași API și aceleași convenții de proveniență ca serviciile AI.

## Livrare incrementală

1. **Contract și nucleu local:** schema, migrații, directoarele RAW/INDEX/DERIVED și proveniența.
2. **Backfill istoric ChatGPT:** imediat ce arhiva este disponibilă, inspectăm formatul și importăm toate conversațiile/mesajele/segmentele prezente, apoi raportăm acoperirea și elementele neprocesate.
3. **API și căutare:** navigare/căutare în transcriptul integral, cu legături către mesaj și poziția din arhiva RAW.
4. **Captură curentă și client Android:** oferim un flux pentru salvarea transcriptului conversației active și a conversațiilor ulterioare; validăm metoda și raportăm golurile. Sincronizăm transcripturile și atașamentele către copia offline Android.
5. **Explorare și graf:** extragem date derivate cu provenance, fără să înlocuim conversațiile.
6. **Adaptoare AI:** MCP, embeddings locale și integrarea ChatGPT acolo unde este suportată.
## În afara primei versiuni

- Acces public la PC, porturi deschise pe router sau sincronizare printr-un cloud terț.
- Presupuneri despre structura arhivei ChatGPT.
- Promovarea automată a rezumatelor/entităților la fapte verificate.
- Scrieri autonome ale agenților fără proveniență și reguli explicite de autorizare.

## Criterii de acceptare pentru fundație

- O sursă poate fi păstrată în RAW și urmărită prin hash și metadate de proveniență.
- Indexurile și datele DERIVED se pot reconstrui fără modificarea RAW.
- Modelul canonic și API-ul nu depind de un singur format de export sau de un singur model AI.
- Arhitectura distinge clar copia principală de pe PC, replica Android și conflictele de sincronizare.
- ChatGPT mobile nu este prezentat ca fiind conectat prin MCP cât timp această funcție nu este suportată.
- Conversația ChatGPT curentă poate fi salvată ca transcript complet, iar raportul indică orice mesaj sau segment lipsă.
