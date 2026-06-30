# Flow A — LTI Follow-up Sender

Power Automate cloud flow. When an adviser submits the LTI follow-up Form, this
flow fetches the matching pre-generated `.ics` from SharePoint and emails it to
them as the single attachment. On any failure it emails a diagnostic alert to
the operator.

Read this alongside [`flow-a-sender.json`](./flow-a-sender.json), which is the
same flow expressed as a Logic Apps / Power Automate workflow definition.

---

## At a glance

| | |
| --- | --- |
| **Trigger** | Microsoft Forms — *When a new response is submitted* |
| **Connectors** | Microsoft Forms, SharePoint, Office 365 Outlook |
| **Premium connectors** | None |
| **Run target** | ~30 seconds, one email, exactly one attachment (the `.ics`) |
| **Region / time zone** | Asia/Singapore (SGT). Only the diagnostic timestamp is formatted; the filename date is passed through untouched. |

---

## Why the date is treated as plain text

The Workshop Date is a **short-text** question on the Form, pre-filled by the QR
with the literal string `2026-06-30` (`yyyy-MM-dd`). Because it is already in the
exact format the filename needs, the flow uses it **as-is** — there is no
`formatDateTime()` on it. This deliberately removes every chance of timezone
drift (e.g. a `Date`-typed question round-tripping through UTC and landing on the
day before). The only place we format a date is the diagnostic timestamp, which
is explicitly converted to SGT.

---

## Field references

