# Coworld's CAOS factory

Start with [the architecture and run contract](../docs/caos-factory.md) and
[the measured pilot](../replays/caos-factory-20260920/README.md).

The host freezes inputs and submits one request. The controller schedules the
entire improvement epoch through native CAOS continuations and bounded maps.

| File | Responsibility |
| --- | --- |
| `lib/factory.py` | Continuations, planning budget, candidate attempt and terminal decision |
| `lib/cas.py` | Git-backed values, linked receipts, narrow worker closures and native scheduling |
| `lib/contracts.py` | Strict budget, proposal, review and edit contracts |
| `lib/mtg.py` | Source verification, case derivation, native fitting and issue origins |
| `lib/build.py` | Pinned dependency acquisition, offline builds and tests |
| `lib/agents.py` | Bounded role contexts, proposals, reviews and validation feedback |
| `lib/evaluate.py` | Allowed edits and the frozen comparison gate |
| `llm_call.py` | One scoped, metered provider call |
| `prepare.py` / `submit.py` | Input snapshot and one root submission |
| `export.py` / `viewer.html` | Public projection of actual receipts and game states |

No Python packages are required for the factory itself. Run the boundary suite:

```sh
python3 -B -m unittest discover -s caos-factory/tests -v
```

The native integration test uses `tests/noop_contributor.py` as a CAOS model-call
capability. It deliberately approves a comment-only candidate. The full pipeline
must return `rejected`, with build/tests passed and zero improved cases.
This test contributor must never be reported as a real model repair.

The provider interface is itself a CAOS value: `submit.py --contributor <id>`
accepts an already prepared model-call capability in place of `--key-file`.
That supports another provider or the explicit integration fixture without
changing scheduling, receipts, edit authority or acceptance policy.
