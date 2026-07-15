# Coworld MTG Phase protocol

Coworld MTG uses JSON text frames over WebSocket:

- `/player?slot=<0|1>&token=<token>` is an authenticated player connection.
- `/global` is a read-only, non-seat spectator connection.
- `/replay` is an omniscient stream available when `COGAME_LOAD_REPLAY_URI` is set.

Phase is the sole rules authority. A client never sends `draw`, `move_cards`,
`tap`, `next_phase`, or a handwritten combat command. Gameplay choices copy one
complete `GameAction` value from the latest `state.legal_actions` or
`state.legal_actions_by_object` collection. The only non-gameplay exceptions
are Phase's actor-scoped `SetAutoPass`, `CancelAutoPass`, and `SetPhaseStops`
preference actions described below.

`seed` is the episode's root seed. If the commissioner omits it, the host
generates a fresh `u64` once while loading the private config. Phase seeds one
serialized ChaCha20 stream from that value before loading the decks; initial
library shuffles, starting-player selection, mulligan reshuffles, random
choices, and all later shuffles consume that same stream. The live public
config omits the seed so fixed decklists cannot turn it into hidden-library
information. Results and replay metadata record the resolved seed after play;
supplying that seed and the same actions reproduces the episode exactly.

## Player frames

On connection:

```jsonc
{
  "type": "hello",
  "slot": 0,
  "seat": 1,
  "seat_name": "human-0",
  "player_names": ["opponent-1", "human-0"],
  "match": {"games_to_win": 1, "game_number": 1, "wins": [0, 0]},
  "config": {/* public Coworld config */},
  "decklist": {/* this slot's bundled deck */}
}
```

`slot` is stable across the match and is used for scoring. `seat` is Phase's
player ID for the current game; seats rotate between games. When the public
config has `swap_decks_each_game: true`, even-numbered games also exchange the
two deck assignments between stable slots, so each player pilots both decks in
a multi-game color-swap series.

Every initial state, accepted action, timeout, and reconnect produces a complete
decision snapshot:

```jsonc
{
  "type": "state",
  "game_number": 1,
  "state": {
    "turn": 3,
    "phase": "PreCombatMain",
    "active_player": 0,
    "priority_player": 0,
    "waiting_for": {"type": "Priority", "data": {"player": 0}},
    "players": [/* life, mana pool, visible hand/graveyard, library count */],
    "battlefield": [/* engine-derived cards */],
    "stack": [/* spells and abilities */],
    "exile": [],
    "combat": null,
    "preference_player": 0,
    "auto_pass_recommended": false,
    "auto_pass_mode": null,
    "phase_stops": [
      {"phase": "Upkeep", "scope": "OpponentsTurns"}
    ],
    "legal_actions": [
      {"type": "PassPriority"},
      {"type": "PlayLand", "data": {"object_id": 12, "card_id": 12}}
    ],
    "spell_costs": {/* object id -> effective Phase cost */},
    "legal_actions_by_object": {/* object id -> exact actions */},
    "phase_client": {
      "state": {/* Phase viewer-filtered GameState */},
      "derived": {/* Phase engine-authored presentation views */},
      "legal_actions": [/* same exact actions as above */],
      "auto_pass_recommended": false,
      "spell_costs": {/* object id -> effective Phase cost */},
      "legal_actions_by_object": {/* object id -> exact actions */}
    }
  },
  "events": [/* viewer-filtered Phase GameEvent values */],
  "clocks_ms": [354000, 349000],
  "decision_cap_ms": 30000
}
```

The state is already filtered by Phase. A player sees their own hand, hidden
placeholders for the opponent's hand, and hidden libraries. The spectator sees
hidden placeholders for both hands. Clients must not derive hidden identity or
rules legality from object IDs.

