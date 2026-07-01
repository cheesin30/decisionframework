# Host the LTI landing page on Azure Static Web Apps

This folder is a **drop-in** for hosting the QR landing page on your own Azure tenant — the Microsoft-native way to get the *scan-a-QR → page → Add to calendar + resources* experience, without GitHub or a SharePoint anonymous link.

It contains one file you keep (`staticwebapp.config.json`) plus the page you generate from the tool (`index.html`).

---

## What you deploy

```
azure-static-web-app/
├─ staticwebapp.config.json   ← keep (sets text/calendar MIME, routing)
└─ index.html                 ← the landing page you export from the tool
```

The `staticwebapp.config.json` sets the **`.ics` content type to `text/calendar`** — important so "Add the calendar" opens the calendar app cleanly (especially on iOS), if you use the separate-`.ics` variant below.

---

## Steps

### 1. Generate the page
In `LTI_Engagement_Calendar_QR_v1.html`: **Share & QR → Download landing page (.html)**. Rename the downloaded file to **`index.html`** and put it in this folder, next to `staticwebapp.config.json`.

### 2. Create the Static Web App (no public GitHub needed)
Your policy rules out public GitHub — so do **not** use the GitHub-integration deploy. Use one of these instead:

- **SWA CLI, standalone deploy (simplest, no repo):**
  ```bash
  # one-time: create an empty Static Web App in the Azure Portal (Deployment source = "Other")
  # copy its deployment token from Portal → your SWA → Manage deployment token
  npx @azure/static-web-apps-cli deploy ./azure-static-web-app \
    --deployment-token <DEPLOYMENT_TOKEN> \
    --env production
  ```
- **Azure DevOps pipeline** (if you host code in private Azure Repos): use the `AzureStaticWebApp@0` task pointing `app_location` at this folder.
- **VS Code** with the *Azure Static Web Apps* extension → right-click → Deploy.

### 3. Get the URL and make the QR
Your site is at `https://<name>.azurestaticapps.net` (add a custom domain in the Portal if you want, e.g. `lti.yourfirm.com`). Back in the tool, paste that URL into **Signed link to the hosted page** → **Generate QR** → **Print**. Because the URL is stable, you print the QR once and reuse it each cohort — just redeploy a new `index.html`.

---

## Access control (pick one)

- **Public** (default here): anyone with the link/QR can open it. Fine for LTI material cleared for external sharing.
- **Gated with email one-time-passcode** (no corporate account needed for advisers): turn on **Microsoft Entra External ID (B2C)** and protect the route. Replace the `routes` block with:
  ```json
  "routes": [
    { "route": "/", "rewrite": "/index.html", "allowedRoles": ["authenticated"] }
  ],
  "responseOverrides": { "401": { "redirect": "/.auth/login/aadb2c", "statusCode": 302 } }
  ```
  This gives the privacy middle-ground SharePoint couldn't: not publicly open, yet usable by external advisers via an email code.

---

## Reliable-iOS variant (optional)

The exported landing page embeds the `.ics` as a `data:` URI, which works on most phones. For the most reliable "Add to calendar" on **all** iOS devices, host the `.ics` as a **separate file** instead:

1. In the tool, also use **Download the .ics only** and save it here as `followup.ics`.
2. Change the page's "Add the calendar" link to point at `/followup.ics` instead of the `data:` URI.
3. Deploy both files. Azure serves `followup.ics` as `text/calendar` (via this config), so tapping it opens the calendar import directly.

> Ask and I can add a one-click "Azure bundle" export to the tool that emits `index.html` (linking to `followup.ics`) + `followup.ics` together, so you skip the manual edit.

---

## Why this fits the privacy constraints

- Runs in **your own Azure tenant** — sanctioned infrastructure, auditable, with DLP/retention — not a third-party public repo.
- You choose **public or email-gated** access per content sensitivity.
- Free tier covers custom domain + SSL; low cost for this scale.
