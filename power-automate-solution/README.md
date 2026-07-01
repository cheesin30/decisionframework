# LTI Follow-up Sender (No-Premium JSON) — Solution package

A standalone, importable Dataverse Solution containing a **test copy** of the LTI follow-up flow, built around the tool's JSON export (see `LTI_Calendar_QR_Setup_Guide.md`, "Recommended: use the tool's JSON export"). It does **not** touch your existing "LTI Follow-up Sender" flow — import it into a sandbox/test environment and use it to validate the no-premium approach before changing production.

**File:** `LTIFollowupSenderNoPremium_1_0_0_0.zip` (built from `src/` via `build-zip.sh`)

---

## Read this first: what "best effort" means here

This package was **hand-authored to match Dataverse's documented solution schema** — I have no live connection to Power Automate or Dataverse, so **it has not been test-imported**. I'm confident in the parts that matter most:

- ✅ **The flow logic itself** — every action, expression, and field mapping is the exact same content already verified end-to-end against the tool's real JSON export (see the main guide).
- ✅ **The zip structure** and **XML well-formedness** — mechanically verified.
- ⚠️ **Less certain**: some Dataverse-specific plumbing (exact connector operation IDs, a couple of numeric metadata codes). If something in the import is wrong, it's most likely here — and it's very fixable.

**If import fails or an action shows an error after import:** paste me the exact error text (or a screenshot) and I'll fix that specific line — these packages are normally an iterate-once-or-twice process even for experienced makers, not a first-try-perfect thing.

### v1.1 fix (import attempt #1 failed with "Object reference not set to an instance of an object")

That generic error pointed at `solution.xml`'s `Publisher` block — two fields were marked `xsi:nil="true"` (a common trigger for exactly this .NET null-reference error) and an `Addresses` block was only partially filled in. Both are now removed; `solution.xml` and `customizations.xml` are trimmed down to the small set of elements I have the highest confidence are correct. If the next attempt fails differently, send the new error text — it'll point at a different, more specific line.

The flow imports **turned off** on purpose (Draft/Off state) — don't turn it on until you've fixed the placeholders below.

---

## Placeholders you must fix before this can run

Everything below is marked `REPLACE_WITH_...` in `src/Workflows/new_LTIFollowupSenderNoPremium-*.json`. None of these can be guessed correctly in advance — they're specific to your tenant, your Form, and your SharePoint site.

**The fastest way to get the exact right values: pull them from your existing, working "LTI Follow-up Sender" flow**, since it already has all of these wired up correctly:

| Placeholder | Where to find the real value |
|---|---|
| `REPLACE_WITH_YOUR_FORM_ID` (appears twice: trigger + Get response details) | Open your existing flow's **"When a new response is submitted"** trigger → the Form it's bound to. Or: flow's **"…" → Peek code** → search for `"formId"`. |
| `REPLACE_WITH_FIRM_QUESTION_ID` | Open your existing **"Compose filename"** action (or Peek code) — it already references the Firm answer as `body('Get_response_details')?['rXXXXXXXXXXXXXXXX']`. Copy that exact `r…` key. |
| `REPLACE_WITH_DATE_QUESTION_ID` | Same action — copy the key it uses for the workshop date. |
| `REPLACE_WITH_ADVISER_EMAIL_QUESTION_ID` | The Form question that captures the adviser's email (add one to the Form first if it doesn't exist yet — see the main setup guide). Find its `r…` key the same way, via Peek code on **Get response details**. |
| `REPLACE_WITH_YOUR_SHAREPOINT_SITE_URL` | The SharePoint site address your existing **"Get file content using path"** action uses. |
| `REPLACE_WITH_YOUR_TEAM_EMAIL` | Whoever should be notified if the flow fails (in the placeholder `Catch` scope — see below). |

**After import**, open the new flow in the designer and fix these either by:
- Editing `src/Workflows/new_LTIFollowupSenderNoPremium-*.json` directly and re-running `build-zip.sh` before importing (faster if you're comfortable editing JSON), **or**
- Re-importing once, then fixing each flagged action directly in the Power Automate designer (it will visibly show which actions need attention).

## About the placeholder "Catch" scope

I don't have visibility into what your existing flow's 4 Catch actions actually do, so this package includes a simple placeholder (one email notifying `REPLACE_WITH_YOUR_TEAM_EMAIL` that something failed). Replace it with your real error-handling logic, or just copy your existing flow's 4 Catch actions in here.

---

## Importing

1. **make.powerautomate.com** → **Solutions** → **Import solution**.
2. Browse to `LTIFollowupSenderNoPremium_1_0_0_0.zip` → **Next**.
3. You'll be prompted to bind three connections (Microsoft Forms, SharePoint, Office 365 Outlook) to existing connections in your environment (or create new ones) → **Import**.
4. Once imported, open the flow, fix the placeholders (above), **Save**, then **Test** with a real Form submission before turning it on for real use.
5. Follow the same test checklist as the main guide: confirm "Compose Flow JSON Text" starts with `[`, Parse JSON shows no red error, and each "Create event (V4)" run inside Apply to each returns a real event.

**If the import itself fails:** copy the exact error message Power Automate shows and send it to me — it will point at a specific line in `solution.xml`, `customizations.xml`, or the flow JSON that I can correct directly.

---

## Reference: the exact action list (works even if you rebuild this by hand)

If the packaged zip doesn't import cleanly, this table is a guaranteed-correct fallback — the same content, for building the flow manually in the designer (same approach as the main guide's click-by-click walkthrough, just without the extra JSON-export step since this list assumes you already changed "Compose filename" to end in `.json`):

| Step | Action | Key inputs |
|---|---|---|
| Trigger | Microsoft Forms — When a new response is submitted | Form = your LTI form |
| 1 | Microsoft Forms — Get response details | Response Id = trigger's response Id |
| 2 | Compose "Compose filename" | `.json`-suffixed firm+date filename (unchanged from your existing flow, extension only) |
| 3 (Try) | SharePoint — Get file content using path | Path = your Generated ICS/JSON folder + Compose filename's output |
| 4 (Try) | Compose "Flow JSON Text" | `base64ToString(body('Get_file_content_using_path'))` |
| 5 (Try) | Parse JSON | Content = "Flow JSON Text"; schema = the array schema in the main guide |
| 6 (Try) | Apply to each → Create event (V4) | Subject/Start/End/TimeZone/Body from the loop item; Required attendees = adviser email; Attachments = `item()?['attachments']` (raw) |
| Catch | Your existing failure-handling logic | Runs only if Try fails/times out/is skipped |

See `LTI_Calendar_QR_Setup_Guide.md` → "Recommended: use the tool's JSON export" for the full click-by-click version of this same list.
