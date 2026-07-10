# cogatrice wire protocol

JSON text frames over WebSocket. Two routes, served by the game container on `COGAME_HOST:COGAME_PORT`:

- `/player?slot=<0|1>&token=<token>` — one connection per seat. Slot and token must match the episode config;
  a second connection for the same slot replaces the first (the old socket is closed).
- `/global` — read-only public-information stream, any number of connections.

All enum-ish payloads use `snake_case` tagged objects, exactly as produced by `tabletop-core`'s serde derives.
`Action`, `Event`, `Expectation`, `Snapshot`, `CardRef` etc. below refer to those shapes (see
`crates/tabletop-core`; docs/specs/tabletop-core-m1.md is the semantic reference).

## Server → player messages

```jsonc
{"type": "hello",
 "slot": 0,
 "seat_name": "goldfish-0",
 "match": {"games_to_win": 2, "game_number": 1, "wins": [0, 0]},
 "config": { /* public episode config: starting_life, turn_cap, clock_s, decision_cap_s, ... */ },
 "decklist": { /* your own DeckList, card specs included */ }}

{"type": "snapshot", "game_number": 1, "state": { /* Snapshot redacted to your seat */ }}

{"type": "events", "game_number": 1, "events": [ /* LoggedEvent[] redacted to your seat */ ]}

{"type": "window",                       // sent whenever it becomes YOUR turn to act
 "game_number": 1,
 "expectation": { /* Expectation */ },
 "clock_ms_remaining": 312000,           // your chess clock for this game
 "decision_cap_ms": 30000}               // per-decision cap; exceeding it auto-passes/auto-keeps

{"type": "ack",    "cmd_id": 17, "seq": 142}            // action accepted; seq of its first event
{"type": "reject", "cmd_id": 17, "error": {"kind": "not_your_window", "detail": "..."}}

{"type": "game_end",  "game_number": 1, "outcome": { /* GameOutcome */ }, "wins": [1, 0]}
{"type": "match_end", "scores": [2.0, 1.0], "games": [ /* per-game outcome summaries */ ]}
```

Notes:
- On connect (and reconnect) the server sends `hello`, then `snapshot`, then resumes `events` deltas. A player can
  always act correctly from the latest `snapshot` + subsequent `events` — no replaying of missed deltas is needed.
- `events` frames are also how you observe the opponent. Every accepted action (yours and theirs) appears exactly
  once, in `seq` order.
- `window` is authoritative for turn-taking: act only after a `window` naming your seat. Acting out of window gets
  a `reject` with `not_your_window` (harmless, but wasteful).
- Timeouts: if your decision cap or game clock expires, the server acts for you (mulligan → keep-with-first-N-cards
  bottomed; reaction window → pass; main window → next_phase/next_turn progression; clock flag → game loss) and
  logs a `Said` event from the server noting the timeout.

## Player → server messages

```jsonc
{"cmd_id": 17, "action": {"type": "draw", "count": 1}}
{"cmd_id": 18, "action": {"type": "move_cards", "moves": [{"card": 12, "to_seat": 0, "to_zone": "battlefield",
                          "position": {"type": "battlefield", "x": 3, "y": 1}, "face_down": null, "tapped": null}]}}
{"cmd_id": 19, "action": {"type": "say", "text": "casting Goblin Raider, 2 mountains tapped"}}
{"cmd_id": 20, "action": {"type": "pass"}}
```

`cmd_id` is a client-chosen number echoed in `ack`/`reject`; use monotonically increasing values. One action per
frame. The full action vocabulary and semantics live in the tabletop-core spec; the wire shape is
`{"cmd_id": n, "action": <Action>}`.

## Server → global messages

Same `hello` (without decklist/slot), `snapshot`/`events` (Global perspective: public information only),
`window` (whose turn, no clocks detail), `game_end`, `match_end`. Global connections send nothing; anything
received is ignored.

## Replay mode

In replay mode (`COGAME_LOAD_REPLAY_URI` set) the server serves `/replay`: on connect it sends the recorded
episode as `{"type": "replay_meta", ...}` followed by the full-perspective (unredacted) event stream in batches
with original relative timing compressed to a fixed playback rate, looping back to the start when it reaches the
end. `/client/replay` renders this stream and autoplays.
