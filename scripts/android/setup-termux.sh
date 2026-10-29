#!/usr/bin/env bash
# Standalone OpenCode on Android: the phone is the host, the PC is never involved.
#
# Installs OpenCode 2 (aarch64 build), the ai-unlimited-memory layer, the plugin
# shim, the knowledge-base skill and a phone-sized opencode.jsonc. Run it from
# the unpacked bundle:
#
#   bash setup.sh              # keep an existing corpus and config
#   bash setup.sh --force      # overwrite corpus/config from the bundle
#   bash setup.sh --skip-opencode
#   bash setup.sh --tag v1.0.3-rc3
set -euo pipefail

BUNDLE="$(cd "$(dirname "$0")" && pwd)"
MEMDIR="$HOME/memory"
TAG="${OPENCODE_TERMUX_TAG:-}"
SKIP_OPENCODE=0
FORCE=0

while [ $# -gt 0 ]; do
  case "$1" in
    --force) FORCE=1 ;;
    --skip-opencode) SKIP_OPENCODE=1 ;;
    --tag) TAG="${2:-}"; shift ;;
    -h|--help) sed -n '2,11p' "$0"; exit 0 ;;
    *) printf 'unknown option: %s\n' "$1" >&2; exit 2 ;;
  esac
  shift
done

say() { printf '\n== %s\n' "$*"; }
die() { printf 'error: %s\n' "$*" >&2; exit 1; }

[ -d /data/data/com.termux ] || die "run this inside Termux on the phone"
[ "$(uname -m)" = "aarch64" ] || die "needs aarch64 Android; this device reports $(uname -m)"
command -v pkg >/dev/null || die "pkg not found (is this Termux?)"
[ -f "$BUNDLE/repo/kb.py" ] || die "bundle incomplete: $BUNDLE/repo/kb.py missing"

say "packages"
pkg install -y python curl tar xz-utils unzip ripgrep
command -v python >/dev/null || die "python did not install"

install_opencode2() {
  if command -v opencode2 >/dev/null; then
    say "opencode2 already present: $(opencode2 --version 2>/dev/null | head -1)"
    return 0
  fi

  say "resolving the opencode2 aarch64 release"
  eval "$(python - "$TAG" <<'PY'
import json, shlex, sys, urllib.request

tag = (sys.argv[1] if len(sys.argv) > 1 else "").strip()
base = "https://api.github.com/repos/guysoft/opencode-termux/releases"
url = base + ("/tags/" + tag if tag else "?per_page=10")
req = urllib.request.Request(url, headers={"User-Agent": "ai-memory-android-setup"})
try:
    data = json.load(urllib.request.urlopen(req, timeout=30))
except Exception as exc:
    sys.exit("github api: %s (%s)" % (exc, url))
releases = [data] if isinstance(data, dict) and "assets" in data else data

for rel in releases:
    assets = {a["name"]: a["browser_download_url"] for a in rel.get("assets", [])}
    debs = sorted(n for n in assets if n.startswith("opencode2") and "aarch64" in n and n.endswith(".deb"))
    if debs:
        pick = debs[-1]
        print("OC_TAG=%s" % shlex.quote(rel["tag_name"]))
        print("OC_ASSET=%s" % shlex.quote(pick))
        print("OC_URL=%s" % shlex.quote(assets[pick]))
        print("OC_SUMS=%s" % shlex.quote(assets.get("SHA256SUMS", "")))
        break
else:
    sys.exit("no opencode2 aarch64 .deb in the last 10 releases; pass --tag")
PY
)" || die "could not resolve a release (offline, or the asset layout changed)"

  say "downloading $OC_ASSET ($OC_TAG)"
  curl -fL --retry 3 -o "$TMPDIR/$OC_ASSET" "$OC_URL" || die "download failed: $OC_URL"

  if [ -n "${OC_SUMS:-}" ]; then
    curl -fsL -o "$TMPDIR/SHA256SUMS" "$OC_SUMS" || die "checksum list download failed"
    ( cd "$TMPDIR" && grep -F "$OC_ASSET" SHA256SUMS | sha256sum -c - ) || die "checksum mismatch for $OC_ASSET"
  else
    printf 'warning: no SHA256SUMS published for %s\n' "$OC_TAG" >&2
  fi

  case "$OC_ASSET" in
    *.deb)
      command -v dpkg >/dev/null || die "dpkg missing; install it with: pkg install dpkg"
      dpkg -i "$TMPDIR/$OC_ASSET" || die "dpkg -i failed"
      ;;
    *) die "unexpected asset type: $OC_ASSET" ;;
  esac

  rm -f "$TMPDIR/$OC_ASSET" "$TMPDIR/SHA256SUMS"
  command -v opencode2 >/dev/null || die "opencode2 is still not on PATH after install"
  say "installed opencode2 $(opencode2 --version 2>/dev/null | head -1)"
}

