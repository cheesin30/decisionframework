# Power Automate Account Handover — Chee Sin → Capital Learning

How to move the LTI follow-up automation off **Chee Sin's personal account** and onto the **official Capital Learning account**, so the flow, the Microsoft Form and the meeting invites all run under Capital Learning — not an individual — and keep working after Chee Sin's account changes or is deprovisioned.

**Read this first:** the flow is one object, but it depends on three things that are each tied to *whoever authenticated them* — the **Microsoft Form**, the **connections** (Forms, SharePoint, Outlook), and the **mailbox** the invites are sent from. Transferring the flow alone is **not** enough; the connections and the Form have to be moved too, or the automation silently keeps running as Chee Sin and breaks the day that account is disabled.

> **Recommendation on which account to use:** hand over to a **shared / service account or a Microsoft 365 Group owned by Capital Learning**, not a second named individual. That way the next staff change doesn't trigger this whole exercise again, and advisers see invites from *"Capital Learning"* rather than a person.

---

## What breaks if this isn't done

| If left on Chee Sin's account… | Consequence |
|---|---|
| The **flow** stays owned by Chee Sin | When the account is disabled, the flow is orphaned and **stops running** — advisers submit the Form and never get invites |
| The **Outlook connection** stays Chee Sin's | Meeting invites keep going out **from Chee Sin's mailbox**, from a name advisers don't recognise, and stop entirely once the mailbox is gone |
| The **SharePoint connection** stays Chee Sin's | The "get the `.ics`/`.json` file" step runs on Chee Sin's permissions; loses access when the account is removed |
| The **Form** stays owned by Chee Sin | Responses (and the trigger) are tied to a personal form; can't be co-managed and is lost with the account |

The goal of this handover is that **none** of the four rows above still point at Chee Sin when you're done.

---

## Before you start — have these ready

| # | Item | Notes |
|---|------|-------|
| 1 | The Capital Learning account credentials | Ideally a **shared/service account** or a **Microsoft 365 Group**, not a personal one |
| 2 | Confirmation the Capital Learning account is **licensed for Power Automate** | Same plan level Chee Sin used (standard connectors are enough for the JSON-export flow) |
| 3 | The Capital Learning account has **access to the SharePoint site** | Specifically read access to `/Capital Learning Hub/LTI/Generated ICS/` |
| 4 | The Capital Learning account can **send calendar invites** | i.e. has a real mailbox — invites will be sent *from* it after cutover |
| 5 | The name of the existing flow | e.g. *"LTI Follow-up Sender"* — the flow currently in Chee Sin's *My flows* |
| 6 | A test email address you control | For the end-to-end verification submission at the end |
| 7 | ~30 minutes, both accounts available | Some steps need Chee Sin signed in, some need Capital Learning signed in |

---

## Choose your handover route

There are two clean ways to do this. Pick one.

| Route | Best when | Trade-off |
|---|---|---|
| **A · Co-own, re-point, then remove** *(recommended)* | The same flow, same Form and same SharePoint site are being kept — you only want to change *who owns and runs it* | Fewest moving parts; keeps run history; done in place |
| **B · Export & import into Capital Learning** | Capital Learning is a **different environment/tenant**, or you want a clean copy owned outright by the new account | Loses run history; all connections must be rebuilt from scratch; the Form pre-fill URL may change |

The rest of this guide follows **Route A** and notes the **Route B** differences where they matter.

---

## Route A — Co-own, re-point connections, then remove Chee Sin

### Step 1 · Add the Capital Learning account as a co-owner of the flow *(Chee Sin does this)*

1. Sign in to **make.powerautomate.com** as Chee Sin.
2. **My flows** → open the LTI follow-up flow → **Edit** (or the **Share / Owners** panel).
3. Under **Owners / Manage run-only users**, add the **Capital Learning account** as a **co-owner**.
4. Save. The flow now appears under **My flows** for the Capital Learning account too.

