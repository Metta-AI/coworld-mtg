# Harness integration with current main

The publication checkout merged the implemented loop with Coworld main
2eaf798, preserving the existing 0.1.12 release and newer Phase pin b5f468588.
The sole conflict was resolved by keeping that pin and the new loop-contract
dependency. The original fixed-input repair experiment remains on its preserved
source and checker.

The repository check script completed successfully: Phase pin, formatting,
workspace Clippy, Rust tests, generated schemas/catalog, Python/shell checks,
frontend type checking/tests and both frontend builds. This checkout had no
private corpus, so the script's optional private-corpus and browser checks
were not run. Its separate target used one build job, no debug information
and no incremental compilation; these settings do not replace the fixed
repair experiment's builder or workers.

A new ten-case campaign against the integrated main pin produced nine satisfied
cases and the same Hushbringer violation, all repeatable and none inconclusive.
The campaign's exit1 records that expected known violation. It is not a failure
of the harness integration or acceptance of the uncommitted engine repair.
Full case/evaluation artifacts and complete compressed check logs are retained.
