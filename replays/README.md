# Recorded factory runs

These directories preserve replay manifests and content-addressed evidence.
Open them with the factory viewer; the manifest is the record, and the viewer
explains its events and relationships. Start with the [checkpoint handoff](../docs/handoff-2026-09-07.md)
for a plain-language explanation of the current page and the three separate results.

| Run | Recorded outcome |
| --- | --- |
| [17lands-coverage-20260907-03](17lands-coverage-20260907-03/replay.json) | Accepted native CSV source-coverage repair after independent review: 73 events, 95 artifacts, 14 executions. Primary, regression and new-row holdout gates satisfied. |
| [scryfall-mana-20260907-03](scryfall-mana-20260907-03/replay.json) | Rejected Draw candidate; recording complete. 57 candidate cases: 16 satisfied, two Mill violations, 39 inconclusive. Reviewed Draw partial published separately; Coworld runtime pin unchanged. |
| [17lands-observed-cards-20260908-01](17lands-observed-cards-20260908-01/replay.json) | Imported discovery from 230 observed Arena IDs and 436 retained executions: 214 parsed cards, four Saga adapter limits, 12 mapping gaps. Weak feedback only; no acceptance decision. |
| `scryfall-mana-20260907` | Failed during preparation when real source numbers reached an integer-only metadata encoder. No target program ran. |
| `scryfall-mana-20260907-02` | Actual Scryfall development baseline: 41 cases, 82 executions, eight violations, six satisfied controls and 27 inconclusive results. Cancelled before a candidate to make native false classifications explicit at the measurement boundary. |
| `imported-hushbringer-simultaneous-death` | Earlier authored case imported from retained evidence, with its original acceptance identity. Event order is reconstructed from dependencies; elapsed time is unknown. |

The [17Lands decision](17lands-coverage-20260907-03/artifacts/15f6bba8dafa697ec5245ebf2d9a36b7ef92a67515bc46355a04794370d9b31e)
accepts preservation of listed casts and official Arena mappings in the frozen
source partitions. Primary rows 1–46 contain 679 casts, regression rows 47–92
contain 747, and new holdout rows 93–108 contain 276. The 92-row aggregate contains
1,426 casts and overlaps both known partitions; it is informational, not a fourth
independent gate. Baseline ran primary, regression and aggregate twice; candidate
ran all four cases twice. No holdout baseline is claimed.

The holdout was selected from newly acquired complete rows of the same archive
before candidate observations, under the operator's non-exposure attestation.
This checks ingestion of those new rows, not a complete game replay, unseen
formats or rules correctness. The retained [independent review](17lands-coverage-20260907-03/artifacts/228cb35173efe3bba8fcc4bbfe62a843ddfc79eae4767a082e82e96b61f66a1b)
states the source, build and review trust boundaries. Two malformed source-only
preparation drafts remain private failed-preparation evidence, identified by a
diagnostic in the valid run.

The replacement Scryfall experiment is now closed at a rejected decision. Its
reviewed Draw partial fixes six motivating cases, while Deranged Assistant and
Millikin still violate the frozen classification policy. Four holdouts test
genuine-mana controls; there are no qualified library-moving holdouts. The
[checkpoint source note](scryfall-mana-20260907-03/artifacts/14be9612edd16e864d03d5b8b3bee9d45ce9f1ea967bb654841e7f75e4f17bba)
records publication and remaining work. Completion of recording does not imply acceptance.

The observed-card discovery is a separate imported recording. Its logical event
order was reconstructed from retained executions; event elapsed times are unknown.
Its source linkage, raw observations, structural feedback and exact import recipe
are preserved. Parsing success is not a gameplay correctness verdict.

The accepted 17Lands importer result is separate from both investigations.

The full Wizards rules document stays at its recorded source URL. Its exact
hash and URL are in each applicable `external-artifacts.json`. Hydrate it before
verifying or exporting the complete run:

~~~sh
python3 scripts/share_factory_replay.py hydrate replays/scryfall-mana-20260907-03 \
  --runtime target/debug/factory-runtime
target/debug/factory-runtime verify replays/scryfall-mana-20260907-03
target/debug/factory-runtime serve --root replays --web-dist web/dist \
  --bind 127.0.0.1:8030
~~~

Open `/client/factory.html`, choose a run, and use **Save portable** for a complete
UTF-8 replay bundle. Missing or mismatched artifacts block portable export.

The installed 17Lands domain evaluator and adapter must match the hashes frozen
in the run. Recompute the accepted coverage policy with:

~~~sh
python3 scripts/seventeenlands_factory.py verify \
  --run-dir replays/17lands-coverage-20260907-03 \
  --runtime target/debug/factory-runtime
~~~

The public package includes bounded MSH wide-replay CSV slices and the official
Arena mapping, attributed to [17Lands public datasets](https://www.17lands.com/public_datasets)
under CC BY 4.0. Slicing and partitioning are recorded modifications; 17Lands does
not endorse this work. Compressed-prefix hashes describe the retained prefixes,
not the full archive. The private runtime corpus and deck data remain private.

For the completed Scryfall experiment, its installed domain evaluator can also
recompute the recorded feedback:

~~~sh
python3 scripts/scryfall_factory.py verify \
  --run-dir replays/scryfall-mana-20260907-03 \
  --runtime target/debug/factory-runtime
~~~

The [factory guide](../docs/software-factory.md) describes the source population,
frozen expectations, worker/build identities, external-policy trust boundary,
and commands for creating another run. Executables and the full Scryfall bulk
archive remain separately retained inputs identified by hashes in these records.
