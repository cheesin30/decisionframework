#!/usr/bin/env python3
"""Rebuilds LTIFollowupSenderNoPremium_1_0_0_0.zip from the src/ folder.

Uses zipfile directly (not the `zip` CLI) so we control exactly what
goes in: file entries only, no directory-placeholder entries, and
solution.xml / customizations.xml written first, matching how genuine
Dataverse solution exports are structured.

Run again after editing anything under src/ (e.g. filling in a
REPLACE_WITH_ placeholder) before re-importing.
"""
import os
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "src")
OUT = os.path.join(HERE, "LTIFollowupSenderNoPremium_1_0_0_0.zip")

# Explicit order: solution.xml and customizations.xml first (root files),
# then everything under Workflows/, with forward-slash paths and no
# directory entries.
ordered_files = ["solution.xml", "customizations.xml"]
workflow_dir = os.path.join(SRC, "Workflows")
for name in sorted(os.listdir(workflow_dir)):
    ordered_files.append(os.path.join("Workflows", name))

if os.path.exists(OUT):
    os.remove(OUT)

with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
    for rel in ordered_files:
        z.write(os.path.join(SRC, rel), arcname=rel)

print("Built", OUT)
with zipfile.ZipFile(OUT) as z:
    for info in z.infolist():
        print(" ", info.filename, "-", info.file_size, "bytes")
