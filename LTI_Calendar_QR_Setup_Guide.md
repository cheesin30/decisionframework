# LTI Engagement Calendar — QR Setup Guide

A one-time setup so you can turn the follow-up calendar into a **QR code advisers scan to add the touchpoints (with the resource files) to their phone or Outlook.**

The tool is `LTI_Engagement_Calendar_QR_v1.html` — just open it in Chrome, Edge or Safari. There is nothing to install and no server to run.

---

## How it works (the 30-second version)

A QR code is tiny (~3 KB max), so it **cannot** hold a calendar file that has PDFs embedded in it. Instead, the calendar file lives at a **public link**, and the QR points to that link. When an adviser scans it, their phone downloads the file and offers to add it to their calendar / Outlook.

So the flow is always: **build → export the `.ics` → get it to a public link → QR.**

The tool gives you two ways to do the "get it to a public link" part:

- **Option 1 — Publish to GitHub automatically** (recommended): the tool uploads the file and makes the QR for you.
- **Option 2 — Paste a link you hosted yourself** (fallback): you upload the file, paste the link.

The single biggest time-saver: **set up one fixed repo + filename once, and the QR never changes.** Print it once and reuse it for every cohort — you just re-publish to overwrite the file behind it.

---

## One-time setup (about 5 minutes)

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
4. **Option 1 (automatic):** in the *Publish to GitHub* card, enter your repo / branch / file path, paste your token, then click **Publish & make QR**.
   - **Option 2 (manual):** upload the exported `.ics` to your repo (drag it in via **Add file → Upload files**, keep the same filename, **Commit**), then paste the file's link into the *Paste a public link* card and click **Generate QR**.
5. **Download PNG** or **Print** the QR and share it (slide, email, poster, handout).

Because the repo, branch and filename don't change, the URL and QR stay identical — re-publishing just replaces the file behind the same QR.

---

## What the adviser does

1. Scan the QR with their phone camera.
2. Tap the link that appears → the `.ics` downloads.
3. Tap the downloaded file → their phone offers to add the events. To land in **Outlook** specifically, open the file with the Outlook app (set it as the default handler, or choose it from the share sheet).

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
