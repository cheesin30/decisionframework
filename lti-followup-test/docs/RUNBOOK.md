# RUNBOOK — LTI Workshop Follow-up

Operating manual for the Capital Learning team.

---

## What the system does

After an LTI workshop, an adviser scans a QR on the closing slide, enters only
their name and email in a Microsoft Form, and within ~30 seconds receives an
email with a single calendar (`.ics`) file attached — a three-touchpoint
follow-up sequence with talking points built into each event. Power Automate
(**Flow A**) does the work: it rebuilds the file's name from the firm and date
baked into the QR, fetches that pre-generated `.ics` from SharePoint, and emails
it to the adviser. The `.ics` files themselves are produced separately by the
existing LTI Engagement Calendar tool.

---

## The three most common failures and how to fix them

### 1. `.ics` file not found (SharePoint fetch fails)

**Symptom:** The run fails at *Get file content using path*; you get a diagnostic
email. This is by far the most common failure.

**Cause:** The filename Flow A built doesn't match a file in
`/Capital Learning Hub/LTI/Generated ICS/`.

**Fix — check the name character by character:**
- **Firm capitalisation matters.** It is case-sensitive: `DBS`, not `dbs`.
- **The firm segment may contain underscores.** If the consultant typed a longer
  name into the calendar tool (e.g. `DBS Private Bank`), the file is
  `DBS_Private_Bank_LTI_Follow_Up_…` and the QR's Firm value must be
  `DBS_Private_Bank` — not `DBS`.
- **Date format is `yyyy-MM-dd` with hyphens** — `2026-06-30`, not `30-06-2026`
  and not `2026/06/30`.
- Confirm the file actually exists in the folder with **exactly** the name shown
  in the diagnostic email's "Constructed filename" field. The fastest fix is to
  copy the firm and date segments straight off the real filename back into the
  QR's pre-fill URL.

### 2. Email not arriving

**Symptom:** The Form was submitted but the adviser reports no email.

**Fix:**
- Ask the adviser to **check spam/junk** first (external senders often land
  there).
- Then open **Power Automate → Flow A → run history**. A green run means the
  email was sent (re-confirm the adviser's address was typed correctly on the
  Form). A red run means it failed — open it to see which step and read the
  diagnostic email.

### 3. Wrong attachment / wrong pack

**Symptom:** The adviser got an `.ics`, but it's for the wrong firm or date.

**Fix:** The QR's pre-fill URL had the wrong **Firm** or **Date** baked in. Check
the QR's pre-fill URL parameters for *both* Firm and Date, and regenerate the QR
from the correct filename. Remember: **one unique QR per firm-per-workshop
session** — a reused QR carries the previous session's firm/date.

### 3b. Form opens with Firm / Workshop Date blank (nothing pre-filled)

**Symptom:** Scanning the QR opens the Form, but Firm and Workshop Date are
empty, so the adviser sees fields they shouldn't and Flow A can't build the
filename.

**Cause:** The QR was made from the **short share link**
(`forms.office.com/r/<code>`), which ignores pre-fill parameters.

**Fix:** Rebuild the QR from the **long** pre-fill URL that Forms generates via
**Get a link to pre-fill answers** (`…/Pages/ResponsePage.aspx?id=…&r…=…`). Open
that URL in a browser to confirm it pre-fills *before* making the QR. See
[`../form/prefill-url-guide.md`](../form/prefill-url-guide.md) and
[`../qr/qr-setup.md`](../qr/qr-setup.md).

---

## How to add a new workshop session

1. **Generate the `.ics`.** The consultant uses the existing LTI Engagement
   Calendar tool to generate `{Firm}_LTI_Follow_Up_{yyyy-MM-dd}.ics` and drops it
   into `/Capital Learning Hub/LTI/Generated ICS/`.
2. **Generate a new QR** pointing at the Form with **Firm** and **Date**
   pre-filled — copy both values verbatim from the filename produced in step 1
   (see `../form/prefill-url-guide.md` and `../qr/qr-setup.md`).
3. **Display the QR** on the workshop's closing slide.

That's it — no change to Flow A or the Form is needed to add a session.

---

## Test-phase setting to change before production

> **Sender address — TEST PHASE.** Flow A currently sends from
> **`cheesin.foong@capitalgroup.com`** (an individual mailbox), **not** a shared
> mailbox. The reply-to is the same address. This is intentional for testing.

---

## Production handover

When moving from test to live:

1. **Switch the sender to the Capital Learning shared mailbox.** In Flow A,
   replace the **Send an email (V2)** action in the `Try` scope with **Send an
   email from a shared mailbox (V2)** and set **From** to the shared mailbox.
   - The flow connection owner must have **Send as / Send on behalf** rights on
     that shared mailbox.
   - `# TODO: confirm with [stakeholder]` the exact shared mailbox address.
2. **Update reply-to** to the shared mailbox as well (or the desired monitored
   address).
3. **Update the diagnostic recipient** if alerts should go to a team mailbox
   rather than `cheesin.foong@capitalgroup.com`.
4. **Re-test** one full end-to-end run after the switch (scan → submit → receive)
   before announcing it.
5. Leave everything else unchanged — the trigger, Compose filename, SharePoint
   fetch, attachment wiring, and error handling are production-ready as written.

---

## Quick reference

| Thing | Value |
| --- | --- |
| Filename pattern | `{Firm}_LTI_Follow_Up_{yyyy-MM-dd}.ics` (Firm case-sensitive; date hyphenated) |
| SharePoint folder | `/Capital Learning Hub/LTI/Generated ICS/` |
| Form | "LTI Workshop Follow-up" — 2 visible (Name, Email), 2 hidden pre-filled (Firm, Workshop Date), Anyone can respond |
| Attachment count | Exactly one — the `.ics` |
| Test sender / reply-to | `cheesin.foong@capitalgroup.com` |
| Time zone | Asia/Singapore (SGT) |
| QR rule | One unique QR per firm-per-workshop session |
