# Importing the Flow A package (legacy)

> **Having trouble with this legacy package?** Use the **solution** import
> instead — see [`IMPORT-SOLUTION.md`](./IMPORT-SOLUTION.md). It's the modern,
> more robust path and is the recommended option.

This folder ships the flow as an **importable Power Automate package** so you
don't have to rebuild every action by hand. The package is built from the
sources in `package/` and zipped to `LTI_Follow_up_Sender.zip`.

> The package gets you a working flow in a few clicks, but it still needs three
> environment-specific things filled in (Form ID, SharePoint site/path, and the
> four Form question IDs). If the import ever rejects the package on your tenant,
> fall back to building it by hand from [`flow-a-sender.md`](./flow-a-sender.md)
> — that guide is the source of truth and produces an identical flow.

---

## What's in the package

```
package/
├── manifest.json                         # package descriptor + connection list
└── Microsoft.Flow/flows/8f3a1c2e-.../
    └── definition.json                   # the flow definition (trigger + actions)
LTI_Follow_up_Sender.zip                  # the above, zipped — this is what you import
```

The flow uses three **standard** (non-premium) connectors: Microsoft Forms,
SharePoint, and Office 365 Outlook.

---

## Import steps

1. Go to **make.powerautomate.com** → choose the right **environment** (top right).
2. **My flows** → **Import** → **Import Package (Legacy)**.
3. Upload `LTI_Follow_up_Sender.zip`.
4. Under **Review Package Content**:
   - **LTI Follow-up Sender** (the flow) → *Setup: Create as new*.
   - For each connection (Microsoft Forms, SharePoint, Office 365 Outlook) →
     **Select during import** and pick an existing connection, or create one.
     During the test phase, the **Office 365 Outlook** connection should be the
     one for **cheesin.foong@capitalgroup.com** (the flow sends as the connection
     owner).
5. Click **Import**.

---

## After import — fill in the three environment values

The package ships with placeholders that you must replace once:

1. **Form ID** — open the imported flow → trigger **When a new response is
   submitted** and the **Get response details** action → set **Form Id** to your
   *LTI Workshop Follow-up* form. (The placeholder is `REPLACE_WITH_FORM_ID`.)
2. **SharePoint site + path** — open **Get file content using path** → set
   **Site Address** to the *Capital Learning Hub* site and confirm the **File
   Path** matches your library (see
   [`../sharepoint/structure.md`](../sharepoint/structure.md)). The package
   ships `https://capitalgroup.sharepoint.com/sites/CapitalLearningHub` and
   `/LTI/Generated ICS/@{outputs('Compose_filename')}` as a starting point.
3. **Form question IDs** — the expressions reference `['Firm']`,
   `['WorkshopDate']`, `['YourName']`, `['YourEmail']` as readable placeholders.
   After you pick the Form, re-select the proper dynamic-content tokens (or paste
   the real internal IDs from
   [`../form/form-spec.md`](../form/form-spec.md#question--dynamic-content-mapping)).

Then **Save** and run one end-to-end test (scan → submit your own email →
confirm the `.ics` arrives with exactly one attachment).

---

## Rebuilding the zip (if you edit the sources)

If you change anything under `package/`, rebuild the zip from **inside** the
`package/` folder so `manifest.json` sits at the zip root (not nested in a
`package/` directory):

```bash
cd lti-followup-test/flows/package
zip -r ../LTI_Follow_up_Sender.zip manifest.json Microsoft.Flow
```

---

## Honest limitations

- Power Automate can't be "deployed" from here — it lives in your tenant. This
  package is the closest deployable artifact; it still needs the connection
  mapping and the three values above.
- Hand-authored legacy packages occasionally need a small adjustment to import
  cleanly on a given tenant (Microsoft tweaks the package schema over time). If
  yours balks, the `flow-a-sender.md` GUI walkthrough builds the same flow
  reliably.
- The flow sends from the **connection owner** during test
  (`cheesin.foong@capitalgroup.com`). For production, swap the *Send an email
  (V2)* action for *Send an email from a shared mailbox (V2)* — see
  [`../docs/RUNBOOK.md`](../docs/RUNBOOK.md#production-handover).
