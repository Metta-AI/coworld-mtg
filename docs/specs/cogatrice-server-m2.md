# Spec: `cogatrice-server` + `goldfish` (Milestone M2)

Two new crates plus deck data. After this milestone: `goldfish` vs `goldfish` completes a full match over real
websockets against the server binary, results and replay artifacts are written per the Coworld game contract, and
replay mode re-serves the recorded episode. Browser HTML is placeholder-only (M3).

References: /PLAN.md §5–§6, /docs/protocol.md (the wire contract — implement it exactly), /docs/specs/tabletop-core-m1.md.

## Workspace additions

```
crates/cogatrice-server/     # binary `cogatrice-server`
crates/players/goldfish/     # binary `goldfish`
decks/red_rush.json
decks/green_stompy.json
```

Workspace deps to add: `axum` (ws feature), `tokio` (full), `tokio-tungstenite`, `futures`, `reqwest`
(rustls-tls, no default features), `tracing` + `tracing-subscriber`, `anyhow`, `clap` (derive). Pin latest stable
majors. Keep `cargo clippy --all-targets -- -D warnings` clean.

## Small tabletop-core additions (do these first, with tests)

1. `EndReason::ClockFlag` and `pub fn Game::flag(&mut self, seat: SeatId)` — ends the game immediately, winner =
   opponent, reason ClockFlag. Legal in any non-GameOver state.
2. `EndReason` gains no other variants. Update props/tests accordingly.

## Episode config (read from `COGAME_CONFIG_URI`)

```jsonc
{
  "tokens": ["tokA", "tokB"],          // runner-injected; required; index = slot
  "players": [{"name": "goldfish-0"}, {"name": "goldfish-1"}],
  "seed": 42,
  "decks": ["red_rush", "green_stompy"],  // per-slot deck ids, resolved from the bundled deck dir
  "games_to_win": 1,                       // match ends when a seat has this many wins (draws count 0.5 to each,
                                           //   match can also end when wins are mathematically settled or after
                                           //   2*games_to_win-1 games)
  "starting_life": 20,
  "turn_cap": 25,
  "clock_s": 360,                          // per-seat per-game chess clock
  "decision_cap_s": 30,                    // per-decision cap
  "player_connect_timeout_s": 60           // seat not connected in time => that seat forfeits the match
}
```

Defaults apply for every field except `tokens` (all fields above shown with defaults). Deck files live in
`decks/*.json` in the repo, embedded into the binary with `include_str!` via a small generated registry (id =
file stem). Deck JSON shape: `{"name": "...", "cards": [{"count": 4, "spec": <CardSpec>}, ...]}` — expand counts
into the flat `DeckList` at load.

`COGAME_*_URI` handling (config read; results/replay/log write): support plain filesystem paths, `file://` URIs,
and `http(s)://` (GET for config, PUT for outputs). One tiny `uri.rs` module, used for all four.

## Server behavior

- Binary starts, loads config, binds `COGAME_HOST:COGAME_PORT` (defaults `0.0.0.0:8080`), serves:
  - `GET /healthz` → 200 `ok` once listening.
  - `GET /client/player`, `GET /client/global`, `GET /client/replay` → placeholder HTML pages (single static
    string each, real UI is M3) — include the query params echoed into a `<pre>` for debugging.
  - `WS /player?slot=&token=` — validate slot ∈ {0,1} and token == config.tokens[slot], else close with policy
    violation. New connection for an occupied slot replaces the old one (close old, snapshot new).
  - `WS /global` — public stream, read-only.
  - `WS /replay` — only in replay mode, see below.
- **Match loop** (normal mode): wait for both players (up to `player_connect_timeout_s`; on timeout the missing
  seat(s) forfeit — if both missing, scores [0,0] and results still written). Then play games sequentially:
  game k (1-based) maps slot→seat so that the seat acting first alternates: in game k, slot ((k-1) % 2) is seat 0.
  Keep a stable slot↔seat mapping per game and translate in both directions at the socket boundary — everything
  wire-facing speaks SLOTS (players never see "seat"), everything core-facing speaks seats. Per game:
  `Game::new(GameSetup { seed: seed + k - 1, ... })`, stream per protocol.md, run until GameOutcome, send
  `game_end`, update wins (win 1, draw 0.5 each), next game or `match_end`.