`auto_pass_recommended` is true only for the viewer who currently has an
offered `PassPriority` action, and only when Phase's rules-aware presentation
policy recommends passing. `auto_pass_mode` and `phase_stops` contain only the
requesting player's preferences; `preference_player` identifies that Phase
seat, and these fields never expose an opponent's settings.

`phase_client` is the atomic Phase-native state/action pair used by the Phase
React client. It is present only when a live player or global socket
connects with `client=phase`; scripted agents and the legacy browser retain the
smaller compact payload. It is optional on input so version-2 replays remain
readable. During the compatibility window the compact fields and
`phase_client` describe the same engine revision; clients must never combine
state from one frame with legal actions from another.
Player payloads include the viewer's exact `Concede` action while a game is in
progress, even though concession sits outside Phase's current prompt. Coworld's
adapter forwards that action rather than constructing one in the browser.

Version-3 replay files store a full `phase_client` value on the first step and
`phase_client_delta` operations on later steps. `/replay` applies those deltas
server-side and emits complete Phase snapshots, so the browser never reruns the
engine. Version-2 files omit both fields and `/client/replay` selects the bundled
legacy compact viewer for them. The replay WebSocket remains read-only.

To act, copy an offered action exactly:

```jsonc
{
  "cmd_id": 17,
  "action": {"type": "PlayLand", "data": {"object_id": 12, "card_id": 12}}
}
```

The server responds with:

```jsonc
{"type": "ack", "cmd_id": 17, "turn": 3}
{"type": "reject", "cmd_id": 18, "error": {"kind": "illegal_action", "detail": "..."}}
```

`Concede` is the sole action not enumerated by Phase and is always available:

```jsonc
{"cmd_id": 19, "action": {"type": "Concede", "data": {"player_id": 0}}}
```

The `player_id` must equal the current `hello.seat`. The host rejects spoofed
concessions and every gameplay action absent from the latest Phase legal set.

Phase also accepts three exact preference actions:

```jsonc
{"cmd_id": 20, "action": {"type": "SetAutoPass", "data": {"mode": {"type": "UntilStackEmpty"}}}}
{"cmd_id": 21, "action": {"type": "CancelAutoPass"}}
{"cmd_id": 22, "action": {"type": "SetPhaseStops", "data": {"stops": [{"phase": "Upkeep", "scope": "OwnTurn"}]}}}
```

`SetAutoPass` still requires the sender's current priority prompt and consumes
that priority decision. `CancelAutoPass` and `SetPhaseStops` are pure,
actor-scoped preferences: either seat may send them in any prompt, they do not
advance the game, reset a decision deadline, or consume game clock. The bridge
allowlists only these concrete variants; it does not provide a generic bypass
for invented actions. Replays retain these actions and attribute the projected
preference state to its Phase player with `preference_player`.

Games and matches end with `game_end` and `match_end`. `winner_slot` uses stable
Coworld slot identity, not the rotating Phase seat.

## Simultaneous decisions and timeouts

London mulligans and other simultaneous Phase prompts can give both seats legal
actions in the same authoritative state. Either player may answer first. Each
accepted answer produces a new complete snapshot for both seats. The host keeps
an independent decision start for each pending seat, so one player's answer or
preference update cannot charge or reset the other player's clock.

At a decision timeout, the host submits an action from that seat's current legal
set, preferring keep/pass/empty combat declarations. A depleted game clock
submits a real Phase concession and records `clock_flag` as the host end reason.

## Spectator and replay

`/global` receives the same `hello`, `state`, `game_end`, and `match_end` flow,
but the snapshot is filtered using Phase's non-seat spectator identity and has
no legal actions.

New replay artifacts are version 3. Each step records relative time, actor slot,
the accepted Phase action, authoritative compact projection, Phase events, and
either the initial Phase client snapshot or a delta from the prior step.
`/replay` sends `replay_meta`, then reconstructed full `state` frames, followed
by game/match end frames. The Phase replay adapter buffers the first stream and
provides local play, pause, and seek controls. Version-2 replay loading remains
supported as described above.
