# Evaluarea soluțiilor existente pentru Personal Memory

**Data verificării:** 2026-10-01  
**Scop:** să stabilim dacă un produs existent acoperă nevoia sau dacă proiectul propriu aduce valoare tehnică și de utilizare.  
**Notă:** comparația descrie capabilități documentate; absența unei funcții din documentația consultată nu dovedește că produsul nu o poate oferi prin extensii.

## Cerințele proiectului

- PC-ul Windows găzduiește sursa de adevăr locală, iar telefonul Android o poate accesa în rețeaua casei.
- Datele importate originale se păstrează intacte separat de indexuri și date derivate.
- Căutarea lexicală și semantică întoarce proveniență verificabilă spre conversația/documentul sursă.
- Conversațiile și cunoștințele se explorează prin căutare și hartă relațională.
- Importer-ul ChatGPT se scrie după inspectarea arhivei reale, fără presupunerea formatului.
- Nucleul poate fi folosit ulterior de un model local Qwen și de clienți precum OpenCode, Hermes și ChatGPT, prin adaptoare stabile.
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

## Concluzie și decizie

Niciunul dintre produsele evaluate nu documentează, dintr-o singură instalare, întregul flux cerut: arhivă ChatGPT importată după inspectarea formatului real, sursă RAW păstrată intact, indexuri reconstruibile, proveniență granulară, căutare lexicală și semantică, explorare relațională și utilizare comună de pe PC/Android și prin adaptoare MCP.

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
