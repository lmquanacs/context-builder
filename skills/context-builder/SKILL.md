---
name: context-builder
description: Discover, verify, and shape the minimum context needed before acting on a task. Use whenever you must understand code, repos, docs, or files you haven't read — "where is X defined", "how does Y work", starting work in an unfamiliar area or codebase, bug hunts, tracing call sites and data flow, cross-file refactors, auditing a pattern, deciding what to read first, code review, or briefing a subagent or another agent. Covers search-tool craft (rg, fd, ast-grep, jq, yq, tree, plus Semgrep taint mode) and ships reading-list scripts that rank files by keyword for Java, Kotlin, Python, and TypeScript/JavaScript repos. Also use when the user mentions context engineering, context window, token budget, prompt caching, cost per task, running low on context, taint or dataflow tracking, or asks why an agent's answer was wrong or expensive. Prefer it over ad-hoc file reading any time a task touches more than two files — opening files to "get oriented" is what it replaces.
---

# Context Builder

Build context before you act. Four phases: **Frame → Discover → Reflect → Shape**.

## Host compatibility (Codex and Claude Code)

Resolve all bundled paths relative to the directory containing this loaded
`SKILL.md`. Set `SKILL_DIR` to that absolute directory before running examples;
do not assume a user-level install. Claude Code may provide `CLAUDE_SKILL_DIR`;
in Codex, use the skill file path supplied in the skills catalog.

Use the host's file-reading tool, or a ranged shell read such as
`sed -n '40,90p' path/to/file`, wherever this skill says to read a file.
Delegate only when subagents are available and permitted by the session;
otherwise process bounded batches locally and retain a compact findings pack.
Discovery budgets limit investigation, not completion of the user's task:
after shaping context, continue the authorized work unless the user requested
only a context pack.

## Choose the smallest workflow

- **Known file and explicit edit:** read the relevant range and act. No discovery
  round, tool inventory, ledger, or context pack is needed unless an unknown
  dependency affects the change.
- **Exact symbol, error, or endpoint:** start with a scoped literal search. Read
  the useful hit directly; do not run a directory tour first.
- **Ambiguous name or cross-file relationships:** use the discovery loop below.
  The reading-list scripts help when ranking candidates will save reading.

## Budget rules

- Budget both tool runtime and context size. A repository-wide parse or history
  scan can cost more than a scoped search; widen only when evidence requires it.
- Search to narrow the candidates, then read enough to answer the live question.
  Do not repeat searches just to complete a checklist.
- Keep enough context and time for implementation and validation after discovery.
- Per-command guidance: `references/discovery-recipes.md`.

## Phase 1 — Frame

For a discovery task, identify three things before broad reading. Keep these
internal for small tasks; share a compact plan when the task benefits from one.

**1. Context questions.** Questions with checkable answers, not topics. Three to
seven is normal.

- Bad: "understand the auth system"
- Good: "Where is the session token validated?" / "What happens on expiry?" /
  "Is there existing retry logic I'd be duplicating?"

**2. Success shape.** What the acting agent produces: a patch, a review, a
design. This decides what context is relevant.

**3. Budget.** Pick a tier and hold to it.

| Tier | Reads | Pack size | Fits |
|---|---|---|---|
| Micro | 1–3 files, ranges only | < 500 tokens | single-file edit, known location |
| Standard | 4–10 files, mostly ranges | 1.5–3k tokens | feature work, bug with a symptom |
| Deep | 10–25 files | ≤ 8k tokens | architecture review, cross-cutting refactor |

Needs more than Deep? The task is too big. Split it, one pack per piece.

## Phase 2 — Discover

### Pick the tool by the question

