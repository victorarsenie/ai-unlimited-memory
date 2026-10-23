// Memory adapter for OpenCode.
//
// Two shapes, one implementation:
//   - buildContext() -> the text to inject (memory files + knowledge map)
//   - KnowledgeIndex   -> v1 plugin shape (chat.message, synthetic part)
//
// The v2 shim in ~/.config/opencode/plugins/knowledge-index.ts imports
// buildContext() and pushes it into the model request's system parts.
//
// Reads MEMORY_HOME (default E:\AI\memory\ai-unlimited-memory).
import { appendFileSync, mkdirSync, readFileSync, readdirSync, statSync } from "node:fs";
import { execFileSync } from "node:child_process";
import { createHash } from "node:crypto";
import { tmpdir } from "node:os";
import { join } from "node:path";

const HOME = process.env.MEMORY_HOME || "E:\\AI\\memory\\ai-unlimited-memory";
const PROJECTS = join(HOME, "knowledge", "projects");
const LIMITS = { rules: 3200, profile: 1400, projects: 1800, map: 3000, overlay: 1200 };

const HEADER =
  "[memory] Always-on memory from the knowledge layer. The map survived " +
  "compaction; the conversation did not. If the task touches a topic, read " +
  "that file before answering. Save durable findings with the kb_append tool " +
  "(or kb.py append); save uncertain ones with kb_pending for review.\n\n";

// Phrases that mean the user expects this to be remembered. Deliberately
// narrow: a false positive is a reviewable line, a false negative is a lost
// detail. The candidate lands in knowledge/pending/, never in the map.
const CAPTURE_RE =
  /\b(remember|don'?t forget|note that|decision|decided|gotcha|important|save this|add to memory|for future reference|lesson learned)\b/i;

function latestUserText(messages) {
  if (!Array.isArray(messages)) return "";
  let last = null;
  for (let i = messages.length - 1; i >= 0 && !last; i--) {
    if (messages[i] && messages[i].role === "user") last = messages[i];
  }
  if (!last) return "";
  const text =
    typeof last.content === "string"
      ? last.content
      : Array.isArray(last.content)
        ? last.content
            .filter((p) => p && p.type === "text" && typeof p.text === "string")
            .map((p) => p.text)
            .join("\n")
        : "";
  // Compaction checkpoints and harness wrappers quote whole conversations and
  // match every keyword; capturing them is pure noise.
  if (!text || text.length > 2000) return "";
  if (/<conversation-checkpoint>|<summary>|<system-reminder>/.test(text)) return "";
  if (text.trimStart().startsWith("<")) return "";
  return text;
}

export function captureCandidate(messages, sessionID) {
  try {
    const text = latestUserText(messages);
    if (!text || !CAPTURE_RE.test(text)) return false;
    const clean = text.replace(/\s+/g, " ").trim().slice(0, 800);
    const digest = createHash("sha1")
      .update(clean.toLowerCase())
      .digest("hex")
      .slice(0, 12);
    const day = new Date().toISOString().slice(0, 10);
    const dir = join(HOME, "knowledge", "pending");
    mkdirSync(dir, { recursive: true });
    const file = join(dir, `${day}.md`);
    let existing = "";
    try {
      existing = readFileSync(file, "utf8");
    } catch {
      /* first capture of the day */
    }
    if (existing.includes(digest)) return false;
    const stamp = new Date().toISOString().slice(11, 19);
    appendFileSync(
      file,
      `- ${stamp} session=${sessionID} id=${digest} ${clean}\n`,
      "utf8",
    );
    log(`capture queued session=${sessionID} chars=${clean.length}`);
    return true;
  } catch (error) {
    log(`capture error: ${String(error)}`);
    return false;
  }
}

export function log(line) {
  try {
    const file = join(tmpdir(), "kb-inject.log");
    let size = 0;
    try {
      size = statSync(file).size;
    } catch {
      /* first write */
    }
    appendFileSync(
      file,
      `${new Date().toISOString()} ${line}\n`,
      size > 262144 ? { encoding: "utf8", flag: "w" } : "utf8",
    );
  } catch {
    /* logging must never break a turn */
  }
}

function readCapped(path, limit) {
  try {
    const text = readFileSync(path, "utf8").trim();
    if (!text) return "";
    if (text.length <= limit) return text;
    return text.slice(0, limit).replace(/\n[^\n]*$/, "") + "\n[truncated]";
  } catch {
    return "";
  }
}

function normPath(value) {
  return String(value).replace(/\\/g, "/").replace(/\/+$/, "").toLowerCase();
}

function parseList(raw) {
  const value = String(raw || "").trim();
  if (value.startsWith("[") && value.endsWith("]")) {
    return value
      .slice(1, -1)
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean);
  }
  return value ? [value] : [];
}

