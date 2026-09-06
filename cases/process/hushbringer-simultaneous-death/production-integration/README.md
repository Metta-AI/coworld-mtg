# Publishing the accepted repair

The [fixed-checker acceptance](../../../evidence/hushbringer-simultaneous-death/case-note.md)
is preserved unchanged. This archive records the separate integration of that
repair into newer Phase main and the application checks for the resulting pin.

Phase revision: 54227f4527a0b45b01eb3f819d262ee49b665810. Coworld pin commit: 86ac6bc82bd8440846a6be3f5f7f761d6c66d04f.
The automatic merge preserves both parents, with no manual source resolutions.
The independent integration review and complete parent-preservation audit are
in phase-review/. Engine workspace/all-target Clippy, formatting, the full
engine suite (19,783 passing tests), and card generation passed.
The generator validated 35,802 indexed card records and 2,870 token presets.
Its two modified tracked generated inputs were restored to their reviewed bytes with fresh
writes; the final source manifest matches the reviewed merge.

Coworld's scripts/check.sh passed with the matching private runtime corpus.
It includes Rust workspace/private-corpus tests, contract and evidence-catalog
checks, Python tests, both frontend suites/builds, and both browser tests.
The separate production campaign passes all ten cases on repeated execution.
Its checker/worker identity is recorded in summary.json and every bundle.
It is a production health check, not a replacement for the original frozen
baseline/candidate experiment.

The new content-addressed private archive has a matching runtime revision.
Its 46 serialized card records and both deck payloads are byte-identical to
the previous corpus; compatibility is exercised by the runtime and browser
checks. This is not represented as a fresh parser export. The uploaded archive
was read back and SHA-256 verified. Private payloads remain outside Git.

The [artifact manifest](manifest.json) binds every copied receipt, log, review,
source identity and campaign bundle to its original EC2 location. Named
unsupported behaviors and ignored diagnostic tests retain their earlier scope.
