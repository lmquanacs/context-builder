# Code review

Copy the prompt below and fill in the scope. It reviews the code and produces
`review-result.md`; it does not implement fixes.

---

Use context-builder to review this code for actionable defects.

Scope: <PR, branch compared with a base, uncommitted changes, or specific files>
Intended behaviour: <description, or infer it from the task and existing contracts>
Priorities: <correctness / performance / security / compatibility / all>
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

## Verify candidate findings

For each suspected defect, establish:

1. The input, state, or execution path that triggers it.
2. The expected behaviour and the contract or requirement supporting it.
3. The actual behaviour and practical impact.
4. The code path or focused reproduction that demonstrates the difference.

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
findings, ordered by severity:

- **P0 — Critical:** immediate action; broadly blocks use or risks severe loss.
- **P1 — High:** significant failure on a supported, plausible execution path.
- **P2 — Medium:** a concrete defect with narrower impact or a reasonable workaround.
- **P3 — Low:** a minor, actionable defect.

Format each finding as:

### [P1] <short title describing the failure>

**Location:** `<path>:<line>` — the smallest relevant location; prefer a changed
line for a diff review.

**Trigger and impact:** <when it fails, what happens, and why it matters>

**Evidence:** <verified code path or reproduction; expected versus actual result>

**Suggested fix:** <a concise direction, without implementing it>

If Conventional Comments are requested, use
`issue (blocking, correctness): [P1] <title>` or the appropriate topic. Mark
blocking status based on impact and project policy, not tone.

After the findings, include:

- **Open questions:** material uncertainties that need clarification, if any.
- **Validation and coverage:** checks run, areas reviewed, and material gaps.
- **Summary:** the resulting behaviour of the change in one short paragraph.

If no actionable defects survive verification, say **"No actionable findings."**
Do not imply that unreviewed areas are safe or that tests ran when they did not.
Do not modify source files or post comments to external services as part of this
review; propose fixes in the report.
