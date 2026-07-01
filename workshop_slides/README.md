# Long-term Investing — Pre-Workshop Gut Check

An interactive, on-brand replacement for the Microsoft Forms *Pre-Workshop
Diagnostic*. Same diagnostic signal, zero "chore" feeling: advisors **tap to
vote** and watch the room's results build live, all mapped onto the workshop's
**four-box conversation framework** (Acknowledge · Perspective · Confidence ·
Opportunity).

## How to run

Just open `index.html` in any modern browser — it's a single, self-contained
file with **no build step and no internet required** (fonts fall back to system
fonts offline).

- **Navigate:** `←` / `→` arrow keys, or the on-screen ‹ › buttons.
- **Vote:** tap any answer card / confidence level.
- **Reveal results:** the *Show the room* button animates the live bars, crowns
  the most-picked answer 👑, and surfaces a one-line coaching insight.
- **Reset between sessions:** the *↺ Reset votes* button (bottom-right) clears
  all tallies.

Votes are stored locally in the browser (`localStorage`) — nothing leaves the
device and nothing is tied to a name. Run it on one facilitator screen with a
show-of-hands, or let each advisor open it on their own device.

## The 7 slides

| # | Slide | Survey question it replaces |
|---|-------|-----------------------------|
| 1 | Cover — "The 2-minute gut check" | Welcome / intro |
| 2 | How it works | Instructions |
| 3 | **Q1** What lines do you actually hear? *(multi-select)* | "What do clients say when they hesitate?" |
| 4 | **Q2** Your first move *(single)* | "What do you usually do first?" |
| 5 | **Q3** Where does it stall? *(single)* | "Where do you get stuck?" |
| 6 | **Q4** Confidence check *(3 dials + temperature)* | Self-rating scale |
| 7 | Payoff — you just built today's agenda | Bridge into the workshop |

## Editing

Everything lives in `index.html`. Answer options are plain HTML inside each
`.options` / `.dials` block; brand colours are CSS variables at the top
(`--navy`, `--blue`, `--bright`, `--teal`, `--magenta`).
