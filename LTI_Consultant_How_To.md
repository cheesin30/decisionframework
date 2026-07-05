# LTI Engagement Calendar — Consultant How-To

How to run the post-workshop follow-up for an adviser firm, from opening the tool to handing over the QR code. Takes about **5 minutes per workshop** once you've done the one-time setup.

---

## What this tool does

After a Long-Term Investing workshop, advisers get a **3-touchpoint follow-up calendar** (Day 1, Week 1, Month 1) with talking points and the workshop materials. Your job in the tool: enter the firm and date, load the right materials, adjust the touchpoints if needed, and produce a **QR code**.

What the adviser does with it:

1. **Scans the QR** with their phone camera.
2. A short **form opens, already filled in** with their firm and workshop date — they just tap **Submit**.
3. The three **calendar invites arrive in their Outlook** — they accept, and the touchpoints (with the materials) are in their calendar.

You never email files around, and nothing is saved loose on your desktop.

---

## Before your first use (one-time, ~3 minutes)

Do this once per computer.

### 1. Use the right browser
Open the tool file (`LTI_Engagement_Calendar_QR_v1.html`) in **Microsoft Edge** or **Chrome**. Other browsers work for building, but the one-click "Save to SharePoint" needs Edge/Chrome.

### 2. Sync the SharePoint folder
1. In your browser, open the SharePoint folder **`/Capital Learning Hub/LTI/Generated ICS/`**.
2. Click **Sync** in the toolbar (allow the "Open Microsoft OneDrive?" prompt).
3. Check **File Explorer**: under your organisation's name in the left sidebar you'll now see the synced folder (e.g. `Capital Learning Hub - Generated ICS`).

### 3. Point the tool at that folder
1. In the tool, go to **Step 4 (Share & QR)**.
2. Click the **choose folder** link under the *Save to SharePoint* button.
3. Pick the synced folder from step 2 and click **Edit files / Allow** when the browser asks.

Done — the tool remembers this folder from now on. (After restarting the browser, your first Save may ask "allow this site to edit files?" once — just click Allow.)

---

## Running a workshop follow-up (every time, ~5 minutes)

The tool is a 4-step wizard. Use **Next/Back** or click the step names at the top.

### Step 1 — Details
- **Adviser / firm name** — e.g. `DBS`. ⚠️ Use the **same spelling every time** for a firm; the whole chain matches on it.
- **Workshop completion date** — the day the workshop finished.
- **Timing options** (collapsed, usually leave alone): reminder time, duration, time zone, and weekend handling (touchpoints landing on a weekend move to Monday by default).

> The first touchpoint is scheduled the **day after** the workshop, then Week 1 and Month 1.

### Step 2 — Resources
- **Import materials pack (.json)** — the normal route: pick the region's pack file (Europe / Asia) and it loads the resources *and* the touchpoint setup in one go.
- Or **+ Add / swap a file** to upload PDFs/decks manually.
- Watch the size chips: a file flagged **"too big to attach"** (over 3 MB) won't make it into the adviser's invites — compress or split it first.

You can refresh or close the browser without losing anything — files are kept on this computer until you delete them.

### Step 3 — Touchpoints
Three cards, one per touchpoint. Click **Edit** on a card to:
- change the **title** or the **talking-point text** the adviser sees,
- change **when** it happens (e.g. 2 weeks instead of 1),
- **attach resources** from Step 2 (tick the boxes), 
- or disable a touchpoint entirely. **Add touchpoint** / **Reset to default** are at the top.

### Step 4 — Share & QR
Two clicks:

1. **Save to SharePoint** — writes the calendar files into the synced folder with the correct names; OneDrive uploads them automatically. The status line confirms; you can double-check the SharePoint folder the first few times.
2. The **QR code on the right is already generated** for this firm + date (it updates automatically if you change Step 1). **Download PNG** to drop it into slides, or **Print** — the printout is a ready-made handout that explains the three scan steps to the adviser.

Optional: type a **label** (e.g. "DBS — June cohort") to show under the QR.

### Hand it over
Show the QR on screen at the end of the session, include the PNG in the closing slide, or give out the printed handout. Each QR is specific to **one firm + one workshop date** — make a fresh one per session (it's automatic — just change Step 1).

---

## Quick answers

| Question | Answer |
|---|---|
| I refreshed / closed the browser — is my work gone? | No. Touchpoints, resources and settings are all kept on this computer. |
| A resource shows **"Reselect file"** | Rare (cleared browser storage). Click **Reselect** and pick the file again. |
| Can I re-run the same firm + date? | Yes — **Save to SharePoint** again; it cleanly replaces the previous files. |
| The adviser scanned but the form shows the wrong firm | The QR was made with a different Step 1 entry. Fix the firm name in Step 1, reprint the QR. |
| A touchpoint lands on a weekend | It auto-moves to Monday (changeable under *Timing options* in Step 1). |
| "This browser can't write directly into a folder" | You're not in Edge/Chrome. Switch browser, or use *Other ways to get the files there* to download the two files and drop them into the SharePoint folder yourself. |
| Save worked but files aren't in SharePoint | Check the OneDrive cloud icon in your system tray is signed in and not paused. |
| Something looks broken | Note what you clicked and take a screenshot — send it to whoever maintains the tool. |

---

## The three rules that keep the chain working

1. **Same firm spelling every time** — filenames and the form matching are built from it.
2. **Keep resources under 3 MB each** — bigger files won't attach to the adviser's invites.
3. **Always Save to SharePoint before sharing the QR** — the QR is instant, but the adviser's invites are built from the files you saved; no save, no invites.

*(Technical setup — the Form, the flow that sends the invites, SharePoint details — lives in `LTI_Calendar_QR_Setup_Guide.md` and is not something consultants need.)*
