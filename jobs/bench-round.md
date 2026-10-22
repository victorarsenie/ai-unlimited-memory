---
job: bench-round
reads: [knowledge/local-llm.md, knowledge/memory-and-context.md]
---

# Bench round

Before starting:

1. Read `knowledge/local-llm.md` for engines, quant sizes and measured speeds on
   this machine.
2. Confirm no competing load: no model server on 8080 other than the arm under
   test, no downloads, no games.
3. Check the round's probe is the one that matches the arm's task; a probe from
   another round silently produces null evidence.

After the round: append the table to `knowledge/local-llm.md` under Evidence with
the date and hardware, then `kb.py index`.
