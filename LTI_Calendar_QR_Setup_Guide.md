# LTI Engagement Calendar — QR Setup Guide

A one-time setup so you can turn the follow-up calendar into a **QR code advisers scan to add the touchpoints (with the resource files) to their phone or Outlook.**

The tool is `LTI_Engagement_Calendar_QR_v1.html` — just open it in Chrome, Edge or Safari. There is nothing to install and no server to run.

---

## How it works (the 30-second version)

A QR code is tiny (~3 KB max), so it **cannot** hold a calendar file that has PDFs embedded in it. Instead, the calendar file lives at a link, and the QR points to that link. When an adviser scans it, their phone downloads the file and offers to add it to their calendar / Outlook.

So the flow is always: **build → export the `.ics` → host it → QR.**

**About the resource files:** calendar apps (iOS, Outlook, Google) do **not** display files embedded inside a calendar event — they just ignore them. So resources can't travel *inside* the event. Instead, each resource is hosted and a **tappable link to it goes in the event's Notes**, which calendar apps *do* show. The adviser taps the link to open the PDF.

> **Compliance note:** the tool does not send anything anywhere. *You* choose where the calendar and resources are hosted. For Capital Group, host on **firm-controlled cloud storage with a signed (capability) link** — see below. (A public-GitHub auto-publish option also exists under *Advanced*, but only use it if your policy permits public hosting of this material.)

---

## Microsoft Form + Power Automate flow (QR → form → emailed calendar)

The most Capital-Group-native option: the QR opens a **Microsoft Form pre-filled with the firm + workshop date**, and a **Power Automate flow emails the adviser the matching calendar**. Nothing is hosted publicly.

**The flow**

```
Calendar tool  --drops .ics-->  SharePoint /Capital Learning Hub/LTI/Generated ICS/
      |                                        ^
      | firm + date                            | fetches (by firm + date)
      v                                         |
  one unique QR  -->  Microsoft Form  --submit-->  Power Automate (Flow A)  --emails-->  Adviser
  (pre-filled, per firm-per-session)
```

**One-time (in Microsoft 365)**
1. Build a Form with (at least) two questions: **Firm** and **Workshop date** (you can hide/pre-fill them). Add an email question if the flow needs where to send.
2. In the tool, on **Share & QR**, paste the Form's pre-fill URL once (Forms → *Collect responses → Get pre-filled results* → type a sample firm + date → copy the URL). The tool auto-detects which field is the firm and which is the date.
3. Build **Flow A** in Power Automate: trigger *When a new response is submitted* → read Firm + Date → fetch the matching `.ics` from `/Capital Learning Hub/LTI/Generated ICS/` → email it to the adviser.

**Each cohort**
1. In **Step 1**, enter the **firm name** and **workshop completion date**.
2. On **Share & QR**: **Download the .ics** (the tool names it `<Firm>_LTI_Follow_Up_<YYYY-MM-DD>.ics`, e.g. `DBS_LTI_Follow_Up_2026-06-26.ics`, and shows the exact name under the button) and drop it into the SharePoint `Generated ICS` folder **keeping that name**. In Flow A, build the same filename from the submitted firm + date (replace non-alphanumeric characters with `_`, then `_LTI_Follow_Up_`, then the date) to look it up.
3. Click **Generate Form QR** — the QR encodes the Form URL with this firm + date pre-filled (it updates live as Step 1 changes). **Download PNG / Print** it. One unique QR per firm-per-session.

Adviser scans → the Form opens already filled for their firm → they submit → Flow A emails them the calendar.

---

## Removing the desktop "download & import" step (native calendar invites)

**The problem:** in **Outlook on the web / "new Outlook,"** an emailed `.ics` is treated as a plain file attachment, not a calendar invite. Opening it does nothing visible — the adviser has to manually go **Calendar → Add calendar → Upload from file → Browse → Import**. This is a limitation of that client with *any* attached `.ics` file; it can't be fixed by changing the file's contents.

**The fix:** change Flow A so it **parses** the `.ics` it already fetches and calls the Outlook connector's **Create event (V4)** action directly — three times, once per touchpoint — with the adviser as a **Required attendee**. Exchange then sends a genuine meeting invite, which shows the standard **Accept / Tentative / Decline** card right in the message on *any* client (new Outlook, classic desktop, mobile, web). Zero extra navigation, because it's no longer a file the adviser has to import — it's a real invite, the same experience they already know.

