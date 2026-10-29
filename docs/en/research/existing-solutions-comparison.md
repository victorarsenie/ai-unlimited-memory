# Existing-Solutions Evaluation for Personal Memory

**Checked:** 2026-10-01  
**Purpose:** determine whether an existing product covers the need or whether a custom project brings technical and user value.  
**Note:** this comparison describes documented capabilities. A feature missing from the documentation reviewed is not proof that the product cannot provide it through extensions.

## Project Requirements

- Windows PC hosts the local source of truth; Android can access it on the home network.
- Imported original data remains intact, separate from indexes and derived data.
- Lexical and semantic search results include verifiable provenance to the source conversation/document.
- Conversations and knowledge can be explored through search and a relationship map.
- The ChatGPT importer is written after inspecting the real archive, without assumptions about its format; image/file attachments must be preserved and linked to their source message.
- The core can later serve local models such as Qwen, gpt-oss-20b, and Gemma 4, as well as clients/agents such as OpenCode, Hermes, and ChatGPT through stable adapters.
- Imports, indexes, and derived memory can be rebuilt from preserved sources; mobile access and backup have clear behavior.

## Comparison

| Product | Documented strengths | Gaps against Personal Memory |
|---|---|---|
| **Khoj** | Self-hosted personal AI/second brain; chat and search over files; browser and app access; local or cloud models. [Docs](https://docs.khoj.dev/) · [Self-host](https://docs.khoj.dev/get-started/setup/) | I did not identify documented support for a dedicated ChatGPT archive importer with immutable RAW and per-message provenance, or a provenance-aware conversation graph. It is the closest candidate for a personal self-hosted prototype. |
| **Open WebUI** | Knowledge bases/RAG, models through Ollama and compatible APIs, local options, and connections to MCP servers over Streamable HTTP. [Knowledge](https://docs.openwebui.com/features/workspace/knowledge/) · [MCP](https://docs.openwebui.com/features/extensibility/mcp/) | Primarily a chat interface and retrieval layer for document collections. The reviewed documentation does not describe a single managed workflow for an immutable ChatGPT archive, message-level provenance, and graph exploration. It may work as a UI/model client over a separate backend. |
| **AnythingLLM** | Flexible document management, attached or embedded RAG documents, and local or cloud model choices. [Documents](https://docs.anythingllm.com/chatting-with-documents/introduction) · [Models](https://docs.anythingllm.com/setup/llm-configuration/overview) | Workspace/RAG does not by itself provide a canonical conversation repository with preserved RAW, fine-grained provenance, and a relationship graph. It may be evaluated as an existing UI/RAG component rather than assumed to be a complete replacement. |
| **Memos** | Self-hosted note-taking application with built-in MCP server and search/create/update operations for memos. [MCP](https://usememos.com/docs/integrations/mcp) | Useful for personal notes and MCP, but the documented model is memo-centric. I did not find the full conversation archive import, hybrid search, and provenance-aware graph requested here. |
| **Mem0** | Agent memory layer with add/search API, semantic memory, and graph-memory options. [Overview](https://docs.mem0.ai/features/contextual-add) · [Graph memory](https://docs.mem0.ai/open-source/features/graph-memory) | Solves agent memory (selected/retrieved facts), not full preservation and exploration of original conversations with RAW and per-result provenance. Useful later as a reference or adapter, not as the archive repository. |
| **Letta** | Stateful agent runtime with persistent memory, self-hosted App Server, and MCP integration in its ecosystem. [App Server](https://docs.letta.com/self-hosting/app-server) · [MCP](https://docs.letta.com/platform/hosted-mcp) | Agent-centered memory and conversations. Our need is an interoperable personal repository that stays canonical regardless of which agent or client is in use. |

## Active conversation capture (separate from historical archive)

The comparison above primarily evaluates archive backfill; it does not answer whether products capture the active ChatGPT conversation. The official export is user-requested and delivered later as an archive; the documentation reviewed does not describe automatic local per-message sync. [ChatGPT export](https://help.openai.com/en/articles/7260999-how-do-i-export-my-chatgpt-history-and-data).

In **Codex**, the official PreCompact hook can receive transcript_path before compaction. The transcript format is not a stable interface; the safer approach is to archive the accessible raw copy in RAW, then produce a provenance-linked DERIVED checkpoint. [Codex hooks](https://learn.chatgpt.com/docs/hooks). This covers Codex, not conversations in the ordinary ChatGPT app.

In **ChatGPT web**, a custom MCP app can write on certain plans, but MCP is web-only, not mobile, and is not itself a timer/background hook. [Developer mode and MCP](https://help.openai.com/en/articles/12584461-developer-mode-and-mcp-apps-in-chatgpt). A local browser extension sending periodic structured summaries to the PC API is a web prototype hypothesis, not an official method; the UI can change and coverage may be partial. For native Android, I did not identify a documented equivalent hook; an explicit checkpoint to a local page remains the fallback pending validation.

These are separate problems: full historical import and detailed periodic checkpoints for current/future conversations. A checkpoint summary is not a transcript; it records coverage interval, method, coverage status, and source links. Preserve verbatim RAW whenever the transcript is accessible.

## ChatGPT-native memory apps

Further research found memory apps in ChatGPT’s directory, so the initial comparison must not be read as “nothing can extend ChatGPT memory.” Plugins are available on ChatGPT web, desktop, and mobile subject to account, region, and app availability. [ChatGPT plugins directory](https://help.openai.com/en/articles/20001256-plugins-in-chatgpt)

- **Engram** is closest to transcript retention: its ChatGPT listing advertises verbatim storage and semantic search. Its own guide explicitly says capture in ChatGPT is on request through MCP plus one-time full export import; it cannot silently record every message, and ChatGPT provides no per-message hook for connectors. Its data is hosted on Cloudflare, not locally. [ChatGPT listing](https://chatgpt.com/plugins/engram) · [ChatGPT guide and capture limits](https://getengram.app/docs/guides/chatgpt) · [Storage and privacy](https://getengram.app/docs/faq)
- **Empirical** offers structured/graph memory and MCP with a published ChatGPT integration. ChatGPT may share relevant chats/memories for context, and the agent can write/query memory; the reviewed docs do not promise complete, verbatim automatic archiving of every exchange. The hosted service stores/processes data externally; it also documents self-hosting for operators. [ChatGPT listing](https://chatgpt.com/plugins/empirical) · [MCP tools](https://empirical.gauzza.com/docs/mcp-tools) · [Privacy policy](https://empirical.gauzza.com/privacy)
- **Mem** offers notes and a knowledge base; its ChatGPT listing supports saving a chat as a note and searching context. **AI Passport**, **Komplyt Zero**, **Open Context**, **VaultSage**, and **Create State** are other directory integrations advertising persistent memory/context. Evaluate each for automation, export, data residency, and Android availability before treating them as equivalent. [Mem](https://chatgpt.com/plugins/mem) · [AI Passport](https://chatgpt.com/plugins/ai-passport) · [Komplyt Zero](https://chatgpt.com/plugins/komplyt-zero) · [Open Context](https://chatgpt.com/plugins/open-context)

Key distinction: native ChatGPT memory and connected apps can extend context used in responses, but are not automatically a local user-controlled archive. OpenAI says Memory does not retain every detail and only searches chat history when it expects the context to help. [Memory in ChatGPT](https://help.openai.com/en/articles/8590148-memory-in-chatgpt)

**Share on Android:** OpenAI documents tapping Share, then creating/copying a conversation snapshot link; on mobile it may open the device’s native share sheet. For personal accounts, anyone who has the link can open it. This does not mean sharing to your own app publishes it elsewhere; it means the link itself is accessible to anyone who obtains it. [Shared-link steps and access](https://help.openai.com/en/articles/7925741-sharing-conversations-and-scheduled-tasks-in-chatgpt)

## Conclusion and Decision

ChatGPT-connected apps do exist for external memory, including options advertising verbatim transcript storage. However, according to Engram’s guide, complete automatic per-message capture is not available through ChatGPT apps: saving is on request plus archive import. Personal Memory’s remaining distinction is local data control, RAW/INDEX/DERIVED, auditable coverage, and structured checkpoints; these should be compared with the ChatGPT integrations listed and validated through a prototype.

Building a custom system is therefore justified, with two scope constraints:

1. Do not rebuild generic components that can be reused. Evaluate existing products as UIs or model/MCP clients, especially Khoj and Open WebUI.
2. Build the distinctive core: canonical RAW/INDEX/DERIVED repository, importer based on the real archive, provenance, graph, and interoperable API/adapters.

## Portfolio Value

The project demonstrates how to validate a need, compare existing products, define clear boundaries between raw data and indexes, implement repeatable import and provenance, integrate lexical/semantic search, provide cross-device access, and expose API/MCP to multiple agents. Documentation will include rationale, alternatives, architecture, decisions, and demonstrated limitations; it will not claim advantages that have not been implemented and verified.

## Sources Reviewed

- Khoj: [Overview](https://docs.khoj.dev/), [Self-host](https://docs.khoj.dev/get-started/setup/)
- Open WebUI: [Knowledge bases](https://docs.openwebui.com/features/workspace/knowledge/), [MCP](https://docs.openwebui.com/features/extensibility/mcp/)
- AnythingLLM: [Documents](https://docs.anythingllm.com/chatting-with-documents/introduction), [Model configuration](https://docs.anythingllm.com/setup/llm-configuration/overview)
- Memos: [MCP server](https://usememos.com/docs/integrations/mcp)
- Mem0: [Memory overview](https://docs.mem0.ai/features/contextual-add), [Graph memory](https://docs.mem0.ai/open-source/features/graph-memory)
- Letta: [Self-hosted App Server](https://docs.letta.com/self-hosting/app-server), [MCP server](https://docs.letta.com/platform/hosted-mcp)
