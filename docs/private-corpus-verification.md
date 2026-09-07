# Private corpus publication checks

Run these checks in the validation task's owned EC2 checkout, after acquiring
`heavy-compute` and the explicit test port. Keep temporary files, Cargo output,
client checkout, installed corpus and browser reports inside that workspace.
Run native and browser tests sequentially. The examples use the root task's
existing workspace and port 8031; recheck listeners and claim status first.
Port 8030 belongs to the live factory viewer and is not part of this validation.

```sh
~/.local/bin/codex-claim status
uptime
free -h
df -h /home/ubuntu/repos
ss -ltnp
~/.local/bin/codex-claim acquire \
  --owner coworld-factory-20260907-01a06e9f-root \
  --note "Serial private corpus native and Phase client validation" \
  --resource heavy-compute --resource port:8031
```

Wait for the Draw executor to release compute before acquiring. Save the returned
token in the task's private notes. The root workspace already has its own claim;
a different task must acquire its own workspace before creating files.

The September 7 minimal closure contains 50 card-face entries and 46 distinct
Oracle IDs. It preserves the exact bytes of both original 40-card decks and adds
the four required Prepare spell faces. The committed lock may still name the
old 46-entry archive during review. Use both lock and URI overrides when checking
the proposed local artifact; changing only the URI still verifies the old hash.

```sh
cd /home/ubuntu/repos/coworld-factory-20260907-root/repo
export COWORLD_MTG_CORPUS_LOCK=/home/ubuntu/repos/coworld-factory-20260907-root/data/minimal-corpus-closure-01/proposed-corpus.lock.json
export COWORLD_MTG_CORPUS_URI=/home/ubuntu/repos/coworld-factory-20260907-root/data/minimal-corpus-closure-01/minimal-closure-1.tar.zst
scripts/fetch-corpus.sh
```

That archive is `dfb96d582fc0f03cbc00e8837e4d1dcac42bb3cef6c715677ea446bed1be9099`
and its card payload is
`2ff4dca758e8e642bcae4115a01e1e3c9d1c4f561ef505d855064c57171ee092`.
The fetcher validates the archive and every manifest member. If this exact
artifact is already installed and verified, do not fetch it again.

A resource claim is a scheduling reservation, not a memory cap. Use one Cargo
build job, one Rust test thread, and one Playwright worker; cap Node's heap at
4 GiB and leave at least 12 GiB available for the native compiler and browser.
The inspected host had 29 GiB available RAM and 26 GiB free disk. Recheck actual
capacity before execution, especially while another task builds Phase.

```sh
mkdir -p /home/ubuntu/repos/coworld-factory-20260907-root/.task-private/corpus-app-validation/tmp
export TMPDIR=/home/ubuntu/repos/coworld-factory-20260907-root/.task-private/corpus-app-validation/tmp
export CARGO_TARGET_DIR=/home/ubuntu/repos/coworld-factory-20260907-root/target
export CARGO_BUILD_JOBS=1
export CARGO_INCREMENTAL=0
export CARGO_PROFILE_DEV_DEBUG=0
export CARGO_PROFILE_TEST_DEBUG=0
export RUST_TEST_THREADS=1
export RUST_MIN_STACK=33554432
export COWORLD_TEST_BIND=127.0.0.1
export COWORLD_TEST_PORT=8031
export NODE_OPTIONS=--max-old-space-size=4096
export npm_config_store_dir=/home/ubuntu/repos/coworld-factory-20260907-root/.task-private/corpus-app-validation/pnpm-store
export npm_config_child_concurrency=1
```

`COWORLD_TEST_BIND` and `COWORLD_TEST_PORT` affect the Rust episode tests and both
app browser suites only. The bind address must be IPv4 loopback. When a port is
specified, it must be nonzero and already reserved by the task. Without an
override, ordinary isolated CI keeps its existing ephemeral-port behavior.
Both browser suites honor `CARGO_TARGET_DIR` when locating server binaries.

Build the actual Phase client once. The standalone factory viewer distribution
is not sufficient for this check: its player entry is the legacy interface.
The client build script creates an owned checkout at
`repo/tmp/phase-client-54227f4527a0b45b01eb3f819d262ee49b665810`, copies the
Coworld adapter, applies the replay-player-name patch, installs with pinned
`pnpm@10.28.2 --frozen-lockfile`, and writes into `repo/web/dist`. Its Wasm aliases
are stubs because the server owns the engine; no Wasm engine build is required.

```sh
npm ci
npm run build:legacy
PHASE_CLIENT_SKIP_TESTS=1 bash scripts/build-phase-client.sh
scripts/cargo.sh test --workspace --locked --features private-corpus-tests -- --test-threads=1
./node_modules/.bin/playwright test -c web/playwright.config.ts web/e2e/browser-smoke.spec.ts --workers=1
```

Skip `npm ci` when an owned install already matches the lock. Do not use
`npm run test:e2e` after the explicit builds: it repeats both client builds and
runs unrelated factory and screenshot suites. The browser smoke's `beforeAll`
performs a cached server build with the same Cargo target and settings.
For client adapter changes, additionally run `npm run test:phase`; a corpus-only
update does not require repeating those unchanged adapter tests.

Useful retained caches on the inspected box are the root task's 3.8 GiB Cargo
target at `/home/ubuntu/repos/coworld-factory-20260907-root/target`, the read-only
pinned source at `/home/ubuntu/.cargo/git/checkouts/phase-99151a824d73ac02/54227f4`,
and Chromium under `/home/ubuntu/.cache/ms-playwright/`. Reuse the owned Cargo
target; never mutate the shared source checkout or the Draw executor's checkout.
A separate validation task must use its own target/output directories.

The native checks cover:

- 50 loaded entries, 46 distinct Oracle IDs, and the unchanged 45 missing IDs in
  the deliberately one-card Scryfall cross-check fixture.
- Exact original deck hashes and 40-card deck sizes.
- Hydration of Emeritus of Abundance → Regrowth, Emeritus of Truce → Swords to
  Plowshares, Kirol, History Buff → Pack a Punch, and Strife Scholar → Awaken the Ages.
- Casting the real Emeritus of Abundance from hand, becoming prepared through
  entry replacement processing, casting its Regrowth copy with a real Forest
  target, consuming prepared state, and returning Forest from graveyard to hand.
  No debug action marks the creature prepared and no card text is fabricated.
- Seeded games, replay/checkpoint determinism, hidden information, both deck
  assignments, timeout handling and the seed-318 shared-resource regression.

The app browser smoke loads both real decks with seed 5151, renders both Phase
seats, keeps both opening hands, checks hidden opponent cards, and submits a
Phase-stop preference through the server. It does not claim browser coverage
of Prepare casting. That production action sequence is asserted by the native
private-corpus test above. Scryfall card artwork and the Phase client metadata
URLs remain external browser dependencies; distinguish network/artwork failures
from corpus-load or engine-action failures in the retained test report.

Preserve test output, server logs and temporary episode replays under the owned
workspace. Record actual results against the exact installed payload and source
revision before publication. Stop owned processes and release the test port and
compute reservation after validation.
