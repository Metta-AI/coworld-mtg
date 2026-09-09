# coworld-mtg

Magic: The Gathering as a [Coworld](https://github.com/metta-AI/coworld): a Rust game named **coworld-mtg**, packaged
behind the Coworld container contract so LLM agents can play MTG in local episodes, browser play, and hosted leagues
with replays, scoring, and baseline players.

The development goal is to improve that engine from recorded play: turn partial
17Lands observations into executable compatibility checks, discover obstacles,
and retain the evidence behind each repair. See the
[recorded-game discovery plan](docs/17lands-discovery-plan.md).

The original shared-tabletop prototype has been removed in favor of the
pinned, Rust-native [Phase](https://github.com/phase-rs/phase)
rules engine so that mana, casting, priority, the stack, combat, triggers,
replacements, layers, and state-based actions are engine-enforced. See
[the Phase port contract](docs/phase-rules-port.md) for the decision, Scryfall
boundary and invariants.

Browser player, spectator, and current replay routes use the React client from
that same pinned Phase revision. This repository adds only a thin Coworld
transport/replay adapter and series chrome; the former local renderer is built
only to keep version-2 Coworld replays readable. See the
[client migration spec](docs/specs/0001-phase-client-for-coworld.md).

The game views in `web/` are compatibility code for version-2 replays. New
player, spectator, and game-replay work belongs in `phase-client/`.
The independent software-factory viewer lives in `web/src/factory/`.

## Development checks

Rust commands should run through `scripts/cargo.sh`; it selects the toolchain
in `rust-toolchain.toml` even when another `cargo` or `rustc` appears earlier on
`PATH`. Run the complete local/CI gate with:

```sh
scripts/check.sh
```

Generated Rust and frontend output can consume many gigabytes. Preview guarded
cleanup with `scripts/clean-generated.sh --all`; add `--execute` only after
reviewing the resolved paths and sizes it prints.

## Discovering issues from recorded games

We are building a loop that starts with actual 17Lands games and asks whether
Phase can reproduce the recorded play. The data leaves out some actions and
hidden state, so the harness must search for a legal trajectory compatible with
the observations. Unsupported cards and failed fits become issue candidates for
a separate diagnosis and fixing process.

~~~mermaid
flowchart TD
  G[17Lands recorded game] --> I[Resolve card identities]
  I --> C[Check known engine support gaps]
  I --> O[Build ordered observation milestones]
  C --> Q[Issue candidates with source evidence]
  O --> S[Search for compatible Phase trajectories]
  S --> W[Matched prefix or game with witness]
  S --> Q
  Q --> D[Separate diagnosis and fixing process]
  D --> R[Regression, patch and reviewed evaluation]
  R --> G
~~~

The observations supply the initial checks. We should not have to choose a card
rule and write its expected result before discovering a problem. Diagnosis may
then require card rules, rulings or additional experiments. An issue can belong
to the engine, card definitions, data mapping, observation adapter or search.
Running out of search budget creates an investigation candidate; it does not
establish an engine bug.

**[The active plan](docs/17lands-discovery-plan.md)** describes the typed
boundaries, outcome meanings, implementation milestones and checks. The bounded
pipeline now freezes real game cohorts, runs supervised fitting, groups discovered
issues and links repair proposals back to every originating game.
[Run and inspect it](docs/17lands-factory.md).

The fitting viewer puts the recorded observations beside the engine's projected
states, shows the retained path and failure context, and keeps unchecked fields
visible. A before/after comparison reports changed observations and reconstruction;
it does not turn a partial match or a disappearing diagnostic into an acceptance
decision.

## What works today and what is being built

| Part | Current state |
| --- | --- |
| Seeded engine exploration and deterministic replay | Implemented: exact legal actions, events, state hashes, checkpoints and invariant checks. |
| Public 17Lands ingestion | Implemented: official CSV normalization and card-ID mapping with source provenance. The accepted coverage run repaired this layer. |
| Recorded-game trajectory fitting | Implemented legal-action search with backtracking and typed observation/state traces. The frozen first-20-game SOS workload covers two turns from each player; full-game coverage remains in progress. |
| Card support preflight | Current fitting checks names and setup. Complete card-effect support and token/face identity checks remain planned. |
| Regression cases and repair evaluation | Implemented typed case execution, checking, reduction and reviewed acceptance, orchestrated by agents. |
| Factory replays and viewer | Fitting runs now record source-derived cases, actual executions, grouped issue origins, field comparisons and separately attributed repair proposals/comparisons. Earlier ingestion/parsing replays remain available. |

A concrete fault in the older fitter illustrates the work ahead: it combined
“opponent has seven cards after my first turn” and “opponent has six cards after
their first turn” into requirements on one state. That game stopped earlier on
unresolved card IDs; inspecting its extracted requirements exposed the
contradiction. The old run therefore cannot tell us how difficult correctly
specified fitting will be. The active plan also covers missing identity mappings, unnecessary mulligan search and
retaining alternative paths across observations.

The [first fitting measurements](docs/artifacts/17lands-guided-fit-20260908/README.md)
retain three repeated opening-turn examples. The larger
[frozen cohort](fixtures/17lands/sos-cohort-20/README.md) includes all first 20
records without filtering on fitting results. The [recorded before/after run](replays/17lands-trajectories-20260909-01/README.md)
ran all 20 games against each worker. Both found eight supported projection
matches, nine unsupported mulligan reconstructions, two worker deadlines and one
unsupported boundary. The candidate adds inspectable state/action traces; it
does not change these outcomes or increase observation coverage. Even the matches
have zero fully covered milestones. These records were previously inspected and
are not unseen holdouts.

Combat-damage, mana-spent and ability observations remain unchecked where their
source semantics or engine bindings are unestablished. In particular, the raw
source contains negative combat-damage values; a native damage-event total cannot
simply be assumed to represent that column. The replay preserves the observations
and the separate diagnosis behind this limitation.

Seeded exploration remains useful alongside recorded-game fitting. It checks
properties such as deterministic replay and whether advertised actions execute
successfully. Recorded games add external evidence about behavior that exploring
only the engine's own offered actions can miss.

## Harness and evidence tools

See [the harness operations guide](docs/agent-improvement-harness-operations.md)
for corpus, worker, replay, minimization and aggregation commands.
The [verifiable case loop](docs/verifiable-cases.md) describes typed scenarios and
repair acceptance. The [software factory](docs/software-factory.md) describes
the shared recording protocol and viewer; Rust types generate its JSON Schemas
and architecture diagrams.

[Published replays](replays/README.md) retain sources, executions, feedback and
changes so that improvements can be traced back to their originating cases.
Earlier [case notes](cases/evidence/README.md) and article drafts describe
individual experiments; use the active plan for the current direction.
The active workspace and preserved builds are on [EC2](docs/ec2-workspace.md).

## Private runtime corpus

The generated Phase card database and 17Lands-derived deck lists are not distributed in this public repository.
Authorized Softmax builds fetch the content-addressed private corpus pinned by `corpus.lock.json`:

```sh
scripts/fetch-corpus.sh
```

This materializes `.private/corpus`, verifies the archive and every contained file by SHA-256, and leaves all corpus
content gitignored. Docker builds require that materialized directory. Public source builds remain available without
it; run tests requiring real card data with
`scripts/cargo.sh test --workspace --features private-corpus-tests`.

## Play locally

From the repo root:

```sh
npm install
npm run build
scripts/fetch-corpus.sh
scripts/cargo.sh build -p coworld-mtg-server -p goldfish
mkdir -p tmp/local-play
cat > tmp/local-play/config.json <<'JSON'
{
  "tokens": ["tokA", "tokB"],
  "players": [{"name": "browser-0"}, {"name": "browser-1"}],
  "seed": 4242,
  "decks": ["lorehold_excavation", "fractal_convergence"],
  "games_to_win": 1,
  "clock_s": 360,
  "decision_cap_s": 30,
  "player_connect_timeout_s": 60
}
JSON
COGAME_HOST=127.0.0.1 \
COGAME_PORT=8080 \
COGAME_CORPUS_DIR="$PWD/.private/corpus" \
COGAME_CONFIG_URI=tmp/local-play/config.json \
COGAME_RESULTS_URI=tmp/local-play/results.json \
COGAME_SAVE_REPLAY_URI=tmp/local-play/replay.json \
COGAME_LOG_URI=tmp/local-play/log.txt \
COGAME_WEB_DIST="$PWD/web/dist" \
scripts/cargo.sh run -p coworld-mtg-server
```

Open these URLs in separate browser profiles (for example, a normal and an
incognito window) to control both seats:

- `http://127.0.0.1:8080/client/player?slot=0&token=tokA`
- `http://127.0.0.1:8080/client/player?slot=1&token=tokB`

To play against the baseline instead, leave the second browser closed and run:

```sh
scripts/cargo.sh run -p goldfish -- --url 'ws://127.0.0.1:8080/player?slot=1&token=tokB'
```

The supplied decks are real 40-card `SOS.PremierDraft` lists captured from MTG
Arena play data by 17Lands and supplied through the private runtime corpus.
Published play consists of two single-game variants with deck assignments
reversed, so each challenger pilots Lorehold Excavation and Fractal Convergence
once. Published variants omit `seed`, which generates a fresh root seed when
the episode config is loaded. Supply `seed` explicitly, as
in the local example above, to reproduce the exact initial library orders and
all later random outcomes.
