# Accepted fixed-checker comparison

The actual clean committed repair, fa0ebfe88db224ebd32624bb96ef033d338c2d8c,
was compiled in a fresh isolated worker build. Its worker digest is
f5b0de9436da31a00aaf7a1d28b92bd4288bd47077412970e0c3585f0cce1784.
The compiler, builder, relevant flags and all 39 harness source files match
the preserved original worker. All 206 compiler artifacts were newly built.

One preserved checker evaluated both workers with the original plan and corpus.
The baseline passes nine cases and violates Hushbringer simultaneous death;
the candidate passes all ten. The independent acceptance reviewer reverified
all twenty bundles, forty retained executions and every guard, then separately
ran both object orders and the no-Hushbringer control twice on the final worker.

The [bound approval](artifacts/hushbringer-final-comparison/review-approved.json)
and [complete review](artifacts/hushbringer-acceptance-review/acceptance-review.json)
authorize the exact plan and receipts. Root ran the recorded acceptance command
successfully. The [accepted bundle](../../../evidence/hushbringer-simultaneous-death/case-note.md)
contains the automatically generated attribution and case note, source patch,
build records, review and before/after/regression/holdout evidence.
The completion receipt was written last.

The [manifest](manifest.json) preserves the original comparison, build logs,
independent review and actual acceptance execution. Runtime binaries and full
build directories remain on EC2; archived source patches and build identities
do not relabel a future reconstruction as this original execution.

This acceptance covers the fixed experiment. Integration with newer Phase
commits and the production dependency/corpus update are separately verified.
