# Pre-fill URL guide

Each LTI workshop session gets **one unique QR**. The QR points at the Form with
the **Firm** and **Workshop Date** already baked in as URL parameters, so the
adviser only ever types their name and email. This guide shows how to build that
URL and, critically, how to make the baked-in `Firm`/`Date` match the
pre-generated `.ics` filename exactly.

---

## 1. The shape of the URL

A Microsoft Forms pre-fill URL looks like this:

```
https://forms.office.com/r/[FormID]?[FirmFieldId]=DBS&[DateFieldId]=2026-06-30
```

- `[FormID]` — the short id from your form's **Share** link.
- `[FirmFieldId]` and `[DateFieldId]` — the **internal field IDs** of the *Firm*
  and *Workshop Date* questions (they look like `r1a2b3c4...`, **not** the
  words "Firm"/"Date"). The next section shows how to get the real ones.
- The values after `=` are what gets pre-filled. **URL-encode** anything with
  spaces or symbols (a space becomes `%20`).

> Example placeholder form (do not ship this literally — get your real IDs
> first):
> ```
> https://forms.office.com/r/[FormID]?[FirmParam]=DBS&[DateParam]=2026-06-30
> ```

---

## 2. Get the real field IDs (do this once)

Microsoft generates the field IDs for you — don't guess them:

1. Open the Form → **Collect responses** (or **Share**) → **Get a link to
   pre-fill answers** (under the **…** / more menu, depending on the Forms
   version).
2. In the preview that opens, type a throwaway value into **Firm** (e.g. `DBS`)
   and into **Workshop Date** (e.g. `2026-06-30`). Leave Name/Email blank.
3. Click **Get pre-filled link** and copy it.
4. The copied URL already contains the correct field IDs, e.g.:
   ```
   https://forms.office.com/r/abc123XYZ?r3f4...=DBS&r9k8...=2026-06-30
   ```
   The token before `=DBS` is your **Firm** field ID; the one before
   `=2026-06-30` is your **Workshop Date** field ID.
5. Record both IDs in the mapping table in
   [`form-spec.md`](./form-spec.md#question--dynamic-content-mapping). You now
   reuse the same URL skeleton for every session, swapping only the two values.

---

## 3. Making `Firm` and `Date` match the `.ics` filename — the part that matters

The whole system hinges on the QR baking in values that reproduce the **exact**
filename the calendar tool wrote:

```
{Firm}_LTI_Follow_Up_{yyyy-MM-dd}.ics
```

Because the calendar tool **slugifies** the firm name you typed into it (every
run of non-alphanumeric characters → a single `_`, leading/trailing `_`
stripped), the `Firm` in your URL is **not necessarily a tidy short code**:

| What was typed into the calendar tool | Firm segment in the filename | Put this in the URL (URL-encoded) |
| --- | --- | --- |
| `DBS` | `DBS` | `DBS` |
| `AIA` | `AIA` | `AIA` |
| `HSBC` | `HSBC` | `HSBC` |
| `DBS Private Bank` | `DBS_Private_Bank` | `DBS_Private_Bank` |
| `AIA Singapore` | `AIA_Singapore` | `AIA_Singapore` |

> **Golden rule:** open the `.ics` the calendar tool produced and **copy the
> firm segment (everything before `_LTI_Follow_Up_`) verbatim** into the URL's
> Firm value. Copy the date segment verbatim too. Don't retype from memory and
> don't "clean it up" — `Firm` is **case-sensitive** (`DBS` ≠ `dbs`) and the
> date must be `yyyy-MM-dd` with hyphens.

The date value is always the literal `yyyy-MM-dd` (e.g. `2026-06-30`) — never
`30-06-2026`, never `2026/06/30`.

---

## 4. Build a session URL — step by step

For a DBS workshop completed on **30 June 2026**, where the calendar tool
produced `DBS_LTI_Follow_Up_2026-06-30.ics`:

1. Start from your real skeleton (IDs from step 2):
   ```
   https://forms.office.com/r/abc123XYZ?r3f4...=&r9k8...=
   ```
2. Set the Firm value to the firm segment copied from the filename → `DBS`.
3. Set the Date value to the date segment copied from the filename → `2026-06-30`.
4. Final URL:
   ```
   https://forms.office.com/r/abc123XYZ?r3f4...=DBS&r9k8...=2026-06-30
   ```
5. Open it once yourself to confirm the **Firm** and **Workshop Date** fields
   show the right pre-filled values before you turn it into a QR.

Then generate the QR from this URL — see [`../qr/qr-setup.md`](../qr/qr-setup.md).

---

## 5. One QR per firm-per-session

Because **both** Firm and Date are baked into the URL, **every firm-per-workshop
session needs its own QR.** Reusing yesterday's DBS QR for today's AIA session
would email the wrong (or a non-existent) file. When in doubt, regenerate.
