# Twenty real games through the fitting factory

This recording starts from the first 20 complete SOS games in the public
17Lands archive. It runs the native fitter against the same observations before
and after an explanatory-trace change. The patch is attributed to actual
baseline issue groups; no card-specific expected outcome was supplied to discover
those groups.

The checked horizon is two turns from each player, with a fixed reconstructed
hidden setup. This is the first bounded connection of game observations, legal
trajectory search, source-linked issues, a separate proposed change and measured
comparison. Full games, mulligans and comprehensive card-effect support remain
unfinished.

## Open the evidence

Serve the repository's replays directory with the factory viewer, then open:

    /client/factory.html?run=17lands-trajectories-20260909-01

A focused visual DAG for source row 8 is available on that same server:

    /client/case-flow.html?run=17lands-trajectories-20260909-01

Use Play to walk through the evidence dependencies, or select any node. The
detailed trace comes from the candidate rerun; playback does not re-execute the
engine or reconstruct missing search states.

Select source row 8 for the boundary obstacle, row 1 for a partial match, row 0
for unsupported mulligan reconstruction, or row 6 for a worker deadline. Choose
the candidate report to inspect typed traces; the baseline predates those traces.
The exact files remain usable without the viewer:

- [Replay manifest](replay.json)
- [Baseline report](artifacts/5ea2ba333bf885c7fea32ec5b8cb27223639ec5a7641dae81b4e33c37a242551)
- [Candidate report](artifacts/413faa9eff65009754ef307562bdceb8016ea47f36dde065c1ef4931c53b630b)
- [Mechanical comparison](artifacts/188bb412b86a7d6a0900ecb044c1c43575ec6beb533ead14dbdcb4930ed072ee)
- [Independent before/after reconciliation](artifacts/5cabf5cf995abf0e3968a097898bbc8c78bc17a22a8f7c60bd1310e7cc05530f)
- [Exact proposed patch](artifacts/7c3366bd0c119ccf983394bf9cb4a5f1a5eaab9b294417b817661ed9523978aa)

## What happened

| Result | Baseline | Candidate |
| --- | ---: | ---: |
| Matched supported projections | 8 | 8 |
| Unsupported mulligan input | 9 | 9 |
| Unsupported observation boundary | 1 | 1 |
| External 60-second deadline | 2 | 2 |

Each worker attempted every game. Both retained 20 constraint files and 18 native
results; externally stopped workers have constraints and execution evidence but
no invented result. The eight matches reach eight player-specific milestone keys
at four temporal boundaries. Every game still has unchecked observations; there
are zero fully covered milestones.

Row 8 is useful for understanding what the machine discovers. The retained main
prefix matches two of eight milestone keys. A separate search branch reaches
cleanup with eight cards, selects a Forest to discard and then starts the next
turn. The current observation projection requires a stable end-of-turn snapshot
and neutral events before that transition; it cannot safely project this branch.
The trace retains the predecessor actions, states and native discard events.

This explains an adapter boundary. The branch uses reconstructed hidden state:
it does not establish that the recorded human discarded that Forest, that the
game is unreachable, or that the engine violated Magic rules.

## What the change improved

The candidate adds typed initial states, submitted actions, before/after states,
native events, field comparisons and separate failure contexts. Nine games now
have search traces with 429 retained main-path transitions in total. Nine input
issues have explicit no-execution trace objects.

The independent audit reconciled all 52,580 original field values. Node counts,
witness actions, diagnostic identities and coverage are unchanged across all 18
paired native results. The 336 changed constraint records only improve reason
annotations; expected values, dispositions, projections and reconstructed setups
are unchanged.

The proposal's origin cases and motivating feedback are derived from the baseline
report. The comparison deliberately records comparison_only. It does not
approve the patch as an engine repair. No gameplay-correctness improvement or
coverage increase is claimed.

Review also found a distinct provenance-checking gap: an audit-only forged repair
record could cite nonexistent origins. The stricter verifier now rejects that
record and checks origin cases, motivating feedback, baseline and candidate
revisions, and diagnosis references. The run preserves the original recording
adapter and explicitly records its compatible verification update; original
baseline receipts were not rewritten.

## Implementation checks

All 144 Python tests passed with the native factory runtime enabled. The native
change passed 78 workspace Rust tests, formatting, all-target Clippy, phase-pin,
generated-contract and catalog checks. The viewer passed 42 unit tests,
typechecking, its build and 13 browser regressions, plus checks against the actual
candidate and comparison. One older live baseline browser test was skipped in
that final batch; the actual current candidate was checked separately.

The replay retains the [Python validation receipt](artifacts/2c1ad40eb20d91bff5df60d1b6f9421da956a76020f776c0b72348d3a7d27e6b),
[native check inventory](artifacts/4866022f04422f289e90bb37d12bccc4edf34345d2a4b93a02f378e1bea99f3f)
and [actual-data viewer review](artifacts/8863903a305a8c2e172a81c34ec4b685b954c4be65430327ca0edccf6c415f5e).
The completed directory and its portable export both passed native verification;
the discovery verifier also recomputed reports, issue origins and comparisons.

## Scope and reproducibility

The cohort is the exact first 20 rows, without outcome-based filtering. All had
previously been inspected; evaluation-role labels do not imply unseen holdouts.
The original full archive and selected CSV are identified in the
[cohort manifest](../../fixtures/17lands/sos-cohort-20/cohort.json).

Both phases use the same source, official card mapping, runtime manifest,
two-turn-pair horizon, 10,000-node limit, 128-action path limit, 60-second external
deadline and 8 GiB process limit. One worker runs at a time. The opponent setup
uses explicit Plains filler and each game uses its recorded index as the seed.
Name resolution is not a complete card-effect support certificate.

The private full card export and executables remain on EC2; their hashes and
build receipts are retained. A build receipt is an attestation of compilation,
not an independent reproducible-build proof. This public package needs no
external-artifact hydration to inspect or verify its evidence. Re-executing
requires the matching runtime inputs.

From the repository root:

    python3 scripts/fit17lands_factory.py verify \
      --run-dir replays/17lands-trajectories-20260909-01 \
      --runtime /path/to/factory-runtime

Verification recomputes the reports and attribution from retained receipts. It
does not rerun the engine. The runtime can also verify or export the complete
portable replay. See [the pipeline guide](../../docs/17lands-factory.md) to create
another run.

Source data: [17Lands public datasets](https://www.17lands.com/public_datasets),
under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Exact complete rows
were selected, retaining their header, quoting and line endings. Coworld derived
the cohort labels, observations and analysis. 17Lands does not endorse this work.
The original upstream acquisition time is unknown; import timestamps are recorded
separately.
