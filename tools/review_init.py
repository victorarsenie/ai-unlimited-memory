#!/usr/bin/env python3
"""Draft a repo's REVIEW.md from evidence, so it is never a copy of another repo's.

Reads the repo (package.json scripts, framework, tests, lint/type config, routes, CI,
AGENTS.md, python packaging) and prints a REVIEW.md draft to stdout: the shared skeleton
with the parts that can be derived already filled in, and the judgement parts marked TODO.

    python review_init.py --repo D:\\Web\\portfolio-nextjs [--write] [--force]

Without --write it prints. With --write it creates REVIEW.md, refusing to overwrite an
existing one unless --force. The agent is expected to refine the draft (blocking list,
do-not-raise list) before anyone reviews with it.
"""
import argparse
import json
import os
import sys


def read(path, limit=20000):
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            return fh.read(limit)
    except OSError:
        return ""


def detect(repo):
    ev = {"name": os.path.basename(repo.rstrip("\\/")), "scripts": {}, "deps": set(),
          "framework": None, "langs": [], "tests": [], "lint": [], "ci": [],
          "agents": [], "routes": [], "packages": []}

    pkg = os.path.join(repo, "package.json")
    if os.path.exists(pkg):
        ev["langs"].append("Node")
        try:
            data = json.loads(read(pkg))
        except json.JSONDecodeError:
            data = {}
        ev["scripts"] = data.get("scripts") or {}
        deps = dict(data.get("dependencies") or {})
        deps.update(data.get("devDependencies") or {})
        ev["deps"] = set(deps)
        for name, label in (("next", "Next.js"), ("react", "React"), ("vue", "Vue"),
                            ("svelte", "Svelte"), ("astro", "Astro"), ("express", "Express")):
            if name in ev["deps"]:
                ev["framework"] = ev["framework"] or label
        for name, label in (("vitest", "Vitest"), ("jest", "Jest"), ("mocha", "Mocha"),
                            ("playwright", "@playwright/test"), ("cypress", "Cypress")):
            if name in ev["deps"]:
                ev["tests"].append(label)
        for name, label in (("eslint", "ESLint"), ("prettier", "Prettier"),
                            ("@biomejs/biome", "Biome")):
            if name in ev["deps"]:
                ev["lint"].append(label)

    if os.path.exists(os.path.join(repo, "tsconfig.json")):
        ev["langs"].append("TypeScript")
    if os.path.exists(os.path.join(repo, "pyproject.toml")) or \
       os.path.exists(os.path.join(repo, "requirements.txt")):
        ev["langs"].append("Python")
        reqs = read(os.path.join(repo, "requirements.txt")) + read(os.path.join(repo, "pyproject.toml"))
        if "pytest" in reqs:
            ev["tests"].append("pytest")
    for tdir in ("tests", "test", "src/tests"):
        base = os.path.join(repo, *tdir.split("/"))
        if os.path.isdir(base) and any(f.startswith("test_") or f.endswith("_test.py")
                                       for f in os.listdir(base)):
            if "pytest" not in ev["tests"]:
                ev["tests"].append(f"pytest ({tdir}/)")
            break
    if not ev["tests"] and any(f.startswith("test_") and f.endswith(".py")
                               for f in os.listdir(repo)):
        ev["tests"].append("unittest files at the repo root")
    for name in ("AGENTS.md", "CLAUDE.md", ".cursorrules"):
        if os.path.exists(os.path.join(repo, name)):
            ev["agents"].append(name)
    for name in ("eslint.config.mjs", ".eslintrc", ".eslintrc.json", ".prettierrc", "biome.json"):
        if os.path.exists(os.path.join(repo, name)) and name not in ev["lint"]:
            ev["lint"].append(name)

    wf = os.path.join(repo, ".github", "workflows")
    if os.path.isdir(wf):
        ev["ci"] = sorted(os.listdir(wf))[:5]

    for root_name in ("app", "pages", "src/app", "src/pages"):
        base = os.path.join(repo, *root_name.split("/"))
        if not os.path.isdir(base):
            continue
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames[:] = [d for d in dirnames if d not in ("node_modules", ".next", "api")]
            if "page.tsx" in filenames or "page.ts" in filenames or "index.tsx" in filenames:
                rel = os.path.relpath(dirpath, repo).replace(os.sep, "/")
                ev["routes"].append(rel)
    ev["routes"] = sorted(set(ev["routes"]))[:12]

    for sub in ("packages", "apps"):
        base = os.path.join(repo, sub)
        if os.path.isdir(base):
            ev["packages"] = sorted(d for d in os.listdir(base)
                                    if os.path.isdir(os.path.join(base, d)))[:8]
    return ev


def script_cmd(scripts, *names):
    for n in names:
        if n in scripts:
            return f"npm run {n}"
    return None


