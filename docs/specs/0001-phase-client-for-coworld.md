# Phase Client for Coworld

> **Status:** Implemented **Author:** Codex **Created:** 2026-07-14

## Summary

Replace Coworld MTG's bespoke battlefield renderer with the Phase React client while
retaining Coworld as the authoritative episode host. A small `CoworldAdapter`
will implement Phase's existing `EngineAdapter` interface over Coworld MTG's
authenticated WebSocket and replay protocols. The game server will send Phase's
viewer-filtered `GameState`, engine-authored derived views, and exact legal
actions as one atomic snapshot. Coworld-only chrome will display match score,
clocks, connection state, and episode completion around Phase's game board.

## Problem

The current client duplicates Phase's board, stack, combat, targeting, mana,
prompt, and priority presentation in a single local TypeScript application. It
must be updated for every new Phase action or waiting state, despite Phase already
shipping and testing those interactions. That creates two UI implementations for
one engine and encourages the Coworld client to infer presentation or legality
from an intentionally lossy `ViewerSnapshot`.

Using Phase's deployed multiplayer client unchanged is not sufficient. Its
WebSocket handshake owns lobby creation, deck registration, reconnection, and
match hosting, whereas Coworld assigns authenticated slots and owns clocks,
scoring, results, replay persistence, and episode termination. Its replay adapter
also reconstructs games locally in WASM, while Coworld replays stored server
snapshots and must remain readable without rerunning a potentially different
engine build.

## Solution

Use Phase's client at the adapter boundary rather than copying individual visual
components:

1. Pin one Phase revision for both the Rust engine and client source.
2. Build the Phase React client with a small Coworld entry point and
   `CoworldAdapter` implementing Phase's `EngineAdapter` contract.
3. Send an explicitly negotiated Phase-native snapshot alongside the legacy
   compact snapshot during a compatibility window. Each snapshot contains the
   filtered `GameState`,
   `DerivedViews`, legal actions, auto-pass recommendation, effective spell
   costs, and actions grouped by source object.
4. Map Coworld `hello`, `state`, `ack`, `reject`, `game_end`, and `match_end`
   frames into Phase store/adapter events. Actions continue to use Coworld
   `cmd_id` envelopes and are still validated by the server against the current
   exact legal-action set.
5. Add Coworld chrome outside `GameBoard` for clocks, series score, player names,
   connection failures, and match completion.
6. Drive spectator and replay pages through read-only variants of the same
   adapter. Replay playback consumes recorded snapshots; it does not load Phase
   WASM or regenerate history.
7. Remove the legacy renderer and compact projection only after player, global,
   and replay routes pass the same behavioral and hidden-information gates.

## Goals

- [x] Player, global spectator, and replay routes render through Phase's game UI.
- [x] The engine and client are pinned to the same immutable Phase commit.
- [x] Every store update carries state and legal actions from one server snapshot.
- [x] Coworld remains the sole owner of authentication, clocks, scoring, results,
      replay persistence, and episode lifecycle.
- [x] Player and spectator snapshots expose neither hidden cards nor RNG state.
- [x] The browser never invents, rewrites, or locally validates a game action.
- [x] Existing compressed Coworld replays remain readable through a legacy
      compatibility path.
- [x] Phase client updates are performed by advancing a pin and a narrow adapter
      overlay, not by manually recopying components.

## Non-Goals

- Replacing `coworld-mtg-server` with `phase-server`.
- Running an authoritative Phase WASM engine in the browser.
- Adopting Phase's lobby, accounts, deck storage, matchmaking, or local AI flow.
- Reconstructing Coworld replays by rerunning actions against a newer engine.
- Supporting arbitrary deck import as part of the UI migration.
- Maintaining a permanent fork of Phase presentation components in this repo.

## Design

### Ownership boundary

| Owner | Responsibilities |
| --- | --- |
| Phase engine | Rules, redaction, derived presentation views, events, legal actions |
| `phase-bridge` | Pinned engine, deck hydration, atomic viewer snapshot construction |
| `coworld-mtg-server` | Slot auth, clocks, scoring, replay recording, Coworld files and routes |
| Phase client | Board, hand, zones, stack, combat, prompts, targeting, mana and animations |
| Coworld adapter/chrome | Protocol translation, identity, clock/score display, terminal episode UI |

### Phase source strategy

