# coworld-mtg — Plan

Convert Magic: The Gathering, as embodied by [Cockatrice](https://cockatrice.github.io/), into a
[Coworld](https://github.com/metta-AI/coworld): a packaged, agent-playable game environment with local browser play,
hosted league episodes, replays, and scoring. Implementation language: Rust.

This document is the plan. It covers the approach decision (wrap Cockatrice vs. reproduce it), the target
architecture, the agent-facing game design, milestones with acceptance criteria, risks, and what we end up with.

---

## 1. What we get at the end

A certified, uploadable Coworld named **`cogatrice`** (Cockatrice → cog) where LLM policies play real Magic: The
Gathering against each other on a shared virtual tabletop:

- **A Rust game server** implementing Cockatrice-style shared-tabletop semantics (zones, card manipulation, counters,
  life, phases, table talk) behind the standard Coworld container contract — the first Rust Coworld, reusable as a
  template for future Rust games.
- **Agent play**: players connect over a clean JSON WebSocket protocol, receive redacted per-seat observations
  (your hand, public battlefield, opponent's counts), and act through a small tabletop action vocabulary.
- **Local dev loop**: `coworld run-episode` for headless episodes, `coworld play` for browser play — a human can pick
  up a seat in the browser and play against a bot or LLM.
- **Watchability**: a live global viewer showing the table from a spectator's seat, and an autoplaying, looping
  browser replay of any finished episode (full-information once the game is over).
- **Scoring & leagues**: per-episode `results.json` with per-slot scores (win/loss/draw across a configurable number
  of games per episode), so submitted policies can be ranked in hosted leagues.
- **Baselines**: `goldfish`, a deterministic scripted bot (plays lands, casts what it can afford, attacks with
  everything); and `bedrock-baseline`, a minimal LLM player via Bedrock `InvokeModel` that demonstrates the protocol
  and gives leagues a floor above scripted play.
- **A benchmark axis no current Coworld covers**: MTG on an unenforced tabletop tests rules knowledge and
  *rule-following under an honor system*, long-horizon planning with hidden information, opponent modeling, and
  in-context adaptation across games — while the server still structurally guarantees information integrity
  (hidden hands, server-side shuffles, card provenance), so cheating on *information* is impossible and only
  *legality* relies on adjudication.

Not in scope (deliberately): a full MTG rules engine. Comprehensive-rules enforcement is an XMage/Forge-scale project
(years, millions of LOC, Java-only precedents) and Cockatrice itself ships none — see §3.

---

## 2. Background: the two source systems

### 2.1 The Coworld contract (verified against `metta-AI/coworld` docs and local exemplars)

A Coworld is a Docker-packaged game plus bundled players, manifest, docs, and protocols, exercised through a fixed
ladder: `coworld play` → `coworld run-episode` → `coworld certify` → `coworld upload-coworld`.

The **game runnable** is a long-running container that must:

- Listen on `COGAME_HOST:COGAME_PORT` (default `0.0.0.0:8080`).
- Read config JSON from `COGAME_CONFIG_URI`; serve `GET /healthz` when ready.
- Serve WebSockets: `/player?slot=...&token=...` (per-seat, token-authed) and `/global` (spectator).
- Serve browser clients: `GET /client/player?slot=...&token=...`, `GET /client/global`, and — when started in replay
  mode with `COGAME_LOAD_REPLAY_URI` — `GET /client/replay` + `/replay`, autoplaying and looping by default.
- Write results JSON to `COGAME_RESULTS_URI` (validated against `manifest.game.results_schema`, which must include a
  numeric `scores` array, one entry per slot) and opaque replay bytes to `COGAME_SAVE_REPLAY_URI` (which the same
  image must be able to load back).

**Players** are short-lived containers that read `COWORLD_PLAYER_WS_URL` (fully formed `/player` URL), speak the
game-defined protocol from `manifest.game.protocols.player`, optionally upload one debug `.zip` to
`COWORLD_PLAYER_ARTIFACT_UPLOAD_URL`, and exit when the episode ends. Hosted players call LLMs through the Bedrock
sidecar (`AWS_ENDPOINT_URL_BEDROCK_RUNTIME`, `InvokeModel` not `Converse`, model id via `BEDROCK_MODEL`).

**Manifest** requires: `game` (`name`, `version`, `description`, `owner`, `runnable`, `config_schema` — which must
require a runner-injected string-array `tokens` field — `results_schema`, `protocols.player`, `protocols.global`,
`docs.readme`), at least one `player[]`, `variants[]`, and `certification` (fixture config + roster that certify
actually runs). Build via `coworld build <compose.yaml> <template.json> <version> <out>/coworld_manifest.json`;
images must be `linux/amd64`. Hosted episodes get ~1 CPU / 512 MiB for the game container and a **20-minute active
deadline** — a hard budget MTG episode design must respect.

### 2.2 Cockatrice (verified against `Cockatrice/Cockatrice` HEAD)

Cockatrice is a GPL-2.0 C++/Qt virtual tabletop: a desktop client, a server (**servatrice**, protobuf protocol over
raw TCP or WebSocket, official image `ghcr.io/cockatrice/servatrice`), and a card-data pipeline (MTGJSON →
`cards.xml`, tokens from `Cockatrice/Magic-Token`).

The load-bearing fact: **Cockatrice enforces no MTG rules.** It is a shared tabletop. The server owns zones
(library/hand/battlefield/graveyard/exile/sideboard), card objects and their attributes (tapped, face-down, P/T,
annotations, attached counters), per-player counters (life, poison...), arrows, dice, shuffles, a turn/phase pointer,
and chat — and relays ~30 game commands (`move_card`, `set_card_attr`, `create_token`, `inc_counter`, `next_turn`,
`set_active_phase`, `roll_die`, `reveal_cards`, `mulligan`, `concede`, ...) between clients. Players play Magic on
top of it by convention, like paper Magic over a webcam. Games end by concession or agreement. What the server *does*
structurally guarantee: hidden-zone visibility, server-side randomness, and card provenance.

Replays are server-recorded event streams (`GameReplay { game_info, event_list }`) — but only with a MySQL database
(`[database] type=none` mode disables replay persistence). The maintained web client is
[Webatrice](https://github.com/Cockatrice/Webatrice) (React/TS over the WebSocket transport).

---

## 3. The approach decision: reproduce, don't wrap

Two candidate architectures were evaluated against the contract above.

**Option A — wrap servatrice** (the `coworld-vanilla-wow` pattern: run the third-party server in the container,
publish native ports, extract scoring from its state):

- Everything Coworld-specific must be built regardless: the episode orchestrator, results extraction, browser
  player/global/replay clients, and an agent-friendly protocol (LLM agents should not speak length-prefixed
  protobuf; vanilla-wow gets away with native protocols only because its players embed a full Nim game client).
- So the wrap adds, on top of all that work: a protobuf↔JSON gateway tracking servatrice's `cmd_id`/response/event
  model, a C++/Qt/MySQL runtime inside the 512 MiB hosted budget (MySQL required just to get replays out, then
  another exporter to turn DB rows into a replay our container can serve), and GPL-2.0 coupling.
- What the wrap buys — battle-tested tabletop semantics and desktop-client compatibility — is small here because the
  semantics *are* small (a state model of zones/cards/counters plus ~30 commands; the server-side game model is
  ~15 C++ files), and desktop compatibility is a nice-to-have, not a requirement.

**Option B — reproduce the tabletop in Rust** (the `coworld-crewrift` pattern: one native binary that owns the
simulation, the Coworld routes, results, and replay):

- Single static binary in a scratch-ish image; trivially inside hosted resources; deterministic seeding; replay is
  our own event log, so record/load/serve is first-class rather than exhumed from MySQL.
- The protocol becomes JSON-native and designed for LLM consumption from day one (Cockatrice's command vocabulary,
  Coworld's envelope conventions).
- Cost: we re-implement the tabletop state machine (§5.1) and build the web UIs — but the UIs are needed under both
  options, and the state machine is the small part of Cockatrice (the 80k-LOC bulk is Qt client and
  account/room/moderation infrastructure we don't need).
- License note: implement from the concepts and observed protocol semantics, not by translating GPL sources; keep
  proto-derived naming only where it is API vocabulary. (Private repo regardless.)

**Decision: Option B — Rust-native reproduction.** Cockatrice interop (its protobuf protocol so desktop clients can
spectate/play, `.cod` deck import) is preserved as a stretch milestone (§7, M7) rather than a foundation. An
independent gpt-5.5 research pass reached the same conclusion.

---

## 4. Game design: MTG as an agent benchmark on an unenforced tabletop

### 4.1 Format

- **Two-player duels, best-of-N games per episode** (default N=3 wins-count scoring, subject to the 20-minute
  deadline; certification fixture uses N=1 with tight clocks).
- **Fixed preconstructed decks** assigned per slot by the variant config. v1 ships two repo-authored 40-card decks of
  deliberately simple cards (a mono-red aggro list and a mono-green midrange list: mostly vanilla/keyword-light
  creatures, burn, pump, simple removal). Simple cards keep the honor-system load low and games fast; 40-card decks
  shorten games. Later variants add real precons and more complex sets; deck *choice* and ultimately deck
  *building* are further variant dimensions.
- **London mulligan**, server-assisted (server shuffles, deals, moves bottomed cards).

### 4.2 Turn structure and timing

The server maintains the Cockatrice-style turn/phase pointer and enforces *turn-taking, not rules*:

- The active player advances phases explicitly (`next_phase` / `next_turn`).
- Each phase change and each action by the acting player opens a short **reaction window** for the opponent (act or
  `pass`), giving instants/abilities a place to live without modeling the stack. Nested reactions get a bounded
  depth; resolution order is the players' problem (as in paper Magic played casually).
- **Chess clock per player per game** (default ~6 minutes each, config-tunable) plus a per-decision cap; a flagged
  clock loses the game. A **turn cap** (default 25) ends unfinished games by life-total comparison (then draw).
  These bounds keep episodes inside the hosted deadline deterministically.

### 4.3 What the server enforces vs. what it doesn't

Enforced structurally (cheating impossible):

- Zone visibility: hands/libraries hidden, per-seat redaction of observations and of the live `/global` stream.
- Randomness: server-side seeded shuffles and dice.
- Provenance: card objects exist only from decklists (plus tokens, which are marked as tokens); attributes, counters
  and zone locations change only through logged actions.
- Turn ownership: you act on your own objects, in your windows (with explicit allowances for e.g. targeted discard
  reveals, which are requests the opponent fulfills).

Not enforced (the honor-system benchmark surface): mana payment, timing legality, combat math, triggered abilities,
card-text effects. Players narrate what they do through the action log plus `say` (table talk); the opponent sees
every action.

### 4.4 Game end and scoring

A game ends by: concession (`concede`), a player acknowledging lethal (`set_life` ≤ 0 is auto-detected), drawing from
an empty library (server-visible, auto-loss), clock flag, or turn cap (life comparison). Episode `results.json`:
`scores` = games won per slot (draws 0.5), plus per-game detail (end reason, final life, turns, seed).

### 4.5 Adjudication (progressive hardening, later milestones)

- **M6a — mechanical referee (in-server, advisory→binding)**: cheaply checkable invariants flagged in the event log:
  untapped-permanent taps, land-drops-per-turn count, drawing outside draw step without narration, life changes with
  no cause annotation. Config flag turns violations from advisories into game losses for certification-grade play.
- **M6b — judge grader (Coworld grader role)**: post-episode container replays the event log and uses an LLM +
  card-text lookup to score rules compliance per player; league scoring can blend win rate with compliance. This
  makes "plays legally" itself a measured capability rather than an assumption.

---

## 5. Architecture

Rust workspace (edition 2024), single game image, `linux/amd64`:

```
coworld-mtg/
├── PLAN.md
├── Cargo.toml                     # workspace
├── crates/
│   ├── tabletop-core/             # pure state machine: zones, cards, attrs, counters, phases,
│   │                              #   actions → events, per-seat redaction, seeded RNG (rand_chacha),
│   │                              #   event-sourced GameLog; no I/O — fully unit-testable & fuzzable
│   ├── cogatrice-server/          # axum + tokio: COGAME_* lifecycle, /healthz, /player, /global,
│   │                              #   /client/* static assets, replay record/save/load/serve (/replay),
│   │                              #   results writer, chess clocks, episode/match orchestration
│   ├── mtg-cards/                 # embedded card DB (name, mana cost, types, P/T, oracle text,
│   │                              #   scryfall id) + decklist types; build pipeline from Scryfall bulk
│   └── players/                   # baseline bots as ws clients of the public protocol:
│       ├── goldfish/              #   deterministic scripted baseline
│       └── bedrock-baseline/      #   minimal LLM player (InvokeModel, BEDROCK_MODEL env)
├── web/                           # browser clients (vite + TS, kept deliberately light):
│   │                              #   table renderer shared by player/global/replay pages;
│   │                              #   card images lazy-loaded from Scryfall by the *browser*
├── decks/                         # v1 deck lists (checked-in JSON)
├── docs/                          # protocol.md (player + global), rules-of-engagement.md, decks.md
├── compose.yaml                   # game + players services, platform: linux/amd64
├── coworld_manifest_template.json
└── Dockerfile                     # multi-stage: cargo build + vite build → distroless-ish runtime
```

Key design points:

- **Event-sourced core.** Every accepted action becomes an immutable event; game state is a fold over events. The
  replay artifact is the (full-information) event log + seed + config — replay mode just re-serves it through the
  same renderer with tick timestamps; per-seat redaction is a pure view function used identically for live player
  observations, the public global stream, and (unredacted) replay.
- **Protocol** (`protocols.player` in the manifest, JSON text frames):
  - server→player: `hello` (seat, config, decklist), `state` (full redacted snapshot on connect/reconnect — players
    are snapshot-resumable, per nightshift's lesson), `event` deltas (each with actor, action echo, seq),
    `window` (you may act: main window / reaction window / mulligan / clock state), `game_end`, `match_end`.
  - player→server: `{cmd_id, action}` where action ∈ {`draw`, `move_cards` (zone→zone with position/facedown),
    `tap`/`untap`/`set_attr`, `create_token`, `add_counter`/`set_counter` (incl. life), `shuffle`, `roll_die`,
    `reveal` (to opponent/all), `mulligan_keep`/`mulligan_again`, `next_phase`, `next_turn`, `pass`, `say`,
    `point` (arrow), `concede`} — acked/rejected per `cmd_id` (Cockatrice's pairing pattern, JSON-ified).
  - `/global`: public-information event stream + snapshots (drives both the live viewer and standings-agnostic
    spectating).
- **Card data**: build-time script pulls Scryfall bulk `oracle_cards`, filters to the union of shipped decklists,
  embeds compact JSON in `mtg-cards` (a few hundred KB). No card images in the image or repo; browsers fetch art
  from Scryfall at view time with text-frame fallback. (WotC Fan Content Policy / Scryfall guidelines: fine for a
  private research project; don't rehost imagery.)
- **Determinism**: config `seed` drives shuffles/dice/deal order; same seed + same action sequence ⇒ same log
  (property-tested).

## 6. Manifest skeleton (template values)

- `game.name: cogatrice`, owner nishu.builder@gmail.com.
- `config_schema`: requires `tokens` (2..2 for v1) + `players[].name`; options: `seed`, `decks` (per-slot deck id),
  `games_to_win`, `turn_cap`, `clock_s`, `decision_cap_s`, `referee_mode` (`off|advise|enforce`).
- `results_schema`: `scores` (2 numbers) + `games[]` detail (winner, end_reason, turns, final_life, seed).
- `variants`: `duel-precon-r-vs-g` (default), `duel-mirror-red`, certification variant with N=1, 15-turn cap, short
  clocks, `goldfish` vs `bedrock-baseline`.
- `protocols.player` / `protocols.global`: inline text summarizing docs/protocol.md (self-contained, per convention).

## 7. Milestones

| # | Deliverable | Acceptance criteria |
|---|-------------|---------------------|
| M0 | This plan, repo bootstrap | Plan pushed to `nishu-builder/coworld-mtg` (done when you read this) |
| M1 | `tabletop-core` + protocol | Unit/property tests green; two in-process scripted seats complete a seeded game deterministically |
| M2 | `cogatrice-server` container contract | `goldfish` vs `goldfish` over real websockets; `coworld run-episode` completes; `results.json` validates; replay bytes written and reloadable |
| M3 | Browser surfaces | `coworld play` works for player/global/replay; human-vs-goldfish playable; replay autoplays & loops; hidden info verifiably redacted per seat |
| M4 | Baselines + certification | `bedrock-baseline` plays legally-by-construction simple lines; `coworld certify` passes end to end |
| M5 | Upload + hosted verification | `coworld upload-coworld` succeeds; hosted episode runs inside deadline; league-submittable |
| M6 | Adjudication | M6a referee modes shipping in-server; M6b judge grader container scoring compliance from bundles |
| M7 | Stretch: Cockatrice interop | servatrice-protocol adapter so desktop Cockatrice can spectate (then play); `.cod`/`.txt` deck import; more decks/formats; deck-building variant |

Sequencing note: M1+M2 are the critical path and pure Rust; M3 is where taste matters most (table legibility);
M4's LLM baseline doubles as the protocol's usability test — if a minimal prompt+InvokeModel loop can't play, the
protocol needs work before leagues do.

## 8. Risks and mitigations

- **LLM rules fidelity is unknown** → simple v1 card pool; rules-of-engagement doc written for models; referee
  advisories in-band; judge grader makes compliance measurable instead of assumed.
- **20-minute hosted deadline** → deterministic bounds (chess clocks, decision caps, turn cap) enforced by the
  server, tuned in certification fixture; best-of-1 fallback variant.
- **Reaction-window design could deadlock or stall games** → bounded nesting, default-pass on timeout, property tests
  that any action sequence terminates.
- **`coworld certify` checks `source_url` reachability + Dockerfile on GitHub** → repo is private; verify whether the
  certifier's token can read it — if not, options: public mirror of the game source subtree, or org transfer at
  upload time. Flagged as the main packaging unknown; resolve during M4.
- **Scope creep toward a rules engine** → hard line in §1; anything "the server should stop illegal X" routes to
  referee/judge milestones, not the core.
- **Card data/art licensing** → data-only embedding (Scryfall bulk, attributed), browser-side image loading, private
  repo.

## 9. Decision log

- **Reproduce in Rust over wrapping servatrice** — §3. Revisit trigger: M7 interop work discovering semantics we got
  materially wrong, or a hard requirement for desktop-client play appears.
- **Honor-system tabletop over rules enforcement** — §3/§4; the benchmark *wants* the honor system, and enforcement
  is out of reach anyway.
- **JSON protocol over protobuf** — LLM ergonomics and Coworld convention; protobuf compat deferred to M7.
- **40-card simple decks first** — episode time budget and honor-system load; richer pools are variants, not
  rewrites.
- **Name `cogatrice`** — Cockatrice lineage, cog convention.
