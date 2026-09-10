# Form build sheet — copy-paste provisioning

Microsoft Forms has **no import/package format** — a form can't be deployed from
a file the way the Power Automate package can. The next best thing is this build
sheet: every piece of text is a ready-to-paste block in build order, so creating
the form is a couple of minutes of copy/paste rather than authoring from scratch.

For the *why* behind each choice, see [`form-spec.md`](./form-spec.md). This sheet
is the *do-this-now* version.

> Build at **forms.office.com** → **New Form**. Work top to bottom.

---

## 0. Settings (gear icon → Settings)

- [ ] **Who can fill out this form:** **Anyone can respond** *(required — advisers
      are external)*
- [ ] **Record name:** **Off**
- [ ] **One response per person:** **Off**
- [ ] **Accept responses:** **On**
- [ ] **Customised thank you message:** **On** (paste the text in section 6)

---

## 1. Title

Paste into the form title:

```
LTI Workshop Follow-up
```

## 2. Description

Paste into the form description (under the title):

```
Thanks for joining today's Long-Term Investing workshop. Pop your details in below and your follow-up calendar pack will be on its way.
```

---

## 3. Question 1 — Your Name  *(visible)*

- **+ Add new** → **Text**
- **Title** (paste):
  ```
  Your Name
  ```
- **Subtitle** (… → Subtitle, paste):
  ```
  First and last name.
  ```
- **Required:** On · **Long answer:** Off

## 4. Question 2 — Your Email  *(visible)*

- **+ Add new** → **Text**
- **Title** (paste):
  ```
  Your Email
  ```
- **Subtitle** (paste):
  ```
  We'll send your follow-up pack here.
  ```
- **Required:** On
- **Restrictions** (… → Restrictions): choose **Text**, then set it to **must
  contain** and paste:
  ```
  @
  ```

## 5. Question 3 — Firm  *(hidden / pre-filled)*

- **+ Add new** → **Text**
- **Title** (paste):
  ```
  Firm
  ```
- **Subtitle** (paste):
  ```
  Pre-filled from QR — please don't change.
  ```
- **Required:** On

## 6. Question 4 — Workshop Date  *(hidden / pre-filled)*

- **+ Add new** → **Text**  *(deliberately **Text**, not a Date question — it
  carries the literal `yyyy-MM-dd` string with no timezone parsing)*
- **Title** (paste):
  ```
  Workshop Date
  ```
- **Subtitle** (paste):
  ```
  Pre-filled from QR — please don't change.
  ```
- **Required:** On

> Keep Firm and Workshop Date **last** so the adviser's attention lands on
> Name/Email first. They stay editable on screen (Forms has no true "hidden"
> field) but are always pre-filled by the QR and labelled not to touch.

---

## 7. Custom thank-you message

Settings → **Customised thank you message** → paste:

```
You're all set. Your LTI follow-up pack is on its way — check your inbox in the next minute or so for a calendar file to add to your phone or Outlook. If it hasn't arrived, check your junk/spam folder.
```

---

## 8. Immediately after building — capture the field IDs

Do this once; you reuse it for every QR and for wiring Flow A:

1. **Collect responses / Share** → **Get a link to pre-fill answers**.
2. In the preview, type throwaway values into **Firm** (`DBS`) and **Workshop
   Date** (`2026-06-30`); leave Name/Email blank.
3. **Get pre-filled link** → copy it.
4. From that URL, read off:
   - the **Form ID** (the `…/r/<FormID>` segment) → into the flow's trigger and
     *Get response details*,
   - the **Firm** field ID (token before `=DBS`),
   - the **Workshop Date** field ID (token before `=2026-06-30`).
5. Record all of these in the mapping table in
   [`form-spec.md`](./form-spec.md#question--dynamic-content-mapping), then use
   them in [`prefill-url-guide.md`](./prefill-url-guide.md) and the flow.

---

## Build order checklist

- [ ] Settings set (section 0)
- [ ] Title + description
- [ ] Q1 Your Name
- [ ] Q2 Your Email (+ `@` restriction)
- [ ] Q3 Firm
- [ ] Q4 Workshop Date
- [ ] Custom thank-you message
- [ ] Pre-fill link captured → Form ID + 2 field IDs recorded
- [ ] Test pre-fill URL opens with Firm/Date populated
