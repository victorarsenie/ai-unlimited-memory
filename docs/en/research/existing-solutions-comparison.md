# Existing-Solutions Evaluation for Personal Memory

**Checked:** 2026-10-01  
**Purpose:** determine whether an existing product covers the need or whether a custom project brings technical and user value.  
**Note:** this comparison describes documented capabilities. A feature missing from the documentation reviewed is not proof that the product cannot provide it through extensions.

## Project Requirements

- Windows PC hosts the local source of truth; Android can access it on the home network.
- Imported original data remains intact, separate from indexes and derived data.
- Lexical and semantic search results include verifiable provenance to the source conversation/document.
- Conversations and knowledge can be explored through search and a relationship map.
- The ChatGPT importer is written after inspecting the real archive, without assumptions about its format.
- The core can later serve local Qwen and clients such as OpenCode, Hermes, and ChatGPT through stable adapters.
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

## Conclusion and Decision

None of the products reviewed documents, in a single installation, the complete requested workflow: ChatGPT archive import after inspecting its real format, intact RAW preservation, rebuildable indexes, granular provenance, lexical and semantic search, relationship exploration, and shared use from PC/Android and MCP adapters.

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
