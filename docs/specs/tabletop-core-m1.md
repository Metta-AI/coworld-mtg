# Spec: `tabletop-core` (Milestone M1)

The pure game-state crate for cogatrice (see /PLAN.md §4–§5). A Cockatrice-style *unenforced* MTG tabletop for
exactly two seats: zones, card objects, attributes, counters, phases, turn-taking windows, table talk — but **no MTG
rules** (no mana checking, no timing legality, no combat math). What it does enforce, absolutely: zone visibility,
seeded randomness, card provenance, turn ownership, and game termination.

Constraints:
- Pure library. No I/O, no async, no clocks (callers supply wall-time only as opaque annotations if ever needed).
- `serde::{Serialize, Deserialize}` on every public type; JSON-friendly shapes (external tags OK, but prefer
  `#[serde(tag = "type", rename_all = "snake_case")]` for enums that cross the wire).
- Determinism: identical `GameSetup` + identical action sequence ⇒ byte-identical event log (JSON-serialized).
  All randomness from `rand_chacha::ChaCha12Rng` seeded from `GameSetup.seed`.
- Dependencies: workspace `serde`, `serde_json`, `rand`, `rand_chacha`, `thiserror`; dev-deps `proptest`,
  `serde_json`. Nothing else.
- Rust 2021, no unsafe, `cargo clippy -- -D warnings` clean, no docstrings/comments except where genuinely needed.

## Vocabulary and IDs

```rust
pub struct SeatId(pub u8);            // 0 or 1
pub struct CardId(pub u32);           // unique per game, includes tokens
pub struct Seq(pub u64);              // event sequence number, starts at 0, gapless
```

`ZoneKind`: `Library`, `Hand`, `Battlefield`, `Graveyard`, `Exile`. Library and Hand are hidden zones; the rest are
public. Library is ordered (index 0 = top); Hand is unordered (but stable-ordered internally for determinism);
Battlefield cards carry free `x: i16, y: i16` coordinates; Graveyard and Exile are ordered stacks (0 = top).

`Phase` (Cockatrice's 11): `Untap`, `Upkeep`, `Draw`, `Main1`, `BeginCombat`, `DeclareAttackers`, `DeclareBlockers`,
`CombatDamage`, `EndCombat`, `Main2`, `End`. `next_phase` from `End` is invalid — use `next_turn`.

## Setup types

```rust
pub struct CardSpec {          // resolved card data; core does not know about Scryfall
    pub name: String,
    pub type_line: String,
    pub mana_cost: Option<String>,   // e.g. "{1}{R}"
    pub power_toughness: Option<String>, // e.g. "2/2"
    pub oracle_text: String,
    pub art_id: Option<String>,      // opaque (scryfall id), passed through to viewers
}
pub struct DeckList { pub name: String, pub cards: Vec<CardSpec> }  // no size rules enforced
pub struct PlayerSetup { pub name: String, pub deck: DeckList }
pub struct GameSetup {
    pub seed: u64,
    pub players: [PlayerSetup; 2],
    pub starting_life: i32,          // default 20
    pub turn_cap: u32,               // game ends after the cap'd turn completes; default 25
    pub reaction_depth_cap: u8,      // default 4
}
```

On `Game::new(setup)`: assign `CardId`s from a seeded random permutation over all deck cards, shuffle each library
(seat 0 first), set life, deal 7 cards each, enter mulligan flow. Emits setup events (see Events).

## Turn-taking: the `Expectation` state machine

At any moment exactly one thing is awaited. Actions submitted by a seat that isn't the expected actor (or of a kind
not valid in the current window) are rejected with `ActionError::NotYourWindow` / `InvalidInWindow` — rejections are
NOT logged as events.

```rust
pub enum Expectation {
    Mulligan { seat: SeatId, keeping_hand_of: u8, must_bottom: u8 },
    MainWindow { seat: SeatId },                    // the active player's open-ended window
    ReactionWindow { seat: SeatId, depth: u8 },     // responder may act or pass
    GameOver { outcome: GameOutcome },
}
```

