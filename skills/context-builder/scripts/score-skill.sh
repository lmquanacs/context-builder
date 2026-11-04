#!/usr/bin/env bash
# Mechanical half of scoring this skill: everything checkable without a model.
# The other half — does the skill change what the agent does — is ../evals/.
#
# Exit 0 if every check passes, 1 otherwise, so it can gate a commit.
set -uo pipefail

skill="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$skill"
fails=0

check() { # check <label> <condition-exit-code> <detail>
  if [[ "$2" -eq 0 ]]; then
    printf '  ok    %-28s %s\n' "$1" "$3"
  else
    printf '  FAIL  %-28s %s\n' "$1" "$3"
    fails=$((fails + 1))
  fi
}

echo "context-builder — mechanical score"

for tool in rg fd; do
  if ! command -v "$tool" >/dev/null; then
    echo "error: $tool is required to run the mechanical checks" >&2
    exit 1
  fi
done

# --- discoverability: the description is the whole trigger surface, and it is capped
desc_len=$(awk '/^description:/{sub(/^description: /,""); print}' SKILL.md | tr -d '\n' | wc -c | tr -d ' ')
[[ "$desc_len" -le 1024 ]]; check "description <= 1024 chars" $? "$desc_len chars, $((1024 - desc_len)) spare"

# --- weight: the body loads in full every time the skill fires
body_chars=$(awk 'NR>1 && /^---$/{f=1;next} f' SKILL.md | wc -c | tr -d ' ')
body_tokens=$((body_chars / 4))
[[ "$body_tokens" -le 5000 ]]; check "SKILL.md body <= 5k tokens" $? "~${body_tokens} tokens"

# --- wiring: every path SKILL.md names must exist
missing=$(rg -o '(references|scripts|prompts)/[A-Za-z0-9._-]+' SKILL.md | sort -u \
  | while read -r p; do [[ -e "$p" ]] || echo "$p"; done)
[[ -z "$missing" ]]; check "referenced paths resolve" $? "${missing:-all present}"

# --- wiring, the other direction: a shipped file nothing points at is dead weight.
# Reachable means some other shipped text names it: SKILL.md for anything the
# agent is meant to use, or evals for the meta-tooling around it.
orphans=$(fd -t f . references scripts prompts 2>/dev/null \
  | while read -r p; do
      stem=$(basename "$p"); stem=${stem%.*}
      # every other shipped text, so a file mentioning itself doesn't count
      index=()
      for source in SKILL.md scripts/*.sh references/*.md prompts/*.md evals/README.md; do
        [[ "$source" == "$p" ]] || index+=("$source")
      done
      grep -qF "$stem" "${index[@]}" || echo "$p"
    done)
[[ -z "$orphans" ]]; check "no unreachable resources" $? "${orphans:-all reachable}"

# --- executability: shipped scripts run from a cold start
nonexec=$(for p in scripts/*.sh; do [[ -x "$p" ]] || echo "$p"; done)
[[ -z "$nonexec" ]]; check "scripts executable" $? "${nonexec:-all +x}"

# --- fixtures: the evals grade against planted anchors, so a fixture edit that
# moves one silently turns a passing case into a misleading one.
fixture_check() { # fixture_check <label> <pattern> <file>
  rg -qw "$2" "evals/fixtures/$3"; check "$1" $? "$2 in $3"
}
fixture_check "fixture: shop policy"      'interface RetryPolicy'  shop/src/config/settings.ts
fixture_check "fixture: shop nested retry" 'fetchWithRetry'        shop/src/billing/charge.ts
fixture_check "fixture: shop homonym"      'attempt < 3'           shop/src/billing/charge.ts
fixture_check "fixture: inventory policy"  'class RetryPolicy'     inventory/src/inventory/config/settings.py
fixture_check "fixture: warehouse flag"    'decrementOnReserve'    warehouse/src/config/limits.ts
fixture_check "fixture: warehouse 2nd hit" 'adjustStock'           warehouse/src/events/handlers.ts

# --- the recipes the skill documents must actually run on this machine's tools.
if out=$(ast-grep run -p 'interface RetryPolicy { $$$ }' -l ts evals/fixtures/shop 2>&1) \
   && grep -q 'settings.ts' <<<"$out"; then
  check "recipe 8: ts definition" 0 "ast-grep finds RetryPolicy"
else
  check "recipe 8: ts definition" 1 "ast-grep pattern no longer matches"
fi
direct=$(rg -lw 'RetryPolicy' evals/fixtures/shop | wc -l | tr -d ' ')
[[ "$direct" -eq 2 ]]; check "recipe 9: direct references" $? "$direct files name RetryPolicy (expect 2)"

# --- eval wiring: a case directory with no grader scores nothing, silently.
ungraded=$(fd -t d -d 1 '^[0-9]' evals 2>/dev/null \
  | while read -r c; do
      [[ -f "$c/prompt.md" ]] && compgen -G "$c/graders/*.md" >/dev/null || echo "$c"
    done)
[[ -z "$ungraded" ]]; check "every eval case is graded" $? "${ungraded:-all cases have prompt + graders}"

echo
if [[ "$fails" -eq 0 ]]; then
  echo "all mechanical checks passed — behavioural scenarios and graders are in evals/."
  echo "Claude Code runner: claude plugin eval .; in Codex, run the scenarios manually."
else
  echo "$fails check(s) failed"
fi
exit $(( fails > 0 ? 1 : 0 ))
