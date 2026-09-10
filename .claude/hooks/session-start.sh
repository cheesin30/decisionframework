#!/bin/bash
# SessionStart hook: make the bundled design skills available at the user level
# (~/.claude/skills) so they are auto-discovered in every session, surviving
# the ephemeral-container reprovisioning of Claude Code on the web.
#
# Skills are stored durably in this repo under .claude/skills and copied into
# the user-level skills directory on each session start. Idempotent.
set -euo pipefail

# Only needed in the remote (web) environment; local project skills are already
# discovered from the repo. Remove this guard to also populate ~/.claude/skills
# when working locally in this repo.
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

SRC="${CLAUDE_PROJECT_DIR:-$(pwd)}/.claude/skills"
DEST="$HOME/.claude/skills"
mkdir -p "$DEST"

SKILLS="banner-design brand design design-system emil-design-eng impeccable review-animations slides ui-styling ui-ux-pro-max"

for s in $SKILLS; do
  if [ -f "$SRC/$s/SKILL.md" ]; then
    rm -rf "$DEST/$s"
    cp -R "$SRC/$s" "$DEST/$s"
  fi
done

echo "Restored design skills into $DEST: $SKILLS" >&2
