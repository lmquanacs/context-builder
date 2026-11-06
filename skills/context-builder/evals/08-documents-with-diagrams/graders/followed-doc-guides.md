---
with-only: true
---
This checks the process the skill requires for documentation, so it only
applies to the arm that has the skill.

Pass requires all of:

1. **The guides were read.** Before writing `charging.md`, the agent opened
   both `references/doc-writing.md` and `references/doc-diagrams.md` from the
   context-builder skill. Reading only SKILL.md's summary fails.
2. **Key terms came first.** Before researching, the response stated a main
   term and supporting terms taken from the request and repo, e.g.
   `chargeCustomer` as main with `fetchWithRetry` and `defaultRetryPolicy`
   supporting. Researching straight from "charging" with no named terms fails.
3. **The checklist was run.** The response reports the doc-writing
   "Before handing over" checklist, or names which items were not met and why.

Fail if the agent writes the document from SKILL.md alone, or if it says it
followed the guides while the transcript shows neither file opened.