This is a change to **Flow A only** — the calendar tool and the exported `.ics` stay exactly as they are; the `.ics` simply becomes the *data source* Flow A reads instead of the *file* it emails. As a bonus, resource files relayed as native event attachments (see step 4 below) display correctly on phones too, unlike the current embedded `ATTACH` property, which most calendar apps silently ignore.

### Updated Flow A

```
Trigger: When a new response is submitted (Microsoft Forms)
  → Get response details → read Firm, Workshop date, Adviser email
  → SharePoint: Get file content (path built from Firm + date, e.g. DBS_LTI_Follow_Up_2026-06-26.ics)
  → Compose "ICS Text": base64ToString(body('Get_file_content'))
  → Execute JavaScript Code: parse "ICS Text" into an array of {subject, start, end, timeZone, description, attachments}
  → Parse JSON on that output
  → Apply to each event:
      → Office 365 Outlook: Create event (V4)
          Subject:            item()?['subject']
          Start time:         item()?['start']
          End time:           item()?['end']
          Time zone:          item()?['timeZone']
          Body:               item()?['description']
          Required attendees: <adviser email from the form response>
          Attachments:        item()?['attachments'] (Name / ContentBytes — see note below)
```

### An adviser email field (needed either way)

*Create event*'s "Required attendees" needs a real email address, not just the firm name. Open your Form and confirm a question captures the adviser's email; if not, add one now — everything below assumes **Get response details** already exposes it.

---

## Getting the files into SharePoint automatically (no Power Automate needed)

On **Share & QR**, the primary button is **Save to SharePoint**. It writes the `.ics` and `.json` **directly into the consultant's OneDrive-synced copy of the `Generated ICS` library**, and the OneDrive sync client uploads them to SharePoint within seconds. No download folder, no manual upload, **no Power Automate, no premium licence, no IT app registration**.

### One-time setup per consultant (~1 minute)

1. In the browser, open the SharePoint library `/Capital Learning Hub/LTI/Generated ICS/` and click **Sync** (top toolbar). The folder appears in File Explorer under the organisation's name (e.g. `Capital Group / Capital Learning Hub - Generated ICS`). This is the standard OneDrive sync — most corporate machines already have the client running.
2. In the tool → **Share & QR** → click **choose folder** and pick that synced folder. The tool remembers it (a browser permission prompt may appear on first save after reopening — one click).

From then on: **Save to SharePoint** = one click → both files are written with the correct `<Firm>_LTI_Follow_Up_<date>` names → OneDrive syncs them up → Flow A finds them on the next Form submission.

**Notes:**
- Needs **Edge or Chrome** (the File System Access API). On other browsers the button automatically falls back to downloading both files for a manual drop.
- Re-saving the same firm+date **cleanly overwrites** the previous files (no `…(1).ics` duplicates).
- The OneDrive sync client must be signed in and running — on managed corporate Windows machines it is.

---

## Alternative: POST to an ingest flow ("Flow B") — requires a premium trigger

> Skip this if you don't have Power Automate premium — the synced-folder route above does the same job with no licence. This option remains under **"Other ways to get the files there"** for teams that prefer a server-side flow.

The tool can instead **POST both files to a small "ingest" flow** you set up once ("Flow B"), which writes them into `/Capital Learning Hub/LTI/Generated ICS/`.

**What the tool sends** (one HTTP POST, body is JSON as `text/plain`):
```json
{
  "folder": "/Capital Learning Hub/LTI/Generated ICS/",
  "icsFileName": "DBS_LTI_Follow_Up_2026-06-26.ics",
  "icsBase64": "…base64 of the .ics…",
  "jsonFileName": "DBS_LTI_Follow_Up_2026-06-26.json",
  "jsonBase64": "…base64 of the .json…"
}
```

### Build Flow B (a separate flow from Flow A)

