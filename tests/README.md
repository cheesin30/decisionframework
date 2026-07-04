# Regression test for the LTI Engagement Calendar tool

Drives the real `LTI_Engagement_Calendar_QR_v1.html` in headless Chromium and checks the behaviours that have regressed (or nearly regressed) before:

- resource files **restore from IndexedDB after a page reload** (no "Reselect file"), and the `.ics` exports afterwards with the embedded `ATTACH` payload
- the **>3 MB attachment guard** fires on the flow-JSON export and blocks it when dismissed
- the oversized-file **chip** appears on the resource card
- touchpoint summary **pluralisation** ("1 day … 2 resources")
- the **stepper is keyboard-operable** (focus + Enter switches step, `aria-current` set)
- the **printed QR handout** contains the adviser instructions

## Run it

```bash
node tests/regression.spec.cjs
```

Requirements: Node 18+, Playwright (`npm i playwright` or a global install), and a Chromium binary — set `CHROMIUM_PATH` if it isn't at `/opt/pw-browsers/chromium`.

Every line of output should end in `true` / `NONE` (the `dialogs seen` line should show the 3 MB warning). If you change the tool, run this before committing; extend it when you add behaviour worth protecting.
