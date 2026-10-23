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
import { appendFileSync, mkdirSync, readFileSync, statSync } from "node:fs";
import { createHash } from "node:crypto";
import { tmpdir } from "node:os";
import { join } from "node:path";

const HOME = process.env.MEMORY_HOME || "E:\\AI\\memory\\ai-unlimited-memory";
const LIMITS = { profile: 900, projects: 900, map: 3000 };

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

export function buildContext() {
  const parts = [];
  for (const [name, limit] of [
    ["profile.md", LIMITS.profile],
    ["projects.md", LIMITS.projects],
  ]) {
    const text = readCapped(join(HOME, "memory", name), limit);
    if (text) parts.push(text);
  }
  const map = readCapped(join(HOME, "knowledge", "INDEX.md"), LIMITS.map);
  if (map) parts.push(map);
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