- **Clocks**: chess clock per slot per game, ticking while that slot holds the open window; per-decision cap on
  top. On decision-cap expiry apply the default action (mulligan → `MulliganKeep` bottoming the first
  `must_bottom` cards of the hand snapshot; reaction → `Pass`; main window → `NextPhase`, or `NextTurn` when
  phase == End). On chess-clock expiry call `Game::flag(seat)`. After any server-applied default, emit the
  regular `events` plus a `window` for whoever is next. Use tokio::select on (socket msg, deadline) — single
  task owning the game state; socket readers forward into an mpsc.
- **Fault tolerance**: a disconnected player's clock keeps running (defaults fire); malformed JSON → `reject`
  with kind `bad_request`; an action from a slot when it isn't the expected seat → normal `reject` (core error
  mapping: serde-name of ActionError kind).
- **Artifacts** on match end (also on panic-free early termination like double forfeit):
  - `results.json` → `COGAME_RESULTS_URI`:
    `{"scores": [f64; 2], "games": [{"game_number", "winner_slot": 0|1|null, "reason", "turns", "final_life": [i32;2], "seed"}], "seed", "policy_names": [..]}`.
  - replay bytes → `COGAME_SAVE_REPLAY_URI`: JSON
    `{"version": 1, "config": <public config, tokens stripped>, "games": [{"game_number", "slot_of_seat0", "events": [{"wall_ms": u64, "event": <LoggedEvent (Full perspective)>}]}], "results": <same as results.json>}`.
  - if `COGAME_LOG_URI` set, PUT a plain-text line-oriented log (tracing output buffer or a simple summary).
  - Exit 0 after artifacts are written. Also write results before exiting on fatal errors if at all possible.
- **Replay mode** (`COGAME_LOAD_REPLAY_URI` set): load replay JSON, do NOT run a match, serve `/client/replay`
  placeholder + `WS /replay`: on connect send `{"type":"replay_meta", "config", "results", "games":[summary]}`
  then loop forever: for each game, `{"type":"events", "game_number", "events":[...]}` in batches paced to a
  fixed rate (e.g. 10 events/sec, `wall_ms` ignored for M2), then a `game_end`-shaped frame, then after the last
  game a `match_end`-shaped frame and restart from the first game. `/global` and `/player` are absent in replay mode.

## Goldfish player

`crates/players/goldfish`: reads `COWORLD_PLAYER_WS_URL` (or `--url` flag for local runs), connects, plays the
whole match, exits 0 after `match_end`. No LLM, no randomness (fully determined by observations). Strategy:

- Mulligan: always `MulliganKeep`, bottoming the first `must_bottom` card ids of its hand (sorted by id asc).
- Track own state from snapshot+events: hand, battlefield, untapped lands, creatures and their
  entered-this-turn flag (summoning sickness), turn/phase, own/opponent life.
- On `window` where expectation is MainWindow(self): run the turn script for the current phase, one action per
  ack, then advance:
  - Untap: untap all own tapped cards (`set_card_attr` tapped=false each), `next_phase`.
  - Upkeep: `next_phase`. Draw: `draw 1` unless (turn == 1 && self is seat 0), `next_phase`.
  - Main1: play one land if any in hand (move to battlefield, `say` "plays <name>"); then greedily cast
    creatures: mana available = count of untapped lands on own battlefield; for each creature in hand with
    mana_value ≤ remaining (mana_value = crude parse of mana_cost: sum of numeric symbols + count of letter
    symbols), tap that many lands (`set_card_attr`), move creature to battlefield, `say` "casts <name>".
    Then `next_phase`.
  - BeginCombat: `next_phase`. DeclareAttackers: set `attacking=true` on every own untapped creature that
    isn't summoning-sick and `say` attack announcement, `next_phase`. DeclareBlockers: `next_phase` (goldfish
    never blocks). CombatDamage: `say` "combat damage: N" where N = total power of own attacking creatures,
    `next_phase`. EndCombat: clear `attacking` on own creatures, `next_phase`. Main2: `next_phase`.
    End: `next_turn`.
