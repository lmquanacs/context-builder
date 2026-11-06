# Writing Documentation from Evidence

Required reading for SKILL.md Phase 4, "Documentation tasks". Read it and
`references/doc-diagrams.md` in full before writing. Three steps: **extract key
terms → research from them → write a detailed, structured, visual document**.

---

## 1. Extract key terms before researching

Don't research the topic as stated ("document the payment change"). Pull out
the concrete names the context already gives you, pick one **main term**, and
seed discovery from it.

### Where the terms come from

| Context | Extract |
|---|---|
| Branch, PR, or uncommitted change | Changed files; the class or function enclosing each change; declarations in changed files |
| PR on GitHub | Title, body, changed files |
| Request, ticket, or error | Identifiers (`CamelCase`, `snake_case`), endpoints, error strings, feature names; map each to the repo's spelling (SKILL.md "Several candidates", step 1) |
| Named file | Its declared types and public functions |

```sh
BASE=main   # or: git symbolic-ref --short refs/remotes/origin/HEAD
RANGE="$BASE...HEAD"   # uncommitted: RANGE=HEAD; staged only: RANGE=--cached

# 1. Changed files, sized
git --no-pager diff --stat $RANGE

# 2. Enclosing class/function of each change, most-changed first
git --no-pager diff -U0 $RANGE | rg -o '^@@ [^@]+ @@ ?(.*)$' -r '$1' \
  | sort | uniq -c | sort -rn | head

# 3. Declarations in the changed files (language-agnostic)
git --no-pager diff --name-only $RANGE | xargs rg -n \
  '^\s*(export\s+)?((public|private|protected|internal|abstract|final|open|data|sealed|static)\s+)*(class|interface|enum|object|record|struct|trait|def|fun|func|function)\s+\w+'

# 4. PR on GitHub
gh pr view <n> --json title,body,files | jq -r '.title, .body, .files[].path'
```

Command 2 reports the enclosing class for languages git has no function
pattern for (e.g. Java without `.gitattributes`). That is enough to pick the
main class; use command 3 or a ranged read for the methods.

### Pick the main term

Rank the candidates and choose **one** main term (usually a class, service,
handler, or endpoint), plus **2–4 supporting terms**:

1. **Most change**: the top count in the hunk-context ranking.
2. **Definer, not user**: it is declared in the changed code, not just
   referenced.
3. **Entry point or hub**: a controller, handler, job, or public API, or the
   most-referenced name (`rg -cw 'Term'`).
4. **Named by the user**: an explicit name in the request wins ties.

State the result before researching, so the user can correct it cheaply:

> Key terms: **`OrderService`** (main, 14 changed lines, entry for checkout),
> `PaymentClient` (called from the change), `Order.markPaid` (new state).

Ask only when two candidates tie and the choice changes the document.

### Turn key terms into context questions

Each key term gets the questions the document must answer. For the main term:

- What is it for, in one sentence, from the reader's point of view?
- Where is it defined, and what is its public surface?
- Who calls it (entry points), and what does it call (dependencies)?
- What is the main flow, step by step? Which branches and errors exist?
- What states or data does it create or change?
- What configuration controls it, with defaults?
- For a change: what behaved differently before?
- Which tests show the intended behaviour?

Then run the normal loop (anchor-out from the main term, one hop at a time)
and keep the ledger. Every section below is filled from verified Findings.

---

## 2. Document structure

Use this skeleton. Keep every section that has evidence, drop sections that
genuinely don't apply, and never pad. "Detailed" means each kept section
answers its question completely, not that the document is long.

| # | Section | Contents | Visual |
|---|---|---|---|
| 1 | **Title + summary** | What it is and why it matters, 2–4 plain sentences | — |
| 2 | **At a glance** | Table: component, location (linked), entry point, key config, owner if known | Table |
| 3 | **Who this is for** | Audience, prerequisites, what's out of scope | — |
| 4 | **Big picture** | Where the main term sits: what calls it, what it calls, outside systems | Context diagram |
| 5 | **How it works** | Main flow as numbered steps; branches and errors | Flowchart or sequence diagram + walkthrough |
| 6 | **Key parts** | Table: name, role in plain words, file link, one per key term | Table |
| 7 | **States and data** | Lifecycle of the main object; data shapes the reader sees | State diagram, field table |
| 8 | **Configuration** | Table: key, default, effect, where it's set | Table |
| 9 | **What changed** *(code change only)* | Before vs. after behaviour, why, migration or rollout notes | Before/after diagram or table |
| 10 | **Using it** | Task steps or example request/response, each checkable | Code block |
| 11 | **Errors and troubleshooting** | Table: what you see, why, what to do | Table |
| 12 | **Glossary** | Every unavoidable term, one line each | Table |
| 13 | **Related** | Source, tests, ADRs, runbooks, tickets, with stable links | List |

### Visual minimum

Diagrams carry the document: a reader who looks only at the diagrams and their
captions should get the main idea. Every document has at least:

- **one overview diagram** in section 4: a context diagram, or a mind map for
  a concept;
- **one diagram per main flow** in section 5: a flowchart or sequence diagram;
- **a state diagram** in section 7 when the main object has three or more
  statuses;
- **a before/after visual** in section 9 for any change that alters a flow,
  plus a timeline when rollout order matters.

Any other kind from `references/doc-diagrams.md` section 2 is welcome where it
answers a reader's question faster than prose. Every diagram passes that
file's five-second rule. Use tables rather than prose for anything the reader
scans: config, errors, parts, glossary.

Draft the diagrams **before** the prose: settle each caption (the takeaway)
and its boxes from the Findings, then write the sections around them.

### Writing rules

- Lead each section with the answer, then the detail.
- Behaviour before implementation: say what happens, then where in the code.
- Plain words first, code names second, in backticks and linked:
  "the order service (`OrderService`)".
- One idea per paragraph; keep paragraphs to about four lines.
- Link every code name to its file at first mention.
- Don't publish anything that is only `inferred`. Verify it, or state the
  limit plainly ("Retries are not documented here; see open question 2").

---

## 3. Before handing over

- [ ] Main and supporting key terms stated, and each one appears in the doc.
- [ ] Every kept section answers its question; empty sections removed.
- [ ] The visual minimum is met; every diagram has a takeaway caption,
      numbered steps, and a walkthrough, and passes the five-second check.
- [ ] Every diagram edge and table row traces to a `verified` finding.
- [ ] Links resolve, diagrams render (or the doc says they weren't checked).
- [ ] A reader new to the code can follow sections 1, 4 and 5 without opening it.
