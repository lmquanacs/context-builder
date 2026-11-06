---
name: context-builder
description: Discover, verify, and shape the minimum context needed before acting. Use whenever you must understand code, repos, docs, or files you haven't read — "where is X defined", "how does Y work", unfamiliar codebases, bug hunts, tracing call sites and data flow, cross-file refactors, pattern audits, deciding what to read first, code review, docs with flow diagrams, or briefing a subagent. Covers rg, fd, ast-grep, jq, yq, tree, and Semgrep taint mode; separating ambiguous candidates; and labelling findings verified, inferred, or assumed. Also use for context engineering, context window or token budget, prompt caching, cost per task, running low on context, or why an agent's answer was wrong or expensive. Prefer it over ad-hoc file reading whenever a task touches more than two files.
---

# Context Builder

Build context before you act: **Frame → Discover → Reflect → Shape**.

## Host compatibility

Resolve bundled paths relative to this `SKILL.md`'s directory (`SKILL_DIR`;
Claude Code may set `CLAUDE_SKILL_DIR`, Codex gives the path in its catalog).
"Read a file" means the host's read tool or a ranged read
(`sed -n '40,90p' file`). Delegate only if subagents are available and allowed;
otherwise work in bounded local batches. Budgets cap discovery, not the task:
after shaping, continue the authorized work unless only a pack was requested.

## Choose the smallest workflow

- **Known file, explicit edit:** read the range and act. No ledger or pack.
- **Exact symbol, error, or endpoint:** scoped literal search, read the hit. No
  directory tour.
- **Ambiguous name or cross-file relationships:** run the loop below.

## Budget rules

- Budget runtime and context. Repo-wide parses and history scans cost more than
  scoped searches; widen only on evidence.
- Search to narrow, read to answer the live question; no checklist searches.
- Leave room for implementation and validation.
- Disable pagers (`git --no-pager`, `GIT_PAGER=cat`); they block forever.

## Phase 1 — Frame

Before broad reading (internally for small tasks):

1. **Context questions** with checkable answers, usually 3–7. Not "understand
   auth" but "Where is the session token validated?"
2. **Success shape:** patch, review, or design. It decides relevance.
3. **Budget tier**, held to:

| Tier | Reads | Pack | Fits |
|---|---|---|---|
| Micro | 1–3 files, ranges | < 500 tokens | single-file edit |
| Standard | 4–10 files, mostly ranges | 1.5–3k | feature, bug with a symptom |
| Deep | 10–25 files | ≤ 8k | architecture review, cross-cutting refactor |

Beyond Deep, split the task: one pack per piece.

## Phase 2 — Discover

### Tool by question

| Question | Tool |
|---|---|
| Repo shape at a glance | `tree` |
| Where does this *text* appear? | `rg` |
| Which files *exist* by name, extension, age? | `fd` |
| Where does this *code shape* appear? | `ast-grep` |
| Does a value *reach* a sink? | `semgrep` taint mode |
| JSON / YAML output or config | `jq` / `yq` |
| ≤10 candidate files to understand | ranged reads |
| >10, and the reading *is* the work | a briefed subagent |

Switch from `rg` to `ast-grep` once a regex must handle whitespace, line breaks,
nesting, or balanced parens. Semgrep is optional: check `command -v semgrep` only
for a flow question; if absent, log it open. Check only tools the next step
needs; a missing optional tool never blocks work. Flags and fallbacks:
`references/tool-cookbook.md`.

### Ladder (cheapest rung first, skip what's irrelevant)

1. **Structure** — `tree -L 2 -I '.git|node_modules|build|dist|target'`, only if
   layout is an open question.
2. **Paths** — `fd -g '*repository*'` on names; names encode intent.
3. **Content** — `rg -l` / `rg -c` before bodies, then `rg -n -C3`. 400 hits
   means narrow (`-t`, `-g`, `-w`).
4. **Shape** — `ast-grep` for code-shaped patterns.
5. **Ranged reads** — ~40 lines around the hit.
6. **Full reads** — only small, central files: interfaces, configs, schemas.
7. **Delegated reads** — when 5–6 would pull >10 files here and the volume
   justifies the overhead. Pass the Phase 1 questions verbatim, the tier, and
   require `[verified] claim — path:line`. "Look into X" returns prose you must
   re-verify.

### Seed

- **Named symbol, error, endpoint, or file** → anchor-out (default): search the
  exact string, expand through callers and callees.
- **Vague task or unfamiliar domain** → top-down: README, entry point, config,
  structure; then anchor.

Follow one hop at a time: implemented interface, direct caller, config, and
focused tests when they establish the behaviour in question.

### Several candidates

Rank with cheap signals before opening; stop once answered:

1. **Spelling** — the repo's own names for the stem:
   `rg -oIi --no-filename '\w*retry\w*' | sort | uniq -c | sort -rn | head`.
2. **Concentration** — `rg -cw 'Term'`; definer and heaviest user top the list.
3. **Definition** — the one declaration (`ast-grep`, or
   `rg -nw '(class|interface|type|def|fun|function|const|object) Term'`).
4. **Edges, one hop** — no import/call edge to the definer usually means a homonym.
5. **Tie-breakers** — reachability from the entry point, config wiring, a
   focused test, churn (`git log --oneline -5 -- path`).

Note why each was kept or dropped; that makes stopping early safe. Per-language
commands: `references/discovery-recipes.md` Recipe 8.

