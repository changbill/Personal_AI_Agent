#!/bin/sh
# Verify CLAUDE.md and AGENTS.md are byte-identical.
#
# Claude Code reads CLAUDE.md and Codex reads AGENTS.md. If they drift, the two
# tools follow different rules on the same repo. This has already happened once:
# AGENTS.md silently lost four DOMAIN.md-related entries.
#
# Usage:  sh scripts/check_docs_sync.sh
# Fix:    cp CLAUDE.md AGENTS.md   (edit CLAUDE.md, then mirror)
#
# Exit 0 = in sync, 1 = drifted, 2 = a file is missing.

set -e

# Run from the repo root regardless of where the script was invoked from.
cd "$(dirname "$0")/.."

A="CLAUDE.md"
B="AGENTS.md"

for f in "$A" "$B"; do
  if [ ! -f "$f" ]; then
    echo "FAIL: $f not found (looked in $(pwd))"
    exit 2
  fi
done

if cmp -s "$A" "$B"; then
  echo "OK: $A and $B are byte-identical ($(wc -c < "$A" | tr -d ' ') bytes)"
  exit 0
fi

echo "FAIL: $A and $B have drifted."
echo
echo "--- diff ($A vs $B) ---"
diff "$A" "$B" || true
echo "-----------------------"
echo
echo "Edit CLAUDE.md as the source, then mirror it:"
echo "    cp CLAUDE.md AGENTS.md"
exit 1