In Power Automate, "Get response details" exposes each answer keyed by the
question's **internal ID**, not its display label. The expressions below use
readable placeholders — `['Firm']`, `['WorkshopDate']`, `['YourName']`,
`['YourEmail']` — for clarity. **Replace each placeholder with the real question
ID** from your Form. The full mapping is in
[`../form/form-spec.md`](../form/form-spec.md#question--dynamic-content-mapping).

> `# TODO: confirm with [Form owner]` the four real question IDs and substitute
> them everywhere `['Firm']`, `['WorkshopDate']`, `['YourName']`,
> `['YourEmail']` appear.

---

## Steps

### Trigger — When a new response is submitted (Microsoft Forms)

- **Form Id:** the LTI Workshop Follow-up form.
- Output: a response id. The trigger itself does **not** return answers — the
  next action does.

### 1. Get response details (Microsoft Forms)

- **Form Id:** same form.
- **Response Id:** `@{triggerOutputs()?['body/resourceData/responseId']}`
  (in the designer, the dynamic-content token *"Response Id"* from the trigger).
- Output `body('Get_response_details')` now carries every answer, including the
  two hidden pre-filled fields (`Firm`, `WorkshopDate`).

### 2. Compose — construct the `.ics` filename

Action name: **`Compose_filename`**.

```
@{concat(
   body('Get_response_details')?['Firm'],
   '_LTI_Follow_Up_',
   body('Get_response_details')?['WorkshopDate'],
   '.ics'
)}
```

For `Firm = DBS` and `WorkshopDate = 2026-06-30` this yields:

```
DBS_LTI_Follow_Up_2026-06-30.ics
```

> **Naming contract.** `Firm` and `WorkshopDate` are passed through verbatim —
> capitalisation and hyphens are preserved exactly as the QR baked them, which
> is exactly how the calendar tool named the file. Do not trim, lower-case, or
> reformat either value here. See the README's *Critical naming convention*.

### 3. Try scope — fetch and send

A **Scope** named `Try` wraps the two actions that can fail, so a single catch
can handle either one.

#### 3a. Get file content using path (SharePoint)

- **Site Address:** the *Capital Learning Hub* site.
  `# TODO: confirm with [SharePoint owner]` the exact site URL, e.g.
  `https://capitalgroup.sharepoint.com/sites/CapitalLearningHub`.
- **File Path:**
  ```
  /LTI/Generated ICS/@{outputs('Compose_filename')}
  ```
  (Server-relative path within the document library — adjust the leading
  segment to match your library; see
  [`../sharepoint/structure.md`](../sharepoint/structure.md).)
- Output `body('Get_file_content_using_path')?['$content']` is the base64 file
  content used as the attachment.

#### 3b. Send an email (V2) (Office 365 Outlook)

| Field | Value |
| --- | --- |
| **From** | `cheesin.foong@capitalgroup.com` — **test phase only** (see note below). |
| **To** | `@{body('Get_response_details')?['YourEmail']}` |
| **Subject** | `Your LTI workshop follow-up` |
| **Body** | The HTML from [`../emails/advisor-pack-email.html`](../emails/advisor-pack-email.html), with its `@{...}` placeholders kept as Power Automate expressions. Set the body editor to **code view** before pasting so the HTML is preserved. |
| **Reply To** | `cheesin.foong@capitalgroup.com` |
| **Attachments Name - 1** | `@{outputs('Compose_filename')}` |
| **Attachments Content - 1** | `@{body('Get_file_content_using_path')?['$content']}` |

There must be **exactly one** attachment — the `.ics`. No separate tipsheet, no
extra files.

> **Sender nuance (production-quality note).** The standard *Send an email (V2)*
> action sends as the **owner of the Outlook connection**. During the test phase
> the connection is `cheesin.foong@capitalgroup.com`, so the email correctly
> goes out from that address — there is no separate "From" field to set on the
> plain V2 action. For production you switch to **Send an email from a shared
> mailbox (V2)** and set **From** to the shared mailbox (the connection owner
> must have *Send as* / *Send on behalf* rights). This is the one action that
> changes at handover; everything else stays identical. See
> `docs/RUNBOOK.md` → *Production handover*.

### 4. Catch — diagnostic alert on failure

A second **Scope** named `Catch`, configured to run **after `Try` fails or times
out** (`runAfter: { "Try": ["Failed", "TimedOut"] }`). It captures whichever
action failed and emails the operator.

#### 4a. Filter array — isolate the failed action

Action name: **`Filter_failed_actions`** (the *Filter array* action — WDL has no
`filter()` expression, so this is a real action, not an inline expression).
`result('Try')` returns the result objects of the actions inside the `Try`
scope; we keep only the failed one.

- **From:** `@result('Try')`
- **Filter (advanced mode):** `@equals(item()?['status'], 'Failed')`

#### 4b. Compose — error message

Action name: **`Compose_error`**. Pull the message off the first failed action:

```
@{first(body('Filter_failed_actions'))?['error']?['message']}
```

#### 4c. Send an email (V2) — diagnostic to operator

| Field | Value |
| --- | --- |
| **From / connection** | `cheesin.foong@capitalgroup.com` |
| **To** | `cheesin.foong@capitalgroup.com` |
| **Subject** | `⚠ LTI Follow-up FAILED — @{outputs('Compose_filename')}` |
| **Body** | The HTML from [`../emails/error-alert-email.html`](../emails/error-alert-email.html). |

The diagnostic body includes, as placeholders:

- Constructed filename — `@{outputs('Compose_filename')}`
- Firm — `@{body('Get_response_details')?['Firm']}`
- Workshop date — `@{body('Get_response_details')?['WorkshopDate']}`
- Adviser email — `@{body('Get_response_details')?['YourEmail']}`
- Timestamp (SGT) —
  `@{convertFromUtc(utcNow(), 'Singapore Standard Time', 'yyyy-MM-dd HH:mm:ss')}`
  (`Singapore Standard Time` is the Windows time-zone id; `+08:00`, no DST.)
- Error message — `@{outputs('Compose_error')}`

#### 4d. Terminate

End the run as **Failed** (status `Failed`, code `ICSDeliveryFailed`) so the run
shows red in the Power Automate run history and is easy to spot.

---

## WDL functions used (validated)

All expressions use Workflow Definition Language functions from Microsoft's
published reference:

- `concat()` — build the filename and subject.
- `body()` — read action outputs (`Get_response_details`, `Get_file_content_using_path`).
- `outputs()` — read Compose outputs (`Compose_filename`, `Compose_error`).
- `triggerOutputs()` — read the trigger's response id.
- `convertFromUtc()` — render the diagnostic timestamp in SGT.
- `result()`, `first()`, `equals()`, `item()` — extract the failure message in
  the catch (`equals`/`item` inside the *Filter array* action; `result`/`first`
  in the Compose).

`formatDateTime()` is intentionally **not** applied to `WorkshopDate` (it is
already a literal `yyyy-MM-dd` string). It would only be needed if the Form's
Workshop Date question were changed to a `Date` type — see `form/form-spec.md`.