- **Mulligan flow (London)**: seats resolve sequentially, seat 0 fully first. `MulliganAgain` reshuffles hand into
  library, draws 7 again, increments that seat's mulligan count. `MulliganKeep { bottom: Vec<CardId> }` requires
  exactly `mulligan_count` cards from hand, placed on the bottom of the library in the given order. When both seats
  have kept: turn 1 begins, seat 0 active, phase `Untap`, `MainWindow { seat: 0 }`. (No first-turn draw skip — no
  rules; the deck docs tell players turn-1 active player skips their draw by convention.)
- **MainWindow**: the active player may submit any number of game actions. Two actions hand control over:
  - `Pass` — offers a reaction window: `ReactionWindow { seat: opponent, depth: 0 }`.
  - `NextPhase` / `NextTurn` — advances, then opens `ReactionWindow { seat: opponent, depth: 0 }` so the opponent
    can respond to the phase change; when the opponent passes, control returns to `MainWindow { active }`.
    `NextTurn` flips the active seat, increments turn, resets phase to `Untap`. It does NOT untap or draw — manual.
- **ReactionWindow { seat: s, depth: d }**: seat `s` may `Pass` (window closes: if `d == 0` control returns to the
  main-window holder; else pops to `ReactionWindow` of the other seat at `d-1`), or submit game actions. The first
  game action in a reaction window at depth `d` re-opens `ReactionWindow { other, depth: d+1 }` after it resolves,
  unless `d + 1 > reaction_depth_cap`, in which case control stays with `s` until `Pass`. (Simple alternating
  model; termination is guaranteed because only `Pass` moves depth downward and caps bound the nesting.)
- **GameOver**: only `Say` is accepted (post-game chat is dropped from scoring anyway); everything else rejected
  with `GameIsOver`.

`Concede` is legal from any window, any seat, any time (including mulligan).

## Actions

```rust
#[serde(tag = "type", rename_all = "snake_case")]
pub enum Action {
    // zone & card manipulation (any window you hold)
    Draw { count: u32 },                                  // from own library top to own hand
    MoveCards { moves: Vec<CardMove> },                   // see below
    MoveTopOfLibrary { count: u32, to_seat: SeatId, to_zone: ZoneKind,
                       position: MovePosition, face_down: bool },
    SetCardAttr { card: CardId, attr: CardAttr },         // Tapped(bool), FaceDown(bool), Attacking(bool),
                                                          //   PtOverride(Option<String>), Annotation(String)
    CreateToken { spec: CardSpec, x: i16, y: i16 },       // enters own battlefield, is_token = true
    AddCounter { target: CounterTarget, name: String, delta: i32 },  // card or player counters; life is
                                                          //   the player counter named "life"
    Shuffle,                                              // own library
    RollDie { sides: u32 },                               // public result
    Reveal { cards: Vec<CardId>, to: RevealTo },          // Opponent | All; card must be visible to actor
    Say { text: String },                                 // table talk, public, max 2000 chars
    Point { from: CardId, to: Option<CardId> },           // arrow; None clears actor's arrow from `from`
    // flow
    Pass,
    NextPhase,
    NextTurn,
    MulliganKeep { bottom: Vec<CardId> },
    MulliganAgain,
    Concede,
}
pub struct CardMove {
    pub card: CardId,
    pub to_seat: SeatId,          // zone owner (moving cards to opponent zones is allowed — donate/steal by consent)
    pub to_zone: ZoneKind,
    pub position: MovePosition,   // Top | Bottom | Index(u32) | Battlefield { x, y }
    pub face_down: Option<bool>,
    pub tapped: Option<bool>,
}
```

Provenance/ownership rules (enforced): a seat may act only on cards it can *see and touch*: any card in its own
zones, plus cards it controls on any battlefield. Moving opponent-owned cards out of the opponent's zones is
rejected (`NotYourCard`) — with one exception: cards the actor owns that sit in an opponent zone may be reclaimed.
Tokens that leave the battlefield cease to exist (event `TokenRemoved` instead of a zone entry). `Draw` from an
empty library immediately ends the game (loss for the drawer, `EndReason::DrewFromEmptyLibrary`). Hidden-zone
identity integrity: actions that address a card by `CardId` are rejected with `HiddenZoneAddressing` when that card
is currently in any library. This applies to `MoveCards`, `SetCardAttr`, `AddCounter { target: Card }`, and `Point`
(`from` and `to`). Use `MoveTopOfLibrary` to move cards from the actor's own library by position without naming
hidden identities. It takes up to `count` cards from the top in library order and applies the same destination
insertion semantics as `MoveCards`; if `count` exceeds the library size, it moves all remaining cards and does not
end the game. A zero count is invalid. For `MovePosition::Battlefield { x, y }`, every moved card uses the supplied
coordinate. `Draw` remains the only draw action.

