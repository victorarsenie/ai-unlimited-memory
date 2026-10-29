# Cerințe, domeniu și justificarea proiectului Personal Memory

**Versiune:** 1.0
**Data:** 2026-10-01
**Stare:** direcția de dezvoltare proprie a fost confirmată de utilizator; livrare incrementală.
**Documente conexe:** [Design de sistem](../superpowers/specs/2026-10-01-personal-memory-system-design.md), [Comparația soluțiilor existente](../research/existing-solutions-comparison.md), [Planul de implementare](../../tasks/plan.md), [Checklist](../../tasks/todo.md).

## 1. Rezumat

**Obiectivul principal este păstrarea contextului util al conversațiilor în timp.** Arhiva ChatGPT istorică se importă integral, iar originalul rămâne intact în RAW. Pentru conversațiile curente și viitoare, sistemul poate salva checkpoint-uri ca rezumate detaliate și structurate, care elimină repetițiile fără să piardă decizii, preferințe, fapte, corectări, acțiuni, întrebări deschise și context temporal. Când transcriptul-sursă este accesibil, îl păstrăm intact în RAW; rezumatul derivat include trimiteri la conversație și la mesajele-sursă. Un rezumat nu este prezentat drept transcript verbatim.

Personal Memory este un sistem personal, local-first, care adună conversații și alte surse într-un depozit controlat de utilizator. Depozitul trebuie să rămână util independent de furnizorul AI sau de interfața folosită: ChatGPT, modele locale precum Qwen, gpt-oss-20b și Gemma 4, agenți/harness-uri precum OpenCode și Hermes ori o interfață proprie.

Sistemul păstrează sursele originale separat de conținutul normalizat, indexuri și concluzii generate. Permite căutare full-text și semantică, navigarea conversațiilor și relațiilor, urmărirea fiecărui rezultat până la sursă, precum și acces de pe PC Windows și Android. Windows și Android păstrează fiecare o bază locală completă. Aplicațiile se sincronizează bidirecțional în rețeaua locală sau la cererea utilizatorului; ambele dispozitive pot funcționa independent offline.

Acesta este și un proiect de portofoliu: documentează o nevoie reală, alternativele evaluate, compromisurile, modelarea datelor, importul robust, proveniența, căutarea și integrarea mai multor clienți AI. Scopul nu este să pretindă că un produs propriu este superior în orice situație, ci să arate ce cerințe concrete rămân neacoperite de soluțiile existente și cum sunt rezolvate.

## 2. Problema și contextul utilizatorului

Istoricul util este dispersat în conversații și instrumente diferite. Memoria nativă a unui singur asistent nu oferă utilizatorului un depozit independent, ușor de auditat, exportat și refolosit de alt agent. O căutare obișnuită nu ajunge când utilizatorul își amintește ideea, nu formularea exactă; rezumatele fără surse pot deforma contextul; iar conectarea la un PC de acasă trebuie să țină cont de rețeaua LAN și de folosirea telefonului.

