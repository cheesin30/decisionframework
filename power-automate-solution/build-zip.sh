#!/usr/bin/env bash
# Rebuilds LTIFollowupSenderNoPremium_1_0_0_0.zip from the src/ folder.
# Run this again after editing any file under src/ (e.g. filling in a
# REPLACE_WITH_ placeholder) before re-importing.
set -euo pipefail
cd "$(dirname "$0")"
OUT="LTIFollowupSenderNoPremium_1_0_0_0.zip"
rm -f "$OUT"
cd src
zip -r -X "../$OUT" "[Content_Types].xml" solution.xml customizations.xml Workflows
cd ..
echo "Built $(pwd)/$OUT"
