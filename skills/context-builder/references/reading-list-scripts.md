# Reading-List Scripts

For Java, Kotlin, Python, and TypeScript/JavaScript repos, a bundled script can combine
rungs 2–4 of the Phase 2 ladder (`fd` on names → `rg -l`/`rg -c` → `ast-grep`
confirmation). It parses the repo and returns a ranked reading list instead of
a pile of hits.

SKILL.md carries the invocation. This file carries the output format, the
ranking model, and the flags — open it when you need to interpret a run or
narrow one that came back too wide.

| Language | Script | Extensions |
|---|---|---|
| Java | `search-java-sources.py` | `.java` |
| Kotlin | `search-kotlin-sources.py` | `.kt`, `.kts` |
| Python | `search-python-sources.py` | `.py`, `.pyi` |
| TypeScript / JavaScript | `search-ts-sources.py` | `.ts`, `.tsx`, `.js`, `.jsx` |

Same CLI, same flags, same output across all four. In a mixed JVM module run
the Java and Kotlin scripts **separately** — each reads only its own extensions,
so a Kotlin service with Java interfaces needs both runs. The same applies to a
Python service with a TypeScript frontend.

What counts as an edge differs by language, because what a module *is* differs.
Java and Kotlin fan out along types; TS/JS along exported symbols and resolved
import paths; Python along module-level definitions and dotted import paths,
with `subclasses` and `decorated by` as its two strongest edges — a decorator
reference is the Python signal that a file is genuinely wired into a framework
rather than merely naming it.

## Invocation

They are not on `PATH`. Set `SKILL_DIR` to the absolute directory containing the
loaded `SKILL.md` (from Codex's skill catalog or Claude Code's
`CLAUDE_SKILL_DIR`), then invoke by path. This also works for project installs:

```bash
# SKILL_DIR is the loaded skill's directory, not the current project directory.
"$SKILL_DIR/scripts/bootstrap.sh"                              # only if dependencies are missing
"$SKILL_DIR/scripts/search-java-sources.py"   <keyword>... [root]
"$SKILL_DIR/scripts/search-kotlin-sources.py" <keyword>... [root]
"$SKILL_DIR/scripts/search-python-sources.py" <keyword>... [root]
"$SKILL_DIR/scripts/search-ts-sources.py"     <keyword>... [root]
```

`bootstrap.sh` is one-time setup: it creates `scripts/.venv` and installs the
tree-sitter parsers the scripts require, because structure comes from a real
parse and there is **no regex fallback**. Nothing needs activating afterwards —
the scripts re-exec into that venv themselves.

## Reading the output

By default, 20 files and one relationship hop; `-n` can raise the cap to 200
and `--depth` can request up to five hops. Numbered in reading order and tiered:

| Tier | Means |
|---|---|
| **READ FIRST** | Direct keyword matches or primary fuzzy matches |
| **THEN** | One-hop neighbours, fuzzy references, or co-change |
| **SKIM IF NEEDED** | Two or more hops from the starting files |

Every tier carries a line count, so you know what you're signing up for before
you open anything. Read top-down and **stop when the question is answered** —
the tiers are what make stopping early safe. A small repo may not have enough
material to fill every tier; a missing tier is not an error.

Preserve the tiers and evidence columns when you report a run. Flattening the
output into a plain file list throws away exactly the information that lets the
next reader stop early.

## The evidence columns

Most files can be triaged without being opened, because every row carries its
own evidence:

| Column | What it tells you |
|---|---|
| Matched source line | The actual text that matched, so you can reject a false positive on sight |
| Mention count | How central the symbol is to that file |
| Test attached | Whether the file has a test bound to its subject |
| Relation | *Why* the file was pulled in — `implements X`, `calls X`, `renders X` |

Subtyping and calls outrank a bare mention, so "who implements this interface"
answers itself from the ranking. A **`changed with`** row means git history keeps
moving the two files together — that is what finds the migration script or
config file that no type reference points at.

`--json` carries all of it per file, for when you want to filter with `jq`
rather than read.

## When ranked discovery helps

- **It is fuzzy, so a wrong guess still lands.** Matching runs against the
  repo's own vocabulary: `srvconfig` finds `ServerConfig` (0.86), `McpServelt`
  finds `McpServlet` (0.93). Use it **instead of spending a discovery round on
  synonyms** — one run tells you whether the name you are guessing at exists in
  another spelling. When nothing clears the bar, the error names the closest
  identifiers in the repo, which answers the vocabulary question directly.
- **Several keywords narrow better than one.** `auth retry --all` keeps only
  files carrying both and ranks by the weaker one — "where do X and Y meet" in a
  single run. An empty `--all` run reports per-keyword counts, which *is* the
  answer, not a failure.
- **`--from-file PATH` starts from a file instead of a guess** — callers,
  collaborators, tests, co-changes. Combines with a keyword or stands alone.
  This is the move when you have landed an anchor and want its one-hop
  neighbourhood without browsing.

## Flags

| Flag | Use when |
|---|---|
| `--all` | Every source result must match each keyword (including fuzzy matches unless `--fuzzy 0`) |
| `--from-file PATH` | Seed from a file rather than a keyword |
| `--depth 0` | Direct hits only; skips relationship and git expansion |
| `--no-tests` | Test files are drowning the list |
| `-n <N>` | Limit results (default 20, maximum 200; 0 prints no source rows) |
| `--fuzzy <0–1>` | Move the similarity bar (0.8 default); 0 skips fuzzy computation |
| `--json` | Machine-readable, all evidence per file |
| `--no-git` | Skip history lookup |
| `--no-evidence` | Skip textual evidence lookup and omit evidence in text/JSON |
| `--no-cache` | Force reparsing to diagnose cache issues; usually slower |

## Troubleshooting

| Symptom | Fix |
|---|---|
| `tree_sitter is required by this script` | Bootstrap has not run. Run `scripts/bootstrap.sh` if feasible; otherwise use scoped searches and reads |
| Nothing clears the fuzzy bar | Read the error: it names the closest identifiers in the repo. That is your vocabulary answer |
| Result is too wide | Add a second keyword with `--all`, or `--depth 0` |
| Result is all tests | `--no-tests` |
| Language is not Java/Kotlin/Python/TS/JS | Use the Phase 2 ladder in SKILL.md; there is no script for it |

## Scope and cache

All eligible sources under the requested root are searched, respecting ripgrep's
ignore rules and the scripts' generated/vendor exclusions. Conventional `src`,
`app`, or `tests` directories do not hide sibling sources. Pass a narrower root
when the task is confined to a package.

`search_common.py` shares option validation and cache fingerprints across the four
scripts. The fingerprint includes sorted file paths, sizes, modification times,
and change times. An unchanged tree reuses its parsed index; a changed tree is
reparsed. Config/resource mentions are a separate supplemental list and can match
any keyword, even with `--all`; the intersection applies to source results.
