# Cogatrice roadmap

Cogatrice is Magic: The Gathering packaged as a Coworld. The original
Cockatrice-style honor-system prototype has been retired. The Rust-native
[Phase](https://github.com/phase-rs/phase) engine is the sole game authority.

## Shipped architecture

- `phase-bridge` pins Phase, loads the card export, resolves bundled decks,
  produces per-viewer projections, and accepts exact legal `GameAction` values.
- `cogatrice-server` owns Coworld authentication, clocks, match scoring,
  results, replay persistence, and viewer fan-out. It contains no Magic rules.
- `goldfish` ranks the legal actions supplied by Phase. It contains no manual
  mana, draw, timing, or combat implementation.
- `web` renders visible Phase zones, mana, stack, combat state, prompts, events,
  and exact legal action controls. Scryfall supplies card imagery.

The mechanics and data contract is in [docs/phase-rules-port.md](docs/phase-rules-port.md).
The live wire format is in [docs/protocol.md](docs/protocol.md).

## Next milestones

1. Replace the compact bundled-card fixture with a content-addressed Phase card
   export and Scryfall bulk metadata cache suitable for arbitrary deck import.
2. Add a deck-import endpoint keyed by Scryfall Oracle ID, with explicit errors
   for cards Phase cannot resolve or parse.
3. Improve action presentation for target selection, modal spells, mana pinning,
   damage assignment, and uncommon interactive prompts without duplicating
   engine legality in TypeScript.
4. Add Phase AI difficulty variants and LLM policies that rank the same exact
   legal-action surface.
5. Package, certify, upload, and run hosted episodes inside Coworld resource and
   deadline limits.

## Non-negotiable invariants

- Phase owns every Magic state transition.
- A non-concession command must be present in the submitting viewer's current
  exact legal-action set.
- Player/spectator projections never expose hidden hands, libraries, or RNG.
- Replays store Phase actions, events, and authoritative state—not inferred
  tabletop moves.
- Unsupported cards fail import rather than falling back to honor-system play.
