# A software factory that keeps its evidence

Our importer read 92 real game rows, exited successfully, and returned an empty card-frequency list. The input contained 1,426 listed casts. A successful process had silently lost the information we wanted from it.

The rows came from a public [17Lands dataset](https://www.17lands.com/public_datasets). Coworld's native miner could count these wide CSV rows, but it did not extract their numbered per-turn cast columns and resolve the Arena card IDs through the official mapping. We repaired that ingestion path and recorded an [accepted decision](../replays/17lands-coverage-20260907-03/artifacts/15f6bba8dafa697ec5245ebf2d9a36b7ef92a67515bc46355a04794370d9b31e) after checking the original failures, frozen regression and holdout inputs, and an independent review.

The accepted claim is precise: the importer preserves the listed cast occurrences, their source identities and mapped names in the frozen CSV partitions. The records do not establish complete gameplay order or correct execution of Magic's rules.

The useful result is both the repair and the record explaining it. The [completed replay](../replays/17lands-coverage-20260907-03/replay.json) contains 73 events and 95 artifacts: source identities, cases, executions, feedback, a patch, builds, a frozen plan, review and decision. The viewer reads these records directly. This article describes the result; the replay carries the evidence needed to inspect it.

We are building this in [Coworld MTG](https://github.com/Metta-AI/coworld-mtg). Its software factory can investigate both the Phase rules engine and the software used to prepare and inspect inputs. This particular change targets Coworld's native CSV importer. The Phase pin in its minimal input manifest serves the existing loader's compatibility check; it is not the source revision being repaired.

Before running the candidate, we retained the exact CSV bytes and official `cards.csv` mapping, wrote an independent source-coverage evaluator, and froze the case partition. The evaluator counts each pipe-separated occurrence in the declared cast columns. It keeps the row, column, pipe position, raw and parsed Arena ID, turn, and active and casting player. Repeated casts remain separate. The resulting name frequencies combine IDs that share an official name: the known 92 rows contain 230 Arena IDs but 229 names, because two IDs map to Lightning Strike.

The first 92 rows were already known to the implementer. We split them into disjoint primary and regression cases, then acquired a longer compressed prefix of the same archive. Its first 65,536 bytes matched the earlier prefix exactly. We selected the first 16 newly completed rows, preserving their raw byte slices, and froze them before candidate observations. The acquisition receipt records the HTTP response identifiers, source hashes and slicing recipe. The operator attests that these new rows were withheld from the implementer; their non-exposure is not something a content hash proves.

The measured results are small enough to show in full:

| Case | Source rows | Expected cast occurrences | Baseline | Candidate |
| --- | ---: | ---: | --- | --- |
| Primary | 1–46 | 679 | Empty frequency list, twice | Coverage satisfied, twice |
| Regression | 47–92 | 747 | Empty frequency list, twice | Coverage satisfied, twice |
| Holdout | 93–108 | 276 | Not executed | Coverage satisfied, twice |
| Informational aggregate | 1–92 | 1,426 | Empty frequency list, twice | Coverage satisfied, twice |

The aggregate overlaps the two known partitions. It reproduces the original 92-row failure and repair; it is not another independent gate or another 92 unique games. The acceptance plan requires the primary, regression and holdout cases. The holdout tests ingestion of previously unseen rows from the same archive, not a different format or population.

There were 14 separate worker executions: six baseline and eight candidate. Each retained its exact input manifest, command arguments, raw output, process result, executable identity and measured wall time. The worker received source data and invocation parameters. Expected coverage stayed with the evaluator.

The baseline used the legacy arguments it supported. The candidate additionally received an explicit public-replay schema and the official mapping path and hash. That invocation difference is recorded. The experiment checks the new ingestion capability with the frozen source and mapping; it does not hide a changed command behind a before-and-after score.

We also built a controlled baseline from a clean Coworld commit before applying the miner change. The candidate was built from a distinct clean commit, and its recorded patch is the exact diff from that baseline. Retained source archives, before-and-after file hashes, Cargo lock, compiler identity, command, environment and executable hashes make those claims inspectable. The independent reviewer checked them against Git objects and retained bytes. Compilation linkage remains a caller attestation: the review did not independently rebuild the executable and prove reproducibility.

The strong feedback checks source coverage. It recomputes expected occurrences from the retained CSV and official mapping, decodes the native output bytes, and compares them with the recorded observation. Unknown source or normalization schemas, missing rows, unresolved IDs and unsupported observations remain inconclusive. A provided unknown normalization schema cannot turn a differing frequency list into a confident failure. The known baseline's empty list, under its supported report schema, does independently establish the measured loss.

Repeatability also has a defined scope. The two coverage projections must agree after excluding the temporary mapping-file path. Their raw bytes remain available even when that path makes their file hashes differ. Unrelated workload statistics do not become acceptance gates accidentally.

The [independent result review](../replays/17lands-coverage-20260907-03/artifacts/228cb35173efe3bba8fcc4bbfe62a843ddfc79eae4767a082e82e96b61f66a1b) inspected source slices, artifact identities, raw outputs, build and patch bindings, and the frozen plan. It recommended approval without material findings. The subsequent decision binds that exact review to the before-and-after primary receipts and the required regression and holdout receipts. A successful test count or a green viewer element cannot substitute for that recorded decision.

The same distinction between signals and claims matters when the factory examines the rules engine. In a separate experiment, we audited 38,633 rows from an actual [Scryfall Oracle Cards snapshot](https://api.scryfall.com/bulk-data/oracle_cards). A declared source filter retained 29,530 representatives. A broad text scan nominated 47 cards that might combine mana production with library movement; ten mechanically selected simple-mana controls brought the queue to 57 cases.

Darkwater Egg gives a concrete example. Its activated ability adds mana and draws a card. Under CR605.1a in the [pinned rules snapshot](https://media.wizards.com/2026/downloads/MagicCompRules%2020260819.txt), moving a card to or from a library prevents that ability from being a mana ability. The baseline Phase parser nevertheless reported `is_mana_ability = true`.

A text match was only a weak nomination. The stronger evaluator first established that the full source sentence fitted its frozen grammar and aligned with Phase's actual syntax tree. Two separate executions then reproduced the classification disagreement. The [retained Scryfall baseline](../replays/scryfall-mana-20260907-02/replay.json) records eight such violations, six satisfied controls and 27 inconclusive development cases. A later inspector made false boolean values explicit while preserving the source cohort and evaluator.

The Scryfall acceptance plan has 18 frozen gates: eight development failures, six development controls and four held-out controls. No qualified library-moving card fell in holdout, so those four controls cannot establish held-out repair performance for the motivating family. The Phase repairs are ongoing. The accepted 17Lands ingestion decision does not imply that these classification failures have been repaired, or that payment, priority, replacement effects and resolution behave correctly.

These two investigations use different inputs and different notions of correctness. One worker consumes public CSV game records; another consumes raw card definitions. Both fit the same typed factory boundary:

| Recorded relationship | What it explains |
| --- | --- |
| Target and build | Which program and executable were evaluated, with source and build provenance. |
| Source and case ancestry | Which retained inputs produced the case, including selection and reduction recipes. |
| Weak nomination | Why an input warranted investigation or compute. |
| Strong feedback | Which bounded claim an identified evaluator checked, and whether the evidence satisfied it. |
| Proposed change | The exact patch and the feedback that motivated it. |
| Frozen plan, review and decision | Which checks were required and why this particular change was accepted or rejected. |
| Compute | Recorded execution cost; missing measurements remain unknown. |

Rust contracts define those records. The recorder stores immutable artifacts, updates live snapshots atomically and runs bounded worker processes. The standalone runtime validates and serves the replay. Domain adapters supply source interpretation, worker invocation, evaluators and acceptance policy. A compiler adapter could use source programs and a frozen reference-language subset; its unsupported programs would still need an explicit uncertainty outcome. The common layer does not need Magic-specific fields to represent that work.

The viewer uses the producer's stage topology, also available as a [generated lifecycle graph](contracts/factory-lifecycle.mmd). Moving the replay cursor shows cases entering the queue, execution evidence arriving, feedback being recorded and decisions following review. Errors, cancellations and inconclusive evaluations have separate meanings. A passing feedback receipt is displayed as feedback; acceptance appears when the producer records an accepted decision.

Attribution follows the stored references automatically. The 17Lands decision leads to its review and frozen gates. Those lead to feedback and executions, then to builds, cases and source slices. The patch names the failures that motivated it. That chain lets a reader inspect where the improvement came from without treating a hand-written case post as the evidence store. The same structure can retain rejected patches, reduced cases and superseded attempts as the loop continues.

The measuring system has its own history. Real source numbers exposed an integer-only metadata assumption; source data now remains in byte-preserving artifacts. An output audit required nested observations to be checked against retained native bytes. Two source-only 17Lands preparation drafts had malformed cancellation metadata. Their exact invalid files remain private failed-preparation evidence, with an explicit diagnostic in the valid run. They are not presented as successfully verified replay manifests.

There are limits at each boundary. Hashes bind bytes; they do not establish source authority, reviewer independence, unexposed holdouts or compiler execution by themselves. The generic runtime checks structure and identities. The installed, hash-matched domain verifier recomputes the claim. Review assesses the interpretation and remaining trust assumptions. A declared strength of “strong” has meaning only with that stated scope and evidence.

The public replay package retains bounded CSV slices, the official mapping and the artifacts needed to follow the accepted decision. It attributes the [17Lands public data](https://www.17lands.com/public_datasets) under CC BY 4.0, describes slicing as a modification and carries the non-endorsement notice. Compressed prefixes and executables have separately retained identities; a prefix hash is not a full-archive hash. The private runtime corpus and deck data remain private.

Open the [recorded runs](../replays/README.md) in the factory viewer to follow the accepted ingestion repair or the separate Scryfall investigation. Portable UTF-8 bundles support offline inspection without executing embedded evaluator code. The [factory guide](software-factory.md) describes the runtime, domain checks and adapter commands, so the next improvement can arrive with the same inspectable connection between its source inputs, change and recorded decision.