1. **New → Instant cloud flow → When a HTTP request is received.**
2. Leave the request-body schema empty (the tool sends `text/plain`, so you'll parse it yourself in the next step).
3. **Compose "Payload"** = expression `json(triggerBody())` — turns the posted text into an object.
4. **SharePoint → Create file** (the `.ics`):
   - **Site Address**: your Capital Learning Hub site
   - **Folder Path**: `outputs('Payload')?['folder']`
   - **File Name**: `outputs('Payload')?['icsFileName']`
   - **File Content**: expression `base64ToBinary(outputs('Payload')?['icsBase64'])`
5. **SharePoint → Create file** again (the `.json`): same, but `jsonFileName` / `base64ToBinary(outputs('Payload')?['jsonBase64'])`.
6. **Save**, then copy the trigger's generated **HTTP POST URL**.
7. In the tool → **Share & QR → "Other ways to get the files there"** → paste that URL into the ingest-flow field, tick *Remember on this device*, and use **Upload via ingest flow**.

### Caveats for this alternative

- **Licensing:** the **When a HTTP request is received** trigger is a **premium** Power Automate feature in most plans, just like *Execute JavaScript Code*. If your environment doesn't have premium, use the synced-folder route above instead.
- **No success confirmation in the browser:** Power Automate's request trigger doesn't return CORS headers, so the browser **cannot read the flow's response**. The tool therefore says *"Upload request sent — verify in SharePoint,"* which is expected, not an error. After clicking Upload, glance at the `Generated ICS` folder to confirm both files landed. (This is a limitation of calling Power Automate from a browser, not of the tool.)
- **Re-uploads / overwrites:** *Create file* doesn't overwrite — re-uploading the same firm+date can produce `…(1).ics`. If consultants will re-run a cohort, change the two Create file actions to a *"get file / if exists then Update file, else Create file"* pattern, or delete the old file first.

---

## Recommended: use the tool's JSON export (no Power Automate premium needed)

`Execute JavaScript Code` — used in the walkthrough further below — is a **premium** Power Automate action. If your environment doesn't have Power Automate premium licensing, or you'd simply rather not parse the `.ics` yourself, the tool can do that parsing for you and export the result as **plain JSON** instead:

On **Share & QR**, next to **Download the .ics**, click **Download flow data (.json)**. It's the same 3 touchpoints, already broken out into exactly the shape `Create event (V4)` needs — subject, start, end, time zone, description, and any attached resource pre-shaped as a Microsoft Graph `fileAttachment` object — as one clean array. Flow A then needs only **standard, free** actions: no custom code, no unfolding, no escaping, no premium licensing.

```
Trigger: When a new response is submitted (Microsoft Forms)
  → Get response details → read Firm, Workshop date, Adviser email
  → Compose filename → change its extension from .ics to .json (same firm+date convention)
  → SharePoint: Get file content using path (now fetches the .json)
  → Compose "Flow JSON Text": base64ToString(body('Get_file_content_using_path'))
  → Parse JSON on "Flow JSON Text"          ← standard action, no premium needed
  → Apply to each event:
      → Office 365 Outlook: Create event (V4)
          Subject / Start time / End time / Time zone / Body — from the current item
          Required attendees: adviser email from Get response details
          Attachments: item()?['attachments'] (already Graph-shaped, paste as raw value)
```

### Click-by-click (for your flow: `When a new response is submitted → Get response details → Compose filename → Try [Get file content using path → Send advisor email] → Catch`)

1. **Open "Compose filename"** and find the expression that builds the file name (it should end in `.ics`, matching the tool's `<Firm>_LTI_Follow_Up_<date>.ics` convention). Change just the trailing `.ics` to **`.json`**. Nothing else in that expression needs to change — the tool's JSON export uses the exact same naming convention, just with a different extension, so this one edit is enough for "Get file content using path" to now fetch the right file.
   > If "Get file content using path" has the `.ics` extension hardcoded separately rather than reading it from "Compose filename", update it there too.
2. Each cohort, drop **both** files the tool exports (`…ics` and `…json`) into the same SharePoint folder with matching names — Flow A now only reads the `.json` one, but keeping the `.ics` alongside costs nothing and keeps you future-proof if you ever want the parser-based route below.
3. Inside the **Try** scope, click **+** below "Get file content using path" → **Add an action** → search **`Compose`** → rename it **`Flow JSON Text`**. Set its Input (via the Expression tab) to:
   ```
   base64ToString(body('Get_file_content_using_path'))
   ```
4. Click **+** below it → search **`Parse JSON`** (Data Operation — standard, no licensing required) → add it.
   - **Content**: Dynamic content → the "Flow JSON Text" output.
   - **Schema**: click **Generate from sample** and paste:
     ```json
     [
       {
         "subject": "DBS: Prepare, then capture one real client concern",
         "start": "2026-06-26T09:00:00",
         "end": "2026-06-26T09:15:00",
         "timeZone": "Asia/Singapore",
         "description": "Review one resource and decide which client concern it helps you address.",
         "attachments": [
           {
             "@odata.type": "#microsoft.graph.fileAttachment",
             "name": "Inflation One-Pager.pdf",
             "contentType": "application/pdf",
             "contentBytes": "JVBERi0xLjQK"
           }
         ]
       }
     ]
     ```
5. Click **+** below Parse JSON → search **`Apply to each`** → its input = Dynamic content → the **Body** of Parse JSON.
6. Inside the loop, **Add an action** → search **`Create event`** → **Office 365 Outlook: Create event (V4)** → fill every field via Dynamic content (never type these by hand):

   | Field | Pick from Dynamic content |
   |---|---|
   | Subject | `subject` |
   | Start time | `start` |
   | End time | `end` |
   | Time zone | `timeZone` |
   | Body | `description` |
   | Required attendees | the adviser-email field from **Get response details** (not from this loop) |
   | Attachments | switch to raw/array input (small icon at the field's edge, or via "…" → Peek code for that action) and enter `item()?['attachments']` |

7. **Delete "Send advisor email"** (Create event's own invite replaces it), or edit it into a plain courtesy note with the `.ics` attachment removed.
8. **Save draft** → **Test** with a real test Form submission → open the run, confirm "Flow JSON Text" starts with `[` (a JSON array), Parse JSON shows no red error, and 3 "Create event (V4)" iterations each return success → check your test inbox for 3 real invites with the resource attached → **Publish**.

**Troubleshooting**

| Symptom | Likely cause | Fix |
|---|---|---|
| "Get file content using path" fails / file not found | "Compose filename" still builds `.ics`, or the path is hardcoded elsewhere | Recheck step 1 — the composed name must end in `.json` and match exactly what the tool exported |
| Parse JSON shows a red schema error | Sample schema didn't include `attachments`, or a touchpoint has none (empty array is fine — that's valid, not an error, so this usually means the schema itself is off) | Regenerate the schema from a real run's output, or paste the schema block above directly |
| Invite arrives with no attachment | Attachments field wasn't switched to raw/array input | Redo step 6 with `item()?['attachments']` in raw mode |

---

## Alternative: parse the `.ics` directly (requires Power Automate premium)

If you *do* have Power Automate premium and would rather avoid an extra exported file, `Execute JavaScript Code` can parse the `.ics` itself — same end result, one file instead of two. This is more work to set up; skip it unless you have a specific reason to prefer it over the JSON export above.

### Detailed click-by-click walkthrough

This expands the outline above into every click, for the flow shown in your screenshot (`When a new response is submitted → Get response details → Compose filename → Try [Get file content using path → Send advisor email] → Catch`). You're inserting new steps **inside the Try scope**, between `Get file content using path` and `Send advisor email`, so the existing `Catch` keeps handling file-lookup failures exactly as it does today.

**Part A — Compose "ICS Text" (decode the file to readable text)**

1. Inside the **Try** scope, hover directly under the **"Get file content using path"** card until a small **+** appears on the connecting line. Click it, then choose **Add an action**.
2. Search **`Compose`**. Under **Data Operation** (sometimes just listed under "Built-in"), click **Compose** to insert it.
3. Click the action's title text ("Compose") and rename it to exactly **`ICS Text`** — the exact spelling matters, you'll reference it by name in Part B.
4. Click into the **Input** box → click the **Expression** tab (next to "Dynamic content") → type:
   ```
   base64ToString(
   ```
   → switch to the **Dynamic content** tab → find **Get file content using path** → pick its **File Content** field (this auto-inserts a reference like `body('Get_file_content_using_path')`) → close the parenthesis. The finished expression should read:
   ```
   base64ToString(body('Get_file_content_using_path'))
   ```
5. Click **Add/OK** to confirm.

> Always let the picker insert the reference rather than typing an action name by hand — whatever it inserts *is* the correct name, even if it looks slightly different from the label on the card.

**Part B — Execute JavaScript Code (the parser)**

1. Click **+** below "ICS Text" → **Add an action** → search **`Execute JavaScript Code`**. If it doesn't show up, see the licensing note above and stop here.
2. Paste the full script from the **"4. Parse it"** section below into the code editor, replacing any placeholder text.
3. Find the last two lines of the script:
   ```javascript
   var icsText = workflowContext.actions['ICS_Text'].outputs;
   return parseLtiIcs(icsText);
   ```
   This assumes your Compose action's internal name became `ICS_Text` (its display name "ICS Text" with the space turned into an underscore — this is how Power Automate names actions internally; it is **not** prefixed with the connector type, so it's `ICS_Text`, *not* `Compose_ICS_Text`).
4. **Don't just trust that guess** — confirm it: click the flow's **"…" menu** (top toolbar, near Save/Test/Publish) → **Peek code**. This shows the flow's raw JSON. Press Ctrl+F and search for `ICS Text`; the key that JSON uses for that action (inside the `"actions": { ... }` block) is the exact string to put inside the quotes in step 3. Update the script if it differs from `ICS_Text`.

**Part C — Parse JSON**

1. Click **+** below the Execute JavaScript Code action → search **`Parse JSON`** (Data Operation) → add it.
2. **Content**: Dynamic content → the Execute JavaScript Code action's output (labelled "Output" or "Result").
3. **Schema**: click **Generate from sample** and paste:
   ```json
   [
     {
       "subject": "DBS: Prepare, then capture one real client concern",
       "start": "2026-06-26T09:00:00",
       "end": "2026-06-26T09:15:00",
       "timeZone": "Asia/Singapore",
       "description": "Review one resource and decide which client concern it helps you address.",
       "attachments": [
         {
           "@odata.type": "#microsoft.graph.fileAttachment",
           "name": "Inflation One-Pager.pdf",
           "contentType": "application/pdf",
           "contentBytes": "JVBERi0xLjQK"
         }
       ]
     }
   ]
   ```
   Click **Done** (or paste the schema from the "Parse JSON schema" block further below directly, if your designer offers a raw-schema paste option — same result either way).

**Part D — Apply to each → Create event (V4)**

1. Click **+** below Parse JSON → search **`Apply to each`** → add it.
2. Its **"Select an output from previous steps"** field → Dynamic content → pick the **Body** of **Parse JSON** (the array of 3 events).
3. Inside the now-expanded loop container, click **Add an action** → search **`Create event`** → choose **Office 365 Outlook → Create event (V4)**.
4. Fill every field using **Dynamic content** (this inserts the correct `item()?['…']` expression for you — don't type these by hand):

   | Field | Pick from Dynamic content |
   |---|---|
   | Calendar id | leave default, unless Flow A should book on a shared/service mailbox |
   | Subject | `subject` (from the current Apply-to-each item) |
   | Start time | `start` |
   | End time | `end` |
   | Time zone | `timeZone` |
   | Body | `description` |
   | Required attendees | the adviser-email field from **Get response details** (further up the flow — not from this loop) |

5. **Attachments** needs one extra step because the default UI only exposes single Name/Content fields, not an array. Look for a small icon at the right edge of the Attachments field (varies by designer version: "Switch to input entire array", or open the action's **"…" → Peek code** for just that action) and switch it to raw/array input. Then enter:
   ```
   item()?['attachments']
   ```
   The array is already shaped exactly as this field expects, so nothing further is needed.

**Part E — Retire "Send advisor email"**

- Click its **"…" menu → Delete**. `Create event (V4)` triggers Exchange's own invite automatically once an attendee is set, so this step is no longer needed.
- If you'd rather keep a courtesy note instead of deleting it outright, edit it: remove the `.ics` attachment and change the wording to something like *"Your calendar invites for the 3 follow-up touchpoints have been sent separately — check your Outlook calendar."*

**Part F — Save, test, then publish**

1. **Save draft** (not Publish yet).
2. Click **Test** → **Manually** → submit a real *test* response on the Form (use your own email as the "adviser") so the whole chain runs end to end.
3. Open the completed run and click into each new action to check its Inputs/Outputs:
   - "ICS Text" output starts with `BEGIN:VCALENDAR`.
   - Execute JavaScript Code output is a JSON array of **3** objects.
   - Parse JSON shows no red error.
   - Three "Create event (V4)" iterations inside Apply to each each show a green check with a returned event ID.
4. Check the test inbox — you should get **3 normal meeting invites** (not a file to import), each with Accept/Tentative/Decline, and the resource attached as a real file on the invite that shows one you attached it to.
5. Only once that looks right, click **Publish**.

**Troubleshooting**

| Symptom | Likely cause | Fix |
|---|---|---|
| *Execute JavaScript Code* missing from search results | Premium action not licensed in this environment | Ask your Power Platform admin to enable premium, or switch to the Azure Function version |
| Parse JSON shows a red schema error | The sample used to generate the schema didn't include an `attachments` array, or a touchpoint has no resource so the field is genuinely empty | Regenerate the schema from a run that includes at least one attachment, or make `attachments`/`description` optional (remove from the schema's `"required"` list if present) |
| `workflowContext.actions['ICS_Text']` errors with "Cannot read properties of undefined" | The Compose action's real internal name differs from `ICS_Text` | Use **Peek code** (Part B, step 4) to find the exact key and update the script |
| Create event fails with an attachment/size-related error | The embedded resource is too large for a direct attachment (a few MB ceiling via Graph) | Keep resources compact (the tool already warns about this on export), or host that resource as a link instead of embedding it |
| Invite arrives but with no attachment | Attachments field wasn't switched to raw/array input | Redo Part D, step 5 |

---

### 1–3. Get the `.ics` as text

Same SharePoint lookup as today (`Get file content` on the path built from firm + date), then add one **Compose** action, e.g. named `ICS Text`, with the expression:

```
base64ToString(body('Get_file_content'))
```

### 4. Parse it — "Execute JavaScript Code" action

Add Power Automate's premium **Execute JavaScript Code** action (no external Azure resource needed) with this script. It's written specifically for this tool's output — it unfolds RFC 5545 continuation lines, un-escapes text fields, and pulls out each embedded resource — so paste it as-is:

```javascript
function parseLtiIcs(icsText) {
  // RFC 5545 unfolding: a continuation line starts with a single space.
  var unfolded = icsText.replace(/\r\n /g, "");
  var lines = unfolded.split(/\r\n/);

  // Reverse of the tool's escIcs(), applied in the opposite order it was encoded.
  function unescapeText(v) {
    return v.replace(/\\;/g, ";").replace(/\\,/g, ",").replace(/\\n/g, "\n").replace(/\\\\/g, "\\");
  }
  // Split "NAME;PARAM=x;PARAM2=y:value" into its parts.
  function splitLine(line) {
    var colon = line.indexOf(":");
    var head = line.slice(0, colon);
    var value = line.slice(colon + 1);
    var semi = head.indexOf(";");
    var name = semi === -1 ? head : head.slice(0, semi);
    var paramsRaw = semi === -1 ? "" : head.slice(semi + 1);
    var params = {};
    paramsRaw.split(";").forEach(function (p) {
      var eq = p.indexOf("=");
      if (eq > -1) params[p.slice(0, eq)] = p.slice(eq + 1);
    });
    return { name: name, params: params, value: value };
  }

  var events = [];
  var current = null;
  lines.forEach(function (line) {
    if (line === "BEGIN:VEVENT") { current = { attachments: [] }; return; }
    if (line === "END:VEVENT") { if (current) events.push(current); current = null; return; }
    if (!current) return;
    var p = splitLine(line);
    if (p.name === "SUMMARY") current.subject = unescapeText(p.value);
    else if (p.name === "DESCRIPTION") current.description = unescapeText(p.value);
    else if (p.name === "DTSTART") { current.startRaw = p.value; current.timeZone = p.params.TZID || "UTC"; }
    else if (p.name === "DTEND") { current.endRaw = p.value; }
    else if (p.name === "ATTACH") {
      // Shaped exactly as Microsoft Graph / Create event (V4) expects, so it
      // can be passed straight into the Attachments field with no transform.
      current.attachments.push({
        "@odata.type": "#microsoft.graph.fileAttachment",
        name: p.params["X-FILENAME"] || "resource",
        contentType: p.params.FMTTYPE || "application/octet-stream",
        contentBytes: p.value
      });
    }
  });

  // "20260626T090000" -> "2026-06-26T09:00:00" (a local/floating time; paired with the Time Zone field, Create Event interprets it correctly).
  function toIso(raw) {
    return raw.slice(0,4)+"-"+raw.slice(4,6)+"-"+raw.slice(6,8)+"T"+raw.slice(9,11)+":"+raw.slice(11,13)+":"+raw.slice(13,15);
  }
  events.forEach(function (e) { e.start = toIso(e.startRaw); e.end = toIso(e.endRaw); delete e.startRaw; delete e.endRaw; });
  return events;
}

// Reference the Compose action from step 3 above (rename to match your action's name).
var icsText = workflowContext.actions['ICS_Text'].outputs;
return parseLtiIcs(icsText);
```

> **Verified:** this parser was tested directly against a real file exported by the tool — 3 events extracted with correct subjects, start/end times, time zone, and an embedded resource (including a filename with spaces/parentheses and description text containing semicolons, commas and line breaks) decoded back byte-for-byte correctly. The attachment objects come out already shaped as `{"@odata.type": "#microsoft.graph.fileAttachment", name, contentType, contentBytes}` — Microsoft Graph's own attachment schema — so they can go straight into the Attachments field with no extra transform step.

### 5. Create the events

Add **Parse JSON** on the script's output (sample schema below), then **Apply to each** → **Office 365 Outlook: Create event (V4)**, mapping the fields as shown in the flow outline above. For **Required attendees**, use the adviser's email from the Form response (add an email question to the Form if it doesn't collect one already). For **Attachments**, switch that field to *"Enter raw value"* / *"Edit in advanced mode"* and enter `item()?['attachments']` directly — the array is already in the shape the action expects.

**Parse JSON schema** (generate from sample, or paste this):
```json
{
  "type": "array",
  "items": {
    "type": "object",
    "properties": {
      "subject": { "type": "string" },
      "start": { "type": "string" },
      "end": { "type": "string" },
      "timeZone": { "type": "string" },
      "description": { "type": "string" },
      "attachments": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "@odata.type": { "type": "string" },
            "name": { "type": "string" },
            "contentType": { "type": "string" },
            "contentBytes": { "type": "string" }
          }
        }
      }
    }
  }
}
```

**Caveats**
- Keep resources modest in size — attaching files to a created event has a lower size ceiling (a few MB) than emailing a raw file, so the tool's existing "keep files compact" guidance matters even more here.
- If an uploaded resource's filename contains a semicolon, it will arrive escaped (`\;`) in the parsed `X-FILENAME` — rename the file first if that happens; it's a rare edge case.
- This replaces the "email the `.ics`" action in Flow A entirely — the adviser no longer receives the file at all, only the native invite.

---

## Recommended: the landing page (one scan = calendar + files)

The simplest, most reliable result is the **landing page**. On **Share & QR → Download landing page (.html)**, the tool builds **one self-contained HTML file** that bundles:

- an **"Add the calendar"** button (the `.ics` is embedded in the page), and
- every resource, grouped under its touchpoint, as a **tap-to-open button**.

You host that **single `.html`** on your approved storage (signed link, below) and point the QR at it. The adviser scans → sees the page → taps **Add the calendar** (events + talking points go into Outlook) → and opens any resource right there. Because the files live on the page, you don't have to host each resource separately for advisers to get them.

> Want the calendar event itself to also carry a tap-to-open link to a file (not just the page)? Host that resource separately too and paste its signed link in **Resources → Edit** — then the touchpoint's notes link straight to it. (A file embedded *inside* a calendar event never displays on phones, so a link is the real-world equivalent.)

The QR still points to a hosted link — so you host the **landing page** with the same signed-link method described next.

---

## Private hosting with a signed link (the compliant path)

### Why a signed link

A QR points to a URL the adviser's phone fetches. For an **external** adviser to open it **without a login**, the link has to be anonymously reachable — but you don't want it *public*. The enterprise answer is a **capability URL**: an unguessable, **time-limited signed link** to a file in the firm's own cloud storage:

- **Azure Blob Storage** → a **SAS** (Shared Access Signature) URL
- **Amazon S3** → a **pre-signed** URL
- **Google Cloud Storage** → a **signed** URL

These are **private** (unguessable + expiring + revocable), the data stays in **the firm's own tenant** (not a third party), and they open with **no login** on any adviser's phone. The tool recognises all three and a SharePoint "Anyone with the link" URL.

> SharePoint also works *if* your tenant allows "Anyone with the link" sharing — but many financial firms disable that (external advisers then hit an **HTTP 403** login wall). Signed cloud links avoid that problem, which is why they're the recommendation here.

**Important — don't modify a signed URL.** The signature covers the exact URL, so paste it exactly as issued. The tool will not alter signed links (unlike SharePoint, where it adds `download=1`). When you create the link, set the storage object's content settings so it **downloads** (e.g. `Content-Disposition: attachment`) rather than rendering inline.

### Each cohort

1. **Upload your resource files** to the storage. For each, generate a **signed download link** with an expiry that comfortably outlasts the follow-up window (e.g. **3+ months**). In the tool, open **Resources → Edit** and paste it into the resource's **hosted link** field — the card shows **"Hosted link set."**
2. On **Share & QR**, click **Download the .ics file.** The calendar already has each resource's signed link in the event Notes (no files embedded — calendar apps ignore those).
3. **Upload the `.ics`** the same way and generate **its** signed download link.
4. Back in the tool, paste it into **Signed link to the .ics** and click **Generate QR.** The tool shows a checklist to confirm before you share, then **Download PNG / Print** the QR.

**On expiry:** signed links lapse on purpose. Set them long enough for the whole journey, and re-issue + re-generate the QR when you start a new cohort. (If your storage supports it, a stored access policy lets you rotate/revoke without re-issuing every link.)

---

## Alternative: SharePoint "Anyone with the link"

Only if your tenant permits anonymous link sharing. Same steps as above, but the share URL is a SharePoint one; the tool appends `download=1`. If IT blocks anonymous sharing, external advisers get a 403 — use signed cloud links instead.

---

## Optional: public GitHub hosting (only if your policy allows)

> Skip this entirely if public hosting is not permitted. Use signed cloud links above instead.

### Step 1 — Create a public GitHub repository

1. Sign in at [github.com](https://github.com) (create a free account if needed).
2. Click **+ → New repository**.
3. Name it, e.g. `lti-calendar`.
4. Set visibility to **Public**.
   > Public means anyone with the link or QR can open the file and its resources. Only put **generic LTI material** in it — nothing client-specific or confidential.
5. Tick **Add a README file** (this gives the repo its first commit, which the tool needs to publish onto).
6. Click **Create repository**.

Your repository is now `your-username/lti-calendar`.

### Step 2 — Create an access token (for Option 1)

> Skip this step if you only want to use Option 2 (manual upload).

1. Go to **github.com → your avatar → Settings → Developer settings → Personal access tokens → Fine-grained tokens**.
2. Click **Generate new token**.
3. Give it a name (e.g. `lti-calendar-publish`) and an expiry.
4. Under **Repository access**, choose **Only select repositories** and pick `lti-calendar`.
5. Under **Permissions → Repository permissions**, set **Contents** to **Read and write**. (Leave everything else as "No access".)
6. Click **Generate token** and **copy it now** — GitHub only shows it once.

> The token is a password. The tool keeps it **in your browser only** and never sends it anywhere except GitHub. It is stored on your device only if you tick "Remember on this device".

### Step 3 — Decide your fixed naming (so the QR is reusable)

Pick these once and **keep them the same every time**:

| Field | Example |
|-------|---------|
| Repository | `your-username/lti-calendar` |
| Branch | `main` |
| File path | `lti-followup.ics` |

With those fixed, the public link is always:

```
https://raw.githubusercontent.com/your-username/lti-calendar/main/lti-followup.ics
```

…and so is the QR. Generate/print it once and you're done forever.

---

## Each cohort (about 1 minute)

1. Open `LTI_Engagement_Calendar_QR_v1.html`.
2. Fill in **Session details** and adjust the **touchpoint sequence** / **resources** if needed.
3. Click **Export calendar** (this also jumps you to the **Share by QR** tab).
4. **Option 1 (automatic, recommended):** in the *Publish to GitHub* card, enter your repo / branch / file path, paste your token, then click **Publish & make QR**. The tool uploads your attached resources to a `resources/` folder, links them inside the events, commits the calendar, and draws the QR — all in one click.
   - **Option 2 (manual):** upload the exported `.ics` to your repo (drag it in via **Add file → Upload files**, keep the same filename, **Commit**), then paste the file's link into the *Paste a public link* card and click **Generate QR**. *(Note: Option 2 does not auto-host resources — for resources to appear in advisers' calendars, use Option 1.)*
5. **Download PNG** or **Print** the QR and share it (slide, email, poster, handout).

Because the repo, branch and filename don't change, the URL and QR stay identical — re-publishing just replaces the file behind the same QR.

---

## What the adviser does

1. Scan the QR with their phone camera.
2. Tap the link that appears → the `.ics` downloads.
3. Tap the downloaded file → their phone offers to add the events. To land in **Outlook** specifically, open the file with the Outlook app (set it as the default handler, or choose it from the share sheet).
4. Open any event → its **Notes** show the talking-point and a **tappable link to each resource**. Tap a link to open the PDF.

This is a couple of taps — not fully automatic. No QR can silently write events into someone's mailbox; that would need an authenticated calendar integration, which is out of scope for a simple shareable QR.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| **401 Token rejected** | The token is wrong or expired. Generate a new one (Step 2). |
| **403 Forbidden** | The token lacks **Contents: Read and write**, or isn't scoped to this repo. |
| **404 Not found** | Check `owner/repo` spelling and that the **branch exists** (the repo needs at least one commit — that's why Step 1 adds a README). |
| **Conflict updating the branch** | Something else pushed at the same time. Just click **Publish** again. |
| **QR scans but the file is old** | `raw.githubusercontent.com` caches for a few minutes after each update. Wait briefly and re-scan. |
| **Phone won't open the file** | Confirm the link downloads the raw `.ics` (not a GitHub web page). Option 1 always produces a correct raw link. |

---

## Privacy notes

- Resource files stay in your browser session until you export.
- Nothing leaves your device except (a) the calendar file you publish to GitHub and (b) the API calls to GitHub when you click Publish.
- Anything you publish to a **public** repo is public. Keep it to generic LTI material.
