# Recorded factory runs

These directories preserve replay manifests and content-addressed evidence.
Open them with the factory viewer; the manifest is the record, and the viewer
explains its events and relationships.

| Run | Recorded outcome |
| --- | --- |
| `scryfall-mana-20260907` | Failed during preparation when real source numbers reached an integer-only metadata encoder. No target program ran. |
| `scryfall-mana-20260907-02` | Actual Scryfall development baseline: 41 cases, 82 executions, eight violations, six satisfied controls and 27 inconclusive results. Cancelled before a candidate to make native false classifications explicit at the measurement boundary. |
| `imported-hushbringer-simultaneous-death` | Earlier authored case imported from retained evidence, with its original acceptance identity. Event order is reconstructed from dependencies; elapsed time is unknown. |

The live replacement experiment is recorded separately while its engine repair
is being developed and independently reviewed. Its acceptance claim is
limited to the frozen source-qualified classification grammar. Four holdouts
test genuine-mana controls; there are no qualified library-moving holdouts.

The full Wizards rules document stays at its recorded source URL. Its exact
hash and URL are in each applicable `external-artifacts.json`. Hydrate it before
verifying or exporting the complete run:

~~~sh
python3 scripts/share_factory_replay.py hydrate replays/scryfall-mana-20260907-02 \
  --runtime target/debug/factory-runtime
target/debug/factory-runtime verify replays/scryfall-mana-20260907-02
target/debug/factory-runtime serve --root replays --web-dist web/dist \
  --bind 127.0.0.1:8030
~~~

Open `/client/factory.html`, choose a run, and use **Save portable** for a complete
UTF-8 replay bundle. Missing or mismatched artifacts block portable export.

For the cancelled Scryfall baseline, the installed domain evaluator can also
recompute the recorded feedback:

~~~sh
python3 scripts/scryfall_factory.py verify \
  --run-dir replays/scryfall-mana-20260907-02 \
  --runtime target/debug/factory-runtime
~~~

The [factory guide](../docs/software-factory.md) describes the source population,
frozen expectations, worker/build identities, external-policy trust boundary,
and commands for creating another run. Executables and the full Scryfall bulk
archive remain separately retained inputs identified by hashes in these records.
