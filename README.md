# coworld-mtg

Magic: The Gathering as a [Coworld](https://github.com/metta-AI/coworld): a Rust game named **cogatrice**, packaged
behind the Coworld container contract so LLM agents can play MTG in local episodes, browser play, and hosted leagues
with replays, scoring, and baseline players.

The original Cockatrice-style shared tabletop has been removed in favor of the
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

## Fidelity harness

`cogatrice-harness` runs seeded games directly against `phase-bridge`, records
exact actions, authoritative events, canonical state hashes, and RNG-preserving
checkpoints, then replays every trace as a hard determinism gate. It also
materializes hash-verified Phase/Scryfall/MTGJSON/17Lands artifacts, mines
17Lands only into soft workload signals, resumes deterministic seed shards, and
deduplicates findings into a scoreboard.

See [the harness operations guide](docs/agent-improvement-harness-operations.md)
for corpus, worker, replay, minimization, and aggregation commands.

## Play locally

From the repo root:

```sh
npm install
npm run build
cargo build -p cogatrice-server -p goldfish
mkdir -p tmp/local-play
cat > tmp/local-play/config.json <<'JSON'
{
  "tokens": ["tokA", "tokB"],
  "players": [{"name": "browser-0"}, {"name": "browser-1"}],
  "seed": 4242,
  "decks": ["red_rush", "green_stompy"],
  "games_to_win": 1,
  "clock_s": 360,
  "decision_cap_s": 30,
  "player_connect_timeout_s": 60
}
JSON
COGAME_HOST=127.0.0.1 \
COGAME_PORT=8080 \
COGAME_CONFIG_URI=tmp/local-play/config.json \
COGAME_RESULTS_URI=tmp/local-play/results.json \
COGAME_SAVE_REPLAY_URI=tmp/local-play/replay.json \
COGAME_LOG_URI=tmp/local-play/log.txt \
COGAME_WEB_DIST="$PWD/web/dist" \
cargo run -p cogatrice-server
```

Open these URLs in separate browser profiles (for example, a normal and an
incognito window) to control both seats:

- `http://127.0.0.1:8080/client/player?slot=0&token=tokA`
- `http://127.0.0.1:8080/client/player?slot=1&token=tokB`

To play against the baseline instead, leave the second browser closed and run:

```sh
cargo run -p goldfish -- --url 'ws://127.0.0.1:8080/player?slot=1&token=tokB'
```
