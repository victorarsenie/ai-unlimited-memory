# Sistem personal de memorie — design

**Stare:** propunere pentru revizuire  
**Data:** 2026-10-01

## Scop

Construim incremental un sistem personal de memorie accesibil de pe Windows și Android. PC-ul găzduiește serviciile și copia principală; telefonul păstrează o copie locală, cautabilă offline, pe care o sincronizează cu PC-ul când ambele sunt conectate la aceeași rețea Wi-Fi. Accesul din afara casei poate fi adăugat ulterior printr-o rețea privată precum Tailscale.

Sistemul trebuie să păstreze sursele intacte, să arate proveniența fiecărei informații și să poată alimenta ulterior Qwen local, OpenCode și Hermes. Integrarea ChatGPT este o țintă separată: aplicațiile MCP personalizate sunt disponibile momentan în ChatGPT web, nu în aplicația mobilă; un serviciu MCP local poate necesita un tunel securizat pentru suprafețele OpenAI compatibile.

## Arhitectură propusă

- **Windows host:** serviciu local cu baza de date principală, API versionat și căutare. Serviciul ascultă numai pe rețeaua locală configurată; accesul necesită asocierea/autorizarea telefonului. Nu se configurează redirecționare de porturi.
- **Android:** aplicație proprie, instalabilă, cu bază locală/cache pentru căutare offline și coadă de sincronizare. Prima versiune a clientului va fi aleasă între PWA instalabilă și aplicație nativă după verificarea cerințelor de offline și a mediului disponibil.
- **Sincronizare:** protocolul transferă modificări identificabile, cu versiuni și proveniență, între telefon și PC. Schimbările conflictuale nu se suprascriu în tăcere; se păstrează ambele variante și se marchează pentru rezolvare.
- **Clienți AI:** API-ul este contractul comun pentru aplicațiile proprii. Un adaptor MCP separat expune operații limitate de căutare/citire și, ulterior, scriere controlată. Integrarea ChatGPT se activează doar pe suprafețele și planurile care o suportă.

## Separarea datelor

- **RAW:** fișierele originale primite/importate, păstrate byte-cu-byte și identificate prin hash. Nicio normalizare sau editare nu le modifică.
- **INDEX:** date normalizate pentru căutare și sincronizare, cu referințe către fișierele și înregistrările RAW de origine.
- **DERIVED:** text extras, fragmente, embeddings, entități, relații, rezumate și afirmații deduse. Acestea pot fi reconstruite sau marcate ca revizuite fără a modifica RAW.

Schema sursă de adevăr va include surse și importuri, conversații/documente, mesaje, persoane/entități, afirmații și relații, proveniență, fragmente de căutare și evenimente de sincronizare. Faptele extrase vor păstra referința exactă la sursa și pasajul care le justifică, precum și starea lor (derivat, verificat sau contestat).

## Import ChatGPT fără presupuneri

Nu codificăm un format de export anticipat. Importatorul va avea o interfață de adaptor și un flux în etape: inspectarea arhivei reale (lista fișierelor și structura observată), raportarea conținutului, maparea formatelor observate către un model canonic, apoi import idempotent. Arhiva originală se copiază în RAW înainte de procesare. Elemente necunoscute sunt raportate și păstrate, nu eliminate. Importul nu începe până când utilizatorul furnizează arhiva și formatul ei este inspectat.

## Căutare și knowledge graph

Prima etapă de căutare folosește full-text și filtre după sursă, dată și entități. Căutarea semantică folosește embeddings generate local, printr-un adaptor de model configurabil; indexul vectorial este derivat și regenerabil. Graful de cunoștințe păstrează entități, relații și afirmații împreună cu proveniența lor. Extracția automată nu devine fapt verificat fără confirmare.

## Interfață

Interfața Windows/Android oferă căutare, rezultate cu surse, vizualizarea conversațiilor/documentelor, explorarea entităților și relațiilor, stare de sincronizare și inspectarea provenienței. Editările și validarea afirmațiilor sunt acțiuni explicite. Interfața de pe Android folosește aceeași API și aceleași convenții de proveniență ca serviciile AI.

## Livrare incrementală

1. **Contract și nucleu local:** schema, migrații, directoarele RAW/INDEX/DERIVED, proveniența și configurarea Windows.
2. **Căutare și API:** full-text, endpointuri versionate și contractul comun pentru clienți.
3. **Client Android și sincronizare LAN:** cache local, asociere sigură, sincronizare și căutare offline.
4. **Explorare și graf:** interfață de căutare/hartă și afirmații cu proveniență.
5. **Adaptoare AI:** MCP pentru clienții locali, embeddings locale și integrarea ChatGPT acolo unde este suportată.
6. **Import ChatGPT:** după sosirea arhivei, inspectare reală și implementarea adaptorului potrivit.

Fiecare felie rămâne utilizabilă și aditivă. Importul, indexurile și datele derivate trebuie să poată fi reconstruite fără pierderea sursei brute.

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
