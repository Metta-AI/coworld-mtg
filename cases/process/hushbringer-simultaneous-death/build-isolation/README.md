# Build isolation from the Hushbringer investigation

An active Phase integration compile saw a baseline ZoneChangeRecord without
the newly added suppression field after the two checkouts had shared a Cargo
target directory. The active source still declared the field. The
[retained compiler log](stale-artifact-compile.log) records the rejected build;
no field assertion was removed to make it compile.

Phase verification now uses distinct active, baseline and mutation target
directories. The Coworld worker builder receives the same correction:
each invocation builds into its own output/target, preventing one checkout's
artifacts from being reused by another invocation.

The [manifest](manifest.json) binds the before/after builder and the failure
log to the originating case. This is an improvement to the verification
workflow, with its own provenance. It does not repair Magic rules.

The original checker executable, case, corpus and acceptance plan remain
unchanged. Both baseline and candidate workers must be rebuilt with the same
revised builder and reevaluated by that preserved checker. Earlier binaries
and receipts remain available; they are not relabeled as the rebuilt workers.
