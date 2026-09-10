# Microsoft Form — "LTI Workshop Follow-up"

The form the adviser fills in after scanning the QR. It captures **only name and
email**. The `Firm` and workshop `Date` are **not** asked — they ride in as
hidden, pre-filled fields baked into each session's QR (see
[`prefill-url-guide.md`](./prefill-url-guide.md)).

---

## Form settings

| Setting | Value |
| --- | --- |
| **Title** | `LTI Workshop Follow-up` |
| **Description** | `Thanks for joining today's Long-Term Investing workshop. Pop your details in below and your follow-up calendar pack will be on its way.` (friendly, 1–2 lines) |
| **Who can respond** | **Anyone can respond** — advisers are external to the tenant, so this must not be restricted to people in the organisation. |
| **Record name** | **Off** ("One response per person" off; do not automatically record the submitter's M365 name — we collect the name ourselves). |
| **Accept responses** | On. |
| **Custom thank-you message** | On (see below). |

### Custom thank-you message

> **You're all set.** Your LTI follow-up pack is on its way — check your inbox in
> the next minute or so for a calendar file to add to your phone or Outlook. If
> it hasn't arrived, check your junk/spam folder.

---

## Questions

Four questions total: **two visible** (the adviser fills these) and **two
hidden, pre-filled** (the QR fills these; the adviser never sees them).

### Visible

1. **Your Name** — *Short text*, **required**.
   - Subtitle: `First and last name.`

2. **Your Email** — *Short text*, **required**, with **"@" restriction**.
   - Turn on **Restrictions → must contain `@`** (Microsoft Forms validates the
     entry contains an `@`). This is the address the pack is sent to.
   - Subtitle: `We'll send your follow-up pack here.`

### Hidden / pre-filled (populated by the QR's URL parameters)

Microsoft Forms has no literal "hidden" flag, so these two questions are made
effectively invisible by **always pre-filling them from the QR** and labelling
them clearly as not-to-be-touched. Place them **last** so the adviser's eye
lands on Name/Email first.

3. **Firm** — *Short text*, **required**.
   - Subtitle: `Pre-filled from QR — please don't change.`

4. **Workshop Date** — *Short text*, **required**.
   - Subtitle: `Pre-filled from QR — please don't change.`
   - **Type is short text, not a Date question**, on purpose. The QR pre-fills it
     with the literal `yyyy-MM-dd` string (e.g. `2026-06-30`). Keeping it as text
     means the value Power Automate reads is byte-for-byte what the filename
     needs — no date parsing, no timezone drift. (A `Date`-type question would
     return a locale/UTC-influenced datetime that can land on the wrong day in
     SGT and break the filename match.)

> `# TODO: confirm with [Form owner]` Microsoft Forms shows pre-filled values in
> editable fields; there is no server-side "lock". If advisers tampering with
> Firm/Date ever becomes a real problem, the fallback is to add a short Power
> Automate validation branch (reject/alert if `Firm` or `WorkshopDate` is empty
> or malformed). Out of scope for this minimal test build.

---

## Question → dynamic-content mapping

When you build **Flow A**, "Get response details" exposes each answer under its
**internal question ID**, not the display label. Capture the real IDs once
(easiest via the pre-fill link — see `prefill-url-guide.md`) and use this table
to wire the flow.

| Question (label) | Visible? | Used in Flow A as | Real internal ID |
| --- | --- | --- | --- |
| Your Name | Yes | `body('Get_response_details')?['YourName']` → email greeting | `# TODO: paste real ID` |
| Your Email | Yes | `body('Get_response_details')?['YourEmail']` → email **To** | `# TODO: paste real ID` |
| Firm | Hidden | `body('Get_response_details')?['Firm']` → filename + diagnostics | `# TODO: paste real ID` |
| Workshop Date | Hidden | `body('Get_response_details')?['WorkshopDate']` → filename + diagnostics | `# TODO: paste real ID` |

The placeholder keys (`YourName`, `YourEmail`, `Firm`, `WorkshopDate`) are what
`flows/flow-a-sender.md` and `flows/flow-a-sender.json` use for readability —
swap in the real IDs from the right-hand column everywhere they appear.