| Question | Tool |
|---|---|
| What does this repo/directory look like at a glance? | `tree` |
| Where does this *text* appear? | `rg` |
| What files *exist* with this name, extension, or age? | `fd` |
| Where does this *code shape* appear (calls, defs, JSX, imports)? | `ast-grep` |
| Does a value *reach* a sink (flow, not shape)? | `semgrep` taint mode |
| Something emitted JSON | `jq` |
| Something is YAML (config, CI, compose) | `yq` |
| I have <10 candidate files and need to understand them | a file-reading tool or ranged shell read |
| I have >10, and the reading *is* the work | a subagent, briefed (below) |

Use `rg` for text and `ast-grep` for structure. Switch to `ast-grep` the moment a
regex would need to care about whitespace, line breaks, nesting, or balanced
parens.

Escalate to Semgrep for dataflow — it's the only tool here that answers whether a
value *reaches* something. It isn't one of the six: check `command -v semgrep`
only when a flow question arises, and log the question as open if it's absent.

Check availability only for tools the next step needs, and reuse that result.
Use an available equivalent when appropriate; mention a fallback when it changes
coverage or confidence. A missing optional tool must not block ordinary work.

Flags, `ast-grep` gotchas, taint rules, fallbacks: `references/tool-cookbook.md`.

### Climb the ladder

Start at the cheapest rung that answers the question. Skip irrelevant rungs;
these are choices, not mandatory stages.

1. **Structure** — `tree -L 2 -I '.git|node_modules|build|dist|target'` when directory
   structure is itself an open question. Scope large directory trees first.
2. **Paths** — `fd` on names: `**/*repository*`, `**/*.config.*`. Names encode
   intent; use them before content.
3. **Content** — `rg -l` / `rg -c` for *which* and *how many* files before
   printing any match bodies, then `rg -n -C3`. 400 hits means narrow
   (`-t ts`, `-g`, `-w`), not read 400 hits.
4. **Structure confirmation** — `ast-grep` when the pattern is code-shaped.
5. **Ranged reads** — the 40 lines around the hit, not the 900-line file.
6. **Full reads** — only files that are both small and central: interfaces,
   configs, schemas, the one class the task is about.
7. **Delegated reads** — when rungs 5–6 would pull more than ~10 files into
   *this* window, send the reading to a subagent instead. Its reads cost its
   context, not yours; what comes back is a page of anchors.

Delegation adds startup and coordination costs. Use it only when permitted and
the independent read volume justifies those costs. Give it your Phase 1 questions
verbatim, name the tier, and require the Findings format from Phase 4 —
`[verified] claim — path:line`. A subagent asked to "look into" something
returns prose you then have to verify, which is worse than reading it yourself.

### Seed

- **Task names a symbol, error string, endpoint, or file** → anchor-out. Search
  the exact string, land on it, expand through callers and callees. This is the
  default; it beats browsing.
- **Task is vague, or the domain is unfamiliar** → top-down. README, entry point,
  config, directory structure. Build a map, then anchor.

Follow references one hop at a time. From an anchor, take the interface it
implements, its direct caller, and its configuration as needed. Read focused
tests when they establish the behaviour or regression that the task concerns.

### Java, Kotlin, Python, TS/JS: ranked discovery when needed

When a scoped search leaves ambiguous candidates or you need relationships, use: `search-java-sources.py` (`.java`),
`search-kotlin-sources.py` (`.kt`/`.kts`), `search-python-sources.py`
(`.py`/`.pyi`), `search-ts-sources.py` (`.ts`/`.tsx`/`.js`/`.jsx`). Not on
`PATH` — invoke by path:

```bash
# Set SKILL_DIR to the absolute directory containing this loaded SKILL.md.
"$SKILL_DIR/scripts/bootstrap.sh"                          # only if parser dependencies are missing
"$SKILL_DIR/scripts/search-ts-sources.py" <keyword>... [root]   # or -python-, -java-, -kotlin-
```

You get a reading list tiered **READ FIRST / THEN / SKIM IF NEEDED**, each row
carrying its matched line, mention count, and the relation that pulled it in.
Read top-down, stop when the question is answered. Keep the tiers and evidence
columns when you report a run — they're what makes stopping early safe.