## Phase 3 — Reflect

For Standard/Deep, keep a compact ledger (without it packs end up both
incomplete and bloated); update only changed rows:

| # | Question | Status | Evidence |
|---|---|---|---|
| 1 | Where is the token validated? | answered | `auth/Filter.kt:88` |
| 2 | What happens on expiry? | partial | refresh path, unread |

After each round ask: Which open question has a specific search that closes it
(none nameable → more reading won't help)? Does a new identifier serve a live
question (else skip it)? Did any status change (no → change direction or stop)?

### Three rounds per open question

A round is one hypothesis: (1) the user's exact term, `rg -lw`; (2) loosened:
drop `-w`, add `-i`, `-u`, widen the glob; (3) structural or the repo's own
synonyms. No candidates after round 3 → **stop**: ask if the user can resolve
it, otherwise log it under Open questions. "Couldn't determine X; likely in Y"
beats a confident guess. Never invent.

### Stop when

Live questions are answered or the budget is spent. A dead round ends that
direction only. Zero hits rule out a spelling, not the concept. Several
candidates → callers, config, tests; ask only if intent is unknown. 100+ hits →
scope by entry point or subsystem. Intent not in the code (design choice, bug
vs. deliberate) → ask.

### Tight window

Shape the pack now (it survives compaction). Re-anchor, don't re-read: cite
the pack and re-open only stale ranges. Delegate the rest with the pack as the brief. Never
spend the last of the window on discovery.

### Confidence before acting

- A search hit proves text, not behaviour; `verified` requires reading the range.
- "This path runs" needs code plus reachability (caller, wiring, or test);
  code alone is `inferred`.
- Negative claims carry their command, scope, and blind spots (reflection, DI,
  string-built names, generated code, other repos).
- Separate direct dependents (break on rename) from indirect (behaviour changes).
- Anchors expire when you edit their file.

Load-bearing but unverified → one targeted check, or state it as a risk.

### Questions carry the search

Never a bare "can you clarify?". State what you searched and found, then offer
the choice:

> `rg -lw 'sessionToken'` finds nothing; closest are `authToken`
> ([auth/session.ts:18](auth/session.ts#L18)) and `refreshToken`
> ([auth/refresh.ts:40](auth/refresh.ts#L40)). Which is expiring early?

Not before round 1, not for derivable facts, not for routine judgment calls:
make those and say so.

## Phase 4 — Shape

A briefing, not an archive.

- **Anchor, don't excerpt:** `auth/Filter.kt:88 — validates JWT, throws on
  expiry`. Paste only exact syntax (signatures, schemas, keys, error strings).
  Use the host's link format when it has one.
- **Label every claim** `verified`, `inferred` (say from what), or `assumed`.
- **Position:** task and constraints first, bulk middle, next action last. For
  reused packs, stable material first so the prefix caches.

**Pack (Standard/Deep; omit empty):** Objective · Constraints · Map · Findings
(`[verified] claim — path:line`) · Excerpts · Open questions · Not included ·
Next action. Micro: Objective, Findings, Next action. Routine edits: none.
Templates: `references/pack-templates.md`.

### Diagrams for basic-user docs

Draw one for branching steps, handoffs, or status lifecycles; ≤5 linear steps
stay a list. Every box and arrow traces to a `verified` finding (inferred ones
are dropped or dashed and logged). Use plain reader labels ("You sign in"), not
code names; about nine boxes max. Flowchart for decisions, sequence for who
talks to whom, state for status. Use Mermaid if the target renders it, plain
text otherwise, plus a caption and numbered walkthrough. Check it renders, or
say it wasn't. Templates: `references/doc-diagrams.md`.

## Anti-patterns

| Instead of | Do |
|---|---|
| Reading to "get oriented" | Search the task's own words |
| Whole files, every test | The hit's range; interface, then focused tests |
| Match bodies first | `rg -l` / `rg -c` |
| A fourth synonym | Stop: ask or log open |
| Big excerpts | Anchor + one-line claim |
| Chasing every identifier | Only what a live question needs |
| 20 files in this window | Delegate, take back anchors |
| Adjacent problems | One line after the answer |
| Regex for dataflow | Semgrep taint, or log open |
| Hit labelled `verified` | Read the range, or `inferred` |
| "Nothing else uses it" | Show command, scope, blind spots |
| One pack for a sprawling task | Split it |
| Re-reading what's in context | Cite it |

## Where to go next

| Scenario | Open |
|---|---|
| Empty search, saved pipelines, `ast-grep` patterns, taint rules, fallbacks | `references/tool-cookbook.md` |
| Tracing values, config, error origins, blast radius, candidates, no anchor, costs | `references/discovery-recipes.md` |
| Delta, handoff, review, working-set packs; hand-off self-check | `references/pack-templates.md` |
| Flowchart, sequence, state diagrams; plain labels; render checks | `references/doc-diagrams.md` |

Workflow prompts in `prompts/`: `01-before-debugging`,
`02-before-planning-implementing`, `03-before-reviewing-code`,
`04-before-refactoring`, `05-for-documentation`, `06-for-improvement-research`.
Kotlin Spring Boot: `prompts/kotlin-backend-spring-boot/` (`01-design.md`,
`02-plan-implement.md`, `03-code-review.md`), self-contained, so no extra profile.
