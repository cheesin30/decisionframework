# LTI Engagement Calendar — Project Handoff

A single-file primer so a fresh Claude chat (or a new person) can pick this up with full context. Read this top to bottom before changing anything.

---

## 1. What this project is

A **self-contained HTML tool** that Capital Group "Capital Learning" consultants use to build a **3-touchpoint post-workshop follow-up calendar** for financial advisers (e.g. DBS, OCBC), attach resource files (PDFs/decks) to each touchpoint, and get it to advisers so it lands in their **Outlook / phone calendar**.

- **Main tool:** `LTI_Engagement_Calendar_QR_v1.html` — open in a browser, no install, no server. All logic is inline (incl. a bundled MIT QR-code library). State persists in `localStorage`.
- **Audience split that matters:** the *consultant* operates the HTML tool; the *adviser* (often external to Capital Group) only ever receives a calendar. Optimise the tool for the consultant; optimise delivery for external advisers on any device.
- **Repo:** `cheesin30/decisionframework`, branch **`claude/file-improvement-l8fb07`**, open as **PR #1**. (The repo's `app.py` / `wte_decision_framework` is an unrelated Streamlit project — ignore it.)

---

## 2. The hard constraints we learned (do NOT re-litigate these)

These were each discovered the hard way, sometimes via the user's real device tests. A new chat will be tempted to "solve" them — don't; they're physics/vendor limits, not bugs.

