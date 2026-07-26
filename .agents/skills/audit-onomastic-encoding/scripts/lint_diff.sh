#!/usr/bin/env bash
# Lint-diff reviewed TSVs against a git baseline, with the sign-span trap avoided.
#
# Usage:  lint_diff.sh [git-ref] [file ...]
#   lint_diff.sh                       # HEAD, all changed reviewed/*.tsv
#   lint_diff.sh HEAD~3                # different baseline
#   lint_diff.sh HEAD "KTU 1.4.tsv"    # specific files
#
# The linter only drops the reviewed 'sign span' column when the file's parent
# directory is literally named 'reviewed', so both trees below must nest it.
set -euo pipefail

REF="${1:-HEAD}"
shift || true

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

FILES=()
if [ "$#" -gt 0 ]; then
  FILES=("$@")
else
  # `mapfile` is bash 4+; macOS ships bash 3.2, so read the list portably.
  while IFS= read -r line; do
    [ -n "$line" ] && FILES+=("$line")
  done < <(git diff --name-only "$REF" -- reviewed/ | sed 's#^reviewed/##')
fi

if [ "${#FILES[@]}" -eq 0 ]; then
  echo "No changed files under reviewed/ versus $REF." >&2
  exit 0
fi

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
mkdir -p "$TMP/base/reviewed" "$TMP/cur/reviewed"

for f in "${FILES[@]}"; do
  git show "$REF:reviewed/$f" > "$TMP/base/reviewed/$f"
  cp "reviewed/$f" "$TMP/cur/reviewed/$f"
done

PY="${PYTHON:-python3}"
for d in base cur; do
  (cd "$ROOT/agent" && "$PY" linter/lint.py "$TMP/$d/reviewed"/*.tsv) > "$TMP/$d.txt" 2>&1 || true
  sed -E "s#$TMP/$d/reviewed/##g; s#(KTU [0-9.]+)\.tsv:[0-9]+#\1#g" "$TMP/$d.txt" | sort > "$TMP/$d.norm"
done

echo "baseline ($REF): $(grep -c '^ERROR' "$TMP/base.norm" || true) errors"
echo "current:         $(grep -c '^ERROR' "$TMP/cur.norm" || true) errors"

echo
echo "=== NEW errors (regressions) ==="
comm -13 "$TMP/base.norm" "$TMP/cur.norm" | grep '^ERROR' || echo "  (none)"

echo
echo "=== RESOLVED errors ==="
comm -23 "$TMP/base.norm" "$TMP/cur.norm" | grep '^ERROR' || echo "  (none)"

echo
echo "Note: 'Surface X parsed inconsistently' INFO churn and changed"
echo "'choose one of: …' hints are expected when option rows or overrides change."
echo
echo "Both runs read agent/data_sources/*.tsv from the WORKING TREE, so this diff"
echo "isolates the TSV edits. To measure an override-table change, stash it and"
echo "re-run, or lint one tree before and after editing the table."
