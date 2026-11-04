This case tests the skill's confidence rules: a dependency list is only useful
if the reader can see why it is complete.

Pass requires all of:
1. Direct dependents are named with `path:line` anchors: the declaration and
   `defaultRetryPolicy` in `src/config/settings.ts`, and the import, parameter
   type, `policy.attempts`, and `policy.backoffMs` uses in `src/http/client.ts`.
2. `src/billing/charge.ts` and `src/billing/refund.ts` are classed as indirect:
   they reach the policy only through `fetchWithRetry`'s default argument, so
   the rename does not break them. Listing them as direct references fails.
3. The response does not claim `charge.ts` reads `attempts`. Its loop variable
   is `attempt` with a hard-coded `3`, a homonym a loose search will match.
4. The completeness claim carries its search: the command(s) run, the scope
   searched, and at least one blind spot (string lookups, other repos, runtime
   names). A bare "that's everything" fails.
5. Claims are labelled `verified` / `inferred`, and nothing is labelled
   `verified` on the strength of a search hit the response did not read.
