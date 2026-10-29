# Captură prin ChatGPT Share și baze locale replicate — design

**Versiune:** 0.1  
**Data:** 2026-10-02  
**Stare:** propunere pentru revizuire înainte de implementare  
**Scop:** prima felie PersonalMemory: import explicit al unui snapshot partajat din ChatGPT Android și arhitectură Windows–Android cu copii locale independente.

## 1. Context și obiective

Testul realizat în ChatGPT Android a confirmat că Share → WhatsApp transmite un URL chatgpt.com/share/.... Deschiderea URL-ului afișează copia web a conversației partajate. Pentru conversația verificată, pagina a inclus întreaga conversație ChatGPT vizată. Conținutul ulterior discutat în Codex era într-un alt fir și nu făcea parte din acel snapshot.

Cerința actualizată este ca aplicațiile Windows și Android să păstreze fiecare o bază locală completă. O conversație salvată pe oricare dispozitiv trebuie să ajungă pe celălalt după sincronizarea în rețeaua locală, automat sau printr-o acțiune Sync. Fiecare aplicație trebuie să poată captura, căuta și citi datele sale fără ca celălalt dispozitiv să fie pornit.

Prima felie urmărește un traseu concret: ChatGPT Android → Share → PersonalMemory Android → snapshot salvat local pe telefon → sincronizare ulterioară către Windows. Importul arhivei istorice rămâne backfill separat. Interogarea memoriei PersonalMemory direct din ChatGPT este o integrare ulterioară și distinctă.

## 2. Decizii propuse

1. **Replici locale complete.** Windows și Android au fiecare baza locală și directoarele RAW/INDEX/DERIVED. Nu există o bază exclusivă pe PC.
2. **Sincronizare de conținut, nu copierea fișierului SQLite.** Fiecare dispozitiv își actualizează propria bază prin operații/înregistrări sincronizabile. Fișierul SQLite deschis nu se copiază între dispozitive.
3. **Captură locală pe telefon.** Android primește URL-ul din Sharesheet și descarcă snapshot-ul pe telefon chiar dacă serviciul Windows este oprit. Accesul la pagina Share necesită internet în acel moment; când internetul lipsește, URL-ul poate fi pus în coada locală, dar conversația nu se declară importată până nu este salvat conținutul.
4. **Client Android nativ pentru prima validare.** Android documentează primirea textului și URL-urilor prin Activity intent cu ACTION_SEND și MIME text/plain. Un Activity nativ poate accesa rețeaua și stocarea privată locală fără să depindă de CORS-ul unei pagini web. Disponibilitatea JDK/Android SDK pe mașina de build trebuie verificată înainte de prima compilare. O PWA instalabilă rămâne alternativă, dar trebuie demonstrat că poate prelua snapshot-ul cross-origin și îl poate salva pe telefon când PC-ul este indisponibil.
5. **Importer pentru snapshot, nu acces la istoricul privat ChatGPT.** Sursa este URL-ul de share și conținutul publicat la acel URL. Importerul acceptă doar domeniul și ruta Share aprobate, respinge URL-uri arbitrare și nu urmează redirecționări către domenii neaprobate.
6. **RAW intact, index separat.** Răspunsul/pagina salvată, hash-ul, momentul capturii și proveniența se păstrează în RAW/metadata. Mesajele extrase intră în INDEX; checkpoint-uri și embeddings sunt DERIVED. Nu se declară captură completă dacă parserul nu poate confirma acoperirea.
7. **Legături Share tratate ca secrete de acces.** O persoană care deține URL-ul poate vedea pagina partajată. Linkurile nu se publică, nu se scriu în loguri generale și nu se includ în Git; după importul confirmat, utilizatorul poate revoca linkul fără a șterge copia RAW locală.
8. **Sincronizare eventuală bidirecțională.** Fiecare captură are identificator stabil/hash și eveniment idempotent. Transferul din LAN copiază obiectele RAW lipsă și înregistrările persistente; indexurile FTS și embeddings locale pot fi reconstruite. Conflictele de editare nu se suprascriu în tăcere.
9. **Accesul ChatGPT la baza locală este în afara acestei felii.** MCP/API de citire necesită o integrare și accesibilitate separate. Documentația OpenAI indică limite după plan și interfață și declară MCP apps indisponibile în aplicația mobilă ChatGPT; conectarea pe planul Free nu se presupune. Aplicația PersonalMemory poate căuta local și partaja către ChatGPT fragmente cu citate ca soluție intermediară.

