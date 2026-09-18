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
- **Shape** — pack findings as anchors (`path:line`) rather than excerpts, label
  every claim `verified` / `inferred` / `assumed`, and order stable material
  first so the prefix stays cacheable.

Bundled: **four reading-list scripts** ([below](#the-reading-list-scripts)) that
collapse the whole narrowing pass into one command for Java, Kotlin, Python, and
TypeScript repos,
and a **`.scripts/` convention** — any command worth running twice gets saved as
a parameterized script instead of retyped with slight variations every pass.

Source: [`skills/context-builder/SKILL.md`](skills/context-builder/SKILL.md).
The body stays under 500 lines; the detail lives in `references/` and loads only
when needed — [`tool-cookbook.md`](skills/context-builder/references/tool-cookbook.md)
(tool flags, `ast-grep` gotchas, Semgrep taint mode, fallbacks, `.scripts/`),
[`discovery-recipes.md`](skills/context-builder/references/discovery-recipes.md)
(search patterns by question type),
[`reading-list-scripts.md`](skills/context-builder/references/reading-list-scripts.md)
(interpreting, narrowing, and troubleshooting a script run), and
[`pack-templates.md`](skills/context-builder/references/pack-templates.md)
(delta, handoff, review, and working-set pack variants).

#### The reading-list scripts

Answer "which files should I read for X?" with a reading list of at most 200
files — the narrowing move the skill describes, packaged so it doesn't get
retyped per repo. The output is written to be handed to an agent (or read
yourself): files are grouped into **read first / then / skim if needed** by how
they were found, numbered in reading order, and each group carries a line count
so the reader knows what it is signing up for.

| Script | Reads |
|---|---|
| `search-java-sources.py` | `.java` |
| `search-kotlin-sources.py` | `.kt`, `.kts` |
| `search-python-sources.py` | `.py`, `.pyi` |
| `search-ts-sources.py` | `.ts`, `.tsx`, `.js`, `.jsx`, `.mts`, `.cts`, `.mjs`, `.cjs` |

Same CLI, same flags, same output; they differ only where the languages do. They
ship inside the skill, so installing the skill installs them — and they run
standalone just as well.

```bash
skills/context-builder/scripts/search-java-sources.py <keyword>... [root] \
  [-n 200] [--depth 5] [--fuzzy 0.8] [--all] [--no-tests] [--from-file PATH] [--json]

# Claude Code user install (for Codex, replace ~/.claude with ~/.agents):
~/.claude/skills/context-builder/scripts/search-java-sources.py AuthToken ~/work/api
~/.claude/skills/context-builder/scripts/search-kotlin-sources.py AuthToken ~/work/api
~/.claude/skills/context-builder/scripts/search-python-sources.py AuthToken ~/work/api
~/.claude/skills/context-builder/scripts/search-ts-sources.py useAuth ~/work/app
~/.claude/skills/context-builder/scripts/search-ts-sources.py billing . --no-tests
~/.claude/skills/context-builder/scripts/search-ts-sources.py 'vector store' . --json \
  | jq -r '.results[] | select(.tier=="READ FIRST") | .file'
```

Inside the skill, scripts resolve relative to the loaded `SKILL.md`: Codex
supplies that file path in its skill catalog, and Claude Code provides
`CLAUDE_SKILL_DIR`. This supports personal, project, and symlinked installs.

```
Reading list for 'mcp server' — 7 files, ~1,159 lines to read
searched 45 sources under .
Read top-down; stop as soon as the question is answered.

READ FIRST (2 files, ~172 lines) — the keyword is named or declared here
    1. java/dev/mcp/workspace/config/ServerConfig.java:86       1 mention, defines ServerConfig
    2. java/dev/mcp/workspace/transport/ServerIdentity.java:14  1 mention, uses ServerConfig

THEN (4 files, ~918 lines) — direct collaborators of the files above
    3. java/dev/mcp/workspace/transport/HttpRunner.java:20      uses ServerConfig, uses ServerIdentity, uses McpServlet
    4. java/dev/mcp/workspace/transport/McpServlet.java:41      uses ServerConfig, uses ServerIdentity, uses McpError
    5. java/dev/mcp/workspace/Main.java:18                      uses HelpRequested, uses ServerConfig
    6. java/dev/mcp/workspace/fs/WorkspaceService.java:32       uses ServerConfig

SKIM IF NEEDED (1 file, ~69 lines) — further out, reached through an on-topic type
    7. java/dev/mcp/workspace/transport/McpError.java:11        uses McpServlet
```

- **Source roots only.** It locates `src/` trees and keeps the source sets
  (`main/java`, `main/kotlin`, `test/…`, `commonMain/…`), so `build/`, `out/`,
  `target/`, `generated/` and resource dirs never reach the results. Pointing it
  straight at `some/module/src/main` works too; a repo with no `src/` layout at
  all gets a printed note and a whole-root search.
- **Keyword, however it's spelled.** `user profile`, `userProfile`,
  `USER_PROFILE` and `User-Profile` all compile to one case-insensitive pattern,
  so the spelling in the code doesn't have to be guessed.
- **Fuzzy, so a wrong guess still lands.** Matching runs against the repo's own
  vocabulary — file names and declared type names — not against raw text, because
  that's where a misspelling is recoverable: `srvconfig` scores 0.86 against
  `ServerConfig` and below 0.5 against everything else. `McpServelt` → `McpServlet`,
  `workspace svc` → `WorkspaceService`, and word order is free (`config server`).
  Hits show as `≈ServerConfig (0.86)`, discounted by similarity so they never
  outrank a real match, and a file that merely *mentions* a fuzzy match is tiered
  as a collaborator rather than a direct hit. `--fuzzy 0.9` tightens the bar,
  `--fuzzy 0` turns it off. When nothing clears the bar the error names the
  closest identifiers in the repo, which is usually the answer you wanted.
- **Direct hits, then fan-out.** Files that name the keyword score first — file
  name, package path, matching type or member declaration, mention count. Those
  seeds then pass a decaying share of their score to files that *use* their
  types and files that *define* what they import, five hops by default
  (`--depth 0` for direct hits only). That's what puts the call sites and
  collaborators on the list rather than just the obvious file.
- **Deep hops stay on the keyword.** Hop 1 follows any collaborator of a seed.
  From hop 2 on, a file only qualifies if it mentions the keyword itself or is
  reached through a type whose name carries one of the keyword's words — an
  ungated walk stops being a search and just enumerates the dependency closure,
  which in an MCP server meant pulling in every protocol value type for the query
  `mcp server`. The gate is why raising `--depth` is safe: past hop 1 the list
  grows only along on-topic edges, so most repos converge well before hop 5.
- **Tests demoted, not hidden** — tagged `[test]` at 0.3× score; `--no-tests`
  drops them.
- Every row is `path:line` anchored at the relevant declaration, so it's
  clickable. `--json` carries the same thing plus `tier`, `hops`, `score` and
  `lines_total` per file — `jq -r '.results[] | select(.tier=="READ FIRST") | .file'`
  is a ready-made read queue.

Declared names come from `ast-grep`, by node kind rather than by regex — a Java
comment containing "the record that ..." otherwise registers a type called
`that`, which then fans out to every file using that word. Needs `rg`; `fd` and
`ast-grep` each fall back (`os.walk`, a declaration regex) with a printed notice
when missing. An 1800-file JVM tree and a 250-file TS monorepo each rank in well
under a second.

**Where the TypeScript one differs**, because the language does:

- **Source roots** are `src/`, `app/`, `lib/`, `source/` and test dirs at any
  depth, so monorepos (`packages/*/src`, `apps/*/src`) work without configuration.
  `node_modules/`, `dist/`, `.next/`, `.turbo/`, `coverage/` and friends are out.
  Roots holding no JS/TS are dropped, so an Android `app/` doesn't sneak in.
- **Imports name files, not types**, so the fan-out resolves module specifiers to
  real paths and follows them *both* ways — what a seed imports and who imports
  it. Relative paths resolve through extensions and `index` files; `@/lib/auth`,
  `~/lib/auth` and `src/lib/auth` all land on the same file via longest-suffix
  matching, with no tsconfig parsing.
- **Only exported declarations** become graph symbols. Locals would make every
  `const res` an edge joining unrelated files.
- **Symbols used across more than 20% of the repo are ignored** as edges — an
  exported `Props` or `formatDate` reaches everything and so distinguishes nothing.
- **`index.ts` files that only re-export are demoted**; a barrel teaches you
  nothing. One that exports a real factory is not treated as a barrel.
- Tests, stories, `__tests__/`, `e2e/` and `cypress/` are demoted and tagged
  `[test]`, not hidden.

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
| `python3` (3.9+) | runs the bundled reading-list scripts |

```bash
brew install ripgrep fd ast-grep jq yq tree
```

Note that ast-grep's binary is `ast-grep`. It also ships an `sg` alias, but that
one is deprecated and prints a warning on every invocation.

The reading-list scripts need five tree-sitter packages on top of `python3` —
they read declarations and import edges from a real parse, and there is no regex
fallback. Those are not brew packages; `bootstrap.sh` installs them into a venv
the scripts own, which is [step 2 of installing](#2-install-the-parsers). You do
not need to install them by hand.

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

The installer links or copies the shared skill, installs its parser dependencies,
and runs the mechanical checks. Invoke it in Codex with `$context-builder`,
or select it using `/skills`. If it does not appear, restart Codex.
Codex supports symlinked skills in these locations; see the
[official skill documentation](https://learn.chatgpt.com/docs/build-skills).

The same `SKILL.md`, references, prompts, and Python scripts serve both agents.
`agents/openai.yaml` supplies Codex display metadata. The Claude plugin manifest
and `claude plugin eval` runner are Claude-specific; Codex can run the bundled
eval prompts manually against their graders. Mechanical checks run in either
environment. No global Codex configuration changes are needed.

The standalone script examples elsewhere in this README use Claude's user
path. For a Codex user install, replace `~/.claude/skills` with
`~/.agents/skills`; for a project install, use that project's skill directory.

### Claude Code (default)

Claude Code discovers skills in two places: `~/.claude/skills/` (available in
every project) and `<project>/.claude/skills/` (that project only). The command
you type comes from the **directory name**, so the installed directory must be
called `context-builder` for `/context-builder` to work. This repo keeps skills
in a plain top-level `skills/` directory, so installing is two steps: make the
directory visible to Claude, then install the parsers the bundled scripts need.

### The short way

```bash
./install.sh                        # symlink into ~/.claude/skills, all projects
./install.sh --project ~/code/app   # or into one project's .claude/skills
./install.sh --copy                 # copy instead of symlink, to pin a version
```

It does both steps and then verifies: symlinks (or copies) each skill in
`skills/`, runs `bootstrap.sh` to install the parsers, and finishes with
`score-skill.sh` so a broken install fails now rather than mid-task. It exits
non-zero if anything is wrong.

Re-running it is how you reinstall. An existing same-name skill is cleared
first — a symlink is dropped, while a real directory might hold edits this repo
has never seen, so that one is moved to `<name>.bak-<timestamp>` and the path is
printed for you to delete. If you install to project scope while a user-scope
copy exists, it says so. In Claude Code, project scope wins; in Codex, both
same-name skills can appear in the selector.

The rest of this section shows the Claude Code installation by hand.

### 1. Make it visible to Claude

Pick one of the three.

#### Symlink for personal use — recommended

Keeps this repo as the single source of truth. Edits to `SKILL.md`, the
`references/`, and the scripts take effect immediately, and `git pull` updates
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

### 2. Install the parsers

Once, per machine. The scripts re-exec into this venv themselves, so nothing
needs activating afterwards and it does not matter which shell you run them from.

```bash
~/.claude/skills/context-builder/scripts/bootstrap.sh
```

It creates `scripts/.venv`, installs `tree-sitter` and the Java, Kotlin, Python
and TypeScript grammars from `scripts/requirements.txt`, and verifies they
import. Re-running it when everything is already in place does nothing;
`--force` rebuilds the venv from scratch.

The venv is gitignored, so it does not travel with a `git clone` or a `cp -R` —
run bootstrap on each machine. Skipping this step is not silent: the scripts
exit with `error: tree_sitter is required by this script` and name the fix.

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
`SKILL.md` names exists, that the scripts are executable with the parsers
importable, and that a fuzzy keyword still lands on the right file. It exits
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

- **Java, Kotlin, Python, or TS/JS repo** — prepend: *"Run the bundled
  reading-list script first
  (`~/.claude/skills/context-builder/scripts/search-ts-sources.py <keyword>`) and
  triage from its evidence column before opening anything."* That replaces the
  whole manual narrowing pass.
- **Unsure of the vocabulary** — append: *"If my term returns zero hits, don't
  try synonyms. Tell me the closest identifiers in the repo and ask."* Stops the
  fourth-synonym spiral before it starts.
- **Task already in progress** — swap the output shape for a delta pack: *"Only
  what changed since the last pack: ledger, new findings, next action. Don't
  restate anything we already established."*
- **Handing off to another agent or a fresh session** — ask for a handoff pack:
  self-contained, assuming no shared history.
- **Two keywords, one question** — *"where do auth and retry meet"* is a single
  run: `search-ts-sources.py auth retry --all`.
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
