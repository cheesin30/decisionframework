# QR setup guide

Each LTI workshop session gets one QR on the closing slide. Scanning it opens the
Form with **Firm** and **Workshop Date** already pre-filled, so the adviser only
types name and email. This guide covers building the URL into a QR and walks
through three worked examples.

Build the pre-fill URL first using [`../form/prefill-url-guide.md`](../form/prefill-url-guide.md);
this guide assumes you have that URL ready.

> ⚠️ **Use the long pre-fill URL, not the short `/r/` share link.** The QR must
> encode the full `…/Pages/ResponsePage.aspx?id=…&r…=DBS&r…=2026-06-30` link that
> Forms generates from **Get a link to pre-fill answers**. A QR made from the
> short `forms.office.com/r/<code>` link (even with parameters appended) opens
> the Form **blank** — the parameters are ignored. Always open your pre-fill URL
> in a browser and confirm it pre-fills *before* turning it into a QR.

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

For each, start from the long pre-fill link Forms generated for you (base
`…/Pages/ResponsePage.aspx?id=<LONG_FORM_ID>` with your two `r<fieldId>=`
parameters), copy the **Firm segment** (before `_LTI_Follow_Up_`) and the **date
segment** straight off the filename into the two values, then make the QR. Below,
`r<FirmId>` / `r<DateId>` stand for your real parameter names.

### Example 1 — DBS, 30 June 2026

- Filename: `DBS_LTI_Follow_Up_2026-06-30.ics`
- Firm = `DBS`, Date = `2026-06-30`
- Pre-fill URL:
  ```
  https://forms.office.com/Pages/ResponsePage.aspx?id=<LONG_FORM_ID>&r<FirmId>=DBS&r<DateId>=2026-06-30
  ```
- QR (URL-encode the whole pre-fill URL into `data=`):
  ```
  https://api.qrserver.com/v1/create-qr-code/?size=600x600&data=https%3A%2F%2Fforms.office.com%2FPages%2FResponsePage.aspx%3Fid%3D<LONG_FORM_ID>%26r<FirmId>%3DDBS%26r<DateId>%3D2026-06-30
  ```

### Example 2 — AIA, 15 July 2026

- Filename: `AIA_LTI_Follow_Up_2026-07-15.ics`
- Firm = `AIA`, Date = `2026-07-15`
- Pre-fill URL:
  ```
  https://forms.office.com/Pages/ResponsePage.aspx?id=<LONG_FORM_ID>&r<FirmId>=AIA&r<DateId>=2026-07-15
  ```

### Example 3 — HSBC, 22 July 2026

- Filename: `HSBC_LTI_Follow_Up_2026-07-22.ics`
- Firm = `HSBC`, Date = `2026-07-22`
- Pre-fill URL:
  ```
  https://forms.office.com/Pages/ResponsePage.aspx?id=<LONG_FORM_ID>&r<FirmId>=HSBC&r<DateId>=2026-07-22
  ```

> If a firm name in the calendar tool was longer — say `DBS Private Bank`, which
> the tool slugs to `DBS_Private_Bank` — the Firm value in the URL is
> `DBS_Private_Bank` (URL-encoded, the underscores are safe as-is). Always copy
> from the actual filename; see `../form/prefill-url-guide.md`.

`<LONG_FORM_ID>`, `r<FirmId>` and `r<DateId>` all come straight from the pre-fill
link Forms generated (section 2 of the pre-fill guide) — don't hand-build them,
and don't substitute the short `/r/` share link.
