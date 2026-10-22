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
import { appendFileSync, readFileSync, statSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const HOME = process.env.MEMORY_HOME || "E:\\AI\\memory\\ai-unlimited-memory";
const LIMITS = { profile: 900, projects: 900, map: 3000 };

const HEADER =
  "[memory] Always-on memory from the knowledge layer. The map survived " +
  "compaction; the conversation did not. If the task touches a topic, read " +
  "that file before answering. Append durable findings with kb.py in the same " +
  "turn.\n\n";

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
