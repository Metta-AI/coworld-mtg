# Cogatrice Phase protocol

Cogatrice uses JSON text frames over WebSocket:

- `/player?slot=<0|1>&token=<token>` is an authenticated player connection.
- `/global` is a read-only, non-seat spectator connection.
- `/replay` is an omniscient stream available when `COGAME_LOAD_REPLAY_URI` is set.

Phase is the sole rules authority. A client never sends `draw`, `move_cards`,
`tap`, `next_phase`, or a handwritten combat command. It chooses one complete
`GameAction` value from its latest `state.legal_actions` or
`state.legal_actions_by_object` collection and echoes that value unchanged.

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
player ID for the current game; seats rotate between games.

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
    "legal_actions": [
      {"type": "PassPriority"},
      {"type": "PlayLand", "data": {"object_id": 12, "card_id": 12}}
    ],
    "spell_costs": {/* object id -> effective Phase cost */},
    "legal_actions_by_object": {/* object id -> exact actions */}
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
concessions and every non-concession action absent from the latest Phase legal
set.

Games and matches end with `game_end` and `match_end`. `winner_slot` uses stable
Coworld slot identity, not the rotating Phase seat.

## Simultaneous decisions and timeouts

London mulligans and other simultaneous Phase prompts can give both seats legal
actions in the same authoritative state. Either player may answer first. Each
accepted answer produces a new complete snapshot for both seats.

At a decision timeout, the host submits an action from that seat's current legal
set, preferring keep/pass/empty combat declarations. A depleted game clock
submits a real Phase concession and records `clock_flag` as the host end reason.

## Spectator and replay

`/global` receives the same `hello`, `state`, `game_end`, and `match_end` flow,
but the snapshot is filtered using Phase's non-seat spectator identity and has
no legal actions.

Replay artifacts are version 2. Each step records relative time, actor slot, the
accepted Phase action, full authoritative projection, and Phase events. `/replay`
sends `replay_meta`, then one `state` frame per step, followed by game/match end
frames, and loops.
