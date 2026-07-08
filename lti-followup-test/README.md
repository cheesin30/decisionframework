# LTI Workshop Follow-up — Minimal Delivery System

A Microsoft 365-native system that emails a calendar (`.ics`) follow-up pack to
advisers after a Capital Group **Long-Term Investing (LTI)** workshop. There is
**no external hosting** — everything runs in Microsoft Forms, Power Automate,
SharePoint and Outlook.

---

## What this system does (and who it is for)

**Audience:** the Capital Learning team running LTI workshops for financial
intermediary firms (DBS, AIA, HSBC, Manulife, and similar).

**The adviser experience:**

1. At the end of a workshop, the adviser scans a QR code on the closing slide.
2. A Microsoft Form opens. The adviser enters **only their name and email**.
3. Within ~30 seconds they receive an email with a single `.ics` calendar file
   attached. Tapping it drops three follow-up touchpoints — each with talking
   points already written into the event — straight into their calendar.

The `.ics` file is **pre-generated** by the existing *LTI Engagement Calendar*
tool and already contains everything (touchpoints, talking points, embedded
resources, alarms). Power Automate's only job is to **fetch the right file and
forward it**. It never builds calendar content.

---

## How the pieces fit together

```
 Calendar tool ──drops .ics──▶ SharePoint ◀──fetches── Power Automate ──emails──▶ Adviser
 (existing)                    /Capital Learning Hub/      (Flow A)
                               LTI/Generated ICS/
        ▲                                                      ▲
        │ Firm + Date                                          │ Firm + Date
        └──────────────── one unique QR per firm-per-session ──┘
                          (hidden, pre-filled Form fields)
```

The system works only because **both ends agree on one filename**:

```
{Firm}_LTI_Follow_Up_{yyyy-MM-dd}.ics
```

The calendar tool writes this name; the QR bakes the same `Firm` and `Date`
into the Form; Power Automate rebuilds the name and fetches it. If any of the
three disagree by a single character, the fetch fails. See the **Critical
naming convention** section below — it is the most important thing in this repo.

---

## File-by-file

| Path | What it is |
| --- | --- |
| `README.md` | This file. |
| `flows/flow-a-sender.md` | Human-readable spec for the Power Automate flow (**Flow A — LTI Follow-up Sender**): trigger, every step, and the exact WDL expressions. |
| `flows/flow-a-sender.json` | A realistic Logic Apps / Power Automate workflow-definition JSON for the same flow, to read alongside the `.md` when building it in the portal. |
| `flows/LTI_Follow_up_Sender_solution.zip` | **Importable Power Platform solution (recommended)** — the modern, more robust import path (handles connections via connection references). |
| `flows/IMPORT-SOLUTION.md` | How to import the solution, map connections, and fill in the three environment-specific values. |
| `flows/solution-package/` | Unzipped sources of the solution (`solution.xml`, `customizations.xml`, `[Content_Types].xml`, flow clientdata). |
| `flows/LTI_Follow_up_Sender.zip` | Importable Power Automate **legacy package** (alternative to the solution). |
| `flows/IMPORT.md` | How to import the legacy package and fill in the three environment-specific values. |
| `flows/package/` | Unzipped sources of the legacy package (`manifest.json` + flow `definition.json`). |
| `form/form-spec.md` | Specification for the Microsoft Form: title, settings, the 2 visible + 2 hidden questions, thank-you message, and the question → dynamic-content mapping table. |
| `form/form-build-sheet.md` | Copy-paste build sheet — every form field as a ready-to-paste block in build order (Forms has no import format). |
| `form/prefill-url-guide.md` | How to build the per-session pre-fill URL that bakes `Firm` and `Date` into the QR, including how to get the real field IDs from Microsoft's "Get a link to pre-fill answers" feature. |
| `sharepoint/structure.md` | The minimal SharePoint layout, the exact folder the `.ics` files live in, and a sample listing. |
| `emails/advisor-pack-email.html` | The adviser-facing HTML email body, with Power Automate placeholders and inline (mobile-friendly) CSS. |
| `emails/error-alert-email.html` | The diagnostic email body sent to the operator when the flow fails, with full debug context. |
| `emails/how-to-guide.html` | Source for the how-to PDF (rendered to PDF with headless Chromium). |
| `emails/LTI_Calendar_How-To.pdf` | The "how to open the calendar file" guide (phone + desktop) attached to every adviser email — upload once to SharePoint `/LTI/Assets/`. |
| `qr/qr-setup.md` | How to generate the QR for each session, plus three worked examples (DBS, AIA, HSBC). |
| `docs/RUNBOOK.md` | Operating manual: what the system does, the most common failures and their fixes, how to add a new workshop session, and the production handover steps. |
| `docs/troubleshooting-guide.html` | Source for the technical troubleshooting PDF (rendered with headless Chromium). |
| `docs/LTI_Flow_Troubleshooting.pdf` | Printable technical troubleshooting reference for the flow — how to read a failed run, symptom→cause→fix catalogue, connection fixes, and how to resubmit. Share with consultants/support. |

