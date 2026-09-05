# Nine trigger-matcher mutation checks

These records cover nine exact production mutations against the frozen v9
source. All nine caused the designated public runtime assertions to fail.
Fourteen exact failing invocations and one independent passing control were
observed; every baseline and restoration also passed the full 91-check matrix
with 20 explicitly retained ignored diagnostics.

The [report](report.md) explains the named assertions, runtime context and
limits. Each mutant was freshly compiled. Baseline and restoration checks
explicitly reuse a preserved freshly built canonical executable, after exact
source restoration and runtime-input verification. They do not claim a fresh
restoration compilation.

Two batching mutations were held for the later v10 fixture snapshot and are
not counted here. Setup failures remain in the source artifact directory and
are not counted as semantic discrimination or repair approval.

The archive keeps receipts, exact mutation patches and complete compressed
logs. Large executables and full source/runtime archives remain on EC2;
[archive-manifest.json](archive-manifest.json) identifies them by path and hash.
All files in the agent's original manifest were rehashed before archiving.