## 3. Fluxul de captură

1. Din conversația ChatGPT Android, utilizatorul alege Share și selectează PersonalMemory.
2. Android transmite textul/linkul partajat aplicației prin Sharesheet. Receiver-ul caută URL-ul în câmpurile intentului acceptate; nu presupune că providerul completează separat un câmp URL.
3. Aplicația validează schema HTTPS, host-ul și ruta Share înainte de orice request. O pagină de confirmare arată că se va importa conversația identificată și unde va fi păstrată.
4. Importerul descarcă pagina în fundal, fără să afișeze interfața unui browser. În prima iterație se încearcă HTTP direct; dacă mesajele sunt generate de JavaScript, se evaluează o randare încorporată fără browser vizibil.
5. Parserul extrage titlul, mesajele, rolurile, ordinea, datele și locatorii disponibili. Fișierele/imagini atașate sunt înregistrate doar dacă pagina le expune și pot fi descărcate cu proveniență; în rest raportul le marchează ca nerecuperate.
6. Importul salvează instantaneul și datele extrase local pe telefon, cu hash, metoda chatgpt_share_link și acoperirea complete, partial sau unknown. Erorile păstrează linkul într-o coadă vizibilă și nu raportează succes fals.
7. La sincronizare, aplicația schimbă cu Windows evenimentele noi și obiectele RAW lipsă. Repetarea aceluiași share nu produce o a doua conversație identică.

## 4. Modelul de date și sincronizare

- Identitățile conversației capturate, mesajelor și obiectelor RAW sunt stabile peste replici.
- Obiectele binare sunt adresate prin SHA-256; transferul sare peste obiectele cu același hash deja prezente.
- Fiecare dispozitiv are ID propriu, secvență/jurnal local de schimbări și cozi outbound/inbound. Operațiile de ingestie sunt idempotente; confirmările de recepție permit retry după întreruperi.
- Capturile-sursă sunt append-only. Modificările utilizatorului la metadate/derivate au versiune și proveniență; versiuni concurente se păstrează și se semnalează pentru reconciliere.
- Windows poate oferi endpoint-ul de sincronizare cât timp aplicația sa rulează, dar baza telefonului este completă și utilizabilă și când endpoint-ul nu este disponibil.
- Specificația exactă a protocolului (REST vs. alt transport, pairing/autorizare, protecție TLS în LAN, limitarea porturilor, reconcilierea câmpurilor editabile) se stabilește într-un ADR separat înainte de activarea sync-ului bidirecțional.

## 5. Alternative analizate

### PWA instalabilă ca Share target

Avantaje: reutilizează interfața web pe Android și Windows și poate apărea în Sharesheet după instalare. Chrome documentează share_target pentru PWA instalate. Dezavantaje: preluarea paginii ChatGPT din JavaScript poate fi împiedicată de CORS, iar folosirea serverului Windows drept proxy nu permite import complet pe telefon când PC-ul este oprit. Se păstrează ca alternativă dacă prototipul demonstrează preluare locală fiabilă.

### Android nativ (recomandat pentru prima captură)

Avantaje: primește explicit ACTION_SEND, poate descărca pagina pe telefon fără proxy-ul PC-ului și păstrează RAW/INDEX local. Dezavantaje: adaugă proiect și toolchain Android; UI-ul nu se reutilizează integral cu Windows. Alegerea atacă cerința centrală de captură offline față de PC și stocare mobilă independentă.

### Engram sau alt serviciu de memorie terț

Avantaj: integrare ChatGPT și depozit disponibil rapid. Dezavantaje: stocare cloud, limite/cost separat și captură la cerere; nu îndeplinește cerința de două replici locale controlate de PersonalMemory.

## 6. Limite și riscuri cunoscute

