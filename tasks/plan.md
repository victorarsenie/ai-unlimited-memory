# Plan de implementare — Personal Memory

**Data:** 2026-10-01  
**Bază:** `docs/superpowers/specs/2026-10-01-personal-memory-system-design.md`  
**Stare:** direcția de evaluare și dezvoltare proprie a fost aprobată de utilizator la 2026-10-01; implementarea se face incremental.

Documentația detaliată a cerințelor, scopului și valorii de portofoliu este în [`docs/project/requirements-and-scope.md`](../docs/project/requirements-and-scope.md).

## Decizii de lucru

- Baza locală de pe PC este sursa de adevăr; importurile brute rămân nemodificate în RAW.
- INDEX conține date normalizate și indexuri regenerabile; DERIVED păstrează legături, rezumate și vectori cu proveniență către sursă.
- Înainte de a scrie cod, compară aplicațiile existente cu cerințele și încearcă configurația celei mai potrivite. Construim componente proprii doar pentru golurile confirmate. Dacă nucleul propriu rămâne necesar, varianta inițială este SQLite/FTS5 și API Python/FastAPI; runtime-ul se alege după verificarea mediului.
- Importer-ul ChatGPT va fi modular: întâi contractul și interfața adaptorului, apoi parserul concret numai după primirea arhivei reale și inspectarea structurii sale.
- Pentru Android se începe cu o interfață web instalabilă și accesibilă în rețeaua locală. Sincronizarea offline bidirecțională și aplicația nativă se decid după validarea prototipului și a cerințelor reale de utilizare.
- Modelele locale Qwen, gpt-oss-20b și Gemma 4, plus clienții/agenții ChatGPT, OpenCode și Hermes, se conectează prin adaptoare peste API-ul și modelul de date stabile; niciunul nu devine dependență a nucleului.
- Fiecare etapă păstrează provenance (sursa, locatorul, timpul importului, transformarea și identificatorii legați) și oferă operații de reindexare fără modificarea RAW.

## Etape și criterii de acceptare

### 0. Evaluare de soluții existente (înaintea implementării)

Comparația inițială este documentată în [`docs/research/existing-solutions-comparison.md`](../docs/research/existing-solutions-comparison.md). Utilizatorul a confirmat că dezvoltarea proprie este potrivită dacă produsele existente nu acoperă cerințele și că motivația/comparația trebuie păstrate în documentația de portofoliu.

- Evaluează practic Khoj, Open WebUI, AnythingLLM și Memos față de cerințele prioritare: date locale, funcționare cu model local, Android/browser în LAN, import de arhivă, păstrarea RAW, proveniență, hartă relațională și MCP.
- Pentru 1–2 candidați, verifică documentația curentă și fă un prototip cu date fictive; nu importa arhiva ChatGPT reală înainte de a o inspecta.
- Criteriu: recomandare comparativă clară: (a) configurăm un produs existent, (b) îl folosim ca UI peste un depozit/API propriu, sau (c) implementăm nucleul, explicând golurile care justifică efortul.
- Verificare: walkthrough manual PC și Android unde este posibil; consemnează cerințele neacoperite și orice limitare de acces la ChatGPT/MCP.
- Direcția de bază proprie, cu reutilizarea produselor existente acolo unde ajută, este aprobată; rafinăm produsul concret și adaptoarele după evaluarea practică.


### 1. Fundație și contracte de date

- Inspectează mediul și documentația existentă; consemnează alegerile efective de runtime și structura directoarelor.
- Definește structura `RAW/`, `INDEX/`, `DERIVED/`, configurarea locală și regulile de backup.
- Definește schema inițială pentru surse, conversații, mesaje, binare/atașamente, entități, relații și provenance; folosește migrații versionate și stochează hash, nume, tip MIME și dimensiune.
- Criteriu: un depozit gol poate fi inițializat reproductibil; datele sursă nu sunt suprascrise de transformări sau reindexare.
- Verificare: revizuire manuală a schemei, directoarelor și instrucțiunilor de inițializare.

### 2. API local și căutare lexicală

- Adaugă endpoint-uri locale versionate pentru sănătatea serviciului, surse, căutare și citirea elementelor cu proveniență.
- Configurează SQLite FTS5 pentru căutare lexicală, filtrare și navigarea rezultatelor către sursă.
- Adaugă import generic documentat pentru conținut textual și metadate, fără a pretinde compatibilitate cu un export ChatGPT neinspectat.
- Criteriu: utilizatorul poate adăuga, căuta și deschide conținut indexat; fiecare rezultat indică sursa și locația sa.
- Verificare: walkthrough manual pe date sintetice clar etichetate, fără date personale reale. Prototipurile și fixturile comise/publicate sunt exclusiv sintetice.