Life reaching ≤ 0 (via `AddCounter` on "life"): game ends, loser is the seat whose life dropped, unless both ≤ 0 in
the same action (draw). `turn_cap` reached: when `NextTurn` would begin turn `turn_cap + 1`, instead the game ends —
higher life wins, equal life draws (`EndReason::TurnCap`).

## Events

Every accepted action produces one or more `LoggedEvent { seq, turn, phase, actor: Option<SeatId>, event: Event }`.
`Event` variants mirror actions (`Drew { seat, cards }`, `CardsMoved { .. }`, `AttrSet`, `TokenCreated`,
`CounterChanged`, `Shuffled { seat }`, `DieRolled { seat, sides, result }`, `Revealed { .. }`, `Said`, `Pointed`,
`Passed`, `PhaseChanged`, `TurnChanged`, `MulliganResolved`, plus lifecycle: `GameStarted { setup-summary }`,
`HandDealt`, `WindowOpened { expectation }`, `GameEnded { outcome } }`). Design for the wire: these become the
protocol's observation deltas verbatim.

`CardMoveEvent` includes `was_face_down: bool`, the card's face-down state before the move. `AttrSet` also includes
`was_face_down: bool`, the card's face-down state before the attribute change.

### Redaction

```rust
pub enum Perspective { Seat(SeatId), Global, Full }
impl LoggedEvent { pub fn redact(&self, p: Perspective) -> Option<LoggedEvent>; }
impl Game       { pub fn snapshot(&self, p: Perspective) -> Snapshot; }
```

Rules:
- `Full` sees everything (replay-after-game-end, server internal).
- `Global` = public information: hand/library cards appear as anonymous stubs (`CardRef::Hidden { id }`); face-down
  battlefield cards likewise; `Drew` shows count not identity; `Revealed { to: All }` shows identity, `to: Opponent`
  shows identity only to that opponent and `Global` sees that a reveal happened.
- `Seat(s)`: `Global` plus full identity of s's own hand, own face-down cards, own library cards *only* when an
  event legitimately disclosed them (e.g. `Revealed` to s; `Drew` by s shows the drawn identities). Library order
  is never in any snapshot, not even `Full` (the log's `Shuffled` events plus determinism reconstruct it; snapshots
  expose `library_count` only).
- `Snapshot` contains: turn, phase, active seat, expectation, per-seat: name, counters (life...), mulligan count,
  zone contents (with `CardRef::Known(CardView)` / `Hidden { id }` per rules above), arrows, and `seq` high-water
  mark. A player reconnecting gets `snapshot(Seat(s))` and can act correctly (nightshift's self-containedness
  lesson).
- Redaction property: for every event/snapshot, `Seat(a)` output never contains the `name`/`CardSpec` of a card
  that rules say is hidden from `a`. Enforced by proptest (below).

## Outcome

```rust
pub struct GameOutcome { pub winner: Option<SeatId>, pub reason: EndReason, pub final_life: [i32; 2], pub turns: u32 }
pub enum EndReason { Concession, LifeZero, DrewFromEmptyLibrary, TurnCap }  // clock-flag added in M2 (server-owned)
```

## Public API

```rust
impl Game {
    pub fn new(setup: GameSetup) -> (Game, Vec<LoggedEvent>);
    pub fn submit(&mut self, seat: SeatId, action: Action) -> Result<Vec<LoggedEvent>, ActionError>;
    pub fn expectation(&self) -> &Expectation;
    pub fn outcome(&self) -> Option<&GameOutcome>;
    pub fn snapshot(&self, p: Perspective) -> Snapshot;
    pub fn log(&self) -> &[LoggedEvent];
}
```