- Snapshot-ul publicat poate fi revocat ori inaccesibil înainte de download; în acel caz linkul se păstrează ca import eșuat/în așteptare, nu ca transcript salvat.
- Structura DOM/HTML poate să se schimbe. Importerul versionat trebuie să raporteze numărul de mesaje și acoperirea, nu să pretindă compatibilitate permanentă.
- Snapshot-ul poate să nu includă fișierele originale ori toate ramurile conversației. Captura actuală nu demonstrează importul atașamentelor.
- URL-ul Share este accesibil oricui îl deține până la revocare. Stocarea locală a copiei nu schimbă stocarea conversației originale de către ChatGPT.
- Documentația Android confirmă API-ul generic de primire a textului/URL-ului, dar nu confirmă payload-ul specific emis de ChatGPT pentru PersonalMemory; receiver-ul trebuie validat pe telefon.
- Toolchain-ul Android nu este vizibil în PATH-ul mediului de dezvoltare inspectat (java, adb, gradle nu au fost găsite). Instalarea/configurarea înainte de build rămâne o verificare necesară; nu se instalează dependențe în acest design.

## 7. Felii de implementare propuse

1. **Corectarea specificațiilor:** înlocuirea modelului PC canonical + cache Android în cerințe, design, README, plan și checklist cu două replici locale; înregistrarea ADR-ului de replicare.
2. **Prototip de captură Android:** Activity Share target pentru text/link și stocare locală; request HTTP direct către URL Share; raport de import și păstrarea RAW.
3. **Întărirea parserului:** idempotency, limite URL/redirect, acoperire, atașamente și fallback pentru pagini renderizate dinamic.
4. **Replica Windows și sincronizare:** API local autentificat, exchange de evenimente și blob-uri content-addressed, buton Sync și retry; PC-ul nu este singura copie.
5. **Căutare și acces între clienți:** căutare locală offline pe ambele dispozitive; ulterior MCP/API read-only pentru clienții compatibili, fără promisiuni de ChatGPT Free până la verificare.

## 8. Criterii de acceptare pentru prima felie

- PersonalMemory apare ca destinație pentru text/link partajat în Android Share și primește payload-ul fără a cere WhatsApp ca intermediar.
- Linkurile care nu corespund host-ului/rutei aprobate sunt respinse înainte de fetch.
- Un URL valid se descarcă și se importă fără fereastră vizibilă de browser; dacă direct HTTP nu e suficient, limitarea și alternativa de randare sunt demonstrate înainte de a declara complet.
- RAW se păstrează nemodificat; INDEX identifică mesajele; raportul arată metoda, timestamp-ul, hash-ul și completitudinea.
- Repetarea aceluiași import nu dublează conversația.
- Cu PC-ul oprit, copia telefonului rămâne căutabilă și exportabilă; după pornirea PC-ului și apăsarea Sync, aceeași conversație apare pe ambele replici.
- Datele sintetice sunt folosite în teste repetabile; linkul personal folosit la explorarea inițială nu este inclus în repo, loguri sau fixture-uri.

## 9. Referințe tehnice

- [Android Developers — Receive simple data from other apps](https://developer.android.com/develop/ui/compose/sharing/receive) — ACTION_SEND, intent filter și primirea link/text.
- [Chrome Developers — Receiving shared data with the Web Share Target API](https://developer.chrome.com/docs/capabilities/web-apis/web-share-target) — PWA instalată ca alternativă de Share target.
- [OpenAI Help — Developer mode and MCP apps in ChatGPT](https://help.openai.com/en/articles/12584461-developer-mode-and-mcp-apps-in-chatgpt) — limite MCP după plan și suprafață.

## Auto-revizuire

- Domeniul primei felii este limitat la importul explicit al unui link snapshot în copia Android; importul ZIP rămâne separat.
- Cele două replici locale sunt cerință, nu o implementare deja existentă.
- Payload-ul ChatGPT Share, parsarea raw HTTP, atașamentele și sincronizarea reală rămân de validat.
- Compatibilitatea MCP pentru planul Free nu este afirmată.
- Înainte de implementare trebuie revizuite această propunere, alternativele și ordinea feliei; protocolul final de sync rămâne ADR ulterior.
