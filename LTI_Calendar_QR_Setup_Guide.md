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