def draft(ev):
    L = []
    add = L.append
    title = ev["name"]
    add(f"# Review rules — {title}")
    add("")
    add("What matters when reviewing a change here. `AGENTS.md` covers stack and conventions; this file")
    add("covers judgement: what to flag, what to ignore, and what blocks a merge.")
    add("")

    stack = ", ".join(x for x in [ev["framework"], *ev["langs"]] if x) or "unknown"
    add("## This repo")
    add("")
    add(f"- Stack: {stack}")
    if ev["tests"]:
        add(f"- Tests: {', '.join(ev['tests'])}")
    else:
        add("- Tests: **none detected** — decide whether that is acceptable here")
    if ev["lint"]:
        add(f"- Lint/format: {', '.join(ev['lint'])}")
    if ev["ci"]:
        add(f"- CI: {', '.join(ev['ci'])}")
    if ev["agents"]:
        add(f"- Agent rules present: {', '.join(ev['agents'])}")
    if ev["packages"]:
        add(f"- Workspaces: {', '.join(ev['packages'])}")
    if ev["routes"]:
        add(f"- Routes ({len(ev['routes'])}): {', '.join(ev['routes'][:8])}"
            + (" …" if len(ev["routes"]) > 8 else ""))
    add("")

    add("## Blocking")
    add("")
    build = script_cmd(ev["scripts"], "build")
    typecheck = script_cmd(ev["scripts"], "typecheck", "type-check", "tsc")
    lint = script_cmd(ev["scripts"], "lint")
    test = script_cmd(ev["scripts"], "test", "test:unit")
    for label, cmd in (("Broken build", build), ("Type errors", typecheck),
                       ("Failing tests", test)):
        if cmd:
            add(f"- **{label}** — `{cmd}` must pass.")
    if not any((build, typecheck, test)):
        add("- **TODO:** the command that must pass before merge (no build/test script detected).")
    if ev["routes"]:
        add("- **A route that regressed** — every route must still render, with no console or")
        add("  hydration errors, not merely a 200 response.")
    add("- **TODO:** the failure modes specific to this repo that must never merge.")
    add("- **Secrets, keys or personal data in the diff.**")
    add("")

    add("## Worth mentioning, not blocking")
    add("")
    add("- Duplication this change makes worse.")
    add("- Missing tests for behaviour that is easy to get wrong.")
    add("- Naming that will confuse the next reader.")
    add("")

    add("## Do not raise")
    add("")
    if lint:
        add(f"- Formatting, import order and style — `{lint}` owns these.")
    else:
        add("- Formatting, import order and style — tooling owns these.")
    add("- Anything in a file the change did not touch: pre-existing issues are not this change's")
    add("  job. (Anthropic's own data: 59% of recurring review findings were pre-existing code,")
    add("  which is how review loops start.)")
    add("- Taste-level preferences when the change follows the surrounding style.")
    add("")

    add("## The loop rule")
    add("")
    add("- **Three rounds maximum per change.** A third round means stop and rethink the approach.")
    add("- **Re-review only the diff** after round one, never the whole file.")
    add("- **State a finding once, as a class**, not per line.")
    add("- **Never re-raise a finding that was answered or deferred.** Put the answer here.")
    add("")

    add("## How to verify before asking for review")
    add("")
    add("Run and show the output, do not assert it:")
    add("")
    n = 1
    for label, cmd in (("Build", build), ("Types", typecheck), ("Lint", lint), ("Tests", test)):
        if cmd:
            add(f"{n}. `{cmd}`")
            n += 1
    if ev["routes"]:
        add(f"{n}. the affected route in a browser, with the console open")
    if not any((build, typecheck, lint, test)):
        add(f"{n}. **TODO:** the verification steps for this project")
    add("")

    add("## Risk tiers")
    add("")
    add("- **No human needed once checks are green:** docs, copy, comments, additive work behind a flag.")
    add("- **One reviewer:** ordinary feature work.")
    add("- **Two reviewers:** **TODO:** this repo's high-blast-radius areas — routing, layout shell,")
    add("  data, build config, deployment path.")
    add("")
    add("<!-- draft produced by tools/review_init.py; fill every TODO before first use -->")
    return "\n".join(L) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()

    repo = os.path.abspath(a.repo)
    if not os.path.isdir(repo):
        print(f"not a directory: {repo}")
        return 1
    text = draft(detect(repo))

    if not a.write:
        sys.stdout.write(text)
        return 0

    target = os.path.join(repo, "REVIEW.md")
    if os.path.exists(target) and not a.force:
        print(f"REVIEW.md already exists at {target} (use --force to overwrite)")
        return 1
    with open(target, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    print(f"wrote {target} ({text.count(chr(10))} lines, "
          f"{text.count('TODO')} TODO(s) to fill)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