// knowledge/projects/<slug>/project.md; front matter only, no YAML dependency.
export function projectMetas() {
  let dirs = [];
  try {
    dirs = readdirSync(PROJECTS, { withFileTypes: true })
      .filter((d) => d.isDirectory())
      .map((d) => d.name)
      .sort();
  } catch {
    return [];
  }
  const out = [];
  for (const slug of dirs) {
    let raw = "";
    try {
      raw = readFileSync(join(PROJECTS, slug, "project.md"), "utf8");
    } catch {
      continue;
    }
    const fm = /^---\s*\n([\s\S]*?)\n---/.exec(raw);
    if (!fm) continue;
    const fields = {};
    for (const line of fm[1].split(/\r?\n/)) {
      const at = line.indexOf(":");
      if (at <= 0) continue;
      fields[line.slice(0, at).trim()] = line.slice(at + 1).trim();
    }
    out.push({
      slug,
      title: fields.title || slug,
      paths: parseList(fields.paths),
      remotes: parseList(fields.remotes),
    });
  }
  return out;
}

function gitRemote(cwd) {
  try {
    return execFileSync("git", ["-C", cwd, "remote", "get-url", "origin"], {
      encoding: "utf8",
      timeout: 5000,
      stdio: ["ignore", "pipe", "ignore"],
    }).trim();
  } catch {
    return "";
  }
}

// Longest matching `paths:` entry wins; otherwise compare the git origin URL.
export function detectProject(cwd = process.cwd()) {
  const here = normPath(cwd);
  const metas = projectMetas();
  let best = null;
  for (const meta of metas) {
    for (const path of meta.paths) {
      const np = normPath(path);
      if (np && (here === np || here.startsWith(np + "/"))) {
        if (!best || np.length > best.size) best = { slug: meta.slug, size: np.length };
      }
    }
  }
  if (best) return best.slug;
  const url = normPath(gitRemote(cwd)).replace(/\.git$/, "");
  if (url) {
    for (const meta of metas) {
      for (const remote of meta.remotes) {
        const nr = normPath(remote).replace(/\.git$/, "");
        if (nr && (url.includes(nr) || nr.includes(url))) return meta.slug;
      }
    }
  }
  return "";
}

export function buildContext(cwd) {
  const parts = [];
  // Rules first: harness-agnostic behaviour, the same file Hermes injects.
  const rules = readCapped(join(HOME, "memory", "rules.md"), LIMITS.rules);
  if (rules) parts.push(rules);
  for (const [name, limit] of [
    ["profile.md", LIMITS.profile],
    ["projects.md", LIMITS.projects],
  ]) {
    const text = readCapped(join(HOME, "memory", name), limit);
    if (text) parts.push(text);
  }
  const map = readCapped(join(HOME, "knowledge", "INDEX.md"), LIMITS.map);
  if (map) parts.push(map);
  // The server runs as a service, so its own cwd is not the workspace; the
  // caller passes the session directory and this falls back to cwd for tests.
  const slug = detectProject(cwd || process.cwd());
  if (slug) {
    const overlay = readCapped(join(PROJECTS, slug, "INDEX.md"), LIMITS.overlay);
    if (overlay) parts.push(overlay);
  }
  if (!parts.length) return "";
  return HEADER + parts.join("\n\n---\n\n");
}

// v1 plugin shape: synthetic part hidden from the transcript.
export const KnowledgeIndex = async () => ({
  "chat.message": async (input, output) => {
    try {
      const text = buildContext();
      if (!text) return;
      output.parts.unshift({
        id: `prt-kb-${Date.now()}`,
        sessionID: input.sessionID,
        messageID: output.message.id,
        type: "text",
        text,
        synthetic: true,
      });
      log(`v1 injected session=${input.sessionID} chars=${text.length}`);
    } catch (error) {
      log(`v1 error session=${input.sessionID}: ${String(error)}`);
    }
  },
});

export default KnowledgeIndex;
