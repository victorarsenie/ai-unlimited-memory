# Memoria extinsă și capturarea conversațiilor ChatGPT

## Versiunea 0.3

**Dată:** 2 octombrie 2026  
**Stare:** versiune de lucru, revizuită pe măsură ce cercetarea și prototiparea avansează.  
**Domeniu:** proiectul Personal Memory și fluxurile de memorie ChatGPT.  
**Repo proiect:** [PersonalMemory](https://github.com/victorarsenie/PersonalMemory)  
**Scop:** cercetare de produs și fezabilitate, nu raport de test comparativ final.

> Lucrarea examinează metodele de extindere a memoriei conversaționale în ChatGPT și fezabilitatea capturării controlate într-un depozit personal. Constatările documentare, ipotezele de proiectare și rezultatele experimentale sunt delimitate explicit. Revizuirile ulterioare se consemnează cu dată și versiune.

## Rezumat

Personal Memory investighează o problemă de continuitate conversațională: conversațiile ChatGPT acumulează decizii și detalii, dar contextul nu este întotdeauna disponibil când conversația devine lungă sau se începe un chat nou. Obiectivul este extinderea memoriei utilizabile din aplicația ChatGPT pe Android și PC, păstrând controlul asupra datelor într-un depozit independent.

Analiza distinge trei capabilități:

1. **Memoria pe care ChatGPT o folosește pentru personalizare:** context selectat din conversații anterioare, nu o arhivă exhaustivă.
2. **Capturarea conversației active:** păstrarea unui transcript sau a unui checkpoint la cerere/periodic, fără dependență de memoria implicită a modelului.
3. **Arhivarea istorică:** exportul contului și importul integral al conversațiilor deja existente; util ca backfill, dar lent și inițiat separat.

Comparația inițială a analizat Khoj, Open WebUI, AnythingLLM, Memos, Mem0 și Letta. Acestea sunt în principal chat-uri proprii, depozite de documente/notițe ori infrastructură de memorie pentru agenți; nu sunt în sine conectori pentru conversația din ChatGPT Android. Cercetarea ulterioară a identificat însă aplicații publicate direct în directorul ChatGPT, între care Engram, Empirical, Mem, AI Passport, Komplyt Zero și Open Context. Prin urmare, afirmația inițială „nu există nimic care să extindă memoria ChatGPT” ar fi greșită.

Cea mai apropiată soluție găsită pentru păstrarea conversațiilor verbatim este **Engram**. Listarea sa din ChatGPT declară stocare verbatim cu căutare semantică. Ghidul Engram pentru ChatGPT precizează totuși că scrierea în Engram se face la cerere prin MCP și prin importul arhivei; nu există captură silențioasă, completă, per mesaj în fundal. Memoria serviciului este găzduită pe Cloudflare. **Empirical** oferă memorie structurată și graph cu integrare ChatGPT, documentația consultată nu indică o promisiune de arhivă verbatim exhaustivă; serviciul găzduit păstrează date în infrastructură externă.

Share din ChatGPT Android a fost testat prin trimiterea către WhatsApp: destinația a primit URL-ul unui snapshot, nu transcript inline. Pagina web a afișat întreaga conversație ChatGPT vizată în acel test. Importul direct în PersonalMemory este fezabil de explorat printr-un Share target Android și preluarea URL-ului în fundal; tipul de payload către aplicația noastră și metoda HTTP de extragere încă trebuie validate.

Direcția de proiect actualizată folosește două aplicații distincte — Android și Windows — fiecare cu o bază de date locală completă. Dispozitivele păstrează copii replicate ale aceluiași set de date și se sincronizează bidirecțional când sunt disponibile în aceeași rețea locală, automat sau la cererea utilizatorului. Ambele aplicații trebuie să poată captura, căuta și funcționa independent offline. Importul exportului ChatGPT rămâne mecanismul de backfill istoric; capturile viitoare pot fi rezumate structurate, cu surse și interval acoperit. Datele reale se păstrează pe dispozitivele personale, iar materialele publice/GitHub folosesc date sintetice.

## 1. Originea problemei și contextul

Motivația proiectului este degradarea accesului la detalii pe parcursul conversațiilor de lungă durată. Acestea combină informații utile cu repetiții; valoarea arhivistică stă atât în concluzii, cât și în raționamente, corectări și evoluția planurilor. În consecință, conversația este o sursă primară, iar memoriile și rezumatele sunt reprezentări derivate.

Exportul ChatGPT constituie mecanismul de backfill pentru conversațiile istorice, însă procesarea poate dura zile și nu oferă captură continuă pentru conversațiile noi. Prin urmare, schema și depozitul pot fi pregătite înaintea arhivei, iar parserul concret se implementează numai după inspecția fișierelor efectiv primite.

În faza inițială, istoricul vizibil în browser nu apărea în aceeași suprafață a aplicației desktop. Investigația a distins între ChatGPT, Codex și identitatea contului. Această separare motivează un depozit de memorie independent de interfață, model sau agent.

Contextul de deployment include două aplicații, una pentru Windows și una pentru Android, fiecare cu stocare locală. Sincronizarea locală bidirecțională menține copii echivalente fără a necesita un depozit exclusiv pe PC; PC-ul poate oferi temporar endpoint-ul de sync când este pornit, iar telefonul păstrează și folosește propria bază independent. Repo-ul GitHub PersonalMemory conține cod și documentație; datele personale sunt în afara lui. Modelele locale vizate sunt Qwen, gpt-oss-20b și Gemma 4; OpenCode și Hermes sunt agenți/harness-uri, integrați ulterior prin API/MCP.

## 2. Cerințe funcționale și operaționale

### 2.1 Obiectiv principal

Păstrarea și regăsirea contextului conversațiilor în timp, în special a conversațiilor ChatGPT purtate pe telefon. Asistentul trebuie să poată găsi din nou informații și să nu piardă motive, corectări ori decizii importante când se schimbă chatul sau se compactează contextul.

### 2.2 Istoric versus conversații noi

- **Istoric:** când arhiva de export devine disponibilă, importul trebuie să păstreze toate conversațiile și mesajele furnizate în formatul observat. Formatul exportului se stabilește prin inspecția arhivei efective.
- **Conversații viitoare:** arhivarea verbatim a fiecărui schimb nu constituie o condiție pentru capturile viitoare. Acestea pot utiliza checkpoint-uri sau rezumate detaliate și structurate, cu reducerea repetițiilor și conservarea informației relevante.
- **Când transcriptul este accesibil:** copia brută se păstrează intactă în RAW; rezumatul aparține stratului DERIVED și nu se prezintă drept transcript.
- **Acoperire:** fiecare captură trebuie să precizeze metoda, perioada, ce a salvat, dacă acoperirea e completă/parțială/necunoscută și ce elemente au lipsit.

Conținutul minim al unui checkpoint util:

- context și fapte de durată;
- preferințe și corectări declarate în conversație;
- decizii și raționamentul lor;
- acțiuni, stare, termene și responsabilități;
- întrebări nerezolvate și următorul pas;
- schimbări în timp și contradicții, fără a le șterge;
- conversația, mesajele, atașamentele sau snapshot-ul-sursă, în măsura în care pot fi referite.

### 2.3 Arhitectură și proprietatea datelor

- Aplicațiile Windows și Android păstrează fiecare baza locală completă; setul logic de date este replicat între dispozitive.
- Sincronizarea este bidirecțională în aceeași rețea locală, automat sau pornită manual din aplicație; fiecare dispozitiv rămâne utilizabil offline.
- PC-ul poate găzdui temporar serviciul de sincronizare, fără a fi singura copie sau unica sursă de adevăr.
- Identificatorii stabili, amprentele și versionarea trebuie să prevină duplicatele și să permită reconcilierea modificărilor de pe ambele dispozitive.
- **RAW** păstrează fișierele originale și transcripturile capturate fără modificare.
- **INDEX** conține structura normalizată și indexurile reconstruibile.
- **DERIVED** conține rezumate, embeddings, OCR, extrageri, entități și relații, întotdeauna cu proveniență și versiune.
- Sistemul include imagini și fișiere atașate conversațiilor.
- Căutarea trebuie să fie lexicală și semantică; explorarea include o hartă/graph; citatele trebuie să indice sursa.
- Copiile PersonalMemory ale datelor reale se păstrează local pe dispozitivele Windows și Android și se sincronizează între ele; acest lucru nu mută sau elimină copia conversației originale păstrată de serviciul ChatGPT. Codul, fixture-urile, demonstrațiile și materialele publice folosesc date sintetice/permise, niciodată arhive personale.
- Exportul arhivei este backfill istoric, nu soluția unică și nici un mecanism de captură periodică.

## 3. Evoluția cadrului de cercetare și a deciziilor de proiect

### A. Fundația înaintea arhivei istorice

Depozitul, schema, RAW/INDEX/DERIVED, importerul modular, căutarea full-text/semantică, graph-ul, provenance-ul, API-ul și interfața pot fi pregătite înaintea exportului. Parserul specific rămâne condiționat de inspecția arhivei reale.

### B. Locație și separarea datelor

Codul și documentația sunt gestionate în D:\AI\PersonalMemory și în repo-ul GitHub PersonalMemory. Instanța cu date reale se află separat în ai-unlimited-memory-data, în afara repo-ului. Datele de demonstrație/publicare sunt sintetice.

### C. Comparația de produse — prima abordare prea largă

Comparația a inclus:

- **Khoj:** second brain self-hosted, căutare/chat în documente și clienți web/PWA.
- **Open WebUI:** interfață proprie de chat/RAG, modele și integrare MCP; suportă importul exportului ChatGPT, dar aceasta este migrare de date, nu captură live din aplicația ChatGPT.
- **AnythingLLM:** chat/workspace/RAG și modele locale/cloud.
- **Memos:** notițe self-hosted, API și MCP.
- **Mem0:** infrastructură pentru extragerea și regăsirea memoriilor agentului, cu opțiune graph.
- **Letta:** runtime de agent cu memorie persistentă și conversații proprii.

Evaluarea inițială s-a concentrat prea mult pe depozite și importul arhivei. Analiza a fost rafinată pentru a separa aplicațiile de chat proprii și memoria furnizată agenților de integrarea directă cu aplicația ChatGPT existentă.

### D. Prioritizarea ChatGPT Android

Aplicația ChatGPT de pe Android este suprafața principală de integrare; Codex este secundar. Soluțiile care presupun mutarea conversațiilor într-un chatbot separat nu satisfac singure scopul. Sistemul trebuie fie să extindă contextul ChatGPT, fie să capteze datele din fluxul folosit deja.

### E. Android Share ca mecanism de captură explicită

Share din ChatGPT Android poate transmite către aplicația destinatară un URL către pagina snapshot a conversației. Un test realizat prin WhatsApp a confirmat că destinația a primit linkul, iar deschiderea lui a afișat copia web cu mesajele conversației partajate. Conversația observată corespundea integral conversației ChatGPT vizate; discuțiile continuate ulterior în Codex nu făceau parte din acel snapshot. Pagina vizibilă confirmă accesul la textul conversației prin URL, însă transmiterea directă către PersonalMemory și importul automat în baza locală nu au fost încă prototipate. Oricine deține linkul îl poate accesa.

### F. Aplicații de memorie în directorul ChatGPT

Au fost identificate aplicații publicate direct în directorul ChatGPT, infirmând ipoteza că nu există integrări de memorie relevante pentru ChatGPT. Capabilitățile variază: furnizarea de context și salvarea memoriilor la cerere nu echivalează cu arhivarea automată a fiecărui mesaj.

### G. Limitele și costul Engram

Ghidul Engram pentru ChatGPT descrie salvarea la cerere, nu captură în fundal pentru fiecare mesaj. Salvarea explicită poate declanșa apeluri la instrumente care creează conversația în Engram și adaugă mesajele disponibile; arhiva istorică se importă separat. Planul Engram Free și planul ChatGPT Free sunt produse și limite distincte.

### H. Testul Share a confirmat livrarea unui link

Partajarea unei conversații ChatGPT Android către WhatsApp a transmis URL-ul share, nu transcriptul inline. Deschiderea URL-ului a afișat copia snapshot a conversației. În testul observat, conținutul coincide cu întreaga conversație ChatGPT vizată; mesajele de continuare purtate ulterior în Codex aparțin altui fir și nu sunt incluse în snapshot. Acesta este un rezultat empiric pentru conversația testată, nu o garanție privind fiecare tip de share sau atașament.

### I. Două aplicații și două replici locale

Arhitectura s-a clarificat de la ipoteza anterioară cu PC drept depozit canonic. Aplicațiile Android și Windows trebuie să păstreze fiecare baza locală completă și să sincronizeze schimbările în ambele direcții în LAN, automat sau la comandă. Telefonul poate primi și importa o conversație când PC-ul este offline; datele se copiază ulterior pe PC. Același flux funcționează în sens invers. PC-ul poate găzdui temporar punctul de sincronizare cât timp este disponibil, fără să fie unica copie a datelor.

### J. Importul URL și accesul ChatGPT la bază sunt probleme diferite

Share oferă URL către pagina snapshot. Importul în PersonalMemory poate fi declanșat direct de aplicația Android fără fereastră de browser: clientul transmite URL-ul unui importer care descarcă pagina. Dacă transcriptul este inclus în răspunsul HTTP, parserul îl poate extrage direct; dacă este construit dinamic, poate fi necesară randare fără interfață vizibilă. Răspunsul HTTP brut și comportamentul JavaScript nu au fost încă inspectate.

Accesul ChatGPT la conversațiile salvate nu vine automat din faptul că telefonul și PC-ul se sincronizează. Necesită o integrare de căutare/citire separată. Documentația OpenAI descrie limite pe plan și suprafață pentru MCP personalizat și indică indisponibilitatea MCP apps în aplicația mobilă; compatibilitatea cu ChatGPT Free rămâne de verificat.

## 4. Ce face butonul Share, conform documentației

Documentația OpenAI curentă descrie în mare următorul flux:

1. Se deschide conversația și se alege Share.
2. Se examinează conținutul/opțiunile și se creează sau copiază linkul, în funcție de interfață.
3. Pe mobil ChatGPT poate deschide meniul nativ de partajare Android; destinațiile disponibile depind de dispozitiv și aplicații.
4. Partajarea din conversația completă produce un snapshot până în momentul creării; partajarea de pe un răspuns poate limita linkul la acel răspuns.
5. Pentru conturile personale, oricine deține linkul îl poate deschide; snapshot-ul nu include mesajele adăugate ulterior în mod automat.

**Observație empirică (2 octombrie 2026):** Share → WhatsApp a transmis un link `chatgpt.com/share/...`, nu transcriptul inline. Linkul a deschis în browser o pagină cu copia conversației partajate și mesajele sale. Comparația cu conversația de referință a confirmat că snapshot-ul includea toată conversația ChatGPT respectivă. Testul confirmă fluxul prin WhatsApp și lizibilitatea paginii; nu verifică ce payload va primi un Share target PersonalMemory și nici dacă pagina poate fi preluată direct printr-o cerere HTTP fără randare JavaScript.

**Consecință tehnică:** aplicația Android poate primi URL-ul prin mecanismul nativ Share și poate iniția importul fără să afișeze o fereastră de browser. Serviciul poate prelua pagina în fundal prin HTTP dacă răspunsul conține transcriptul; dacă acesta este generat de JavaScript, poate fi necesară randare headless. Ambele variante trebuie testate. Importul păstrează în RAW răspunsul/pagina preluată și metadatele sursei; INDEX conține mesajele extrase.

## 5. Produse și mecanisme comparate

### 5.1 Soluții de memorie în directorul ChatGPT

| Produs | Ce declară/permite | Relevanță și limită preliminară |
|---|---|---|
| **Engram** | ChatGPT app/MCP; listarea declară stocare verbatim și căutare semantică. Salvarea se declanșează la cerere prin ChatGPT; ghidul Engram descrie trimiterea conversației prin operații de creare și adăugare de mesaje. Istoricul vechi se importă separat. | Candidatul cel mai apropiat de păstrarea verbatim, dar fără captură silențioasă per mesaj și cu stocare cloud. Planul gratuit Engram este listat cu plafon de 10.000 mesaje; Pro este listat la 9 USD/lună (verificat la 2026-10-02). Acestea sunt limitele Engram, separate de planul ChatGPT. Disponibilitatea aplicației și a acțiunilor în ChatGPT Free trebuie verificată în contul concret. |
| **Empirical** | Memorie structurată/graf, API/MCP și app ChatGPT publicată; ChatGPT poate furniza context relevant și memoriile pot fi căutate/scrise. | Potrivit pentru memorii durabile selectate, documentația consultată nu garantează arhivarea completă verbatim. Politica declară procesare/stocare cloud; self-hosting este opțiune de operare separată și necesită administrare. |
| **Mem** | Knowledge base/notițe și operații din ChatGPT; listarea include salvarea conversației ca notă și căutarea ideilor. | Captură utilă explicită ca notă; nu este demonstrat că păstrează automat fiecare turn într-o arhivă RAW locală. |
| **AI Passport** | Memorie portabilă între aplicații AI; listarea descrie propuneri de memorii aprobabile și acces controlat pe categorii. | Interesant pentru aprobare și portabilitate; necesită validarea integrității, modului de captură, arhivării și găzduirii. |
| **Komplyt Zero** | Bază structurată pentru cunoștințe/proiecte, disponibilă ca app ChatGPT; declară găzduire UE și fără folosire pentru antrenare. | Potrivire posibilă pentru memorii extrase; trebuie verificat dacă salvează checkpoint-uri ori transcripturi, export și condițiile de acces. |
| **Open Context** | Stocare și recuperare de context, documente, profile și instrucțiuni în workflow-uri AI. | Memorie/context cross-tool; nu este dovedită arhivare automată integrală a conversației. |
| **VaultSage / Create State / altele** | Aplicații ChatGPT cu memorie, stocare text, proiecte ori knowledge graph, în funcție de listare. | Candidați suplimentari de inventariat; descrierile directorului sunt afirmații ale dezvoltatorilor și trebuie verificate prin documentație, termeni și test. |

Prezența în directorul ChatGPT atestă publicarea unei integrări, nu certificarea acesteia de către OpenAI a retenției, calității sau securității produsului. Disponibilitatea și capabilitățile exacte diferă în funcție de plan, regiune, workspace și versiunea aplicației.

### 5.2 Soluțiile evaluate inițial, care sunt apropiate dar nu echivalente

| Soluție | Rol documentat în comparația inițială | De ce nu răspunde singură la captura ChatGPT Android |
|---|---|---|
| **Khoj** | Second brain self-hosted și căutare/chat în documente; web/PWA și sincronizare de fișiere. | Indexează documentele furnizate; documentația consultată nu descrie un conector care preia automat conversațiile ChatGPT. |
| **Open WebUI** | Chat UI/RAG propriu, modele locale/API, MCP; importă export ChatGPT. PWA/Computer poate primi URL, text sau fișier din meniul Share în workspace. | Importul exportului e backfill, iar Computer Share target e o cale de captură posibil relevantă de prototipat, însă nu reprezintă citirea automată a istoricului ChatGPT. Ar presupune mutarea conversației în Open WebUI. |
| **AnythingLLM** | Chat/workspaces, RAG pe fișiere și modele locale/cloud; desktop local. | Memoria conversațiilor aparține workspace-urilor AnythingLLM, nu aplicației ChatGPT. |
| **Memos** | Depozit de memo-uri, API/MCP, integrare Telegram pentru captură de note. | Poate fi un backend/notebook pentru checkpoint-uri, dar nu înseamnă acces automat la ChatGPT. |
| **Mem0** | SDK/API prin care o aplicație sau un agent trimite mesaje, apoi extrage memorii și relații. | Apelează codul integratorului; nu este automat conectat la ChatGPT Android doar prin instalarea Mem0. |
| **Letta** | Runtime pentru agenți persistenti și propriile conversații/canale conectate. | Memoria se formează în conversații/integrații Letta; nu capturează independent conversația din ChatGPT. |

Aceste produse rămân utile drept componente/alternative sau repere tehnice. Prin urmare, aceste produse sunt soluții adiacente, nu neapărat substituenți direcți: trebuie precizat dacă folosirea lor presupune mutarea conversației într-un chat propriu.

### 5.3 Memoria nativă ChatGPT

Memoria ChatGPT poate folosi informații din istoricul anterior pentru personalizare și poate păstra memorii distincte de chat-uri. Este comodă și funcționează în produs, dar OpenAI spune că nu păstrează fiecare detaliu și că sistemul caută context relevant când consideră că ar ajuta. Prin urmare poate completa UX-ul, dar nu înlocuiește un jurnal cu provenance, export complet și control asupra fișierelor RAW.

### 5.4 Accesarea memoriei externe din ChatGPT

Importul și sincronizarea locală nu oferă automat ChatGPT acces la baza PersonalMemory. Pentru regăsire directă în chat, este necesară o aplicație/conector care expune operații de căutare și citire și este disponibilă planului, regiunii și interfeței folosite. Documentația OpenAI consultată descrie MCP personalizat pentru planuri eligibile, notează că MCP apps nu sunt disponibile în aplicația mobilă ChatGPT și că suportul complet de scriere este limitat la anumite planuri de workspace; suportul echivalent pentru un MCP personalizat pe ChatGPT Free nu este confirmat. Prin urmare, integrarea directă cu Free rămâne o ipoteză de validat, nu o condiție de proiectare.

Ca flux intermediar, aplicația Android poate căuta local și poate partaja către ChatGPT pasajele selectate împreună cu citatele și proveniența. Modelele și agenții locali pot interoga API-ul PersonalMemory direct. Accesul ChatGPT la date necesită o integrare explicită; simpla prezență a dispozitivelor în aceeași rețea nu este suficientă.

## 6. Tabelul metodelor de captură

| Metodă | ChatGPT Android | Auto/periodică? | Poate păstra verbatim? | Depozit propriu local? | Stare |
|---|---:|---:|---:|---:|---|
| Memorie nativă ChatGPT | Da | Se actualizează în funcție de produs, fără garanție de arhivă integrală | Nu e arhivă verbatim externă | Nu | Documentat ca personalizare, nu ca export controlat |
| App de memorie ChatGPT (Engram/Empirical etc.) | Directorul/plugin-urile sunt disponibile pe mobil, dar verificăm fiecare app/cont | Engram spune la cerere; automatizarea completă nu e promisă în ghidul ChatGPT | Engram declară verbatim când i se trimite conținut | Nu implicit; Engram cloud; Empirical are opțiune self-host cu operare proprie | Cel mai direct de încercat ca add-on, cu date sintetice |
| Share → WhatsApp (test observat) | Da | Nu; acțiune explicită | Link către snapshot web al conversației | Nu în baza PersonalMemory prin acel flux | Linkul a deschis copia web și a inclus conversația vizată; nu a livrat transcript inline |
| Share → PersonalMemory | Android, după implementarea Share target | Nu; acțiune explicită | Se așteaptă URL; conținutul poate fi preluat din pagina snapshot | Da, pe dispozitivul care primește linkul, apoi replicat | Netestat; necesită prototip Share target |
| Lipire/checkpoint manual în PersonalMemory | Da, via clipboard/browser/app | La cerere | Poate salva conținutul furnizat explicit | Da | Fallback fezabil, dar UX manual |
| Export oficial ChatGPT | Inițiat din Android/web | Nu; întârziat și separat | Da, în măsura exportului efectiv | După descărcare și import | Backfill istoric obligatoriu; nu soluție curentă |
| Importul linkului Share în PersonalMemory | Telefon sau Windows | La cerere, prin Share | Snapshot web; extragerea directă și eventualele atașamente necesită testare | Da, apoi sincronizat bidirecțional cu cealaltă replică | Fezabilitate susținută de pagina web observată; parserul și fluxul automat rămân de implementat și verificat |

## 7. Rezultate și concluzii provizorii

1. **Directorul ChatGPT include aplicații de memorie externe.** Existența integrărilor publicate nu demonstrează captură verbatim sau automată; funcțiile declarate trebuie evaluate individual.
2. **Există diferență între memorie extinsă și arhivare.** Un conector poate furniza context la întrebare ori salva memorii la cerere, fără să captureze toate mesajele.
3. **Engram este candidatul cel mai apropiat ca mesaj publicat pentru stocarea verbatim**, dar propriul ghid limitează ChatGPT la apeluri la cerere plus import de export. Găzduirea sa este cloud, deci nu oferă replici locale controlate de proiect.
4. **Integrarea directă a unei baze proprii cu ChatGPT Free nu este încă confirmată.** Disponibilitatea aplicațiilor depinde de plan, interfață și aplicația concretă; în schimb, căutarea locală urmată de partajarea pasajelor către ChatGPT rămâne o cale intermediară.
5. **Share este o cale concretă de captură explicită**: testul Android → WhatsApp a transmis un URL, iar pagina rezultată a afișat conversația partajată. Rămâne de implementat primirea URL-ului de către PersonalMemory și importul snapshot-ului fără fereastră vizibilă de browser.
6. **Exportul rămâne backfill-ul istoricului.** Timpul de așteptare de până la 7 zile îl face nepotrivit pentru captură la intervale scurte.
7. **Checkpoint-ul detaliat e acceptat pentru viitor.** Stocarea verbatim a fiecărui turn nu este obligatorie dacă platforma nu oferă acces robust; checkpoint-ul trebuie să păstreze informația utilă, proveniența, intervalul și golurile.
8. **Sistemul este offline-first și replicat.** Fiecare aplicație păstrează o bază locală completă; sincronizarea LAN propagă importurile și modificările în ambele direcții.

## 8. Propunere de experimente următoare

### Experiment 1 — Share target și importul snapshot-ului

- Implementează Share target Android pentru URL-uri și primește linkul direct în PersonalMemory.
- Începe importul pe dispozitivul care primește linkul, fără fereastră de browser vizibilă.
- Testează mai întâi recuperarea prin HTTP; inspectează dacă HTML-ul include mesajele ori dacă pagina le generează dinamic.
- Dacă e necesar, folosește randare headless și păstrează atât răspunsul-sursă, cât și conținutul extras.
- Folosește date sintetice pentru testele repetate; verifică începutul, mijlocul, finalul, atașamentele și ramurile.
- Calculează hash, generează raportul de acoperire și verifică importul idempotent al aceluiași link.
- După ce copia RAW este salvată cu succes, testează revocarea linkului și confirmă că copia locală rămâne accesibilă.

**Criteriu de succes:** PersonalMemory primește linkul prin Android Share, stochează snapshot-ul și proveniența, explică orice lipsă de acoperire și importă aceeași conversație o singură dată.

### Experiment 2 — Prototip ChatGPT app memory connector

- Disponibilitatea Engram și Empirical se verifică în directorul de aplicații pentru contul și regiunea vizate.
- Nu autoriza conversații personale în testul inițial; folosește un cont/workspace și informații sintetice dacă posibil.
- Cere explicit salvarea unui checkpoint structurat; începe un chat nou și testează dacă se recuperează prin query.
- Verifică dacă răspunsul folosește tool call și dacă textul salvat e rezumat, transcript sau doar memorie semantică.
- Evaluează exportul/ștergerea/revocarea și locația de stocare înainte de orice folosire reală.

**Criteriu de succes:** aflăm dacă add-on-ul reduce frecarea și oferă recall util pe Android, fără să îl confundăm cu arhiva locală a proiectului.

### Experiment 3 — Criterii de achiziție/folosire pentru soluțiile existente

Pentru Engram, Empirical, Mem și orice nou candidat, notează:

- suportul real în ChatGPT Android;
- automat, on-request sau bulk import;
- verbatim versus structurare/sumarizare;
- dacă ingerează istoricul vechi fără export manual;
- locația datelor, subprocesori și transferuri internaționale;
- export complet, ștergere, versionare și retenție;
- posibilitate local/self-host, cost și dependențe;
- provenance până la chat/mesaj și suport pentru atașamente;
- comportamentul celor două replici locale când sincronizarea lipsește, precum și protocolul și regulile de reconciliere.

### Experiment 4 — Backfill cu exportul propriu, în privat

- Așteaptă exportul deja solicitat; nu porni altă cerere fără motiv.
- Descarcă-l înainte de expirarea linkului și inventariază fișierele fără să le publici.
- Inspectează JSON/HTML/imagini/atașamente și ramuri; documentează versiunea/formatul observat.
- Construiește parser idempotent cu raport de conversații, mesaje, segmente, atașamente, necunoscute și erori.
- Păstrează arhiva originală în RAW; toate testele cu arhiva reală rămân private.

## 9. Riscuri, limitări și corectări de formulare

- Nu descrie memoria semantică a unui app drept copie transcript.
- Afirmațiile despre payload-ul Android Share trebuie limitate la ceea ce confirmă documentația sau testarea directă.
- Absența unei funcții din documentația examinată se formulează ca limită a dovezilor disponibile („documentația consultată nu descrie…”), fără a deduce imposibilitatea produsului.
- Un snapshot link personal ChatGPT e accesibil oricărei persoane care îl deține; partajarea către propria aplicație locală nu înseamnă transmitere externă, dar linkul trebuie tratat ca un credential bearer și ținut privat.
- Un MCP/app ChatGPT poate extinde contextul și permite acțiuni numai când ChatGPT/clientul îl folosește; nu se presupune existența unui daemon în fundal pe telefon.
- Stocarea verbatim într-un serviciu cloud intră în conflict cu preferința local-first dacă nu este acceptată explicit. Pentru Engram, documentația spune Cloudflare; Empirical are serviciu găzduit și documentație de self-hosting.
- Arhiva reală, extrasele, hash-urile identificabile și rezultatele personale nu intră în GitHub.
- Documentația produselor se schimbă; afirmațiile de disponibilitate/cost trebuie reverificate înainte de decizie.

## 10. Decizii de proiect și întrebări deschise

### Decizii de proiect

- Arhiva exportată este import obligatoriu pentru backfill, nu singurul flux.
- Pentru capturile viitoare e acceptat checkpoint/rezumat detaliat și structurat; nu e obligatoriu transcript literal la fiecare pas.
- RAW, INDEX și DERIVED sunt straturi distincte; RAW rămâne intact.
- Conversațiile și fișierele reale se folosesc local; demonstrațiile GitHub sunt sintetice.
- ChatGPT Android este suprafața principală; Codex capture hooks sunt secundare.
- Aplicația Windows și aplicația Android au fiecare o bază locală completă; sincronizarea este bidirecțională, nu o descărcare dintr-o bază unică de pe PC.
- O conversație importată pe telefon sau pe PC se propagă la cealaltă replică la următoarea sincronizare LAN.
- Android Share poate transmite un link snapshot; PersonalMemory trebuie să primească linkul direct și să-l importe în dispozitivul care primește share-ul.
- Integrarea trebuie să fie utilă chiar din aplicația ChatGPT, fără să impună trecerea permanentă în alt chatbot.
- Căutarea din ChatGPT a memoriei PersonalMemory este o integrare distinctă de sincronizarea dintre aplicațiile Windows și Android; compatibilitatea directă cu ChatGPT Free rămâne neconfirmată.

### Întrebări deschise

- Ce payload exact transmite ChatGPT Android către un Share target PersonalMemory? Testul existent a verificat doar trimiterea către WhatsApp.
- Conține răspunsul HTTP al paginii partajate transcriptul sau acesta este construit de JavaScript?
- Cum sunt preluate și asociate imaginile și fișierele dintr-un snapshot?
- ChatGPT Android arată aplicațiile memory/plugin pe contul ChatGPT vizat și permite apelul la cerere în conversații obișnuite și Voice?
- Care app de memorie are cel mai bun compromis între transcript complet, Android UX, controlul asupra datelor și hosting?
- Ce cale de integrare pentru căutare/citire în ChatGPT este disponibilă efectiv pe planul Free și în aplicația Android?
- Cum legăm rezumatul/checkpoint-ul de mesajele exacte dacă snapshot-ul e accesibil doar ca pagină/link?
- Ce protocol de replicare, detectare a duplicatelor, reconciliere a modificărilor și retry este potrivit pentru sincronizarea bidirecțională Windows–Android?

## 11. Mediul de dezvoltare și continuitatea lucrului

În etapa de prototipare a apărut o distincție practică între istoricul conversației și accesul la fișierele proiectului. Contextul conversațional poate păstra deciziile și discuțiile anterioare, însă nu atașează automat un depozit Git sau nu schimbă rădăcina de lucru a unei sarcini deja pornite.

La 2 octombrie 2026, setarea Windows „Projectless task folder” a fost clarificată ca locație implicită pentru sarcini noi pornite în afara proiectelor; ea nu mută sarcini existente. Selectarea folderului `D:\AI` ca proiect a creat contextul de proiect, nu o conversație în sine. Pentru a lucra cu repo-ul `D:\AI\PersonalMemory`, este necesară o discuție nouă pornită în proiectul respectiv. Repo-ul rămâne copilul proiectului `D:\AI`.

În aceeași etapă, shell-ul sarcinii a eșuat la inițializare, deși runtime-ul Python inclus în Codex era prezent. Verificarea a indicat că problema nu era absența Python: procesul de shell nu pornea, iar accesul de scriere la baza SQLite din D: era refuzat pentru acea sarcină. Acest incident a întârziat verificarea/importul bazei existente; nu este o limitare funcțională a PersonalMemory și nici dovadă că ar fi necesară o unealtă externă. Implementarea trebuie executată din sarcina Codex atașată repo-ului, iar datele personale trebuie să rămână în directorul local separat.

**Implicație pentru metodă:** documentația de proiect și contextul discuției sunt complementare. Deciziile se consemnează în repo; fiecare sarcină de implementare trebuie să aibă acces explicit la folderul repo și la datele locale strict necesare. Mutarea setării implicite nu se tratează drept migrare a unei sarcini deja deschise. Utilizatorul a păstrat commit/push în OpenCode ca pas manual propriu; Codex continuă implementarea și verificările atunci când rulează în spațiul proiectului.

## 12. Jurnal incremental

| Versiune | Data | Modificare |
|---|---|---|
| 0.1 | 2026-10-01 | Sinteză inițială: origine, obiective locale, diferența export/captură, revizuirea evaluării comparative și inventarierea aplicațiilor de memorie ChatGPT, Share Android și experimente deschise. |
| 0.2 | 2026-10-02 | Înregistrarea testului Share prin link snapshot; analiza prețurilor Engram și a conectării din ChatGPT Free; separarea importului URL de interogarea memoriei; trecerea de la baza canonică unică pe PC la două replici locale cu sincronizare bidirecțională. |
| 0.3 | 2026-10-02 | Adăugarea constatărilor privind accesul Share și extractibilitatea snapshot-ului, plus lecțiile de continuitate între discuție, proiect și directorul local în Codex; documentarea blocajului de shell ca problemă de mediu observată, nu limitare a produsului. |

## Referințe

### Documentație OpenAI

1. [ChatGPT Android App FAQ](https://help.openai.com/en/articles/8142208-chatgpt-android-app-faq) — istoric, acțiuni de răspuns, Share/Copy în funcție de mesaj/context și export Android.
2. [Sharing conversations and scheduled tasks in ChatGPT](https://help.openai.com/en/articles/7925741-sharing-conversations-and-scheduled-tasks-in-chatgpt) — snapshot, share sheet pe mobil, acces la linkurile personale.
3. [Plugins in ChatGPT](https://help.openai.com/en/articles/20001256-plugins-in-chatgpt) — director disponibil pe web/desktop/mobile și variația după cont/plan.
4. [Connected apps in ChatGPT](https://help.openai.com/en/articles/11487775-connected-apps-in-chatgpt) — cum folosesc aplicațiile externe date/context în ChatGPT.
5. [Memory in ChatGPT](https://help.openai.com/en/articles/8590148-memory-in-chatgpt) — memorie, referință la istoricul conversațiilor și limitări.
6. [Exporting ChatGPT history and data](https://help.openai.com/en/articles/7260999-how-do-i-export-my-chatgpt-history-and-data) și [Android export](https://help.openai.com/en/articles/8167885-how-to-export-your-data-from-the-chatgpt-android-app) — ZIP-ul istoric și fluxul din Android.
7. [Android app-specific storage](https://developer.android.com/training/data-storage/app-specific?hl=en) — izolarea spațiului privat Android față de alte aplicații.

### Aplicații ChatGPT de memorie

8. [Engram ChatGPT listing](https://chatgpt.com/plugins/engram) și [Engram ChatGPT integration guide](https://getengram.app/docs/guides/chatgpt) — verbatim listing; explicația capturii la cerere și a importului istoric.
9. [Engram FAQ](https://getengram.app/docs/faq) și [Privacy](https://getengram.app/privacy) — Cloudflare D1/Vectorize, retenție, ștergere și acces conectoare.
10. [Empirical ChatGPT listing](https://chatgpt.com/plugins/empirical), [MCP tools](https://empirical.gauzza.com/docs/mcp-tools), [Privacy](https://empirical.gauzza.com/privacy), [Self-hosting](https://empirical.gauzza.com/docs/self-hosting).
11. [Mem](https://chatgpt.com/plugins/mem), [AI Passport](https://chatgpt.com/plugins/ai-passport), [Komplyt Zero](https://chatgpt.com/plugins/komplyt-zero), [Open Context](https://chatgpt.com/plugins/open-context).

### Soluții conexe din comparația inițială

12. [OpenAI Developer mode and MCP apps](https://help.openai.com/en/articles/12584461-developer-mode-and-mcp-apps-in-chatgpt), [Connected apps in ChatGPT](https://help.openai.com/en/articles/11487775-connected-apps-in-chatgpt), [Plugins in ChatGPT](https://help.openai.com/en/articles/20001256-plugins-in-chatgpt) — planuri, disponibilitate, suprafețe și limitele aplicațiilor/MCP personalizate.
13. [Engram ChatGPT save flow](https://getengram.app/blog/chatgpt-to-claude-shared-memory), [Engram pricing](https://getengram.app/pricing) — salvare explicită și planul gratuit/Pro, verificate la 2026-10-02.
14. [Khoj data sources](https://docs.khoj.dev/data-sources/share_your_data/), [Open WebUI ChatGPT import/export](https://docs.openwebui.com/features/chat-conversations/data-controls/import-export/), [Open WebUI phone share target](https://docs.openwebui.com/ecosystem/computer/phone-and-remote/phone-app/), [AnythingLLM document/RAG guide](https://docs.anythingllm.com/chatting-with-documents/introduction), [Memos MCP](https://usememos.com/docs/integrations/mcp), [Mem0 contextual add](https://docs.mem0.ai/features/contextual-add), [Letta stateful agents](https://docs.letta.com/concepts/stateful-agents).

---

*Actualizările ulterioare consemnează data, observația, sursa și impactul asupra concluziilor. Constatările infirmate sau revizuite rămân documentate, astfel încât evoluția cercetării să poată fi urmărită.*