> Co-owning does **not** change who the flow *runs as* — that's the connections, handled in Step 3. It only lets the Capital Learning account edit and, crucially, attach its own connections.

### Step 2 · Create the Capital Learning connections *(Capital Learning account does this)*

Sign in to **make.powerautomate.com** as the **Capital Learning account**, go to **Data → Connections → + New connection**, and create one for each connector the flow uses. Sign in as Capital Learning when prompted for each:

- **Microsoft Forms**
- **SharePoint**
- **Office 365 Outlook** ← this is the one that determines the invite sender

You should end up with three connections owned by the Capital Learning account, sitting alongside Chee Sin's existing ones.

### Step 3 · Re-point every action in the flow to the Capital Learning connections

Still as the **Capital Learning account**, open the flow → **Edit**. For **each** action, switch its connection from Chee Sin's to the matching Capital Learning one:

| Action in the flow | Connector | Set connection to |
|---|---|---|
| Trigger — *When a new response is submitted* | Microsoft Forms | Capital Learning |
| *Get response details* | Microsoft Forms | Capital Learning |
| *Get file content using path* | SharePoint | Capital Learning |
| *Create event (V4)* | Office 365 Outlook | **Capital Learning** — invites now come from this mailbox |

**How to change a connection on an action:** open the action → click the **"…" menu → + Add new connection** or the connection name shown at the bottom of the card → pick the Capital Learning connection. (Some designer versions expose this under **My connections** at the bottom of the action panel.)

After all four, use the flow's **"…" → Peek code** and confirm no `connectionReferences` still name Chee Sin.

### Step 4 · Hand over the Microsoft Form

The trigger listens to a **specific Form**. If that Form stays personally owned by Chee Sin, the handover is incomplete.

**Preferred — move the Form to a Microsoft 365 Group Capital Learning owns:**
1. Sign in to **forms.office.com** as Chee Sin → open the LTI follow-up form.
2. **… (More) → Move** → choose the **Capital Learning group**. The form becomes a **group form**, co-owned by everyone in that group. Ownership no longer depends on Chee Sin.
3. Back in the flow, reopen the **trigger** and, if the form picker no longer lists it under the same name, re-select it from the group forms. Re-check *Get response details* points at the same form.

**If you can't move it — add a co-owner and share the collaboration link:**
1. In the form → **Collaborate or Duplicate (the "…") → + Get a link to view and edit** → set to your org → share with the Capital Learning account so it can co-manage responses.
2. Note this is weaker than a group move — the form is still rooted in Chee Sin's account. Move to a group when you can.

> **Route B note:** if you rebuilt the flow in a different environment, you likely created a **new** form. A new form means a **new pre-fill URL** → you must paste it into the calendar tool (*Share & QR → Form settings*) and **re-generate/re-print the QR codes**. With Route A you keep the same form and the **existing QR codes keep working** — no re-print.

### Step 5 · Confirm SharePoint access

The Capital Learning connection (Step 2) runs *Get file content using path* under the Capital Learning account's SharePoint permissions.

1. Confirm the Capital Learning account can open `/Capital Learning Hub/LTI/Generated ICS/` in SharePoint directly. If not, grant it **read** access to that library.
2. The **consultants' file drop is unaffected** — *Save to SharePoint* in the tool writes via each consultant's own OneDrive sync, independent of the flow's account. Nothing to change there.

### Step 6 · Verify end-to-end *(as the Capital Learning account)*

1. Make sure a real `.json` (and `.ics`) file for a test firm+date exists in the `Generated ICS` folder — e.g. run the tool once with firm `TEST` and today's date and save it.
2. **Test the flow:** flow → **Test → Manually** → submit a **real test response** on the Form, using **your own email** (from Step 7 of prerequisites) as the adviser email.
3. Open the completed run and confirm:
   - Trigger and *Get response details* ran on the **Capital Learning** Forms connection.
   - *Get file content using path* succeeded on the **Capital Learning** SharePoint connection.
   - *Create event (V4)* returned success **three times**.
