# The Long Game — Live Room: running it on company infrastructure

This folder lets you run the whole live audience game **inside the company**,
with nothing going to Google/Firebase or a public website. It's a plain-English
guide: the first part is for you, the second part is the ask for IT.

---

## The situation in one picture

The live game has two halves:

1. **The game page** (`long-term-game-live.html`) — what the big screen and the
   phones open in a browser.
2. **A tiny "switchboard"** that passes votes from the phones to the big screen
   in real time.

Right now the demo uses Google Firebase as that switchboard, and the page is
hosted on a public web address. **To bring it in-house, we swap the switchboard
for the small program in this folder (`server.js`) and run everything on a
company computer.** No other changes — the game plays identically.

---

## What you (non-technical) actually need to do

**Step 1 — Prove it to yourself first (15 minutes, your own laptop).**
You don't need IT, and you don't edit any files. On any Mac/Windows laptop:

1. Install **Node.js** (the free "LTS" version from nodejs.org — a normal installer).
2. Download this project (on GitHub: green **Code** button → **Download ZIP**),
   and unzip it.
3. Open a terminal **in the unzipped folder** and run:
   `node live-server/server.js`
   It prints a line like `…relay on http://localhost:8877/`.
4. Open `http://localhost:8877/?live=host` in your browser — that's the big
   screen; it shows a room code. Open `http://localhost:8877/?room=CODE`
   (using that code) in a second window — that's a "phone." Vote on the phone,
   press reveal on the big screen: it all runs on your machine, nothing online.

That's it — no file editing. When this server hands out the game page it
automatically switches it to "talk to me" mode, so the same game file works
against Firebase (on the public site) or against this local server, untouched.
If it works on your laptop (it does — tested end to end), you've proven the
whole thing runs self-contained. Now it just needs a company home.

**Step 2 — Get the two approvals that actually gate this.** These matter more
than the tech:
- **Compliance / brand review.** It's Capital Group-branded and uses market
  data that's marked "verify before external use." Get sign-off before any
  real audience sees it. *(This is the real long pole — start it early.)*
- **A home to run it on.** That's an IT request (Step 3).

**Step 3 — Send IT the ask below.** Your job here is just to forward it and say
"we'd like to run this small internal web app for a live event." You don't need
to understand the wiring — they will.

**Step 4 — On event day.** Whoever hosts opens the big-screen link IT gives you,
puts the QR code on the projector, and the audience scans it. Everyone must be
on the **company network or VPN** to reach an internal address — for an internal
event that's usually fine (and is actually a security plus).

---

## The ask for IT (forward this part)