### 3. Importer modular ChatGPT

- Definește interfața adaptorului, raportul de import și politica pentru fișiere repetate, atașamente și erori.
- După disponibilitatea arhivei, inspectează structura și documentația inclusă înainte de a implementa parserul concret.
- Inventariază atașamentele efectiv întâlnite; păstrează originalele byte-cu-byte, leagă-le de mesajele sursă și raportează formatele necunoscute fără să oprească importul.
- Păstrează fișierele originale exact; scrie extrasele și indexurile doar în zonele destinate.
- Criteriu: importul este reluabil/idempotent, raportează ce a acceptat sau respins și permite refacerea indexurilor din RAW.
- Verificare: validare locală, privată, pe o copie a arhivei reale, cu controlul numărului de elemente și al provenienței; datele și rezultatele nu intră în Git.

### 4. Interfață de explorare și acces Android în LAN

- Construiește UI pentru căutare, navigarea conversațiilor/surselor și inspectarea provenienței.
- Adaugă vizualizarea grafului ca strat de explorare peste entități și relații aprobate/derivate.
- Configurează acces local controlat, instrucțiuni clare pentru PC și telefon și comportament util când serverul nu este disponibil.
- Adaugă previzualizări pentru imaginile și fișierele suportate, acces la original și transferuri reluabile pentru atașamentele sincronizate offline.
- Criteriu: PC-ul și telefonul din aceeași rețea pot accesa sistemul; UI afișează sursa și legăturile fără a expune directoarele brute.
- Verificare: walkthrough manual pe PC și Android în rețeaua locală.

### 5. Semantic search și integrare locală

- Integrează modele locale precum Qwen, gpt-oss-20b și Gemma 4 prin runtime-uri compatibile; configurează embeddings printr-un provider interschimbabil separat, cu metadate de versiune.
- Stochează vectorii doar în INDEX/DERIVED și leagă fiecare vector de versiunea modelului și textul sursă.
- Adaugă căutare semantică și fuziune cu căutarea FTS, fără a cere un model cloud.
- Indexează text extras din formatele suportate; tratează OCR-ul, descrierea vizuală și embeddings vizuale drept procesări locale opționale în DERIVED.
- Criteriu: schimbarea modelului permite re-embedding fără atingerea RAW; rezultatele păstrează proveniența.
- Verificare: walkthrough manual cu un model local disponibil; dacă lipsește, documentează clar funcționalitatea amânată.

### 6. MCP bridge și adaptoare pentru agenți

- Publică un MCP bridge cu un set restrâns de operații read-only inițial: căutare, citire, hartă și provenance.
- Separă adaptoarele pentru ChatGPT și agenții/harness-urile OpenCode și Hermes de serverul și schema centrale; acestea pot apela modele locale precum Qwen, gpt-oss-20b sau Gemma 4.
- Adaugă operații de scriere numai după definirea autorizării, validării și jurnalizării modificărilor.
- Criteriu: clienții suportati pot găsi și citi aceleași date prin API/MCP, iar sursa fiecărui rezultat este vizibilă.
- Verificare: conectare manuală per client, după confirmarea suportului și setărilor clientului.

### 7. Sincronizare, securizare și backup

- Evaluează un model PC-authoritative cu replică/cache local pe Android și cozi pentru schimbări offline.
- Documentează autentificarea în LAN, expunerea minimă a porturilor, backup-ul și restaurarea.
- Ia în calcul acces de la distanță numai la cerere, printr-un tunel privat; fără port forwarding implicit.
- Criteriu: procedura de backup/restaurare și conflictele de sincronizare sunt explicate înainte de a activa sincronizarea bidirecțională.
- Verificare: walkthrough manual de backup și recuperare pe copii locale.

## Ordinea dependențelor

Fundație → API și FTS → importer concret (după arhivă) și UI/LAN → semantic search și MCP → sincronizare/întărire. UI prototip poate începe după ce API-ul și modelul minim sunt stabile. Qwen, gpt-oss-20b și Gemma 4 sunt modele locale vizate; OpenCode și Hermes sunt clienți/agenți integrați ulterior.

## În afara primei felii

- Interpretarea arbitrară a arhivei ChatGPT înainte de a o vedea.
- Expunerea serverului direct la internet.
- Scrierea autonomă a „amintirilor” de către agenți fără aprobare și provenance.
- Alegerea unui format de replicare Android înainte de a verifica performanța și experiența PWA în utilizarea reală.