`ActionError` (thiserror): `NotYourWindow`, `InvalidInWindow`, `NotYourCard`, `UnknownCard`, `WrongZone`,
`HiddenZoneAddressing`, `BadMulligan`, `GameIsOver`, `InvalidArgument(String)`. Every rejection carries enough
context to be relayed to an LLM as a corrective message.

## Tests (acceptance for M1)

1. **Determinism (proptest)**: random valid action sequences (generated via a driver that picks from currently-legal
   actions) applied to two `Game`s with the same setup produce identical JSON logs; different seeds produce
   different shuffles.
2. **Redaction (proptest)**: over random games, `Seat(a)`-redacted events/snapshots never leak hidden identities
   (walk the JSON: any card whose id is in a hidden set must have no `name` field).
3. **Termination**: any action sequence ends by `turn_cap`; reaction nesting cannot exceed cap.
4. **Window rules unit tests**: wrong-seat rejection, pass/reaction handoff transcript, mulligan London flow
   (keep-with-bottoming, multiple mulligans), concede everywhere.
5. **Provenance unit tests**: can't move opponent hand cards, tokens die on zone exit, empty-library draw loses,
   life ≤ 0 ends game, turn-cap life comparison.
6. **Scripted integration game** (`tests/scripted_duel.rs`): two hand-written script bots (~"goldfish-lite": play a
   land by moving it to battlefield, tap for narration, cast a creature via move+say, attack by setting Attacking +
   phases, opponent takes damage via AddCounter life) drive a full game from `Game::new` to `LifeZero` through the
   public API only, asserting the final outcome and a few mid-game snapshots. This doubles as the reference
   transcript for docs/protocol.md in M2.

Deck fixture for tests: build tiny `CardSpec` lists inline (e.g. 10 Mountains, 10 "Goblin Raider" 2/2s) — no
external data.

## Layout

```
crates/tabletop-core/
├── Cargo.toml
├── src/
│   ├── lib.rs          # re-exports
│   ├── ids.rs
│   ├── setup.rs
│   ├── zones.rs
│   ├── cards.rs        # card instances, attrs, CardRef/CardView
│   ├── actions.rs
│   ├── events.rs
│   ├── expectation.rs  # window state machine
│   ├── game.rs         # Game: submit / validate / apply
│   ├── redact.rs
│   └── rng.rs
└── tests/
    ├── scripted_duel.rs
    ├── windows.rs
    ├── provenance.rs
    └── props.rs        # proptest determinism/redaction/termination
```

## Implementation decisions

- `Game::new` treats `starting_life <= 0`, `turn_cap == 0`, and `reaction_depth_cap == 0` as requests for the M1
  defaults: 20 life, 25 turns, and reaction depth 4.
- Main-window game actions keep priority with the active player; only `Pass`, `NextPhase`, and `NextTurn` open a
  reaction window.
- `Say` is legal for the expected actor in live windows and for either seat after `GameOver`; every other post-game
  action is rejected with `GameIsOver`.
- A multi-card `Draw` from a short library logs any successfully drawn cards, then ends the game on the first failed
  draw.
- `CardId`s for deck cards are assigned from a seeded random permutation before library shuffles, so ids carry no
  decklist-position information. Token ids continue from the deck-card id range.
- `MoveCards`, `SetCardAttr`, card `AddCounter`, and `Point` reject cards currently in any library with
  `HiddenZoneAddressing`. `MoveTopOfLibrary` is the positional mechanism for moving cards out of the actor's own
  library.
- `MoveTopOfLibrary` emits `CardsMoved`; each move has `from = { actor, Library }` and `was_face_down = true`. A
  face-up destination in a public zone discloses identity to public perspectives; hidden or face-down destinations
  remain anonymous except to seats that can see the destination.
- Redacted move and attribute events decide card identity visibility from both the pre-action state and post-action
  state. Identity is known to a perspective if either state is visible under that perspective's normal zone and
  face-down rules, so public cards remain identified in the event that moves or turns them hidden.
- `MulliganAgain` emits `Shuffled`, `HandDealt`, `MulliganResolved { kept: false }`, and the next
  `WindowOpened`.
