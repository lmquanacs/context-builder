# context-builder

Personal Claude Code and Codex tooling.

## Skills

### `context-builder`

One skill covering the whole arc from "I don't know this codebase" to "here is
exactly what the next agent needs to know." A four-phase loop — **Frame →
Discover → Reflect → Shape** — built on the premise that most bad agent output
is a context failure, not a reasoning failure: the model was missing the one
file that mattered, or it was buried under forty that didn't.

- **Frame** — turn the task into three to seven checkable questions and pick a
  budget tier before opening anything.
- **Discover** — climb the cost ladder (structure → paths → text search →
  structural search → ranged reads → full reads → delegated reads), where each
  rung costs ~10× the one below — except the last, which costs a subagent's cold
  start instead, and earns it only when the reading itself is the work.
  **`rg` for text, `ast-grep` for structure**; `fd` for files by name,
  extension or age; `jq`/`yq` for anything structured. `semgrep` is the one
  escalation off the ladder — the only tool here with dataflow, for whether a
  value *reaches* a sink rather than where a shape appears.
- **Reflect** — the phase that gets skipped. Write a ledger of question →
  status → evidence after each round. **Three rounds per open question**, then
  either ask a question that carries the search, or log it as an open question.
  An open question is a legitimate output; a confident guess is not.
  Before acting, every load-bearing finding is held to explicit **confidence
  rules**: a search hit is not verified behaviour, a claim needs a second
  independent signal, and a negative claim ("nothing else uses it") carries its
  command, scope, and blind spots.
- **Shape** — pack findings as anchors (`path:line`) rather than excerpts, label
  every claim `verified` / `inferred` / `assumed`, and order stable material
  first so the prefix stays cacheable.

No bundled parsers or ranking scripts: when a name matches several files, the
skill separates them with plain `rg` / `ast-grep` evidence — the repo's own
spelling, mention concentration, the one definition, one hop of import edges,
and tie-breakers — so every ranking decision is a command you can cite. A
**`.scripts/` convention** covers the rest: any long pipeline worth running
twice gets saved as a parameterized script instead of retyped.

Source: [`skills/context-builder/SKILL.md`](skills/context-builder/SKILL.md).
The body stays under 500 lines; the detail lives in `references/` and loads only
when needed — [`tool-cookbook.md`](skills/context-builder/references/tool-cookbook.md)
(tool flags, `ast-grep` gotchas, Semgrep taint mode, fallbacks, `.scripts/`),
[`discovery-recipes.md`](skills/context-builder/references/discovery-recipes.md)
(search patterns by question type, including separating candidates and
proving a negative), and
[`pack-templates.md`](skills/context-builder/references/pack-templates.md)
(delta, handoff, review, and working-set pack variants).

## Prerequisites

The skill assumes these are on your `PATH`:

