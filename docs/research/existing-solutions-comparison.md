# Evaluarea soluțiilor existente pentru Personal Memory

**Data verificării:** 2026-10-01  
**Scop:** să stabilim dacă un produs existent acoperă nevoia sau dacă proiectul propriu aduce valoare tehnică și de utilizare.  
**Notă:** comparația descrie capabilități documentate; absența unei funcții din documentația consultată nu dovedește că produsul nu o poate oferi prin extensii.

## Cerințele proiectului

- PC-ul Windows găzduiește sursa de adevăr locală, iar telefonul Android o poate accesa în rețeaua casei.
- Datele importate originale se păstrează intacte separat de indexuri și date derivate.
- Căutarea lexicală și semantică întoarce proveniență verificabilă spre conversația/documentul sursă.
- Conversațiile și cunoștințele se explorează prin căutare și hartă relațională.
- Importer-ul ChatGPT se scrie după inspectarea arhivei reale, fără presupunerea formatului; imaginile și fișierele atașate trebuie păstrate și legate de mesajul sursă.
- Nucleul poate fi folosit ulterior de modele locale precum Qwen, gpt-oss-20b și Gemma 4, precum și de clienți/agenți precum OpenCode, Hermes și ChatGPT, prin adaptoare stabile.
- Importurile, indexurile și memoria derivată pot fi reconstruite din sursele păstrate; accesul mobil și backup-ul au un comportament clar.

## Comparație