1. **A QR code cannot contain the calendar.** Max ~3 KB; an `.ics` with an embedded PDF is hundreds of KB–MB. Phone cameras also won't import inline calendar text. → **The QR must point to something hosted, or to a Form (see the live architecture).**
2. **Calendar apps ignore files embedded inside an event.** iOS Calendar, Google Calendar, and Outlook *mobile* all silently drop the iCalendar `ATTACH` property. **Confirmed by the user's own iPhone test.** → Resources reach advisers as **tappable links in the event notes**, or as **native Outlook event attachments** (via Create event V4), or on a **landing page** — never as an embedded `.ics` attachment that "just shows up" on a phone.
3. **"New Outlook" / Outlook-on-the-web treats an emailed `.ics` as a plain file attachment**, not an invite. The adviser must manually do Calendar → Add calendar → Upload from file → Import. Can't be fixed by changing the `.ics`; the fix is sending a **real meeting invite** (Create event V4 with the adviser as attendee → Exchange sends an Accept/Decline card). Confirmed by the user's screenshots.
4. **No public hosting.** Capital Group policy forbids publishing this material to public GitHub (or any public third-party). Anything "Anyone with the link" is essentially the same exposure.
5. **SharePoint "Anyone with the link" is usually blocked** at financial firms → external advisers hit an **HTTP 403** login wall. (This is likely why signed/hosted-link routes are dead-ends for them.)
6. **No Power Automate premium.** Both `Execute JavaScript Code` (would parse the `.ics` in the flow) and the `When a HTTP request is received` trigger (would receive browser uploads) are premium and unavailable → parsing lives in the tool (ready-made JSON export), and SharePoint upload happens via the **OneDrive-synced folder**, not a flow.
7. **Solution import is failing.** Hand-authored Dataverse solution `.zip` fails at preview with `Unexpected: Object reference not set to an instance of an object` — three attempts, unchanged. Concluded: **stop hand-authoring the package** (can't test-import it from here). See §6.

---

## 3. The live architecture (what the tool currently does)

The tool is a **guided 4-step wizard**: **Details → Resources → Touchpoints → Share & QR**. Step 1 collects **firm name** + **workshop completion date**; those two values drive everything downstream. Session-detail inputs stay in the DOM across steps so export/QR logic can always read them.

- **Step 2 (Resources)** leads with **"Import a materials pack (Europe / Asia)"** — a `.json` (produced by `exportSettings()`, imported by `importSettings()`) that embeds the region's resource files *and* the touchpoint layout, so a consultant loads a cohort's materials in one click. Import does **not** overwrite the firm/date from Step 1 (those aren't in the pack). Individual add/swap still available.
- **Step 3 (Touchpoints)** is where they fine-tune the pre-loaded touchpoints.
- **Step 4 (Share)** saves the `.ics` + `.json` **straight into the consultant's OneDrive-synced `Generated ICS` folder** (one-time folder pick; OneDrive syncs them to SharePoint) — no local download, no Power Automate (see below).

**Primary delivery = QR → pre-filled Microsoft Form → Power Automate emails/creates the calendar.** Diagram:

```
Calendar tool  --exports .ics + .json-->  SharePoint /Capital Learning Hub/LTI/Generated ICS/
      |                                              ^
      | firm + date                                 | Flow A fetches by <Firm>_LTI_Follow_Up_<date>
      v                                              |
  one unique QR  -->  MS Form (pre-filled)  --submit-->  Power Automate (Flow A)  -->  Adviser
  (auto-built at Step 4, per firm-per-session)
```

On **Step 4 (Share & QR)** the QR is **auto-generated with no pasting/clicking** — the fixed Form link is baked in as the default and the firm+date from Step 1 are substituted into its pre-fill fields. Changing Step 1 updates the QR live.

**The baked-in Form (in the tool's `FORM_DEFAULT_TEMPLATE`):**
`https://forms.office.com/Pages/ResponsePage.aspx?id=VsC4QcMtjUOZ7mHgAoet_u7GC5WcZ6hKmg8zmnXOKQ1UODc1TlMyOFVPV1pKVVRVOVgyTFg4NUg1Wi4u&r2382d0904b5247209e1fd738071b1c48=DBS&r31037180f3664cbfab502d4633d5bdc4=2026-06-26`
- Firm field param: `r2382d0904b5247209e1fd738071b1c48`
- Date field param: `r31037180f3664cbfab502d4633d5bdc4`

**Filename convention (matches files already in the SharePoint folder):**
`<Firm>_LTI_Follow_Up_<YYYY-MM-DD>.ics` — e.g. `DBS_LTI_Follow_Up_2026-06-26.ics`. Firm = `slug()` (non-alphanumeric → `_`). The `.json` export uses the identical name with a `.json` extension.

**Two export buttons on Step 4:**
- **Download the .ics** — `downloadICS()` → `assembleIcs()` (no urlMap) → **embeds** the attached files as `ATTACH;ENCODING=BASE64`. (Embedding was regressed once when link-mode was introduced; it is restored — keep it.)
- **Download flow data (.json)** — `downloadFlowJson()` / `buildFlowJson()` → a plain array Flow A consumes with **standard, free** actions. Each element: `{subject, start, end, timeZone, description, attachments:[{"@odata.type":"#microsoft.graph.fileAttachment", name, contentType, contentBytes}]}`. The `attachments` shape is exactly what Create event (V4) wants — paste `item()?['attachments']` straight in, no transform. **This is the no-premium path and the one to use.**

**Save to SharePoint (Step 4, `saveToSharePoint()`) — the no-premium primary:** uses the **File System Access API** (Edge/Chrome) to write both files into the consultant's **OneDrive-synced copy** of the `Generated ICS` library; the OneDrive client uploads them to SharePoint automatically. One-time setup: SharePoint library **Sync** button, then **choose folder** once in the tool (the directory handle persists in IndexedDB; `createWritable()` gives clean overwrites, no `…(1).ics`). Unsupported browsers automatically fall back to downloading both files. Verified headless with a mocked `showDirectoryPicker` (correct filenames, valid `.ics` with embedded `ATTACH`, Graph-shaped `.json`) plus the fallback path. **The user has no PA premium**, so this replaced the earlier ingest-flow route as primary; the ingest POST (`uploadToSharePoint()`, "Flow B", premium HTTP trigger, no CORS response readable) is kept under "Other ways to get the files there" for premium tenants. Real-machine OneDrive round-trip is the user's to confirm.

Other Share options are tucked under "Other ways to share" (kept, not primary): landing page (`buildLandingPage()` — one self-contained HTML bundling calendar+files), signed-link QR (Azure SAS / S3 / GCS / SharePoint recognised and left byte-exact), and GitHub auto-publish (only if policy ever allows public hosting).

---

## 4. Power Automate "Flow A" — the current recommended build (no premium)

The existing flow is: `When a new response is submitted → Get response details → Compose filename → Try [ Get file content using path → Send advisor email ] → Catch`.

**Recommended approach right now: don't fight the solution import — edit a Save As copy of the flow directly.** Steps (verified logic; exact expressions below):
1. **Save As** a copy of "LTI Follow-up Sender" so the live flow is untouched.
2. **Compose filename** → change trailing `.ics` to `.json`.
3. Inside Try, after "Get file content using path": add **Compose "Flow JSON Text"** = `base64ToString(body('Get_file_content_using_path'))`.
4. **Parse JSON** on that output (schema = the array in §3 / the guide).
5. **Apply to each** = `body('Parse_JSON')` → **Create event (V4)**: Subject=`item()?['subject']`, Start=`item()?['start']`, End=`item()?['end']`, Time zone=`item()?['timeZone']`, Body=`item()?['description']`, Required attendees = adviser email from **Get response details**, Attachments (raw/array input) = `item()?['attachments']`.
6. **Delete "Send advisor email"** (Create event sends the real invite).
7. Add an **adviser email question** to the Form if it isn't captured yet.

Full click-by-click (both the no-premium JSON path and the premium `Execute JavaScript Code` path) is in **`LTI_Calendar_QR_Setup_Guide.md`**. The `.ics`-parsing JavaScript in that guide was verified against a real tool export (unfolds RFC-5545 lines, reverses the escaping, extracts attachments) — but it needs the premium action, so it's the *alternative*, not the default.

---

## 5. Files in the repo

| Path | What it is |
|---|---|
| `LTI_Engagement_Calendar_QR_v1.html` | **The main tool.** Wizard + QR + Form auto-gen + `.ics`/`.json` export + landing page. Edit this for tool changes. |
| `LTI_Engagement_Calendar_v17.html` | Earlier standalone calendar builder (pre-QR). Superseded by the QR file but kept. |
| `LTI_Calendar_QR_Setup_Guide.md` | The operator guide: Form+Power Automate flow, no-premium JSON path (recommended), premium `.ics`-parse path (alternative), landing page, signed-link hosting, filename convention. |
| `azure-static-web-app/` | Drop-in (`staticwebapp.config.json` + README) to host the landing page on Azure if the signed-link/landing route is ever used. |
| `power-automate-solution/` | The **failed** hand-authored Dataverse solution package (`.zip`, `src/`, `build-zip.py`, README documenting the 3 attempts). Kept for reference; see §6. |
| `app.py`, `wte_decision_framework/` | **Unrelated** pre-existing Streamlit project. Do not touch. |

---

## 6. Open items / where we left off

- **Solution import blocked.** `power-automate-solution/` fails to import (`Object reference not set to an instance of an object`) and hand-authoring hasn't cracked it. **Decision: abandon the from-scratch package.** If a real importable package is still wanted, the reliable route is: have the user **export their existing working flow as an unmanaged solution**, then edit the *real* `definition.json` inside it (guaranteed-valid schema + correct tenant IDs). Otherwise, the **Save As copy + manual edits** in §4 is the recommended path and needs no package at all.
- **Worth confirming:** is the target environment ("Personal Productivity (default)") actually **Dataverse-enabled**? Solution import requires it; if it's a plain environment, no package will ever import there.
- **Verification method used throughout:** headless Chromium (Playwright at `/opt/pw-browsers/chromium`) drives the HTML tool; exports are captured by overriding `downloadBlob`, and QR images are decoded with `jsqr` + `pngjs` to confirm the encoded URL/`.ics`. A checked-in suite now exists — **run `node tests/regression.spec.cjs`** before committing tool changes (covers IndexedDB file restore, the 3 MB attachment guard, pluralisation, stepper keyboard access, and the print handout).
- **Robustness now built in:** resource file *bytes* persist in **IndexedDB** (refresh no longer causes "Reselect file"; the reselect UI remains as fallback if IDB was cleared), and `buildFlowJson()` warns when an attached file exceeds **`ATTACH_LIMIT` (3 MB)** — Outlook's Create-event ceiling — with a matching "too big to attach" chip on the resource card.

---

## 7. Parked (raised but not done, at user's pace)

- **Skill install** — user asked to install the `emilkowalski/skills` repo (`emil-design-eng` + `review-animations`, into `.claude/skills/`). Files were fetched; never written/committed. Pending.
- **Design import** — user tried to import a `claude.ai/design` project via the Claude Design MCP; it can't authenticate in this web environment (`/design-login` needs a terminal). Blocked pending the user uploading the file directly or using "Send to Claude Code Web."

---

## 8. Working norms for this project

- Every tool change is verified with the headless-Chromium harness (§6) before committing — don't trust visual inspection alone for the ICS/QR/JSON logic.
- Be honest about client-side limits (§2); propose the achievable version rather than promising the impossible. The user tests on real devices and will catch it.
- Commit style: descriptive body, `Co-Authored-By: Claude ...`. Push to `claude/file-improvement-l8fb07`; work surfaces on PR #1.