Utilizatorul lucrează pe Windows, păstrează proiectele pe `D:\AI`, folosește Android, are de regulă telefonul și PC-ul pe aceeași rețea de acasă și deține un depozit GitHub pentru proiect: [victorarsenie/PersonalMemory](https://github.com/victorarsenie/PersonalMemory). Arhiva de export ChatGPT a fost primită și inspectată local; importerul țintește structura observată, iar arhiva reală rămâne în afara depozitului Git.

## 3. Obiective

1. Un depozit controlat de utilizator, cu copii locale echivalente pe Windows și Android, care păstrează conversațiile complete și toate mesajele disponibile în ordinea sursei.
2. Importul arhivei ChatGPT este backfill-ul istoric necesar: importă fiecare conversație prezentă în arhiva furnizată, fără a reduce conținutul la rezumate sau fapte extrase.
3. Păstrarea byte-cu-byte a arhivei și fișierelor brute, cu hash și metadate.
4. Capturarea conversațiilor noi printr-o metodă validată separat; sistemul afișează explicit conversațiile sau porțiunile care nu au fost capturate.
5. Indexuri și date derivate regenerabile, legate de transcriptul care le justifică; rezumatele și knowledge graph-ul nu înlocuiesc conversația.
6. Căutare lexicală și semantică, cu filtre și rezultate citabile.
7. Explorarea conversațiilor, documentelor, entităților și relațiilor într-o hartă.
8. Folosire de pe Windows și Android; acces în LAN în prima etapă și suport offline pe telefon în măsura stabilită prin prototip.
9. API și adaptoare care permit reutilizarea aceluiași depozit de către aplicații și agenți diferiți.
10. Includerea imaginilor și fișierelor atașate, cu păstrarea originalelor și legătură către mesaj.
11. Documentarea diferențierii față de produse existente și prezentarea onestă a capabilităților implementate în portofoliu.

## 4. Non-obiective și limite

- Nu reconstruim un model lingvistic și nu încercăm să înlocuim ChatGPT, modelele locale Qwen, gpt-oss-20b și Gemma 4, sau agenții/harness-urile OpenCode și Hermes.
- Nu presupunem că o integrare MCP este disponibilă în toate aplicațiile ChatGPT; verificăm transportul, planul și clientul concret la momentul integrării.
- Nu inventăm structura exportului ChatGPT înainte de a o inspecta.
- Nu modificăm arhivele originale și nu promovăm automat extracțiile la fapte certe.
- Nu expunem PC-ul direct la internet și nu deschidem porturi în router ca setare implicită.
- Nu facem sincronizare bidirecțională fără identificatori, versiuni, jurnal și tratarea explicită a conflictelor.
- Nu construim din prima o aplicație Android nativă dacă un client web instalabil satisface cerințele măsurate; alegerea se face după prototip.
- Nu introducem o dependență de cloud pentru căutarea locală de bază.

## 5. Utilizatori și scenarii

### 5.1 Proprietarul depozitului

- Salvează periodic un checkpoint detaliat și structurat al conversației curente, de la ultima captură, și vede ce perioadă/surse acoperă; poate salva suplimentar transcriptul brut când acesta este accesibil.
- Adaugă/importă o sursă și vede raportul de ingestie.
- Caută după cuvinte, concepte, interval de timp, proveniență sau entitate.
- Deschide citatul în contextul mesajului/documentului original.
- Revizuiește, confirmă sau corectează entități și relații derivate.
- Folosește sistemul de pe telefon în aceeași rețea; când PC-ul nu este disponibil, poate consulta copia locală disponibilă și sincroniza ulterior.
- Face backup și poate reconstrui INDEX/DERIVED din RAW.

### 5.2 Agent AI sau client extern

- Caută în baza personală printr-un API stabil ori prin MCP.
- Primește fragmente relevante cu metadate și proveniență, nu doar o afirmație fără sursă.
- În prima versiune, citește datele; orice operație de scriere necesită reguli explicite de autorizare și jurnalizare.

### 5.3 Recuperarea istoricului ChatGPT și capturarea conversațiilor

- Importul arhivei este obligatoriu pentru backfill-ul istoric: preia fiecare conversație inclusă în exportul primit și păstrează arhiva originală în RAW.
- Importer-ul păstrează mesajele din toate rolurile și în ordinea/structura observată, inclusiv variantele și segmentele multimedia pe care exportul le conține.
- Raportul arată conversațiile și mesajele găsite, importate, omise sau imposibil de interpretat; payload-urile necunoscute rămân în RAW și sunt marcate neprocesate.
- Arhiva nu poate recupera conversații șterse sau conținut absent din export. Sistemul nu declară istoricul complet fără să indice acoperirea și erorile.
- Pe lângă backfill, conversația activă și cele ulterioare pot fi păstrate prin checkpoint-uri structurate periodice sau înainte de compactare. Se păstrează elementele importante și legăturile la surse, se elimină repetițiile, iar utilizatorul vede metoda și golurile de captură.

## 6. Cerințe funcționale

### F-01 — Arhivarea conversațiilor și ingestia surselor

La importul arhivei istorice se păstrează fiecare mesaj disponibil, rolul/autorul, ordinea, marcajele temporale, variantele/ramurile și segmentele furnizate de sursă; conținutul necunoscut rămâne payload opac legat de RAW. Pentru capturile curente/viitoare, sistemul poate crea rezumate detaliate și structurate pentru intervalul de la ultimul checkpoint: context/fapte importante, preferințe și corectări, decizii cu motivație, acțiuni cu stare/termen, întrebări nerezolvate și referințe la mesaje/atașamente. Redundanțele se pot comprima; contradicțiile și schimbările în timp nu se șterg. Transcriptul brut accesibil rămâne intact în RAW, iar rezumatul este derivat, versionat și declarat ca rezumat, nu transcript.

Fiecare captură/import înregistrează metoda, momentul, intervalul, reprezentarea salvată (transcript, rezumat structurat sau ambele), acoperirea (completă/parțială/necunoscută) și raportul elementelor procesate, omise și erorilor. Pentru Codex, un hook PreCompact poate furniza calea transcriptului înainte de compactare, dacă este disponibilă; formatul nu este o interfață stabilă, deci copia brută se arhivează în RAW înainte de interpretare. Capturile sunt reluabile fără duplicate.

### F-02 — Separarea datelor

- **RAW:** arhiva sursă și binarele originale ale imaginilor/fișierelor, read-only după ingestie, păstrate byte-cu-byte și identificate prin SHA-256.
- **INDEX:** structura canonică a fiecărei conversații și a fiecărui mesaj, ordinea, rolul, segmentele de conținut, variantele, locatorii către sursă și metadatele atașamentelor. Indexurile lexicale/vectoriale sunt regenerabile; transcriptul normalizat nu este înlocuit de rezumate.
- **DERIVED:** fragmente, text extras, miniaturi, OCR, embeddings, rezumate, entități, relații și afirmații. Fiecare rezultat derivat păstrează proveniența și versiunea procesorului/modelului.

Reindexarea șterge și reconstruiește numai structurile regenerabile, nu RAW.

### F-03 — Proveniență și audit

Orice rezultat sau afirmație trebuie să indice arhiva RAW, conversația, mesajul/varianta, segmentul de conținut și poziția sursă, când formatul o permite. Proveniența leagă transcriptul importat de fișierul original. Distinge între conținut original, extras automat, confirmat de utilizator și contestat/corectat. Păstrează istoricul transformărilor și al sincronizării.

### F-04 — Căutare

Căutarea lexicală suportă expresii și filtre după dată, sursă, conversație, entitate și tip. Căutarea semantică folosește embeddings printr-un provider configurabil, ideal local, și se poate reface când se schimbă modelul. Rezultatele combinate arată fragmente relevante, scoruri utile, metadate și legături către contextul complet.

### F-05 — Knowledge graph

Graful păstrează entități, relații și afirmații ca date derivate, cu provenance. Interfața permite explorarea de la un concept către conversațiile și pasajele justificative. Extracția automată rămâne marcată ca atare până la confirmare; contradicțiile nu sunt suprascrise în tăcere.

### F-06 — API și MCP

API-ul versionat reprezintă contractul comun pentru UI și integrații. MCP expune inițial căutare și citire; fiecare rezultat include provenance. Scrierea prin agenți se activează separat, după definirea aprobării, validării și jurnalului de modificări. Adaptoarele pentru modelele locale Qwen, gpt-oss-20b și Gemma 4, precum și clienții/agenții ChatGPT, OpenCode și Hermes, sunt componente opționale și nu schimbă modelul de date.

**Limită ChatGPT:** documentația oficială OpenAI verificată la 2026-10-01 spune că aplicațiile MCP sunt disponibile numai pe web, nu pe mobil; ChatGPT se conectează la servere MCP remote, nu direct la un server local. Pentru un server în rețeaua privată, este necesar un Secure MCP Tunnel în produsele OpenAI care îl suportă. Disponibilitatea developer mode și a acțiunilor complete MCP depinde de plan și workspace. Prin urmare, UI/API-ul propriu pentru Android rămâne necesar; integrarea ChatGPT este o cale web opțională, nu singura interfață mobilă. [OpenAI: Developer mode and MCP apps in ChatGPT](https://help.openai.com/en/articles/12584461-developer-mode-and-full-mcp-connectors-in-chatgpt).

### F-07 — PC, Android și sincronizare

PC-ul găzduiește serviciul și copia principală. Android se conectează în LAN și poate păstra o replică/cache locală, inclusiv atașamentele sincronizate pentru acces offline. Sincronizarea transferă schimbări identificate/versionate și fișiere, poate relua transferuri întrerupte și detectează conflictele; nu pierde variante. Protocolul exact și clientul PWA versus nativ se aleg după prototip și verificarea cerințelor offline.

### F-08 — Interfață

Interfața oferă căutare, listă de rezultate, vizualizare conversație/document cu salt la pasaj, hartă a entităților și relațiilor, inspector de provenance, stare de sincronizare și flux de import. Afișează imaginile și previzualizările de fișiere în contextul sursei și oferă acces la original. Interfața trebuie să facă vizibilă diferența dintre sursă și inferență.

### F-10 — Imagini și fișiere atașate

Sistemul importă și păstrează fișierele/imaginile atașate conversațiilor și documentelor, inclusiv formatele pentru care încă nu există extractor. Fișierul original rămâne intact în RAW și primește hash, nume, tip MIME observat, dimensiune și proveniență către sursa și mesajul de origine, când aceste informații există. Atașamentul rămâne accesibil din contextul conversației pe PC și Android; interfața poate afișa imaginea sau o previzualizare acceptată și permite deschiderea/descărcarea originalului.

Textul se extrage și se indexează numai pentru formatele pe care procesorii configurați le suportă. Pentru imagini, OCR, descriere vizuală și embeddings vizuale sunt capabilități derivate opționale, preferabil procesate local. Fișierele necunoscute sau imposibil de citit nu blochează importul: se păstrează, se leagă de sursă și pot fi găsite după nume/metadate. Miniaturile, OCR-ul și textul extras sunt regenerabile și nu înlocuiesc originalele. Transferul fișierelor către replica Android suportă reluarea transferurilor întrerupte și acces offline la elementele sincronizate.

Criteriu de acceptare: originalul poate fi deschis sau recuperat cu hash identic după import; atașamentul are legătură navigabilă către sursă; conținutul suportat poate fi căutat; tipurile necunoscute sunt păstrate și raportate.

### F-09 — Backup, confidențialitate și portabilitate

Backup-ul include RAW, baza canonică și configurațiile necesare restaurării; indexurile regenerabile pot fi reconstruite. Accesul LAN este autorizat; nu se expun porturi publice implicit. Formatele exportabile și schema sunt documentate, astfel încât utilizatorul să nu fie captiv într-un singur client.

### F-11 — Backfill istoric și acoperirea capturilor

Importul arhivei ChatGPT este calea obligatorie pentru recuperarea conversațiilor istorice încă prezente în export. Separat, sistemul trebuie să poată salva conversația ChatGPT curentă și cele ulterioare ca checkpoint-uri detaliate și structurate, cu trimiteri la surse și atașamente; când transcriptul brut este accesibil, îl păstrează în RAW. Până la validarea metodei, interfața arată ce surse și intervale nu sunt capturate. Nu se pretinde captură automată sau exhaustivă fără dovezi și raport de acoperire. Fluxul de export documentat de OpenAI este inițiat de utilizator din setări și livrează o arhivă ZIP; documentația consultată nu descrie sincronizarea automată per mesaj către un depozit local. [Exportul datelor ChatGPT pe Android](https://help.openai.com/en/articles/8167885-how-to-export-your-data-from-the-chatgpt-android-app).

## 7. Cerințe non-funcționale

- **Local-first:** stocare și căutare de bază pe echipamentele utilizatorului; conectivitatea cloud nu este necesară pentru funcțiile centrale.
- **Siguranța sursei:** operațiile asupra INDEX/DERIVED nu alterează fișierele RAW.
- **Trasabilitate:** rezultate și relații explicabile prin provenance.
- **Interoperabilitate:** clientul AI se poate schimba fără migrarea depozitului canonic la un serviciu de memorie proprietar.
- **Reproductibilitate:** migrațiile și operațiile de inițializare/import sunt versionate și documentate.
- **Evoluție incrementală:** fiecare etapă produce o felie utilizabilă, cu contracte stabile și migrare clară.
- **Portabilitate:** schema și exporturile sunt descrise suficient pentru backup, audit și mutare.

## 8. Arhitectură și principii

### 8.1 Componente

1. **Data store local:** fișiere RAW și baza de date canonică pe PC.
2. **Ingestion/import adapters:** parsează surse cunoscute și raportează necunoscutele.
3. **Search/index service:** full-text și, ulterior, index semantic.
4. **API local versionat:** folosit de UI, telefon și clienți.
5. **UI de explorare:** browser/aplicație web instalabilă inițial; PWA versus nativ validat separat.
6. **Android replica/sync:** funcție incrementală, cu cache offline și rezolvare explicită a conflictelor.
7. **AI adapters:** MCP, embeddings și clienți specifici, izolați de nucleu.

### 8.2 Model de domeniu inițial

Entități candidate: `Source`, `ImportRun`, `Conversation`, `Message`, `Attachment`, `Document`, `Passage`, `Entity`, `Claim`, `Relation`, `Provenance`, `Embedding`, `SyncEvent` și `Revision`. Identificatorii, schema și stările exacte se stabilesc într-o decizie de arhitectură înaintea implementării nucleului.

### 8.3 Principii de proiectare

- Source of truth în depozitul utilizatorului, nu în indexul unui asistent.
- RAW nu este o zonă de cache și nu este recreată din date normalizate.
- INDEX și DERIVED sunt regenerate cu versiuni explicite de parser/model.
- Relațiile și memoriile derivate nu pierd citatele care le justifică.
- Interfețele sunt adaptoare; contractele de date sunt independente de ele.
- Nu se alege o tehnologie doar pentru familiaritate; dependențele se verifică în mediul Windows al utilizatorului și se consemnează.

## 9. Produse existente și justificarea construirii

Produsele evaluate includ Khoj, Open WebUI, AnythingLLM, Memos, Mem0 și Letta. Ele oferă capabilități utile pentru second brain, RAG, memorie de agent, graf ori MCP; de aceea proiectul nu trebuie să le reproducă automat ca UI sau runtime.

Comparația inițială, cu linkuri la documentația oficială și limite formulate ca „nu am identificat în documentație”, este în [documentul de evaluare](../research/existing-solutions-comparison.md). Ipoteza de lucru este că niciun produs documentat nu unește într-un singur depozit controlat de utilizator: RAW-ul arhivei reale, import ChatGPT adaptat după inspecție, provenance granulară, indexuri reconstruibile, graph explorabil, căutare mixtă și interoperabilitate PC/Android/agenți.

Prin urmare, direcția aprobată este **să construim nucleul care acoperă aceste goluri și să reutilizăm produse existente când reduc efortul fără să compromită proprietatea datelor și proveniența**. Dacă prototipul arată că o alternativă acoperă mai mult decât estimăm, aria proprie se restrânge. Decizia este revizitabilă pe dovezi, nu pe atașament față de implementarea proprie.

## 10. Valoarea și prezentarea în portofoliu

Proiectul poate demonstra:

- analiză de problemă și evaluare a alternativelor;
- arhitectură local-first cu responsabilități RAW/INDEX/DERIVED;
- pipeline de ingestie rezilient, idempotent și explicabil;
- provenance și modelare a datelor/grafului;
- căutare lexicală și semantică cu modele locale precum Qwen, gpt-oss-20b și Gemma 4;
- API/MCP și integrare multi-agent;
- acces PC/Android, LAN, sincronizare offline și tratarea conflictelor;
- decizii de confidențialitate, backup și portabilitate;
- livrare incrementală și documentație tehnică.

Demo-urile, capturile, fixture-urile și toate datele din repo-ul GitHub vor folosi exclusiv date sintetice. Conversațiile și arhiva reale ale utilizatorului se folosesc doar local în instanța Personal Memory. Nu se publică și nu se comit arhive, RAW, extrase, indexuri, embeddings, loguri, capturi sau rezultate care conțin date personale. Nu se afirmă că o funcție este completă până când există o demonstrație verificabilă.

## Politica de date pentru GitHub și utilizare locală

- Repo-ul GitHub, inclusiv commit-urile și materialele de portofoliu, conține numai cod, documentație și date sintetice create special pentru demonstrații.
- Datele sintetice nu se obțin prin anonimizarea conversațiilor reale; se generează separat pentru a evita scurgeri prin detalii sau metadate.
- Arhiva ChatGPT și conversațiile personale se importă numai în instanța locală configurată de utilizator. Nu se copiază în directoarele urmărite de Git.
- RAW, INDEX, DERIVED, backup-urile, logurile de ingestie și artefactele generate din surse personale sunt locale și excluse din Git. Configurația repository-ului trebuie să asigure acest lucru înainte de importul real.
- Prototipurile, walkthrough-urile și materialele publice folosesc date sintetice. Corectitudinea importer-ului poate fi verificată suplimentar local, pe o copie a arhivei reale, fără publicarea conținutului, rezultatelor sau capturilor.
- Erorile și logurile nu trebuie să includă implicit textul mesajelor sau conținutul privat al fișierelor.

## 11. Faze de livrare și criterii de acceptare

### Faza 0 — Evaluare și prototip de produse existente

- Completează evaluarea documentată și verifică practic cei mai apropiați candidați cu date sintetice.
- Decide dacă produsul existent devine UI/client, dacă se extinde un produs sau dacă nucleul propriu rămâne justificat.
- Acceptare: decizie bazată pe criterii și goluri observate, cu utilizatorul implicat la schimbări mari de scope.

### Faza 1 — Fundație de date

- Stabilește repo instructions, runtime, layout RAW/INDEX/DERIVED, configurare ignorată de Git și baza/migrațiile.
- Acceptare: depozit gol inițializabil, schema versionată, demonstrarea invariabilității RAW prin operații de reindexare.

### Faza 2 — API și căutare lexicală

- API versionat, CRUD controlat pentru surse/importuri, FTS și rezultate cu provenance.
- Acceptare: conținut sintetic poate fi introdus/căutat/deschis din contextul său de origine.

### Faza 3 — Importer ChatGPT

- După primirea arhivei, inventariază formatele reale, inclusiv cum sunt reprezentate imaginile și fișierele atașate; păstrează arhiva brută local și implementează parser/adaptor pentru ceea ce s-a observat.
- Acceptare: raport complet, import reluabil, necunoscute păstrate/raportate, proveniență verificabilă și atașamente păstrate cu legătura către mesaj; verificarea pe copia arhivei reale se face numai local și nu se include în Git.

### Faza 4 — UI PC/Android și graph

- Căutare, context, provenance, explorare grafică, acces LAN și cache/sync incremental.
- Adaugă galerie/previzualizare pentru imagini și fișiere suportate, acces la original și disponibilitate offline pentru atașamentele sincronizate.
- Acceptare: utilizare demonstrată pe PC și Android; fișierele se deschid din mesajul de origine, iar conflictele și transferurile incomplete sunt vizibile.

### Faza 5 — Semantic search și modele locale

- Integrează modele locale precum Qwen, gpt-oss-20b și Gemma 4 prin runtime-uri compatibile.
- Provider embeddings local configurabil, metadate model/versionare, fuziune lexicală/semantică pentru textul extras din formatele suportate.
- OCR/descriere/embeddings vizuale pot fi adăugate ca procesare derivată locală, fără a înlocui imaginea originală.
- Acceptare: rezultate semantice provin din pasaje/atașamente identificabile; re-embedding nu schimbă RAW.

### Faza 6 — MCP și clienți

- MCP read-only inițial; probează conexiunea în fiecare client vizat și documentează restricțiile transportului.
- Acceptare: căutarea/citirea întoarce surse/provenance; scrierea rămâne dezactivată până la autorizare explicită.

### Faza 7 — Backup, securizare și hardening

- Procedură backup/restaurare, autorizare LAN, jurnal și opțional acces la distanță prin rețea privată.
- Acceptare: restaurarea datelor este demonstrată; fără expunere publică implicită.

## 12. Riscuri și întrebări de validat

- **Format export necunoscut:** se amână parserul până la arhiva reală; se începe cu interfața și contractul adaptorului.
- **Suport MCP diferit per client:** testare la momentul integrării; aplicațiile MCP ChatGPT sunt web-only și nu se conectează direct la un server local conform documentației OpenAI consultate. Clientul Android propriu rămâne o cerință separată; tunnel-ul privat se evaluează numai pe suprafețele OpenAI suportate.
- **Offline și replicare complexe:** prototip și măsurare înainte de alegerea PWA/nativ și protocol sync.
- **Inferențe inexacte:** stări de verificare și citate; utilizatorul păstrează controlul faptelor.
- **Creștere de scope:** faze cu criterii de acceptare și reutilizare de produse existente unde păstrează cerințele centrale.
- **Disponibilitatea modelelor locale:** nucleul funcționează lexical fără embeddings; providerul semantic poate fi configurat ulterior pentru Qwen, gpt-oss-20b, Gemma 4 sau alte modele compatibile.

## 13. Istoricul deciziilor

- **2026-10-01:** utilizatorul a confirmat PC-ul și Android ca dispozitive țintă, conectarea de regulă prin aceeași rețea de acasă, depozitul în `D:\AI\PersonalMemory`, GitHub pentru versionare, arhiva ChatGPT ulterioară și integrarea cu modelele locale Qwen, gpt-oss-20b și Gemma 4, precum și clienții/agenții OpenCode și Hermes.
- **2026-10-01:** utilizatorul a confirmat dezvoltarea proprie dacă produsele existente nu acoperă cerințele și a cerut ca motivația comparativă și valoarea adăugată să fie documentate ca proiect de portofoliu.
- **2026-10-01:** documentația OpenAI consultată confirmă că MCP apps sunt web-only, se conectează la servere remote, iar serverele din rețele private pot necesita Secure MCP Tunnel; accesul MCP mobil direct nu este presupus.
- **2026-10-01:** utilizatorul a stabilit că repo-ul GitHub va conține doar date sintetice pentru o posibilă publicare open source; conversațiile personale se folosesc exclusiv local în instanța creată.
- Exportul ChatGPT nu a fost încă inspectat; schema lui rămâne necunoscută.
