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
You don't need IT to see it work. On any Mac/Windows laptop:

1. Install **Node.js** (the free "LTS" version from nodejs.org — a normal installer).
2. Put `server.js` and `long-term-game-live.html` in the same folder.
3. In that file, change one line near the top of the live-room script from
   `databaseURL: "https://…firebasedatabase.app"` to `databaseURL: "auto"`.
4. Open a terminal in that folder and run: `node server.js`
5. Open `http://localhost:8877/?live=host` in your browser — that's the big
   screen. Open `http://localhost:8877/?room=CODE` (using the code it shows) in
   another window — that's a "phone." It all runs on your machine, nothing online.

If that works on your laptop (it does — it's been tested end-to-end), you've
proven the whole thing runs self-contained. Now it just needs a company home.

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
