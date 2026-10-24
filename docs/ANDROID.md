# Running the memory layer on Android (Termux)

Goal: work on **phone files**, with the phone as the host — no PC, no server — while
still getting the injected map, the rules and `kb.py` search.

## What runs where

| piece | where | note |
|---|---|---|
| OpenCode CLI | Termux | `npm i -g opencode` or the installer from opencode.ai |
| model | DeepSeek cloud | `opencode auth login`; key lives on the phone only |
| `kb.py` + adapters | cloned repo | stdlib only, root = its own directory |
| `knowledge/`, `memory/` | phone (not from git) | excluded from the repo on purpose |
| corpus sync | Syncthing, optional | phone ↔ PC, no cloud |

## Steps

```bash
pkg install python nodejs git
git clone https://github.com/victorarsenie/ai-unlimited-memory.git ~/memory
export MEMORY_HOME=~/memory          # add to ~/.bashrc
python ~/memory/kb.py index          # creates knowledge/INDEX.md if absent
```

The corpus starts empty on the phone: `knowledge/` and `memory/` are gitignored, so a
clone gives code, not notes. Two ways to fill it:

1. **Start fresh on the phone** — write notes there with `kb.py append`, keep the
   phone as its own brain. Diverges from the PC by design.
2. **Sync with the PC** — Syncthing share of `knowledge/` and `memory/` only (never
   the repo). Works while the PC is on; edits made offline merge on reconnect, and
   `kb.py dupes` catches the double writes.

## Injection on Termux

The OpenCode plugin is the same adapter; only the shim path changes:

```bash
mkdir -p ~/.config/opencode/plugins
cat > ~/.config/opencode/plugins/knowledge-index.ts <<'EOF'
import { Plugin } from "@opencode/plugin"
import { buildContext, captureCandidate } from "file:///data/data/com.termux/files/home/memory/adapters/opencode/knowledge-index.js"
export default Plugin.define({
  id: "local.knowledge-index",
  async setup(ctx) {
    await ctx.session.hook("context", async (event) => {
      captureCandidate(event.messages, event.sessionID)
      const text = buildContext()
      if (text) event.system.push({ type: "text", text, cache: { type: "ephemeral" } })
    })
  },
})
EOF
```

`buildContext()` reads `MEMORY_HOME`; the shim needs no other change.

The skill is a plain copy, no PowerShell:

```bash
mkdir -p ~/.config/opencode/skills/knowledge-base
cp ~/memory/skills/knowledge-base/SKILL.md ~/.config/opencode/skills/knowledge-base/
```

## Manual transfer (no sync daemon)

The simplest arrangement, and the one to prefer if updates are occasional: copy the
folder once, point at it, and re-copy when it matters.

1. On the PC, copy the whole `E:\AI\memory\ai-unlimited-memory` directory — code **and**
   the corpus — to the phone, e.g. `Download/memory` in shared storage.
2. In Termux: `termux-setup-storage`, then
   `export MEMORY_HOME=~/storage/shared/Download/memory`.
3. `python $MEMORY_HOME/kb.py lint` — if it reports the same counts as the PC, the copy
   is intact. `kb.py index` regenerates the maps if needed.

Notes:

- `knowledge/INDEX.md` arrives already generated, so search and the map work before
  anything is run on the phone.
- Absolute paths inside notes still say `E:\AI\...`; they are documentation, not links,
  so they simply do not resolve on Android. Relative links between notes do work.
- Treat the phone copy as read-mostly. If you write notes on the phone, copy them back
  by hand before the next transfer, or you will silently overwrite them — the one
  failure mode of a manual copy is a direction nobody wrote down.
- Keep `user.md`, `profile.md` and anything medical off the phone unless the device is
  encrypted; a one-shot copy is also a one-shot disclosure.

## Rules worth keeping

- `kb.py` is ASCII-only output and stdlib-only, so it runs unchanged on Linux;
  Windows-only branches (`ctypes.windll`, `taskkill`, `CREATE_NO_WINDOW`) are guarded.
- Personal notes on a phone are a lost-device risk: enable device encryption, and
  consider syncing only `knowledge/projects`, `models`, `workflow` — not `user.md`.
- Two corpora that both claim to be canonical will drift. Either the phone is a
  reader of the synced corpus, or it is its own brain; do not mix.
