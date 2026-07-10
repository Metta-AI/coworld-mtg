# Spec: browser table (Milestone M3)

Goal: a human can open `/client/player?slot=0&token=...` and play a real game of Magic against goldfish (or another
human in a second tab), and `/client/global` + `/client/replay` render watchable tables. This is the "basic game of
MTG" milestone.

## Stack and constraints

- `web/` — Vite + TypeScript, **no UI framework** (plain DOM + small render helpers), one shared table renderer
  used by all three pages. CSS custom properties for theming; dark theme default.
- Build output committed? No — `Dockerfile` builds it; for local dev `cargo run` serves `web/dist` if present and
  the placeholders otherwise. Server route wiring: `/client/*` serve built assets (player.html, global.html,
  replay.html + shared js/css).
- Protocol: exactly docs/protocol.md over the page's own WebSocket connection (token/slot from query params).
- No card images (art_id is null for v1 decks): cards render as **text frames** — name, mana cost (styled symbol
  chips), type line, oracle text (clamped), P/T. Face-down/hidden cards render as card backs. This is a feature:
  the table must be fully legible from text alone.

## Layout (player view)

```
┌────────────────────────────────────────────────────────────┐
│ opponent: name ♥18  hand:5  lib:29  grave:3  [clock 4:32]   │
│ ──────────────── opponent battlefield ─────────────────────│
│                (lands row / creatures row)                  │
│═════════════ phase track: U UK D M1 BC A B CD EC M2 E ═════│
│                 (your battlefield rows)                     │
│ ──────────────────────────────────────────────────────────│
│ you: name ♥20  lib:31  grave:0   [clock 5:10]  [WINDOW: ●] │
│ [your hand — fanned text cards]                             │
│ [action bar: Draw | Untap all | Next phase | Next turn |    │
│  Pass | Concede]     [log / chat pane on the right side]    │
└────────────────────────────────────────────────────────────┘
```

- **Window indicator** is the loudest signal on screen: a colored banner ("Your window — main phase" / "Opponent
  acting…" / "Reaction window: respond or pass"). When it is not your window, action controls are disabled but
  the table stays fully inspectable.
- **Phase track**: 11 phases as a horizontal strip, active phase lit, turn number + active player shown beside it.
- **Log/chat pane**: every event rendered as a one-line human sentence ("goldfish-0 casts Goblin Raider",
  "you tap 2 Mountains", "die roll: 5"), `say` messages styled as chat; input box sends `say`. This doubles as
  the rules-of-engagement surface — table talk is how MTG is narrated.

## Interactions (click-first, minimal modes)

- Click a hand card → popover: **Play to battlefield** (face up/down), **Discard**, **Reveal**, **To library
  top/bottom**. Playing lands/creatures = Play to battlefield.
- Click own battlefield card → popover: **Tap/Untap**, **Attack on/off** (only lit during DeclareAttackers),
  **Add/remove counter** (+1/+1 default, custom name via small input), **To graveyard / exile / hand**, **Point
  at…** (then click target; draws arrow), **Annotation…**.
- Click opponent battlefield card → popover: **Point at…** only.
- Life: ± steppers next to each life total (own only).
- Library: buttons on the deck stub — **Draw 1**, **Mill 1** (MoveTopOfLibrary→graveyard), **Shuffle**.
- Mulligan window: modal showing the hand with **Keep** / **Mulligan**; when keeping after N mulligans, the modal
  requires selecting exactly N cards to bottom (click to toggle), order = selection order.
- Battlefield placement: new cards auto-place (lands front row, others back row, next free x). Drag to reposition
  is a stretch goal — click-to-place-next-free is acceptable for M3.
- Every interaction = exactly one protocol action with optimistic disable-until-ack; `reject` shows a toast with
  the error detail.

## Global and replay views

- `global.html`: same table, no hand pane, no action bar, both clocks visible, log pane full height.
- `replay.html`: global layout + a playback bar (play/pause, speed 1×/2×/4×, seek by game). Autoplays on load and
  loops (contract requirement). Data source is the `/replay` stream; seeking = re-render from batched events
  (client buffers everything it has received; the stream loops anyway).

## Quality bar

This is user-facing (taste ≥ 7 per repo owner's standards): consistent spacing scale, one accent color for "your
window", tabular numerals for life/clocks, no layout shift as events stream in, readable at 13" laptop width.
Empty states ("waiting for opponent…", "connecting…") for every pane. No spinners longer than 300ms without text.

## Acceptance

- Manual: human vs goldfish full game in the browser start (mulligan) → finish (game_end shown with outcome),
  using only the UI. Two-tab human vs human also works.
- Automated (light): vitest unit tests for the event→log-sentence renderer and the snapshot→table-model mapper;
  Playwright smoke test: page connects to a live local server, mulligan modal appears, keep resolves, a land can
  be played, phase advances — against a goldfish opponent (reuse the M2 harness).
