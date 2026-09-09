# Discovering engine issues from recorded games

Active plan, 8 September 2026. This plan supersedes the discovery direction in the earlier blog drafts and [design notes](verifiable-loop-design.md). At the start of this work, main was e7c578f135f49263896f1b20271feb108741393e. The first bounded integration is now implemented in [201aa8a](https://github.com/Metta-AI/coworld-mtg/commit/201aa8a139db9819911ca9b4e1d9bb02465fb5f1); [measured results and raw receipts](artifacts/17lands-guided-fit-20260908/README.md) describe its scope.

## Goal

Given a real 17Lands game, can Phase reproduce the observed play? If it cannot, preserve the first useful discrepancy and enough evidence to investigate it.

17Lands observations are incomplete. A recorded spell or end-of-turn hand count can leave out priority passes, payment choices, triggers, hidden cards and other intervening actions. The job is therefore to find a legal engine trajectory compatible with the observations, allowing for what the recording does not tell us.

This supplies issue candidates without first asking an agent to invent the particular card rule to test. A separate fixing process investigates each candidate, establishes what should happen, makes a discrete change and evaluates it. The change might belong in the engine, card definitions, identity mapping, observation adapter or search procedure.

The desired cycle is:

1. Select recorded games under a declared sampling policy and retain source identities.
2. Resolve the cards and identify known implementation gaps.
3. Translate the recorded information into ordered observation milestones.
4. Search for a compatible trajectory through the engine.
5. Preserve a witness, a partial match, or an issue candidate with its limits and assumptions.
6. Diagnose and fix candidates separately; evaluate repairs against the original evidence and additional cases.
7. Run discovery again and measure which obstacles disappeared.

The spec we can improve against begins as “explain this recorded play.” It becomes executable through a general observation adapter and compatibility checker. Card-specific rules and rulings can enter during diagnosis; they are not prerequisites for noticing that a game cannot be explained.

## What exists

The current harness can generate seeded Phase games, check invariants, replay exact actions and compare deterministic results. The case loop supports typed scenarios, execution, checking, reduction and reviewed acceptance. The factory records provenance, executions, feedback, changes and decisions in portable replays.

The accepted 17Lands coverage experiment repaired ingestion of public CSV data. The Scryfall and observed-card experiments exercised selected definitions and parsing. Those experiments do not establish that the engine can reproduce recorded games.

An older prototype supplied the starting approach for guided 17Lands fitting. The current fit17lands command reconstructs a starting game, searches exact legal actions with backtracking across milestones, and records witnesses, limits and issue candidates. It requires a known starter and explicitly zero mulligans, and currently checks a declared named-card projection. Complete implementation-support and token/face identity checks remain future work.

## What the old experiment actually found

The retained SOS sample provides several concrete problems to repair before interpreting its results as engine failures.

* **Two different moments were collapsed.** Game 11 says the opponent has seven cards at the end of the user's first turn and six at the end of the opponent's first turn. The source says the user played first and neither player mulliganed. The extractor grouped both observations by the number 1 and observed seat, losing whose turn had ended. The extracted requirements would demand both hand counts from one state. That particular game actually stopped earlier on unresolved card IDs, so the retained run did not execute this contradictory check.
* **Missing identity mappings blocked execution.** Fourteen previously unresolved Arena IDs all have entries in the retained official cards table, including basic lands. Resolving an ID still does not establish a unique engine definition or implementation support, but the initial failure was in the input pipeline.
* **Known setup information was not enforced.** The old search could take mulligan actions even for games recorded with zero mulligans. Missing mulligan counts were also treated as zero.
* **The search committed too early.** It kept the first path matching a milestone and could not revisit that choice if a later observation contradicted it.
* **Hidden setup was narrower than the recorded game.** It searched one reconstructed library arrangement and an opponent deck filled with inferred basic lands. Failure under that setup does not prove no compatible game exists.

The retained later run selected 25 raw rows, extracted 15 games after excluding ten mulligan games, blocked nine on unresolved cards and exhausted its budget on six. It matched no milestones. This is evidence about that pipeline, not a measurement of how hard correctly specified game fitting must be.

The [retained source fixture](../fixtures/17lands/sos-first-turns/README.md) identifies game 11 as zero-based source row 11 of archive SHA-256 db2e760e872e931b3d58238fa4cebff6647e48d178341dc5d21e642546ed4d3e. Its selection manifest preserves exact row offsets and hashes; [the historical anomaly receipt](../fixtures/17lands/sos-first-turns/historical-anomaly.json) preserves the duplicated requirements and the actual input-blocked outcome. The older 25-row result is retained as finding-019-final-run-2/result.json, SHA-256 81e45e84501f7b127ada29164775ab031cd2134f72b5361575ee31bed08ab0a5.

The chronology error alone cannot be solved with more search. We should correct these problems, recover known witnesses, and measure a small real sample before deciding whether search needs substantially more compute.

## Boundaries and outcomes

Use the existing Rust contracts and factory recorder, with domain-specific types for observed games and fitting. Keep one evidence format across the runner and viewer. Protobuf is not needed to obtain typed boundaries or generated diagrams; the existing Rust-to-JSON-Schema path already serves those uses.

The domain types should separate:

| Boundary | Required information |
| --- | --- |
| Source game | Source artifact hash, row identity, selection policy and applicable attribution. |
| Card binding | Original Arena ID; mapping source and version; resolved definition and face, or an explicit unresolved/ambiguous result. Identity and implementation support are separate. |
| Observation moment | Active player, that player's turn index, boundary such as end of turn, and the player or object being observed. Play order determines chronology. |
| Observation requirement | Original column and value, normalized meaning, and whether the field is enforced, informational or unsupported. |
| Initial-state reconstruction | Known starting player, opening cards, draws and mulligans; unknown information; choices or assumptions used to complete it. |
| Fit result | Matched prefix, witness or retained frontier, first obstacle, reconstruction assumptions, budgets and measured work. |
| Issue candidate | Originating evidence, suspected component, strength of the claim and the next useful investigation. |

Never silently omit an unsupported required field and call the complete game compatible. A match can be useful while covering only a declared prefix or subset of observations.

| Outcome | What it establishes |
| --- | --- |
| Unresolved or ambiguous identity | The input cannot yet be bound reliably to a card definition. |
| Known unsupported card or operation | A concrete support gap prevents the requested fit. |
| Invalid or unsupported projection | The adapter cannot faithfully turn selected source fields into engine checks. |
| Compatible prefix or game | A recorded legal trajectory satisfies the declared observations under the stated assumptions. |
| Budget exhausted | This search did not finish within its limits. |
| No witness under reconstruction assumptions | The explored model supplied no witness; alternative hidden states or interpretations may remain. |
| Engine property failure | Execution violated a separately stated engine property, such as accepting an advertised legal action or preserving a state invariant. |

All obstacles can enter the investigation queue. They do not all justify the same diagnosis. A budget exhaustion is useful evidence for improving search; it is not proof that the game engine rejected legal play. A bounded incompatibility claim requires exhausting the declared bounded model and remains conditional on its observation semantics and reconstruction.

## Milestone 1: trustworthy fitting on a small real sample

Initial integration complete. All 73 workspace Rust tests and the Rust lint, formatting, pin, contract and catalog checks passed. Source rows 2, 3 and 11 were each run twice. They matched 14, 15 and 16 supported turn fields at two temporal boundaries in 22, 22 and 31 nodes. Repeated constraints were byte-identical, and results differed only in elapsed time. Each row retains eight unsupported combat-damage/mana-spent fields; row 11 also retains its ability observation. All have zero fully covered milestones and no reported engine failure. The criteria and scope below explain this first integration; full-game coverage and the shared factory connection remain ahead.

Bring forward the guided fitter selectively, preserving the current Phase and corpus pins and existing seeded replay behavior. Do not merge unrelated historical generators or dependency changes.

**Repair extraction and identity resolution.** Use the official card mapping for all relevant observation fields, not only cast lists. Preserve ambiguities, tokens and card-face distinctions. A card first encountered later may limit the fitted prefix; it must not disappear from the requirements. Order player-turn moments using the recorded play order. Keep missing values distinct from zero, and opening cards distinct from later draws. Enforce known mulligan counts.

**Make engine boundary interpretation explicit.** An engine action can advance through several automatic steps. The adapter must check the source's end-of-turn observation against the corresponding engine boundary, not against a later draw. If the available state snapshots cannot support that check faithfully, report the limitation and retain the source.

**Search across milestones.** Retain alternative paths that match an earlier milestone so a later observation can cause backtracking. Search states include both engine state and observation progress. Memoization must preserve distinctions that affect future compatibility. Rank promising actions without eliminating legal alternatives unless the pruning rule is justified. Record any fixed deck or library assumptions instead of treating them as observed facts.

**Establish that a witness can be recovered.** Generate a small legal trace through the production engine, project away substeps, and verify that fitting recovers a compatible trajectory. Include a case where the first locally compatible choice fails a later milestone and another choice succeeds. These are checks of the fitting machinery; real games remain the discovery workload.

**Run a bounded real cohort.** Start with opening hands and first-turn boundaries from exact retained source rows, including game 11 and simpler land-play examples. Use one worker and explicit node, wall-time and memory limits. The old 10,000-node per-milestone and 100,000-node per-game settings are comparison points, not evidence that those limits are sufficient. Report matched prefixes and obstacle categories, then repeat the same cohort with a fixed seed, action order and node budget. A wall-time limit is a safety guard: record when it fires, and do not promise identical search progress across machines when it does.

This milestone succeeds when the command runs on current source, respects the corrected observations, recovers known-compatible examples and produces interpretable results on actual source rows. It does not require immediately finding an engine bug or fitting an entire game. If identity, card export or snapshot limitations stop progress, the result must identify that obstacle concretely.

## Milestone 2: discovery and fixing share an evidence trail

Connect fitting receipts to the existing factory stages and recorder. Each candidate should retain the original source, bindings, observation projection, target revision, reconstruction, search budget, matched prefix and failure details. Deduplicate repeated problems while retaining every originating case.

The fixing process can inspect rules, compare another implementation, minimize a case or improve the adapter. Preserve the distinction between observations that raised the issue and evidence that established the diagnosis. Version changes to the checker and search procedure as well as changes to the target program. Compare outcomes on the same source, declared observation scope, reconstruction policy and budget. Removing a difficult observation is a scope change, not a repaired fit. Corrections to the observation adapter need their own source-based justification and checks; the seven-versus-six example shows why freezing an incorrect adapter forever would also be wrong.

A repair should include a regression that captures the diagnosed fault, a discrete patch, a rerun of the original case, and evaluation on additional frozen cases where appropriate. Existing deterministic replay remains useful within a build; cross-version evaluation should compare the intended behavior rather than insist that a corrected engine retain old internal state hashes.

The seven-versus-six contradiction is a natural first example: the source discovers an impossible demand in our measurement machinery. The improvement belongs to the fitter. Its attribution should arise from the recorded source-to-issue-to-change links, without needing a separately authored case-study post.

## Milestone 3: explain the process and spend compute deliberately

Extend the existing viewer to put recorded observations beside the engine's projected states. A reader should be able to see the last matched moment, the next required observation, the action sequence tried, and why the run stopped. Display assumptions and budget limits where they affect the interpretation.

Measure acquisition failures, identity gaps, known support gaps, projection limitations, matched prefixes, search exhaustion and independently established engine defects separately. Record search nodes, state-copy cost, elapsed time and agent/review work. Compare search policies on frozen cohorts only after the basic observation model passes its checks.

Larger hidden-state searches, richer opponent-deck hypotheses and more sophisticated search policies are subsequent experiments. Prefer source constraints that remove unnecessary branching. More compute is justified when we can show what uncertainty it is resolving.

## Validation and reproducibility

The first integration should cover:

1. Source bytes and mapping hashes survive into receipts.
2. Game 11's two hand counts become two ordered milestones.
3. Known zero mulligans and unknown mulligan counts produce different constraints.
4. Required fields and ambiguous identities cannot silently disappear.
5. A projected production-engine trace yields a compatible witness.
6. A later observation can force reconsideration of an earlier matching path.
7. Node and wall-time limits terminate with an inconclusive outcome.
8. The fixed real cohort reproduces outcomes under deterministic search and node budgets; wall-time termination is recorded separately.

Work runs in reserved EC2 workspaces. Keep historical runs read-only. Publish only source slices permitted for redistribution, with their source and attribution; do not publish private corpus exports or raw private session data. Use readable commits to explain each change and the case that motivated it.

## General form

The reusable pieces are a target program, observed cases, a compatibility relation, bounded execution or search, graded feedback, issue candidates, discrete changes and an evaluator that decides what improved. Magic supplies the domain adapter: card identities, observations, legal actions and rules evidence.

Other domains will have different hidden state and observations. The factory should require adapters to make those choices explicit while reusing recording, provenance, budgets, reviews and replay presentation. The objective is to make fuzzy evidence executable enough to guide improvement, while retaining the assumptions that make each result meaningful.