Matching is fuzzy against the repo's own vocabulary, so a guessed or misspelled
name still lands. Use it instead of spending a round on synonyms.

On `tree_sitter is required by this script`, run `scripts/bootstrap.sh` and
retry if setup is feasible. If installation is unavailable, use scoped text
searches and reads, and label unverified structural relationships. For other
languages, use the ladder.

Output format, evidence columns, `--all` / `--from-file` / `--depth` and the rest
of the flags, troubleshooting: `references/reading-list-scripts.md`.

## Phase 3 — Reflect

Track question status after each round. For Standard/Deep discovery, keep a
compact ledger; update changed entries rather than repeatedly printing the table:

| # | Question | Status | Evidence |
|---|---|---|---|
| 1 | Where is the token validated? | answered | `auth/Filter.kt:88` |
| 2 | What happens on expiry? | partial | refresh path exists, unread |
| 3 | Existing retry logic? | open | — |

Then ask three things:

1. **Which questions are still open, and is there a specific search that closes
   them?** Run it. If you can't name the search, more reading won't help.
2. **What did this round newly expose?** Chase a new identifier only if a live
   question depends on it. Curiosity is how packs reach 40k tokens.
3. **Am I saturating?** A round that changed no statuses means further reads in
   that direction are dead weight. Change direction or stop.

### Three rounds per open question

A round is one hypothesis, however many commands it takes.

1. The user's exact vocabulary — `rg -lw 'theirTerm'`.
2. Loosened — drop `-w`, add `-i`, add `-u` (the file may be `.gitignore`d),
   widen the glob.
3. Structural or synonymous — `ast-grep` for the shape, or the two or three names
   the codebase would plausibly use instead.

No candidate file set after round 3? **Stop.** Don't start a fourth round with a
fourth synonym. Take one of two exits:

- **The user can resolve it** → ask, carrying the search.
- **They can't, or it isn't blocking** → log it under Open questions.

An open question is a legitimate output. "I could not determine X; the likely
place is Y" beats a confident guess and costs almost nothing. Never fill a gap
with plausible invention.

### Stop when

Stop discovery when the live questions are answered or its budget is spent.
A round with no progress ends that search direction, not every other question.
Use a specific alternative hypothesis within the three-round budget when useful.

- **Zero textual hits** rule out that spelling in the searched scope, not the
  concept. Check coverage and a plausible structural or synonymous alternative.
- **Several candidates** call for checking callers, configuration, or focused
  tests when those can distinguish them. Ask only when intent remains unknown.
- **Narrowing still leaves 100+ hits:** use the task's entry point or subsystem;
  ask which subsystem only if available evidence cannot establish it.
- **The answer depends on intent that isn't in the code** — which design they
  want, whether a behavior is a bug or deliberate.

### When the window is already tight

Context pressure changes what to do next, not just how much of it to do.

- **Shape early.** Write the pack now, from what you have. A pack survives
  compaction; scrollback doesn't.
- **Re-anchor, don't re-read.** After a compaction the pack *is* your context.
  Cite it. Re-open only the relevant range when edits or uncertainty make the saved
  evidence stale.
- **Delegate what's left** (rung 7), with the pack as the subagent's brief.
- **Never spend the last of the window on discovery.** Leave enough room to act,
  or you finish with perfect context and no budget to use it.

### Ask a question that carries the search

Never ask a bare "can you clarify?" — it throws away what you learned and makes
the user do the work twice. State what you looked for, what you found, and offer
the specific choice:

