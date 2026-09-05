# EC2 workspace

The active checkout is on `nishadsingh-box-4` at
`/home/ubuntu/repos/coworld-mtg`, branch `codex/verifiable-improvement-loop`.
The engine repair checkout is `/home/ubuntu/repos/phase-verifiable-loop`.
The macOS checkout is a migration backup; run builds and experiments on EC2.

```sh
ssh nishadsingh-box-4
cd /home/ubuntu/repos/coworld-mtg
export PATH=/home/ubuntu/.cargo/bin:$PATH
export CARGO_BUILD_JOBS=1
scripts/check.sh
```

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