The release build shallow-fetches the exact Phase revision already declared by
`phase-bridge`. It builds the client from that checkout with Coworld-owned files
applied as a narrow overlay. The overlay may add an adapter, route, and chrome,
but must not patch Phase board components. Local development uses a script that
materializes the same content-addressed checkout under an ignored build directory.
The Docker build fails if the Rust and client revisions disagree.

This is preferable to an npm dependency because the Phase client is not a
published library, and preferable to vendoring because a copied component tree
would immediately recreate the synchronization problem.

### Wire snapshot

During migration, `ViewerSnapshot.phase_client` is optional and populated for
live player/global sockets that negotiate `client=phase`:

```text
phase_client:
  state: filtered Phase GameState
  derived: Phase DerivedViews for this viewer
  legal_actions: exact GameAction[]
  auto_pass_recommended: boolean
  spell_costs: object-id -> ManaCost
  legal_actions_by_object: object-id -> GameAction[]
```

The server constructs these values together before fan-out. Scripted agents do
not request or pay to serialize the larger browser payload. The adapter assigns
a monotonic client sequence number on receipt and commits it through Phase's
`EngineSnapshot` API. Spectators receive no legal actions. Version-3 replays
persist one full Phase client snapshot followed by structural deltas. The replay
server reconstructs complete snapshots before sending them to the browser.
Version-2 compact replay files continue through the retained legacy renderer.

### Adapter behavior

`CoworldAdapter` has three modes:

- `player`: opens `/player?slot=…&token=…`, learns the rotating Phase seat from
  `hello`, submits `{cmd_id, action}`, and resolves submissions on matching
  `ack`/`reject` frames.
- `spectate`: opens `/global`, commits read-only snapshots, and never exposes a
  dispatch method to the page.
- `replay`: opens `/replay`, buffers the advertised finite snapshot stream, and
  offers seek/play/pause without an engine worker.

Coworld `game_end` and `match_end` are host lifecycle events, not synthetic Phase
actions. Seat-to-slot rotation remains a server concern; the adapter supplies the
current Phase seat as the Phase client's local player id.

### Rollout

1. Add and test the optional Phase-native snapshot while the old UI remains the
   default.
2. Materialize the pinned Phase client and add `CoworldAdapter` contract tests
   using recorded server frames.
3. Introduce an opt-in `/client/phase-player` route and Phase-based spectator
   route; run them in browser CI.
4. Add snapshot-based replay and Coworld clock/score chrome.
5. Make Phase routes default, retain legacy routes for old replay playback.
6. Remove the compact live projection and bespoke renderer after one release;
   preserve a versioned legacy replay viewer if published replay compatibility
   requires it.

### Acceptance tests

- Two browser seats mulligan, play a land, cast with mana payment, respond on the
  stack, and declare attackers/blockers.
- Modal, multi-target, damage-assignment, phase-stop, and Full Control fixtures
  exercise Phase components without Coworld-specific action interpretation.
- A player cannot see the opponent hand, either library order, or RNG seed/stream
  position; the global spectator cannot see private zones.
- Every submitted action was present verbatim in the snapshot being displayed.
- Clock flag, concession, game rotation, match scoring, reconnect, global view,
  replay seek, and compressed replay loading retain current behavior.
- A build-time test proves the client source revision equals `PHASE_REVISION`.

## Open Questions

1. Should the Coworld adapter be proposed upstream in Phase after the first
   release, or remain a small overlay maintained beside this repository?
2. How long must published version-2 compact replays remain browser-playable?
3. Should Phase's animations/audio ship enabled by default under Coworld's image
   and browser resource limits?

## Implementation Progress

- [x] Specify the Phase/Coworld ownership boundary and rollout.
- [x] Add an atomic Phase-native state/action DTO at `phase-bridge`.
- [x] Require `client=phase` capability negotiation so agents retain compact
      frames and episode timing.
- [x] Prove the richer player/spectator payload redacts hidden state and RNG.
- [x] Keep compact replay and scripted-player compatibility green.
- [x] Add the Coworld `EngineAdapter` and Phase-side Coworld entry point.
- [x] Build the Phase client and Rust engine from the same revision.
- [x] Make Phase the default player/global UI and add snapshot-based replay.
- [x] Retain the bespoke client only as the version-2 replay compatibility viewer.
- [x] Gate the pinned overlay build on adapter contract tests, forward the
      server-authored concession action, and terminate replay snapshot streams.
