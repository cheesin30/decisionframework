# SharePoint structure

Deliberately minimal. For this test build the **only** thing SharePoint holds is
the folder of pre-generated `.ics` files that Power Automate fetches. No Excel
logs, no separate tipsheet library, no consent register.

---

## The one folder that matters

```
Capital Learning Hub            ← SharePoint site
└── LTI                         ← document library (or top-level folder)
    └── Generated ICS           ← the existing calendar tool drops .ics files here
        ├── DBS_LTI_Follow_Up_2026-06-30.ics
        ├── AIA_LTI_Follow_Up_2026-07-15.ics
        ├── HSBC_LTI_Follow_Up_2026-07-22.ics
        └── …
```

Full path used in Flow A's *Get file content using path*:

```
/Capital Learning Hub/LTI/Generated ICS/{Firm}_LTI_Follow_Up_{yyyy-MM-dd}.ics
```

> `# TODO: confirm with [SharePoint owner]` the exact **Site Address** and
> whether `LTI` is a document library or a folder inside *Documents*. In Flow A:
> - **Site Address** = the *Capital Learning Hub* site URL
>   (e.g. `https://capitalgroup.sharepoint.com/sites/CapitalLearningHub`).
> - **File Path** = the path **relative to the library**. If `LTI` is its own
>   library, the path is `/Generated ICS/{filename}`. If `LTI` is a folder under
>   the default *Documents* library, it is `/LTI/Generated ICS/{filename}`.
>   Adjust `flows/flow-a-sender.*` to match.

---

## Who writes here vs. who reads here

| Actor | Action |
| --- | --- |
| **Existing LTI Engagement Calendar tool** | **Writes** `.ics` files into `Generated ICS/`, named `{Firm}_LTI_Follow_Up_{yyyy-MM-dd}.ics`. This delivery system does not create these — it assumes they already exist. |
| **Flow A (Power Automate)** | **Reads** one file per form submission, by reconstructing the exact filename. Never writes. |

---

## Naming rules for files in this folder

These are the rules the **calendar tool** already follows; they are repeated here
because Flow A's fetch depends on them being honoured exactly:

- Pattern is fixed: `{Firm}_LTI_Follow_Up_{yyyy-MM-dd}.ics`.
- `Firm` is **case-sensitive** and may contain underscores (it is the slugified
  firm name). `DBS`, `DBS_Private_Bank` — but never `dbs`.
- Date is `yyyy-MM-dd` with **hyphens** — `2026-06-30`, never `30-06-2026` or
  `2026/06/30`.
- One file per firm-per-workshop session.

If a fetch fails, the filename mismatch is almost always the cause — see
[`../docs/RUNBOOK.md`](../docs/RUNBOOK.md).

---

## Access

- The Power Automate **SharePoint connection** (owned by the flow author during
  the test phase) needs **read** access to this folder. Standard member access
  to the *Capital Learning Hub* site is sufficient.
- Nothing in this folder is shared externally. Advisers never touch SharePoint —
  they only ever receive the `.ics` as an email attachment.
