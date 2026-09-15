# Code review

Copy the prompt below and fill in the scope. It reviews the code and produces
`review-result.md`; it does not implement fixes.

---

Use context-builder to review this code for correctness, SOLID design, and
maintainability. Identify actionable defects and justified design improvements.
Write every review comment in [Conventional Comments](https://conventionalcomments.org/)
format, including design suggestions and questions.

Scope: <PR, branch compared with a base, uncommitted changes, or specific files>
Intended behaviour: <description, or infer it from the task and existing contracts>
Priorities: <default: correctness, SOLID, and maintainability; add performance,
security, or compatibility as relevant>
Constraints: <known requirements, or none supplied>

## Establish the scope

- Read the repository instructions that apply to the reviewed files.
- For a PR or branch, establish the intended base and inspect the diff against
  its merge base. Do not assume the base branch is named `main`.
- For uncommitted changes, inspect `git status --short`, unstaged and staged
  diffs, and relevant untracked files. Never reset or overwrite local work.
- For named files, review their current behaviour; distinguish existing defects
  from defects introduced by a diff when a comparison is available.
- Start with a scoped diff summary, then the changed ranges. Disable git paging.
  Inspect history only when a live question depends on why something changed.

## Gather only the context needed

Choose Micro for a small, clear change; Standard for a typical review. Split
larger reviews into bounded areas. Discovery budgets limit investigation, not
completion: disclose any area you could not review rather than claiming coverage.

Start from the changed behaviour and identify the contracts it affects. Read
callers, configuration, and focused tests when they resolve a concrete question;
do not trace every caller of every changed file by default. Use the reading-list
scripts only when ranking candidates or following relationships will help. Start
with one hop and a small result cap.

Check relevant failure modes: incorrect results, boundary conditions, error
handling, resource cleanup, concurrency, compatibility, security boundaries, and
performance regressions. Prioritize those the change can actually affect.

## Review SOLID and practical design

Apply these principles to the language and architecture in use, including
functions and modules. Do not require classes or interfaces just to fit SOLID.
Inspect the relevant boundaries and consumers before proposing a redesign.

| Principle | What to check | Evidence worth reporting |
|---|---|---|
| **Single responsibility** | Does a module combine responsibilities that change for different reasons? | A policy change requires modifying unrelated storage, formatting, or transport logic in the same unit. |
| **Open/closed** | Can established kinds of variation be extended without repeatedly modifying stable policy? | An existing extension requires coordinated edits to duplicated dispatch logic. Do not invent hypothetical extensions. |
| **Liskov substitution** | Can each implementation replace its advertised contract without surprising callers? | Stronger preconditions, weaker guarantees, unsupported operations, or incompatible error behaviour break a real consumer. |
| **Interface segregation** | Do consumers depend only on the capabilities they use? | Implementations need dummy methods, or consumers must import unrelated capabilities through an oversized contract. |
| **Dependency inversion** | Is business policy separated from replaceable infrastructure details? | Hard-coded database, network, clock, or filesystem dependencies prevent an existing substitution or focused test. A function parameter may be enough. |

Also check meaningful names, cohesive modules, explicit dependencies, controlled
side effects, consistent error contracts, and duplication of business rules.
Distinguish repeated knowledge from code that merely looks similar. Prefer simple
control flow and existing project conventions over introducing new frameworks,
layers, factories, or generic abstractions.

For each design suggestion, name the concrete maintenance, extension, or testing
task it makes easier, point to the affected code and consumers, and explain the
tradeoff. Recommend the smallest useful change. File length, class count, an
absent interface, or a principle's name alone is not sufficient evidence.

## Verify candidate findings

For each suspected defect, establish:

1. The input, state, or execution path that triggers it.
2. The expected behaviour and the contract or requirement supporting it.
3. The actual behaviour and practical impact.
4. The code path or focused reproduction that demonstrates the difference.

For a design improvement without a runtime failure, establish the current
coupling or duplication, the supported change or test it obstructs, and how the
suggested refactor reduces that cost. Report it as a design suggestion rather
than inventing a failing input to classify it as a defect.

Inspect surrounding code before concluding that a check or operation is missing.
Run focused existing tests or a small isolated reproduction when useful. A missing
test alone is not a defect. State which checks ran and their limitations.

Use structural or dataflow tools when their capabilities answer the question.
For a security finding involving dataflow, verify the source, sink, and connecting
path. A missing scanner does not prevent a finding supported by a manual trace;
scanner output alone is not proof of exploitability.

Discard disproved findings. Put unresolved, material assumptions under Open
questions. Avoid speculative problems, unrelated cleanup, style preferences,
forced praise, and duplicated comments about the same root cause.

## Write the review

Write `review-result.md` and give a concise summary in the response. Lead with
verified defects, ordered by severity. Severity reflects demonstrated impact,
not how many SOLID principles a change appears to violate:

- **P0 — Critical:** immediate action; broadly blocks use or risks severe loss.
- **P1 — High:** significant failure on a supported, plausible execution path.
- **P2 — Medium:** a concrete defect with narrower impact or a reasonable workaround.
- **P3 — Low:** a minor, actionable defect.

### Comment format

Use the standard structure:

```text
<label> [decorations]: <subject>

[discussion]
```

Use one label. Decorations, when present, go in one pair of parentheses,
separated by commas. The square brackets above indicate optional parts; do not
print them. The subject states the point; discussion explains why and what next.

Choose the label by intent:

- `issue`: a demonstrated problem; include a concrete suggested remedy.
- `suggestion`: a proposed improvement, including SOLID refactoring.
- `question`: a material concern that still needs clarification.
- `todo`: a small necessary change.
- `chore`: a required process task; cite the applicable requirement.
- `praise`: something specifically worth recognizing; never manufacture praise.
- `nitpick`, `thought`, `note`: a minor preference, idea, or useful observation;
  these are non-blocking. Keep them relevant to the requested review.

Decorations are optional in the standard. For this review, explicitly mark
actionable comments `(blocking)` or `(non-blocking)` based on impact and project
policy. Add a useful topic such as `solid`, `correctness`, `security`, or `test`
when needed. Use `if-minor` only when the suggestion is worthwhile if inexpensive.
Keep decorations short; the label itself does not determine blocking status.

P0–P3 are this prompt's severity metadata, not Conventional Comments labels.
Put severity in the discussion of verified defects, leaving the comment header
in standard format. Do not assign defect severity to an unproven concern.

For example, a defect comment uses:

```text
issue (blocking, correctness): Preserve the caller's timeout when retrying

Severity: P1
Location: src/client.py:42
Trigger and impact: ...
Evidence: ...
Suggested fix: ...
```

For each verified defect, include the following in its discussion:

**Location:** `<path>:<line>` — the smallest relevant location; prefer a changed
line for a diff review.

**Trigger and impact:** <when it fails, what happens, and why it matters>

**Evidence:** <verified code path or reproduction; expected versus actual result>

**Suggested fix:** <a concise direction, without implementing it>

Design suggestions use the same header structure, for example:

```text
suggestion (non-blocking, solid): Pass the clock into the expiry policy

Location: src/expiry.py:28
Principle: Dependency inversion
Current cost: ...
Supported change or test: ...
Suggested refactor and tradeoff: ...
```

Questions use `question (non-blocking): <specific uncertainty>` with a code
anchor and the evidence already checked. Mark a question blocking only when its
answer is needed to establish that the change is safe to accept.

After the findings, include:

- **SOLID and maintainability suggestions:** justified improvements, ordered by
  practical value. For each, give the principle or practice, `path:line`, affected
  consumer or change scenario, present cost, smallest refactor, and tradeoff.
  Mark these non-blocking unless an explicit project requirement makes them
  blocking. Keep a SOLID-related runtime defect in the findings only; do not
  repeat it here. Use `suggestion` comments and omit this section when none is
  justified.
- **Open questions:** `question` comments for material uncertainties, if any.
- **Validation and coverage:** checks run, code and applicable SOLID boundaries
  reviewed, and material gaps. Do not force a comment for every principle.
- **Summary:** the resulting behaviour of the change in one short paragraph.

If no defects survive verification, say **"No actionable defects found."**
Still include justified design suggestions separately. If neither defects nor
design suggestions remain, say **"No actionable findings."**
Do not imply that unreviewed areas are safe or that tests ran when they did not.
Do not modify source files or post comments to external services as part of this
review; propose fixes in the report.
