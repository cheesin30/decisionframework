# QR setup guide

Each LTI workshop session gets one QR on the closing slide. Scanning it opens the
Form with **Firm** and **Workshop Date** already pre-filled, so the adviser only
types name and email. This guide covers building the URL into a QR and walks
through three worked examples.

Build the pre-fill URL first using [`../form/prefill-url-guide.md`](../form/prefill-url-guide.md);
this guide assumes you have that URL ready.

---

## 1. From URL to QR

You need a QR that encodes the **exact** pre-fill URL (including the Firm and
Date parameters). Two easy, no-install options:

**Option A — qrserver.com (api.qrserver.com)**
1. Take your full pre-fill URL and URL-encode it.
2. Request:
   ```
   https://api.qrserver.com/v1/create-qr-code/?size=600x600&data=<your-url-encoded-prefill-URL>
   ```
3. Save the returned PNG.

**Option B — Microsoft Edge's built-in generator**
1. Open the pre-fill URL in Edge.
2. Confirm the **Firm** and **Workshop Date** fields show the correct pre-filled
   values.
3. Right-click the page → **Create QR Code for this page** → **Download**.

Either way: **scan your own QR with a phone before the workshop** and check the
Form opens with the right Firm and Date pre-filled.

---

## 2. Format recommendation

- Put a **large QR on the closing PowerPoint slide** — at least ~5 cm / 2 in on
  screen so the back row can scan it. The 600×600 PNG above prints and projects
  cleanly.
- Add a one-line caption: *"Scan to get your LTI follow-up pack."*
- Keep the QR on screen for a minute or two while advisers scan.

---

## 3. One unique QR per firm-per-session

Both the Firm **and** the Date are baked into the URL, so **every
firm-per-workshop session needs its own QR.** Generate a fresh QR for each
session; never reuse a previous firm's or previous date's QR. If you're not
certain a QR is the right one, regenerate it from the filename.

---

## 4. Worked examples

Assume the existing calendar tool has produced these three files in
`/Capital Learning Hub/LTI/Generated ICS/`:

```
DBS_LTI_Follow_Up_2026-06-30.ics
AIA_LTI_Follow_Up_2026-07-15.ics
HSBC_LTI_Follow_Up_2026-07-22.ics
```

For each, copy the **Firm segment** (before `_LTI_Follow_Up_`) and the **date
segment** straight off the filename into the URL, then make the QR.

### Example 1 — DBS, 30 June 2026

- Filename: `DBS_LTI_Follow_Up_2026-06-30.ics`
- Firm = `DBS`, Date = `2026-06-30`
- Pre-fill URL:
  ```
  https://forms.office.com/r/[FormID]?[FirmFieldId]=DBS&[DateFieldId]=2026-06-30
  ```
- QR:
  ```
  https://api.qrserver.com/v1/create-qr-code/?size=600x600&data=https%3A%2F%2Fforms.office.com%2Fr%2F[FormID]%3F[FirmFieldId]%3DDBS%26[DateFieldId]%3D2026-06-30
  ```

### Example 2 — AIA, 15 July 2026

- Filename: `AIA_LTI_Follow_Up_2026-07-15.ics`
- Firm = `AIA`, Date = `2026-07-15`
- Pre-fill URL:
  ```
  https://forms.office.com/r/[FormID]?[FirmFieldId]=AIA&[DateFieldId]=2026-07-15
  ```

### Example 3 — HSBC, 22 July 2026

- Filename: `HSBC_LTI_Follow_Up_2026-07-22.ics`
- Firm = `HSBC`, Date = `2026-07-22`
- Pre-fill URL:
  ```
  https://forms.office.com/r/[FormID]?[FirmFieldId]=HSBC&[DateFieldId]=2026-07-22
  ```

> If a firm name in the calendar tool was longer — say `DBS Private Bank`, which
> the tool slugs to `DBS_Private_Bank` — the Firm value in the URL is
> `DBS_Private_Bank` (URL-encoded, the underscores are safe as-is). Always copy
> from the actual filename; see `../form/prefill-url-guide.md`.

Replace `[FormID]`, `[FirmFieldId]` and `[DateFieldId]` with your real values
(from the pre-fill guide) before generating any QR.
