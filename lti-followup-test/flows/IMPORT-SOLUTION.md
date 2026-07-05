# Importing Flow A as a solution (recommended)

If the **legacy package** import (`IMPORT.md`) gave you trouble, use this instead.
`LTI_Follow_up_Sender_solution.zip` is an **unmanaged Power Platform solution** —
the modern, more robust import path. It handles connections through *connection
references*, which the import wizard prompts you to map.

Built from the sources in `solution-package/`.

---

## What's in the solution

```
solution-package/
├── [Content_Types].xml     # OPC content-type map (required at zip root)
├── solution.xml            # solution manifest: publisher "Capital Learning" (prefix cl), v1.0.0.0, unmanaged
├── customizations.xml      # the cloud flow + three connection references
└── Workflows/
    └── LTIFollowupSender-8F3A1C2E-...-.json   # the flow definition (clientdata)
LTI_Follow_up_Sender_solution.zip              # the above, zipped — this is what you import
```

Three standard (non-premium) connection references are declared, one per
connector:

| Connection reference (logical name) | Connector |
| --- | --- |
| `cl_sharedmicrosoftforms` | Microsoft Forms |
| `cl_sharedsharepointonline` | SharePoint |
| `cl_sharedoffice365` | Office 365 Outlook |

The flow imports **turned off (draft)** on purpose, so the import never fails
trying to activate before its connections exist. You bind connections, then turn
it on.

---

## Import steps

1. Go to **make.powerautomate.com** (or **make.powerapps.com**) → pick the right
   **environment** (top right). *The environment must have Dataverse — solutions
   require it. If "Solutions" isn't in the left nav, use the legacy package
   (`IMPORT.md`) instead, or ask your admin.*
2. Left nav → **Solutions** → **Import solution**.
3. **Browse** → choose `LTI_Follow_up_Sender_solution.zip` → **Next**.
4. On the **Connections** step, for each of the three connection references pick
   an existing connection or create a new one:
   - **Office 365 Outlook** → the **cheesin.foong@capitalgroup.com** connection
     (test phase — the flow sends as this connection's owner).
   - **Microsoft Forms** and **SharePoint** → your own connections.
5. **Import** and wait for "successfully imported".

---

## After import — fill in the three environment values

Open **Solutions → LTI Workshop Follow-up → LTI Follow-up Sender** and edit:

1. **Form ID** — set it on the trigger *When a new response is submitted* and on
   *Get response details* (placeholder `REPLACE_WITH_FORM_ID`).
2. **SharePoint site + path** — on *Get file content using path*, set **Site
   Address** to the *Capital Learning Hub* site and confirm the **File Path**
   matches your library (see [`../sharepoint/structure.md`](../sharepoint/structure.md)).
3. **Form question IDs** — the expressions use `['Firm']`, `['WorkshopDate']`,
   `['YourName']`, `['YourEmail']` as placeholders; re-point them to the real
   dynamic-content tokens / IDs (see
   [`../form/form-spec.md`](../form/form-spec.md#question--dynamic-content-mapping)).
4. **How-to PDF** — upload `../emails/LTI_Calendar_How-To.pdf` to
   `/Capital Learning Hub/LTI/Assets/` once (the *Get how-to PDF* action reads it
   from `/LTI/Assets/LTI_Calendar_How-To.pdf`). If it's missing, **every** send
   fails.

Then **Save**, **Turn on** the flow, and run one end-to-end test (scan → submit
your own email → confirm the email arrives with **two** attachments — the `.ics`
and the how-to PDF).

---

## Rebuilding the zip (if you edit the sources)

Rebuild from **inside** `solution-package/` so `[Content_Types].xml` and
`solution.xml` sit at the zip root:

```bash
cd lti-followup-test/flows/solution-package
zip -r ../LTI_Follow_up_Sender_solution.zip "[Content_Types].xml" solution.xml customizations.xml Workflows
```

If you also bump the flow, keep the `WorkflowId` in `customizations.xml`, the
`<JsonFileName>`, and the actual file name in `Workflows/` all in sync, and raise
`<Version>` in `solution.xml`.

---

## Honest limitations

- This is a **hand-authored** unmanaged solution. It's built to the documented
  shape and validated as well-formed, but I can't import it against your tenant
  from here, so treat the first import as a smoke test.
- It requires a **Dataverse-enabled environment** (all solutions do). If yours
  has none, the legacy package (`IMPORT.md`) or the by-hand GUI build
  ([`flow-a-sender.md`](./flow-a-sender.md)) are the alternatives.
- If the solution import still errors, the **GUI build from
  `flow-a-sender.md` is the guaranteed path** — it produces an identical flow in
  ~15 minutes, and you can then *export* it as your own solution from a known-good
  starting point.
- Production handover (shared-mailbox sender) is unchanged — see
  [`../docs/RUNBOOK.md`](../docs/RUNBOOK.md#production-handover).
```
