# Running the memory layer on Android (Termux)

Goal: work on **phone files**, with the phone as the host — no PC, no server — while
still getting the injected map, the rules and `kb.py` search.

## What runs where

| piece | where | note |
|---|---|---|
| OpenCode CLI | Termux | `opencode2`, aarch64 build - see *Installing OpenCode itself* |
| model | DeepSeek cloud | `opencode auth login`; key lives on the phone only |
| `kb.py` + adapters | cloned repo | stdlib only, root = its own directory |
| `knowledge/`, `memory/` | phone (not from git) | excluded from the repo on purpose |
| corpus sync | Syncthing, optional | phone ↔ PC, no cloud |

## Before you start

Termux is the host, not an alternative to OpenCode: it is a Linux userland inside
Android, and everything below happens **inside** Termux. Install it from
[F-Droid](https://f-droid.org/packages/com.termux/) - stable 0.118.3, built and
signed by F-Droid itself; the F-Droid app is not needed, the page has a direct
APK link. The [GitHub release](https://github.com/termux/termux-app/releases/latest)
works too but is signed with a test key the Termux repo publishes, so anyone can
forge an update over it - use it only from that repo, never from a link someone
sends you. Not the Play Store: outdated build, packages that no longer resolve.
Signatures differ between channels, so switching later means uninstalling.

## Fast path: one bundle

Everything the phone needs - OpenCode 2, the code, the corpus, the shim, the
skill, the phone config - ships as one archive. On the PC:

```powershell
pwsh -File scripts/android/make-bundle.ps1     # -> E:\AI\memory\android-bundle.tar.gz, ~0.3 MB
```

`memory/profile.md` is left out; add `-WithPersonal` if the device is encrypted
and you want the assistant to know you there. Then get the file onto the phone:
USB (`adb push`, or drag it into `Download/`), or send it to yourself in WhatsApp
as a **Document** and save it to `Download/`. WhatsApp works because the archive
is small, but it means your notes transit Meta's servers - USB is the only route
where they don't. In Termux:

```bash
termux-setup-storage
cd ~/storage/downloads
tar -xzf android-bundle.tar.gz -C ~/bundle
bash ~/bundle/setup.sh
```

What `setup.sh` does, in order: installs `python curl tar xz-utils unzip ripgrep`;
resolves the newest `opencode2` aarch64 build, verifies the published SHA256 and
installs it with `dpkg`; copies the code into `~/memory` **without touching an
existing corpus** (unless `--force`); adds `MEMORY_HOME` to `~/.bashrc`; writes
the v2 plugin shim and the knowledge-base skill; puts the keyless websearch
server at `~/websearch`; writes `~/.config/opencode/opencode.jsonc`; runs
`kb.py index` and `kb.py lint`. Re-running it refreshes code and leaves notes
alone. The last step is `opencode2 auth login`, or `/connect` in the TUI.

Default model is `opencode-go/beam-free`: one of exactly two unlimited models on
Go, and the only one of the two that does not train on request data - which
matters, because the memory layer puts your notes into every request.
`iceman-contributor-free` is the other one, and it does train on them.

## Steps (manual route)

```bash
pkg install python git ripgrep
git clone https://github.com/victorarsenie/ai-unlimited-memory.git ~/memory
export MEMORY_HOME=~/memory          # add to ~/.bashrc
python ~/memory/kb.py index          # creates knowledge/INDEX.md if absent
```

OpenCode itself is installed separately, from a package rather than npm (see
below). Nothing in this repo needs Node on the phone: the adapters and `kb.py`
are Python plus plain TypeScript files.

The corpus starts empty on the phone: `knowledge/` and `memory/` are gitignored, so a
clone gives code, not notes. Two ways to fill it:

1. **Start fresh on the phone** — write notes there with `kb.py append`, keep the
   phone as its own brain. Diverges from the PC by design.
2. **Sync with the PC** — Syncthing share of `knowledge/` and `memory/` only (never
   the repo). Works while the PC is on; edits made offline merge on reconnect, and
   `kb.py dupes` catches the double writes.

## Installing OpenCode itself

`npm i -g opencode` does not work in plain Termux: OpenCode is a Bun binary and
Bun has no Android support (upstream closed it as "not planned"), so stock Bun
dies on Android's seccomp policy. The working route is the prebuilt aarch64
build from `guysoft/opencode-termux`, which cross-compiles Bun and WebKit/JSC
and patches around Android's restrictions:

| build | command | what it is |
|---|---|---|
| v2 | `opencode2` | pre-release, OpenCode 2.x on official Bun 1.4.2 - **use this** |
| v1 | `opencode` | stable, OpenCode 1.3.13 on patched Bun 1.2.13 |

They install side by side and never overwrite each other. Prefer v2: the plugin
shim below uses the v2 hook API, so v1 would need a different plugin.

```bash
# by hand: newest v2 build is v1.0.3-rc3 (2026-10-18); setup.sh resolves this itself
curl -LO https://github.com/guysoft/opencode-termux/releases/download/v1.0.3-rc3/opencode2_1.0.3rc3_aarch64.deb
dpkg -i opencode2_1.0.3rc3_aarch64.deb
opencode2 --version
```

Checked 2026-10-29: that `.deb` is 72,824,430 bytes, matches the release's
`SHA256SUMS`, declares `Architecture: aarch64` and `Depends: ripgrep`, and
unpacks to `data/data/com.termux/files/usr/bin/opencode2` plus
`libexec/opencode2/` - so `dpkg -i` installs into `$PREFIX` without root.
`pacman -U` is not a stock Termux command; use `dpkg -i` or the standalone zip.

The v2 builds are GitHub *prereleases*, so `/releases/latest` returns the v1 line
(`opencode` 1.17.9) instead. The setup script lists releases and picks the newest
`opencode2` asset rather than trusting `latest`.

The pacman and deb packages install `ripgrep` as a dependency. Known
degradations: no native file watcher (falls back to polling), `bun upgrade`
disabled, no Android release channel upstream. Release URLs change between
builds - the repo README is the source of truth, not this page.

Alternatives, if the prebuilt binary ever lags behind or misbehaves:
`proot-distro` Debian with Node 22 (the `MeanderX/opencode-android` installer),
heavier but tracks upstream normally; or SSH/a hosted server, which keeps the
phone as a client rather than a host.

## Injection on Termux

The OpenCode plugin is the same adapter; only the shim path changes. This is the
**v2** plugin API - the same shim the desktop uses, and it only loads in
`opencode2`:

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

## Merging the phone back

The phone is a capture device; the PC stays canonical. Nothing is ever copied over a
live note.

1. Export the phone copy to `E:\AI\memory\phone-inbox\<date>\` — never into `knowledge/`.
2. Compare three ways: note missing on the PC (new), `updated:` newer on the phone, or
   content differing while dates match. Review that report before writing.
3. Merge line-level under `## Evidence` — new dated lines are appended, existing ones
   are never replaced. Then `kb.py dupes`, `kb.py consolidate` (dry run), `index`, `lint`.
4. Keep the inbox folder after merging; the next export is diffed against it as well as
   against the live corpus, which is how a phone edit that never arrived gets noticed.

`updated:` decides freshness, the body decides the merge: a newer date is not a licence
to overwrite lines added after the phone was copied.

## Rules worth keeping

- `kb.py` is ASCII-only output and stdlib-only, so it runs unchanged on Linux;
  Windows-only branches (`ctypes.windll`, `taskkill`, `CREATE_NO_WINDOW`) are guarded.
- Personal notes on a phone are a lost-device risk: enable device encryption, and
  consider syncing only `knowledge/projects`, `models`, `workflow` — not `user.md`.
- Two corpora that both claim to be canonical will drift. Either the phone is a
  reader of the synced corpus, or it is its own brain; do not mix.