4. Check your test inbox: **3 meeting invites**, and confirm the **sender is now the Capital Learning mailbox**, not Chee Sin.
5. Only once all of that is green, move to Step 7.

### Step 7 · Remove Chee Sin *(the actual cutover)*

Do this **only after Step 6 passes** — this is the point of no return for the old ownership.

1. In the flow's **Owners**, **remove Chee Sin** (or downgrade to run-only if you want a temporary safety net first).
2. Delete or leave dormant Chee Sin's old **connections** — once no action references them, they're harmless, but removing them proves nothing still runs as Chee Sin.
3. If the Form was moved to a group (Step 4), remove Chee Sin's individual ownership if it lingers.
4. **Publish** the flow.

The automation now runs entirely as Capital Learning.

---

## Route B — Export & import (only if changing environment/tenant)

Use this instead of Route A only when Capital Learning is a **separate environment or tenant**.

1. *(As Chee Sin)* **My flows → … → Export → Package (.zip)**.
2. *(As Capital Learning)* **My flows → Import → Import package**, upload the `.zip`.
3. During import, **map every connection** to a Capital Learning connection (create them if prompted) — Forms, SharePoint, Outlook.
4. Recreate or move the **Form** under Capital Learning; if it's a new form, grab the **new pre-fill URL**.
5. **Update the calendar tool** with the new Form URL (*Share & QR → Form settings*) and **re-generate the QR codes** — old QRs point at the old form and won't work.
6. Run the **Step 6 verification** above.
7. **Turn off** the old flow in Chee Sin's account.

> Because Route B loses run history and forces new QR codes, prefer **Route A** unless a tenant/environment change forces your hand.

---

## Cutover checklist

- [ ] Capital Learning account chosen (shared/service account or M365 group), licensed, with SharePoint + mailbox access
- [ ] Capital Learning added as **co-owner** of the flow
- [ ] Capital Learning **connections** created (Forms, SharePoint, Outlook)
- [ ] **All four actions** re-pointed to Capital Learning connections (verified via Peek code)
- [ ] **Form** moved to / co-owned by Capital Learning (trigger re-selected if needed)
- [ ] SharePoint **read access** to `Generated ICS` confirmed for Capital Learning
- [ ] End-to-end **test** passed — 3 invites, **sent from the Capital Learning mailbox**
- [ ] **Chee Sin removed** as owner; old connections retired
- [ ] Flow **published**
- [ ] *(Route B only)* Tool updated with new Form URL and **QR codes re-printed**

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Invites still show **Chee Sin** as sender | The *Create event (V4)* action still uses Chee Sin's Outlook connection | Re-open that action and switch it to the Capital Learning Outlook connection (Step 3) |
| Flow fails at the trigger after handover | Form wasn't moved/shared, or trigger still points at Chee Sin's personal form | Re-select the form in the trigger from the Capital Learning group forms (Step 4) |
| *Get file content using path* fails with 403/404 | Capital Learning account lacks SharePoint access, or the file name doesn't match | Grant read access to `Generated ICS`; confirm the firm+date file exists with the exact `<Firm>_LTI_Follow_Up_<date>` name |
| Existing QR codes stopped working | You took Route B and the Form URL changed | Re-paste the new pre-fill URL in the tool and re-print the QR (Route A avoids this) |
| Can't add Capital Learning as co-owner | It's in a different environment/tenant | Use **Route B** (export/import) instead |
| "Connection not valid" after re-pointing | The new connection wasn't authenticated as Capital Learning | Re-create the connection under **Data → Connections** while signed in as Capital Learning, then reselect it |

---

## What changes for consultants and advisers

- **Consultants:** nothing in the calendar tool changes under Route A — same tool, same *Save to SharePoint*, same QR codes. (Under Route B they must use re-printed QR codes.)
- **Advisers:** the follow-up meeting invites now arrive **from Capital Learning** instead of Chee Sin — a cleaner, more official sender. The Accept/Tentative/Decline experience is otherwise identical.