---

## Quick start (5 steps)

1. **SharePoint** — create `/Capital Learning Hub/LTI/Generated ICS/` (confirm
   the existing calendar tool drops `.ics` files there) and
   `/Capital Learning Hub/LTI/Assets/`, then upload `emails/LTI_Calendar_How-To.pdf`
   into `Assets/`. See `sharepoint/structure.md`.
2. **Form** — build the Microsoft Form exactly as in `form/form-spec.md`
   (2 visible questions, 2 hidden pre-filled questions, "Anyone can respond").
3. **Flow** — build **Flow A** in Power Automate from `flows/flow-a-sender.md`
   (read `flows/flow-a-sender.json` alongside it). Paste the adviser email body
   from `emails/advisor-pack-email.html` and the diagnostic body from
   `emails/error-alert-email.html`.
4. **QR per session** — for each firm-per-workshop, build the pre-fill URL
   (`form/prefill-url-guide.md`) and turn it into a QR (`qr/qr-setup.md`). Put
   the QR on the closing slide.
5. **Test** — run a real workshop date end-to-end: scan, submit your own email,
   confirm the email arrives within ~30 seconds with **two** attachments (the
   `.ics` and the how-to PDF).

---

## Dependencies

- **Microsoft 365** licence with Power Automate, Microsoft Forms, SharePoint
  Online and Office 365 Outlook (the standard connectors used here are part of
  the Microsoft 365 seeded/standard set — no premium connector is required).
- **The existing LTI Engagement Calendar tool**, which generates the `.ics`
  files and **must keep its current naming convention**
  (`{Firm}_LTI_Follow_Up_{yyyy-MM-dd}.ics`). This delivery system does not
  generate calendar content; it depends entirely on that tool's output.

---

## Critical naming convention

The single contract the whole system depends on:

```
{Firm}_LTI_Follow_Up_{yyyy-MM-dd}.ics
```

- **`Firm`** is produced by the calendar tool by *slugifying* whatever the
  consultant typed into its "Adviser / firm name" field: every run of
  non-alphanumeric characters becomes a single underscore, and leading/trailing
  underscores are stripped. So firm names are **not** guaranteed to be a tidy
  short code — `DBS` stays `DBS`, but `DBS Private Bank` becomes
  `DBS_Private_Bank`. Treat `Firm` as **case-sensitive** (`DBS`, not `dbs`).
- **`yyyy-MM-dd`** is the workshop completion date, with hyphens — never slashes
  or any other separator (`2026-06-30`, not `30-06-2026` or `2026/06/30`).

**The generated filename is the source of truth.** Because firm names vary,
the safest rule for whoever makes the QR is: open the `.ics` the calendar tool
produced and copy the `Firm` segment (everything before `_LTI_Follow_Up_`) and
the date segment **verbatim** into the pre-fill URL. Do not retype or
"tidy up" the firm name. `docs/RUNBOOK.md` and `form/prefill-url-guide.md`
cover this in detail.

---

## Test phase vs. production

During this test build the email is sent from **`cheesin.foong@capitalgroup.com`**
(an individual mailbox), **not** a shared mailbox. This is a deliberate
test-phase setting.

Before going live, switch the sender to the Capital Learning **shared mailbox**
(see "Production handover" in `docs/RUNBOOK.md`). The reply-to address is also
`cheesin.foong@capitalgroup.com` for now and should move with it.
