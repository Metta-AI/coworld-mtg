# coworld-mtg

Magic: The Gathering as a [Coworld](https://github.com/metta-AI/coworld): a Rust reimplementation of the
[Cockatrice](https://cockatrice.github.io/)-style shared tabletop (game name: **cogatrice**), packaged behind the
Coworld container contract so LLM agents can play MTG in local episodes, browser play, and hosted leagues — with
replays, scoring, and baseline players.

Status: planning. Read [PLAN.md](PLAN.md) — it covers the wrap-vs-reproduce decision, architecture, the
honor-system benchmark design, milestones, and risks.

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
  "players": [{"name": "browser-0"}, {"name": "goldfish-1"}],
  "seed": 4242,
  "decks": ["red_rush", "green_stompy"],
  "games_to_win": 1,
  "starting_life": 20,
  "turn_cap": 25,
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

In a second terminal:

```sh
cargo run -p goldfish -- --url 'ws://127.0.0.1:8080/player?slot=1&token=tokB'
```

Open `http://127.0.0.1:8080/client/player?slot=0&token=tokA` in a browser.