- On `window` where expectation is ReactionWindow(self): if the last `PhaseChanged` was to CombatDamage and the
  opponent has attackers, apply own life loss: `add_counter` target self player, name "life", delta = -N
  (N = sum of parsed powers of opponent's attacking creatures), then `pass`. Else just `pass`.
- On `game_end`/`match_end`: reset per-game state / exit.
- Robustness: on `reject`, `say` a one-line note and fall back to `pass`/`next_phase` (never wedge the match).

Mana-value parse: from `mana_cost` like `"{2}{G}"` → 3. `power_toughness` "2/2" → power 2 (`*` → 0).

## Tests (acceptance for M2)

1. `crates/cogatrice-server/tests/episode.rs` — end-to-end: pick a free port, set `COGAME_*` env to temp files
   (config with games_to_win 1, turn_cap 12, short clocks, seed fixed), spawn the server (as a lib call or the
   binary via `assert_cmd`-style spawn — prefer exposing `run()` from a lib target and driving it in-process with
   tokio), connect two goldfish (drive the goldfish logic as a library from the test), assert: healthz 200;
   both `hello`s carry correct slots/decklists; match completes; `results.json` exists, scores sum to 1.0, winner
   consistent with final life; replay file exists and parses; per-seat redaction holds on the wire (a probe
   assertion: slot 0 never receives a Known card ref for a card in slot 1's hand unless revealed).
2. Replay-mode test: start server with `COGAME_LOAD_REPLAY_URI` pointing at the file from test 1 (or a fixture),
   assert `/client/replay` 200 and `/replay` yields `replay_meta` then events, and that after the final
   `match_end` frame the stream restarts (loop observed).
3. Timeout test: config with decision_cap_s ~0.2 and one connected player only (other slot connects but never
   acts... simpler: connect a "mute" client for slot 1); assert the match still terminates via defaults/flag and
   results are written.
4. Goldfish unit tests: mana-value parser, mulligan bottoming, attacker selection with summoning sickness.

Keep tests hermetic (no network beyond loopback, no Docker). Use the two real deck files.

## Decks

Author `decks/red_rush.json` and `decks/green_stompy.json`: 40 cards each, exactly 17 basic lands (Mountain /
Forest), 23 spells. Real, simple Magic cards only — vanilla or single-keyword creatures (haste, trample, reach,
flying), simple burn ("Shock"-style: damage to any target) and pump ("Giant Growth"-style) instants. No
triggered/activated abilities, no card draw, no tutors, no scry. CardSpec fields must be accurate to the real
cards (name, type_line, mana_cost, power_toughness, oracle_text); art_id null for now. Red curve 1–3, green
curve 1–4.

## Implementation decisions

- `docs/protocol.md` preserves the core field names for `Expectation`, `Event`, `Snapshot`, and `Action`, including
  fields named `seat`. The implementation keeps those exact protocol shapes and translates every `SeatId` value to a
  slot id at the websocket boundary.
- Replay artifacts store full-perspective events after the same slot translation used on the wire. `slot_of_seat0`
  is still recorded for each game so replay consumers can inspect the game alternation.
- A player-connect timeout with one missing slot awards the match to the connected slot without adding a synthetic
  game summary. If both slots are missing, scores are `[0.0, 0.0]`.
- Timeout notes are emitted as `said` events with `actor: null` and the timed-out slot in the event payload, keeping
  the event shape from `docs/protocol.md` while distinguishing server-authored text from player chat.
