# Coworld MTG roadmap

Coworld MTG is Magic: The Gathering packaged as a Coworld. The original
Cockatrice-style honor-system prototype has been retired. The Rust-native
[Phase](https://github.com/phase-rs/phase) engine is the sole game authority.

## Shipped architecture

- `phase-bridge` pins Phase, loads the card export, resolves bundled decks,
  produces per-viewer projections, and accepts exact legal `GameAction` values.
- `cogatrice-server` owns Coworld authentication, clocks, match scoring,
  results, replay persistence, and viewer fan-out. It contains no Magic rules.
- `goldfish` ranks the legal actions supplied by Phase. It contains no manual
  mana, draw, timing, or combat implementation.
- The pinned Phase React client renders the game. Coworld supplies only a thin
  WebSocket/replay adapter and series chrome; the old `web` renderer is retained
  solely for version-2 replay compatibility.

The mechanics and data contract is in [docs/phase-rules-port.md](docs/phase-rules-port.md).
The live wire format is in [docs/protocol.md](docs/protocol.md).

## Next milestones

1. Replace the compact bundled-card fixture with a content-addressed Phase card
   export and Scryfall bulk metadata cache suitable for arbitrary deck import.
2. Add a deck-import endpoint keyed by Scryfall Oracle ID, with explicit errors
   for cards Phase cannot resolve or parse.
3. Add deterministic browser fixtures for multi-block combat, first/double
   strike damage, deep stacks, face-down exile, mobile Full Control, and reduced
   motion; keep screenshot baselines alongside behavioral assertions.
4. Prepare the maintained-fork Phase commits as small upstream pull requests
   that independently satisfy `phase-rs/phase` contribution and test rules.
5. Expand hosted smoke beyond two goldfish players to include reconnect, replay,
   clock, preference, and browser-client episodes within Coworld limits.
6. Add Phase AI difficulty variants and LLM policies that rank the same exact
   legal-action surface.

## Non-negotiable invariants

- Phase owns every Magic state transition.
- Gameplay commands must be present in the submitting viewer's current exact
  legal-action set. Only Phase's narrowly allowlisted actor-scoped preference
  actions may bypass prompt membership.
- Player/spectator projections never expose hidden hands, libraries, or RNG.
- Replays store Phase actions, events, and authoritative state—not inferred
  tabletop moves.
- Unsupported cards fail import rather than falling back to honor-system play.
