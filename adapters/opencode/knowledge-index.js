# OpenCode plugin: inject the knowledge map and memory into every turn.
# Same contract as the Hermes hook: read the files, prepend once per turn.
#
# Install: copy to ~/.config/opencode/plugins/knowledge-index.js
import { readFileSync, existsSync } from "node:fs";
import { join } from "node:path";

const HOME = process.env.MEMORY_HOME || "E:\\AI\\memory\\PersonalMemory";
const LIMITS = { persona: 900, profile: 900, projects: 900, map: 3000 };

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

function context() {
  const parts = [];
  for (const [name, limit] of [
    ["persona.md", LIMITS.persona],
    ["profile.md", LIMITS.profile],
    ["projects.md", LIMITS.projects],
  ]) {
    const text = readCapped(join(HOME, "memory", name), limit);
    if (text) parts.push(text);
  }
  const map = readCapped(join(HOME, "knowledge", "INDEX.md"), LIMITS.map);
  if (map) parts.push(map);
  if (!parts.length) return "";
  return (
    "[memory] Always-on memory from the knowledge layer. The map survived " +
    "compaction; the conversation did not. If the task touches a topic, read " +
    "that file before answering.\n\n" +
    parts.join("\n\n---\n\n")
  );
}

export const KnowledgeIndex = async () => ({
  "chat.message": async (input, output) => {
    const text = context();
    if (!text) return;
    output.parts.push({
      id: `prt-kb-${Date.now()}`,
      sessionID: input.sessionID,
      messageID: output.message.id,
      type: "text",
      text,
      synthetic: true,
    });
  },
});