| Tool | Purpose |
|---|---|
| [ripgrep](https://github.com/BurntSushi/ripgrep) (`rg`) | fast text search |
| [fd](https://github.com/sharkdp/fd) | fast file finding |
| [ast-grep](https://ast-grep.github.io/) | structural code search and rewrite |
| [jq](https://jqlang.github.io/jq/) | JSON querying |
| [yq](https://github.com/mikefarah/yq) | YAML querying |
| [tree](https://oldmanprogrammer.net/source.php?dir=projects/tree) | directory orientation |

```bash
brew install ripgrep fd ast-grep jq yq tree
```

Note that ast-grep's binary is `ast-grep`. It also ships an `sg` alias, but that
one is deprecated and prints a warning on every invocation.

One optional escalation, not assumed present:

| Tool | Purpose |
|---|---|
| [Semgrep](https://semgrep.dev/) (`semgrep`) | dataflow and taint — the question `ast-grep` can't answer |

```bash
brew install semgrep
```

The skill checks for it only when a flow question comes up, and logs that
question as open if it's missing. Regex is not a fallback for dataflow.

## Installing the skill

### Codex

```bash
./install.sh --codex                       # ~/.agents/skills, all projects
./install.sh --codex --project ~/code/app  # project's .agents/skills
./install.sh --codex --copy                # standalone copy, pin this version
```

The installer links or copies the shared skill and runs the mechanical checks. Invoke it in Codex with `$context-builder`,
or select it using `/skills`. If it does not appear, restart Codex.
Codex supports symlinked skills in these locations; see the
[official skill documentation](https://learn.chatgpt.com/docs/build-skills).

The same `SKILL.md`, references, and prompts serve both agents.
`agents/openai.yaml` supplies Codex display metadata. The Claude plugin manifest
and `claude plugin eval` runner are Claude-specific; Codex can run the bundled
eval prompts manually against their graders. Mechanical checks run in either
environment. No global Codex configuration changes are needed.

### Claude Code (default)

Claude Code discovers skills in two places: `~/.claude/skills/` (available in
every project) and `<project>/.claude/skills/` (that project only). The command
you type comes from the **directory name**, so the installed directory must be
called `context-builder` for `/context-builder` to work. This repo keeps skills
in a plain top-level `skills/` directory, so installing means making that
directory visible to Claude.

### The short way

```bash
./install.sh                        # symlink into ~/.claude/skills, all projects
./install.sh --project ~/code/app   # or into one project's .claude/skills
./install.sh --copy                 # copy instead of symlink, to pin a version
```

It symlinks (or copies) each skill in `skills/`, then runs `score-skill.sh`
so a broken install fails now rather than mid-task. It exits
non-zero if anything is wrong.

Re-running it is how you reinstall. An existing same-name skill is cleared
first — a symlink is dropped, while a real directory might hold edits this repo
has never seen, so that one is moved to `<name>.bak-<timestamp>` and the path is
printed for you to delete. If you install to project scope while a user-scope
copy exists, it says so. In Claude Code, project scope wins; in Codex, both
same-name skills can appear in the selector.

The rest of this section shows the Claude Code installation by hand.

### Make it visible to Claude

Pick one of the three.

#### Symlink for personal use — recommended

Keeps this repo as the single source of truth. Edits to `SKILL.md`, the
`references/`, and the prompts take effect immediately, and `git pull` updates
the installed skill.

```bash
mkdir -p ~/.claude/skills
ln -s "$(pwd)/skills/context-builder" ~/.claude/skills/context-builder
```

#### Symlink into a single project

When you only want it in one repo, and/or want to commit it for teammates:

```bash
mkdir -p /path/to/project/.claude/skills
ln -s "$(pwd)/skills/context-builder" /path/to/project/.claude/skills/context-builder
```

Symlinks don't survive a `git clone`, so to share it with a team, copy the
directory in and commit it instead:

```bash
cp -R skills/context-builder /path/to/project/.claude/skills/
```

#### Copy instead of symlink

If you'd rather pin a version and not have it move under you:

```bash
mkdir -p ~/.claude/skills
cp -R skills/context-builder ~/.claude/skills/
```

### Verify

Start a new Claude Code session — skills are picked up at session start, so an
already-running session won't see it. Then either invoke it by name with
`/context-builder`, or just ask a question it should trigger on, like
"where is X defined in this repo?"

If it doesn't show up, check that the file is at
`~/.claude/skills/context-builder/SKILL.md` (the directory name and the `name:`
field in the frontmatter should match) and that the YAML frontmatter is intact.

`claude plugin list` confirms it from outside a session:

```
Skills-directory plugins (.claude/skills/*):

  ❯ context-builder@skills-dir
    Version: 0.1.0
    Scope: user
    Status: ✔ loaded
```

And `scripts/score-skill.sh` checks the install end to end — that every path
`SKILL.md` names exists, that nothing shipped is unreachable, that the eval
fixtures still carry their planted anchors, and that the documented recipe
commands still match on this machine's `rg` and `ast-grep`. It exits
non-zero on the first thing it finds, so it also works as a commit gate.

## Use case prompt templates

Six general workflow prompts cover the situations the skill is built for. A
dedicated Kotlin backend and Spring Boot folder provides three self-contained
prompts for design, planning/implementation, and code review. Each prompt names
the skill so it loads, states a **budget tier** so it doesn't over-read, and asks
for a specific **output shape** so what comes back is a briefing rather than a
transcript of the search.

Fill the `<angle brackets>` and delete any line that doesn't apply. The two lines
that carry the most weight are the tier and the output shape — leave them out and
the agent picks its own, and the default instinct is always "read more files."

Every template ends by **writing its result to a markdown file**. That line is
not decoration: a pack that only exists in scrollback has to be rebuilt from
scratch next session, and rebuilding it costs the same tokens as building it did.
Written to a file, it survives a `/clear`, gets read by the next agent for a few
hundred tokens, and can be diffed as the work moves.

Each workflow is on disk as a standalone file, ready to copy whole:

| # | Use | File |
|---|---|---|
| 1 | Debugging | [`prompts/01-before-debugging.md`](skills/context-builder/prompts/01-before-debugging.md) |
| 2 | Planning and implementing | [`prompts/02-before-planning-implementing.md`](skills/context-builder/prompts/02-before-planning-implementing.md) |
| 3 | Reviewing code | [`prompts/03-before-reviewing-code.md`](skills/context-builder/prompts/03-before-reviewing-code.md) |
| 4 | Refactoring | [`prompts/04-before-refactoring.md`](skills/context-builder/prompts/04-before-refactoring.md) |
| 5 | Documentation | [`prompts/05-for-documentation.md`](skills/context-builder/prompts/05-for-documentation.md) |
| 6 | Improvement research | [`prompts/06-for-improvement-research.md`](skills/context-builder/prompts/06-for-improvement-research.md) |

| Tier | Reads | Use for |
|---|---|---|
| Micro | 1–3 files, ranges only | single-file edit, location already known |
| Standard | 4–10 files | most debugging, most feature work, most reviews |
| Deep | 10–25 files | architecture-wide refactors, documentation, audits |

Anything that won't fit in Deep is too big for one pass — split it and run one
prompt per piece.

### Canonical prompt set

The standalone files are the source of truth. They use one consistent shape
adapted from principal-level engineering review prompts:

1. explicit repository, scope, intent, acceptance criteria, and constraints;
2. context-builder discovery before conclusions or edits;
3. a ranked, task-specific checklist;
4. evidence and verification standards that separate facts, inferences, and
   assumptions; and
5. a durable result file with validation, limitations, and open questions.

| Prompt | Primary use | Mutation policy | Result |
|---|---|---|---|
| [Debugging investigation](skills/context-builder/prompts/01-before-debugging.md) | Diagnose a concrete failure | Diagnosis only | `debug-result.md` |
| [Software design and implementation](skills/context-builder/prompts/02-before-planning-implementing.md) | Design, plan, or implement a change | Controlled by `Mode` | `plan-result.md` plus authorized code changes |
| [Evidence-based code review](skills/context-builder/prompts/03-before-reviewing-code.md) | Review a diff or current code | Review only | `review-result.md` |
| [Refactoring design and execution](skills/context-builder/prompts/04-before-refactoring.md) | Map and sequence a refactor | Plan-only by default; `implement` is explicit | `refactor-result.md` |
| [Technical documentation](skills/context-builder/prompts/05-for-documentation.md) | Research and write accurate docs | Documentation files only | `<topic>.md` and `doc-result.md` |
| [Engineering improvement research](skills/context-builder/prompts/06-for-improvement-research.md) | Rank repository-specific opportunities | Research only | `improvement-result.md` |

For Kotlin Spring Boot backends, use one complete prompt from the dedicated
folder rather than composing separate technology fragments:

| Prompt | Primary use | Mutation policy | Result |
|---|---|---|---|
| [Design](skills/context-builder/prompts/kotlin-backend-spring-boot/01-design.md) | Architecture and detailed design | Design only | `design-result.md` |
| [Plan and implement](skills/context-builder/prompts/kotlin-backend-spring-boot/02-plan-implement.md) | Implementation planning or coding | Controlled by `Mode`; plan-only by default | `implementation-result.md` plus authorized code changes |
| [Code review](skills/context-builder/prompts/kotlin-backend-spring-boot/03-code-review.md) | Review a change across the complete stack | Review only | `review-result.md` |

Copy one prompt whole, fill its input section, and remove fields that genuinely
do not apply. Preserve its mutation policy: design and review stop before source
changes, while planning/implementation requires an explicit `implement` mode.
The output file is part of the workflow—it keeps evidence, decisions, and
validation usable across sessions.

### Adapting any of them

- **A name that matches many files** — prepend: *"Before opening anything,
  separate the candidates by definition, import edges, and tests, and tell me
  why each was kept or dropped."* That replaces reading them all to find out.
- **Unsure of the vocabulary** — append: *"If my term returns zero hits, don't
  try synonyms. Tell me the closest identifiers in the repo and ask."* Stops the
  fourth-synonym spiral before it starts.
- **Task already in progress** — swap the output shape for a delta pack: *"Only
  what changed since the last pack: ledger, new findings, next action. Don't
  restate anything we already established."*
- **Handing off to another agent or a fresh session** — ask for a handoff pack:
  self-contained, assuming no shared history.
- **You need to be sure** (a rename, a deletion, a public contract) — append:
  *"For every 'nothing else uses it' claim, show the search, the scope, and what
  it can't see."* That turns a confident guess into a checkable one.
- **A flow or security question** — append: *"Write a throwaway semgrep taint
  rule rather than more grep rounds. If semgrep isn't installed, tell me instead
  of inferring the flow."*

## Should this be a plugin?

**Half-way, deliberately.** There is a manifest at
`skills/context-builder/.claude-plugin/plugin.json`, which is why the skill shows
up as `context-builder@skills-dir` in `claude plugin list` rather than as an
anonymous directory. That much is free: it costs one small JSON file, changes no
paths, and the `ln -s` install above still works exactly as before.

What it buys is tooling that addresses the skill *by name* — `claude plugin
details context-builder@skills-dir` for a token-cost projection, and
`claude plugin eval .` for the scored behavioural runs in
`skills/context-builder/evals/`.

What it does not buy, yet, is distribution. Installing by name from a marketplace
needs a `.claude-plugin/marketplace.json` at the repo root and the manifest moved
up beside it. That move is still purely additive — a plugin expects its skills in
a top-level `skills/` directory, which is the layout here already, so nothing
moves except the manifest itself.

One wrinkle worth knowing if you make that move: with the manifest inside the
skill directory, `plugin details` reports `Skills (0)` and `~0 tok`, because it
looks for `skills/<name>/SKILL.md` beneath the manifest and this `SKILL.md` sits
at the manifest's own root. Loading is unaffected — the skill works today — but
the token accounting is blind. Moving the manifest to the repo root fixes the
count and enables the marketplace path in the same step.

So the trigger to finish the job is wanting someone else to install this by name
rather than by cloning — or adding a second skill, a slash command, or a
subagent to ship alongside it.