install_repo() {
  local src="$BUNDLE/repo" dst="$MEMDIR"
  mkdir -p "$dst"

  # Code is always refreshed from the bundle.
  local item
  for item in adapters examples jobs skills src tasks tools docs; do
    [ -e "$src/$item" ] || continue
    rm -rf "${dst:?}/$item"
    cp -a "$src/$item" "$dst/"
  done
  for item in "$src"/*.md "$src"/kb.py; do
    [ -e "$item" ] && cp -a "$item" "$dst/"
  done

  # The corpus is the only thing worth protecting: never overwrite it silently.
  for item in knowledge memory; do
    if [ -e "$dst/$item" ] && [ "$FORCE" -eq 0 ]; then
      say "kept existing $dst/$item (use --force to replace it from the bundle)"
    else
      rm -rf "${dst:?}/$item"
      cp -a "$src/$item" "$dst/"
    fi
  done
}

write_shim() {
  mkdir -p "$HOME/.config/opencode/plugins"
  cat > "$HOME/.config/opencode/plugins/knowledge-index.ts" <<EOF
// Written by ai-unlimited-memory scripts/android/setup-termux.sh
// Implementation: $MEMDIR/adapters/opencode/knowledge-index.js
// v2 plugin API - loads in opencode2 only. On the phone the process cwd is the
// workspace, so buildContext() needs no directory argument.
import { Plugin } from "@opencode/plugin"
import { buildContext, captureCandidate, log } from "file://$MEMDIR/adapters/opencode/knowledge-index.js"

export default Plugin.define({
  id: "local.knowledge-index",
  async setup(ctx) {
    await ctx.session.hook("context", async (event) => {
      try {
        captureCandidate(event.messages, event.sessionID)
        const text = buildContext()
        if (!text) return
        event.system.push({ type: "text", text, cache: { type: "ephemeral" } })
        log("android injected session=" + event.sessionID + " chars=" + text.length)
      } catch (error) {
        log("android error session=" + event.sessionID + ": " + String(error))
      }
    })
  },
})
EOF
}

write_config() {
  mkdir -p "$HOME/.config/opencode"
  local target="$HOME/.config/opencode/opencode.jsonc"
  if [ -f "$target" ] && [ "$FORCE" -eq 0 ]; then
    sed "s|__HOME__|$HOME|g" "$BUNDLE/config/opencode.jsonc" > "$target.new"
    say "existing config kept; the phone version is next to it as opencode.jsonc.new"
  else
    sed "s|__HOME__|$HOME|g" "$BUNDLE/config/opencode.jsonc" > "$target"
    say "wrote $target"
  fi
}

install_websearch() {
  [ -f "$BUNDLE/websearch/server.py" ] || return 0
  mkdir -p "$HOME/websearch"
  cp "$BUNDLE/websearch/server.py" "$HOME/websearch/server.py"
}

[ "$SKIP_OPENCODE" -eq 1 ] || install_opencode2

say "memory layer -> $MEMDIR"
install_repo

if ! grep -q 'MEMORY_HOME' "$HOME/.bashrc" 2>/dev/null; then
  printf '\nexport MEMORY_HOME=%s\n' "$MEMDIR" >> "$HOME/.bashrc"
  say "added MEMORY_HOME to ~/.bashrc (new shells only)"
fi
export MEMORY_HOME="$MEMDIR"

say "plugin shim and skill"
write_shim
mkdir -p "$HOME/.config/opencode/skills/knowledge-base"
cp "$MEMDIR/skills/knowledge-base/SKILL.md" "$HOME/.config/opencode/skills/knowledge-base/"

say "websearch server"
install_websearch

say "config"
write_config

say "index and check the corpus"
python "$MEMDIR/kb.py" index
python "$MEMDIR/kb.py" lint || printf 'lint reported problems - read them before trusting the corpus\n'
python "$MEMDIR/kb.py" stats 2>/dev/null | head -8 || true

cat <<EOF

== done
Next, on the phone:

  1. opencode2 auth login      # OpenCode Go key, or /connect inside the TUI
  2. cd ~/some-project && opencode2

Notes:
  - the default model is opencode-go/beam-free: unlimited on Go, and the only one
    of the two free models that does not train on request data
  - the memory layer injects rules + map into every request, so the first turn
    is slower than a bare OpenCode
  - the corpus on the phone is a copy: merge notes back on the PC, never the
    other way round (see docs/ANDROID.md)
EOF
