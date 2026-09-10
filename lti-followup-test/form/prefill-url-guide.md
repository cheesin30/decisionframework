# Pre-fill URL guide

Each LTI workshop session gets **one unique QR**. The QR points at the Form with
the **Firm** and **Workshop Date** already baked in as URL parameters, so the
adviser only ever types their name and email. This guide shows how to build that
URL and, critically, how to make the baked-in `Firm`/`Date` match the
pre-generated `.ics` filename exactly.

---

## 1. The shape of the URL

> ⚠️ **The short share link does NOT pre-fill.** A link like
> `https://forms.office.com/r/AbC123` (from the **Share** button) **ignores any
> parameters you add to it** — Firm and Workshop Date will come up blank. This is
> the #1 reason pre-fill "doesn't work". You must use the **long** link that
> Forms generates from **Get a link to pre-fill answers** (next section).

A working Microsoft Forms pre-fill URL looks like this — note the
`ResponsePage.aspx?id=...` base and the parameters that each start with a
literal `r`:

```
https://forms.office.com/Pages/ResponsePage.aspx?id=<LONG_FORM_ID>&r<FirmFieldId>=DBS&r<DateFieldId>=2026-06-30
```

- `<LONG_FORM_ID>` — the long id in the pre-fill link (a ~90-character string
  ending in `.u` / `.2u`), **not** the short `/r/` code.
- `r<FirmFieldId>` and `r<DateFieldId>` — each answer parameter is the letter
  **`r`** immediately followed by the question's internal field ID
  (e.g. `r8c3f0a1b...=DBS`). You do **not** invent these — Forms writes them into
  the pre-fill link for you.
- The values after `=` are what gets pre-filled. **URL-encode** anything with
  spaces or symbols (a space becomes `%20`).

> Don't hand-build this from scratch. Generate it once (section 2), then only
> swap the two values for each session.

---

## 2. Get the real field IDs (do this once)

Microsoft generates the field IDs for you — don't guess them:

1. Open the Form → **Collect responses** (or **Share**) → **Get a link to
   pre-fill answers** (under the **…** / more menu, depending on the Forms
   version).
2. In the preview that opens, type a throwaway value into **Firm** (e.g. `DBS`)
   and into **Workshop Date** (e.g. `2026-06-30`). Leave Name/Email blank.
3. Click **Get pre-filled link** and copy it. **This whole long URL is your
   template** — keep it intact.
4. The copied URL already contains the correct base and field IDs, e.g.:
   ```
   https://forms.office.com/Pages/ResponsePage.aspx?id=DQSIkWd...AANAAR&r3f4a1b=DBS&r9k8c2d=2026-06-30
   ```
   The `r3f4a1b=DBS` parameter is your **Firm** field (its ID is `3f4a1b`); the
   `r9k8c2d=2026-06-30` parameter is your **Workshop Date** field.
5. **Verify it works:** paste that URL into a browser. The Firm and Workshop Date
   questions should show pre-filled. If they don't, you copied the short `/r/`
   link by mistake — go back and use **Get a link to pre-fill answers**, not
   **Share**.
6. Record both field IDs in the mapping table in
   [`form-spec.md`](./form-spec.md#question--dynamic-content-mapping). You now
   reuse this exact long URL for every session, swapping only the two values.

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

1. Start from the long pre-fill link you generated in section 2:
   ```
   https://forms.office.com/Pages/ResponsePage.aspx?id=DQSIkWd...AANAAR&r3f4a1b=DBS&r9k8c2d=2026-06-30
   ```
2. Set the Firm value (after `r3f4a1b=`) to the firm segment copied from the
   filename → `DBS`.
3. Set the Date value (after `r9k8c2d=`) to the date segment copied from the
   filename → `2026-06-30`.
4. Leave the `id=...` base and the `r`-prefixed parameter names **exactly as
   Forms generated them** — only the values change between sessions.
5. Open the finished URL in a browser to confirm the **Firm** and **Workshop
   Date** fields show the right pre-filled values before you turn it into a QR.

Then generate the QR from this **entire long URL** — see
[`../qr/qr-setup.md`](../qr/qr-setup.md).

---

## 5. One QR per firm-per-session

Because **both** Firm and Date are baked into the URL, **every firm-per-workshop
session needs its own QR.** Reusing yesterday's DBS QR for today's AIA session
would email the wrong (or a non-existent) file. When in doubt, regenerate.