| Produs | Ce acoperă bine conform documentației | Goluri față de cerința Personal Memory |
|---|---|---|
| **Khoj** | Second brain personal self-hosted; chat și căutare în fișiere, acces prin browser și aplicații; modele locale sau cloud. [Documentație](https://docs.khoj.dev/) · [Self-host](https://docs.khoj.dev/get-started/setup/) | Nu am identificat în documentația consultată un importer dedicat arhivei ChatGPT cu păstrare RAW și provenance per mesaj sau o hartă conversațională completă cu proveniență. E candidatul cel mai apropiat pentru un prototip personal self-hosted. |
| **Open WebUI** | Knowledge bases/RAG, modele prin Ollama și API-uri compatibile, opțiuni locale; conectare la servere MCP prin Streamable HTTP. [Knowledge](https://docs.openwebui.com/features/workspace/knowledge/) · [MCP](https://docs.openwebui.com/features/extensibility/mcp/) | Este în primul rând interfață de chat și retrieval pentru colecții de documente. Documentația consultată nu descrie arhivă ChatGPT ca sursă imuabilă, provenance la nivel de mesaj și graph explorer ca un singur flux gestionat. Poate fi util ca UI/model client peste un backend separat. |
| **AnythingLLM** | Document management flexibil, documente atașate sau încorporate în RAG și alegerea de modele locale sau cloud. [Documents](https://docs.anythingllm.com/chatting-with-documents/introduction) · [Models](https://docs.anythingllm.com/setup/llm-configuration/overview) | Workspace/RAG nu echivalează automat cu un depozit canonic de conversații cu RAW păstrat, provenance fină și grafic relațional. Ar putea fi evaluat ca interfață/RAG existentă, nu presupus drept înlocuitor complet. |
| **Memos** | Aplicație self-hosted pentru notițe; server MCP integrat, cu operații de căutare/creare/actualizare pentru memo-uri. [MCP](https://usememos.com/docs/integrations/mcp) | Potrivit pentru notițe personale și MCP, dar modelul documentat este memo-centric; nu am găsit fluxul complet de import arhivă conversațională, căutare hibridă și graf cu provenance cerut aici. |
| **Mem0** | Strat de memorie pentru agenți cu API de add/search, memorie semantică și opțiuni de graph memory. [Overview](https://docs.mem0.ai/features/contextual-add) · [Graph memory](https://docs.mem0.ai/open-source/features/graph-memory) | Rezolvă memoria agentului (fapte selectate/recuperate), nu arhivarea integrală și explorabilă a conversațiilor originale, cu RAW și proveniență pe fiecare rezultat. Util ulterior ca reper/adaptor, nu ca depozit de arhivă. |
| **Letta** | Runtime pentru agenți cu stare și memorie persistentă; App Server self-hosted și integrare MCP în ecosistem. [Self-hosted App Server](https://docs.letta.com/self-hosting/app-server) · [MCP](https://docs.letta.com/platform/hosted-mcp) | Este centrat pe agenți și conversațiile lor. Cerința noastră este un depozit personal interoperabil care rămâne canonic indiferent de agentul sau clientul folosit. |

## Captura conversațiilor active (separat de arhiva istorică)

Comparația inițială de mai sus evaluează în principal backfill-ul din arhivă; nu răspunde dacă produsele captează conversația ChatGPT activă. Exportul oficial este solicitat de utilizator și livrat ulterior ca arhivă, iar documentația consultată nu descrie sincronizare locală automată per mesaj. [Export ChatGPT](https://help.openai.com/en/articles/7260999-how-do-i-export-my-chatgpt-history-and-data).

În **Codex**, există hook-ul oficial PreCompact, care poate primi transcript_path înainte de compactare. Formatul transcriptului nu este o interfață stabilă; abordarea sigură este să arhivăm copia brută accesibilă în RAW, apoi să generăm un checkpoint DERIVED cu provenance. [Hooks Codex](https://learn.chatgpt.com/docs/hooks). Acesta acoperă Codex, nu conversația din aplicația ChatGPT obișnuită.

În **ChatGPT web**, o aplicație MCP personalizată poate scrie în anumite planuri, însă MCP este disponibil pe web, nu pe mobil, și nu constituie singur un timer/background hook. [Developer mode și MCP](https://help.openai.com/en/articles/12584461-developer-mode-and-mcp-apps-in-chatgpt). Pentru web, extensia locală de browser care trimite periodic un rezumat structurat către API-ul PC-ului este o ipoteză de prototipat, nu o metodă oficială; UI-ul se poate schimba și acoperirea poate fi parțială. Pentru Android nativ nu am identificat documentat un hook echivalent; checkpoint-ul explicit într-o pagină locală rămâne fallback până la validare.

Așadar, sunt două probleme distincte: import integral pentru istoric și checkpoint-uri periodice detaliate pentru conversațiile actuale/viitoare. Rezumatul checkpoint nu este transcript; include intervalul acoperit, metoda, acoperirea și trimiteri la surse. Păstrăm RAW verbatim ori de câte ori transcriptul este accesibil.

## Aplicații de memorie conectate direct la ChatGPT

Cercetarea suplimentară a identificat aplicații de memorie în directorul ChatGPT, deci evaluarea inițială nu trebuie interpretată ca „nu există nimic care să extindă memoria ChatGPT”. Plugin-urile sunt disponibile în ChatGPT web, desktop și mobil în funcție de cont, regiune și disponibilitatea aplicației. [Director și plugin-uri ChatGPT](https://help.openai.com/en/articles/20001256-plugins-in-chatgpt)

- **Engram** este cel mai apropiat de păstrarea transcriptului: listarea ChatGPT declară stocare verbatim și căutare semantică. Ghidul propriu spune explicit că în ChatGPT capturarea este „la cerere” prin MCP și import integral al exportului; nu poate înregistra silențios fiecare mesaj, iar ChatGPT nu oferă un hook per mesaj pentru conectori. Datele sunt găzduite în Cloudflare, nu local. [Listare ChatGPT](https://chatgpt.com/plugins/engram) · [Ghid ChatGPT și limitările capturii](https://getengram.app/docs/guides/chatgpt) · [Stocare și confidențialitate](https://getengram.app/docs/faq)
- **Empirical** oferă memorie structurată/graf și MCP, cu integrare ChatGPT publicată. ChatGPT poate transmite aplicației conversații/memorii relevante pentru context, iar agentul poate scrie/căuta memorie; documentația pe care am verificat-o nu promite arhivare automată, completă și verbatim a fiecărui schimb. Serviciul găzduit procesează și stochează date externe; există ghid de self-hosting pentru operatori. [Listare ChatGPT](https://chatgpt.com/plugins/empirical) · [MCP tools](https://empirical.gauzza.com/docs/mcp-tools) · [Politica de confidențialitate](https://empirical.gauzza.com/privacy)
- **Mem** oferă notițe și knowledge base; listarea ChatGPT permite salvarea conversației ca notă și căutarea contextului. **AI Passport**, **Komplyt Zero**, **Open Context**, **VaultSage** și **Create State** sunt alte integrări din director care declară memorie/context persistent. Acestea trebuie evaluate individual pentru automatizare, export, reședința datelor și aplicația Android înainte de a fi comparate ca echivalente. [Mem](https://chatgpt.com/plugins/mem) · [AI Passport](https://chatgpt.com/plugins/ai-passport) · [Komplyt Zero](https://chatgpt.com/plugins/komplyt-zero) · [Open Context](https://chatgpt.com/plugins/open-context)

Distincția importantă: memoria nativă ChatGPT și aplicațiile conectate pot extinde contextul folosit în răspunsuri, dar nu sunt automat o arhivă locală controlată de utilizator. Documentația OpenAI spune că memoria nu reține fiecare detaliu și caută în istoricul conversațiilor doar când consideră că acel context ajută. [Memory in ChatGPT](https://help.openai.com/en/articles/8590148-memory-in-chatgpt)

**Share pe Android:** OpenAI documentează apăsarea Share, apoi crearea/copierea unui link snapshot al conversației, iar pe mobil poate apărea meniul nativ de partajare al dispozitivului. Pentru conturile personale, oricine deține linkul îl poate deschide; asta nu înseamnă că trimiterea din Share către propria aplicație îl publică altundeva, ci că linkul în sine este accesibil deținătorilor lui. [Pașii și regulile linkurilor partajate](https://help.openai.com/en/articles/7925741-sharing-conversations-and-scheduled-tasks-in-chatgpt)

## Concluzie și decizie

Există aplicații conectate ChatGPT care adaugă memorie externă, inclusiv opțiuni care declară stocarea transcriptului verbatim. Totuși, conform ghidului Engram, capturarea completă, automată, per mesaj nu este disponibilă prin aplicațiile ChatGPT: salvarea e la cerere plus importul exportului. Diferențierea Personal Memory rămâne controlul local al datelor, RAW/INDEX/DERIVED, acoperirea auditabilă și capturile structurate; acestea trebuie comparate cu integrările ChatGPT menționate și validate prin prototip.

Prin urmare, proiectul propriu este justificat, cu două limite de scope:

1. Nu reconstruim de la zero componente generice care pot fi înlocuite. Evaluăm produse existente ca UI sau clienți de modele/MCP, în special Khoj și Open WebUI.
2. Construim nucleul distinctiv: depozitul canonic RAW/INDEX/DERIVED, importerul bazat pe arhiva reală, provenance, graph-ul și API-ul/adaptoarele interoperabile.

## Valoare pentru portofoliu

Proiectul arată capacitatea de a formula și valida o nevoie, de a compara produse existente, de a proiecta limite clare între date brute și indexuri, de a implementa import reluabil și proveniență, de a integra căutare lexicală/semantică, de a oferi acces cross-device și de a expune API/MCP către mai mulți agenți. Documentația va include motivația, alternativele, arhitectura, deciziile și limitările demonstrate; nu va pretinde că oferă avantaje care nu au fost implementate și verificate.

## Surse consultate

- Khoj: [Overview](https://docs.khoj.dev/), [Self-host](https://docs.khoj.dev/get-started/setup/)
- Open WebUI: [Knowledge bases](https://docs.openwebui.com/features/workspace/knowledge/), [MCP](https://docs.openwebui.com/features/extensibility/mcp/)
- AnythingLLM: [Documents](https://docs.anythingllm.com/chatting-with-documents/introduction), [Model configuration](https://docs.anythingllm.com/setup/llm-configuration/overview)
- Memos: [MCP server](https://usememos.com/docs/integrations/mcp)
- Mem0: [Memory overview](https://docs.mem0.ai/features/contextual-add), [Graph memory](https://docs.mem0.ai/open-source/features/graph-memory)
- Letta: [Self-hosted App Server](https://docs.letta.com/self-hosting/app-server), [MCP server](https://docs.letta.com/platform/hosted-mcp)
