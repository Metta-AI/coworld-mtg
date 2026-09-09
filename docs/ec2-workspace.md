# EC2 workspace

The active software-factory workspace is on `nishadsingh-box-4`:

- Coordinator and viewer: `/home/ubuntu/repos/coworld-factory-20260907-root/repo`.
- Source snapshots, frozen cohort and preserved builds: sibling `data/` and `bin/` directories.
- Live and imported runs: sibling `runs/` directory.
- Isolated Phase repair: `/home/ubuntu/repos/coworld-factory-20260907-phase-fix/repo`.

The read-only factory server listens on remote loopback port 8030. Forward it
with SSH, then open `http://127.0.0.1:18030/client/factory.html`:

```sh
ssh -N -L 18030:127.0.0.1:8030 nishadsingh-box-4
```

Check `~/.local/bin/codex-claim status` before remote work. Use an independently
reserved clone and output directory for new experiments. The active workspace
and port remain reserved while the viewer runs; existing experiment records
must remain immutable.

The macOS checkout is a migration backup. Builds and experiments run on EC2 with
an isolated Cargo target, one build job, disabled incremental compilation and
debug information, and explicit memory limits. See
[software-factory.md](software-factory.md) for commands and replay verification.

## Current fitting run

The completed recording is
`/home/ubuntu/repos/coworld-factory-20260907-root/runs/17lands-trajectories-20260909-01`.
The viewer uses the root workspace's `viewer-dist-20260909` directory. Its native
candidate worker and build receipt remain in
`data/fitting-trace-build-b5d1e6/`; the matching runtime manifest remains at
`/home/ubuntu/repos/coworld-factory-20260908-guided-fit-runtime/inputs/manifest.json`.
These are retained inputs, not authorization to edit another task's workspace.

The [public replay](../replays/17lands-trajectories-20260909-01/README.md) can be
verified and inspected without the private corpus. Re-executing the engine needs
the exact manifest's full pinned export and a matching retained or rebuilt worker.
No fitting workers are left running.

## Earlier experiment

The fixed-input experiment remains at `/home/ubuntu/repos/coworld-mtg`, branch
`codex/verifiable-improvement-loop`, with its engine checkout at
`/home/ubuntu/repos/phase-verifiable-loop`. The historical publication checkouts
are `/home/ubuntu/repos/coworld-mtg-publish` and
`/home/ubuntu/repos/phase-hushbringer-publish`. They preserve the original accepted
comparison and are read-only inputs to the newer experiment.

The migration verified 3,902 source/evidence files by SHA-256 and preserved
Git bundles and the original generated client checkout's history. Migration
receipts, planning/review artifacts and logs live under
`/home/ubuntu/coworld-migration-20260904`. Local cleanup reclaimed
12,964,511,744 bytes from verified migrated evidence and generated files.
Shared local Cargo/Rust caches and the original Phase repository were retained.

The authored card cases and focused corpus live in `cases/`. Full worker
executables and source snapshots live in `tmp/verifiable-loop/` on EC2.
Accepted portable evidence, generated notes and the blog attribution index
live in `cases/evidence/`; they omit large executable and dependency caches.
See [verifiable-cases.md](verifiable-cases.md) for reproducing the loop.
