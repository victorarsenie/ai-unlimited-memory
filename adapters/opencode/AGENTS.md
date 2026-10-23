# Working style

The behaviour rules are **not** kept here. They live in the memory layer, one file
for every harness:

```
E:\AI\memory\ai-unlimited-memory\memory\rules.md
```

Both adapters inject that file into every model request (OpenCode plugin
`~/.config/opencode/plugins/knowledge-index.ts`, Hermes `pre_llm_call` hook). Edit
the rules there, never here, so Hermes and OpenCode cannot drift apart.

**Fallback:** if the injected context above does not contain a section titled
`# Operating rules (every harness)`, read that file before starting work — the
plugin may be disabled or stale after an update.

This file keeps only what is specific to OpenCode: providers, permissions, models
and references, which live in `opencode.jsonc` next to it.
