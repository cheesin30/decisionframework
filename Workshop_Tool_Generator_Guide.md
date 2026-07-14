# Workshop Tool Generator — How-To Guide

How to create an engagement-calendar tool for a **new Capital Learning workshop** (e.g. TKO — Leading Beyond Borders) as an exact, independent replica of the existing LTI tool — same wizard, QR code, SharePoint save and safeguards, rebranded and reconfigured for the new workshop. **No coding involved; about 10 minutes.**

---

## What the generator does

You give it the **current** calendar tool file and the new workshop's details. It produces a new file — e.g. `TKO_Engagement_Calendar_QR_v1.html` — that consultants use exactly like the LTI tool.

Because the replica is built from the live source file you pick (not a stored copy), every improvement and fix in the current tool carries over automatically. Each replica is fully independent: its own saved touchpoints and resources, its own filenames and SharePoint folder — running it never interferes with the LTI tool or any other workshop's tool.

## Before you start — have these ready

| # | Item | Notes |
|---|------|-------|
| 1 | The current calendar tool file | `LTI_Engagement_Calendar_QR_v1.html` — always use the newest version |
| 2 | Workshop full name | e.g. *Leading Beyond Borders* — appears in titles, the calendar advisers see, the printed handout |
| 3 | Workshop short code | 2–10 letters/digits, e.g. `TKO` — used in filenames and headers |
| 4 | SharePoint folder for this workshop | e.g. `/Capital Learning Hub/TKO/Generated ICS/` — create it in SharePoint if it doesn't exist yet |
| 5 | The workshop's Microsoft Form *(can be added later)* | A copy of the LTI follow-up Form with **firm**, **workshop date** and **adviser email** questions |
| 6 | The default touchpoint sequence | What every consultant should start from: timings, titles, talking points |

## Creating the tool — the five sections

Open `Workshop_Tool_Generator.html` in **Edge or Chrome** and work top to bottom.

### 1 · Source tool
Click **Choose the source .html…** and pick the current `LTI_Engagement_Calendar_QR_v1.html`.

A row of checks appears — **all eight must be green** (✓). A red one means the source file has changed shape and the generator needs updating first; stop and contact whoever maintains the tools.

### 2 · Workshop identity
- **Full workshop name** — used everywhere the tool says "Long-Term Investing".
- **Short code** — used everywhere it says "LTI". Letters/digits only.
- **SharePoint folder** — where this workshop's calendar files will be saved. Leave blank to accept the suggested `/Capital Learning Hub/<CODE>/Generated ICS/`.

Check the live filename preview underneath — files will be named `<Firm>_<CODE>_Follow_Up_<date>.ics`.

### 3 · Microsoft Form
Paste the new workshop's Form **pre-fill link**:

1. In Microsoft Forms, open the workshop's form → **Collect responses** → **Get pre-filled results**.
2. Type a sample firm (e.g. `DBS`) and a sample date into the form's questions.
3. Copy the generated link and paste it into the generator.

Two green chips confirm the firm and date fields were detected. **You can leave this blank** and paste the link later inside the replica's *Form settings* panel — the QR just won't generate until it's set.

### 4 · Default touchpoints
The editor is pre-loaded with the source tool's own defaults. Adjust the labels, timing (offset + unit), calendar titles and talking points to fit the new workshop; add or remove touchpoints as needed. Consultants can still tailor these per cohort — this is just their starting point.

### 5 · Generate
Click **Generate workshop tool**. Two outcomes:

- **All chips green** → the new file (e.g. `TKO_Engagement_Calendar_QR_v1.html`) downloads, with a note listing your remaining rollout steps.
- **Any chip red** → nothing is downloaded (deliberately — no half-broken file). The red chip names what couldn't be found; contact the tool maintainer.

## After generating — rollout checklist

1. **Click through the replica once** — open the file, walk the four steps, confirm the names, folder and touchpoints look right.
2. **SharePoint** — make sure the workshop's `Generated ICS` folder exists; consultants will Sync it (see the consultant how-to guide).
3. **Form** — if you left section 3 blank, paste the pre-fill link into the replica's *Form settings* now.
4. **Power Automate** — clone the LTI "Follow-up Sender" flow for this workshop: same structure, pointed at the new folder and the new Form (see `LTI_Calendar_QR_Setup_Guide.md`).
5. **Distribute** — share the replica file with consultants along with the consultant how-to guide (identical usage; only the names differ).

## Troubleshooting

| Problem | Cause | Fix |
|---|---|---|
| A red ✗ chip in section 1 | The source tool has been restructured since the generator was built | Don't generate; ask the tool maintainer to update the generator |
| "No pre-fill fields found" in section 3 | The link isn't a *Get pre-filled results* link, or no sample answers were typed | Redo the three steps in section 3 — sample answers must be typed in before copying |
| Generate button does nothing | Missing name/code, or no touchpoints | Fill sections 2 and 4; the alert says which |
| Replica opens but shows no QR | Form link wasn't provided | Paste it in the replica's *Form settings* panel |
| Consultants' old data appears in a regenerated tool | Same workshop code = same saved-state namespace (by design) | That's expected — regenerating with the same code keeps consultants' saved work; use a new code only for a genuinely different workshop |

## Updating a workshop tool later

When the master calendar tool gains fixes or features, simply **re-run the generator** with the newest source file and the same workshop details, and redistribute the new file. Because the saved-state namespace is based on the workshop code, consultants keep their saved touchpoints and resources when they switch to the updated file.