> We'd like to host a small, self-contained internal web app for a live event.
> It's a single Node.js file with **zero third-party dependencies** (`server.js`,
> Node 18+) that serves one static HTML page and a lightweight real-time API
> (REST + Server-Sent Events) from one port. State is in-memory and ephemeral
> (throwaway "room" data, auto-expired) — no database, no external calls, no
> auth system, no PII beyond self-chosen nicknames.
>
> **What we need:**
> - Somewhere to run it reachable by attendees' phones on corp network/VPN
>   (a small VM, an internal container/app host, or even a shared workstation
>   for a one-off).
> - It listens on `PORT` (default 8877; set the `PORT` env var to change).
> - **HTTPS via your standard reverse proxy** (nginx/ALB/etc.) in front of it.
>   One caveat: the real-time stream needs response buffering **off** for this
>   route (in nginx that's `proxy_buffering off;`). Idle connections are kept
>   alive with a ping every 25s.
> - Put `long-term-game-live.html` next to `server.js` (or point the
>   `STATIC_DIR` env var at wherever it lives).
>
> **To run:** `node server.js` — it prints its URL. That's it.
>
> Notes: it already handles CORS, path-traversal protection on static files,
> request-size and room-count limits, and idle-room cleanup (6h TTL). It's a
> demo/event tool, not a hardened public service — please keep it internal
> (network/VPN reachable only), which is what we want anyway.

---

## Running it on a company laptop (no cloud at all)

Recorded reality (Jul 2026): **Firebase and Azure are blocked / un-set-up-able
from the company machine.** That's fine — the relay in this folder needs
neither. The whole game can run from the company laptop itself. Two engines,
pick whichever the laptop allows:

| | Node.js edition (`server.js`) | Python edition (`server.py`) | PowerShell edition (`server.ps1` + `relay.cs`) |
|---|---|---|---|
| Run with | `node live-server/server.js` | `python3 live-server/server.py` (Windows: `py live-server\server.py`) | double-click **`start-live.bat`** |
| Needs installed | Node 18+ | Python 3.8+ | **NOTHING** — uses what ships with every Windows |
| Extra packages | none | none (stdlib only) | none (compiled on the spot by Windows' built-in compiler) |

All three serve the game and the live API identically, and all three
**auto-switch any page they serve into "talk to me" mode** — you never edit
the HTML. Confirmed reality (Jul 2026): the company laptop has **no Node and
no Python** → the **PowerShell edition is the one for it.** The kit is four
files in one folder: `long-term-game-live.html`, `server.ps1`, `relay.cs`,
`start-live.bat`. Double-click the .bat; a black window stays open (that's
the server); it prints the big-screen link.

PowerShell-edition specifics:
- If it reports **LOCALHOST-ONLY mode**, Windows needs one-time permission to
  accept connections from other devices: run PowerShell **as administrator**
  once, or have an admin run
  `netsh http add urlacl url=http://+:8877/ user=Everyone`. Until then it
  still works fully in two browser windows on the laptop itself.
- If it refuses with a **Constrained Language Mode** message, the laptop is
  locked beyond what any script can do — use the phone-hotspot +
  personal-laptop setup below.

**Company-laptop gotchas, in the order you'll hit them:**
1. **Firewall prompt** — first run, allow "node"/"python" to accept incoming
   connections, or phones can't reach you. If policy silently blocks inbound
   with no prompt, you'll see it as "works in a second browser window on the
   laptop, but not from any phone."
2. **Corporate WiFi client isolation** — many corp/guest WiFis deliberately
   stop devices talking to each other. Same symptom as the firewall. Test with
   one phone before the event.
3. **The reliable fallback: a phone hotspot.** Presenter's phone becomes the
   WiFi: laptop + audience phones all join the hotspot, laptop runs the relay,
   QR points at the laptop's hotspot address. No corporate network involved at
   all — this sidesteps every block above. (Hotspots cap at ~10 devices, so
   for big rooms you need the venue WiFi or IT hosting instead.)
4. **Use the laptop's network address, not localhost**, when you open the host
   screen (e.g. `http://192.168.x.x:8877/?live=host`) — the QR copies whatever
   address the page was opened on.

The game now also **fails loudly** on blocked networks: if the page can't
reach its live service within 8 seconds, the host/join screens show a clear
message (with these workarounds) instead of hanging on "Joining…".

## Reference: the server's knobs

| Setting | Env var | Default | Meaning |
|---|---|---|---|
| Port | `PORT` | `8877` | Which port to listen on |
| Game files location | `STATIC_DIR` | folder above `server.js` | Where `long-term-game-live.html` lives |
| Room expiry | `ROOM_TTL_MS` | 6 hours | Idle rooms are purged after this |

And the one change inside the game file: `const LIVE_BACKEND = { databaseURL: "auto" };`
— `"auto"` means "use whatever server delivered this page," i.e. this one.

---

## Which "how internal" level are you choosing?

| Level | Game page | Live switchboard | What leaves the company |
|---|---|---|---|
| Today's demo | Public web (GitHub Pages) | Google Firebase | Page + vote data |
| Halfway | Internal host | Google Firebase | Just the vote data |
| **Fully internal (this folder)** | **Internal host** | **`server.js` on same host** | **Nothing** |

The bottom row is what to pitch to IT — the ask is deliberately tiny.

## ⚠️ One reality check before choosing: what network are the phones on?

A server that lives only on the company network can only be reached by phones
**on that network** (venue/corp WiFi or VPN). A phone on **cellular data cannot
reach an internal address at all** — private addresses don't exist outside the
building.

**Current decision (Jul 2026): event audiences are expected on mixed/cellular
networks → the live room needs a publicly reachable address.** That means
either (a) today's Firebase + static-host setup, or (b) this relay hosted by IT
*with a public front door* (their reverse proxy exposed to the internet — a
bigger security conversation, since it's then internet-facing). The fully
internal row of the table above is the right choice only for events where
everyone joins the venue/company WiFi.