> `rg -lw 'sessionToken'` finds nothing. The closest things are `authToken` in
> [auth/session.ts:18](auth/session.ts#L18) and `refreshToken` in
> [auth/refresh.ts:40](auth/refresh.ts#L40). Which is the one that's expiring early?

Don't ask before running round 1 — most questions die there. Don't ask what's
derivable from what you've read. Don't ask a routine judgment call a colleague
would just make and mention: make it, say so, move on.

## Phase 4 — Shape

Write a briefing, not an archive.

- **Anchor, don't excerpt.** `auth/Filter.kt:88 — validates JWT, throws on
  expiry` beats pasting the method. Paste code only where the agent must
  reproduce exact syntax: signatures, schemas, config keys, error strings. Write
  anchors as `path/to/file.ts:42` — they're clickable.
- **Label confidence.** Mark every claim `verified` (you read it), `inferred`
  (deduced from naming or structure), or `assumed`. Unlabelled inference is how
  hallucination gets downstream.
- **Position deliberately.** Attention is strongest at start and end. Task and
  constraints first, bulk in the middle, next action last.
- **Order for cache reuse.** For a pack reused across turns, put stable material
  (conventions, schemas, map) first and volatile material (current task, latest
  findings) last. A stable prefix is a cacheable prefix.

### Pack structure

For Standard/Deep discovery, use these sections and omit empty ones:

- **Objective:** what the acting agent must produce.
- **Constraints:** conventions and behaviour that must be preserved.
- **Map:** relevant paths and their roles.
- **Findings:** `[verified] claim — path:line`; label inferences and their basis.
- **Excerpts:** only exact syntax needed for action.
- **Open questions:** unknowns and likely places to resolve them.
- **Not included:** deliberately excluded scope to avoid repeating searches.
- **Next action:** the first concrete step.

Micro discovery needs only Objective, Findings, and Next action. Routine edits
need no pack. Templates and handoff self-check: `references/pack-templates.md`.

## Anti-patterns

| Instead of | Do this |
|---|---|
| Reading files to "get oriented" | Search for the task's own words first |
| Reading the whole file | Read the range the hit is in |
| Reading every test to learn an API | Read its interface, then focused tests for behaviour |
| Printing match bodies on the first pass | `rg -l` / `rg -c` to size the blast radius |
| A fourth synonym after three rounds | Stop: ask, or log it as an open question |
| Pasting large excerpts | Anchor + one-line claim |
| Chasing every new identifier | Chase only what an open question depends on |
| Pulling 20 files into this window yourself | Delegate the reading, take back anchors |
| Investigating an adjacent problem you spotted | One line at the end, after the answer |
| Regexing toward a dataflow answer | A Semgrep taint rule, or log it open |
| Silently guessing a gap | Log it under Open questions |
| One pack for a sprawling task | Split the task, one pack each |
| Re-reading a file already in context | Cite what you already have |

## Where to go next

Open only the row that matches what you're doing.

| Scenario | Open |
|---|---|
| Empty search; a long pipeline to retype; per-language `ast-grep` patterns; a Semgrep taint rule; a missing tool's fallback | `references/tool-cookbook.md` |
| Tracing a value backward or forward; finding config, an error's origin, a convention, or a change's blast radius; unfamiliar repo with no anchor; per-command costs | `references/discovery-recipes.md` |
| Interpreting, narrowing, or troubleshooting a reading-list script run | `references/reading-list-scripts.md` |
| Delta, handoff, review, or working-set packs; the hand-off self-check; producing a pack section with a tool instead of by reading | `references/pack-templates.md` |

`prompts/` holds six ready-to-send workflow prompts that drive this loop — each
fixes the tier, states what discovery must answer, and names the result file.
Offer the matching one: `01-before-debugging`,
`02-before-planning-implementing`, `03-before-reviewing-code`,
`04-before-refactoring`, `05-for-documentation`, or
`06-for-improvement-research`.

For a Kotlin Spring Boot backend task, prefer the self-contained prompt in
`prompts/kotlin-backend-spring-boot/`: `01-design.md` for design only,
`02-plan-implement.md` for planning or authorized implementation, and
`03-code-review.md` for review only. Each combines Kotlin language, backend
system, and Spring Boot framework concerns; do not append a separate profile.

Never read a pager-backed command's output into context. Use ranged reads for files,
and disable paging explicitly (`git --no-pager diff`) or it blocks forever.
