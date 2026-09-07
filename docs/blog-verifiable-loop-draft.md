# A software factory that keeps its evidence

Darkwater Egg is an unassuming Magic card. Its activated ability adds blue and black mana, then draws a card. That last clause is enough to make it useful for testing a rules engine.

In the rules snapshot used by our September 7, 2026 experiment, an activated mana ability cannot have a cost or effect that moves a card to or from a library. Drawing a card crosses that boundary. Our baseline parser classified Darkwater Egg's ability as a mana ability anyway.

We did not start by writing a Darkwater Egg test. We downloaded Scryfall's Oracle Cards snapshot, audited every row, and searched for a family of card definitions that could expose this disagreement. The resulting work item carries the original card record, the rule version, the selection recipe, the executable's identity, two recorded observations, and the evaluator's expected and observed values.

That is the part we want to make repeatable: a path from real inputs to a bounded, inspectable reason to change software.

We are building this in [Coworld MTG](https://github.com/Metta-AI/coworld-mtg), which uses the Rust engine Phase to interpret Magic. The software factory around it records discovery, execution, feedback, proposed changes, checks, reviews, and decisions. Its current output is an evidence replay that a person can inspect while the work is happening.

**This draft describes the measured baseline. The Phase repair is still undergoing plan review; no candidate result or accepted repair is claimed here.**

The source population matters. We audited **38,633 rows** from a saved Scryfall bulk download. A declared filter retained 29,530 normal-layout, paper-printing representatives legal or restricted in Vintage. The acquisition receipt keeps the archive hash, retrieval details, source dates, and pinned Comprehensive Rules version. A later download produces a different input identity.

A broad text scan nominated **47 cards** whose activated abilities might combine mana production with library movement. We added **10 mechanically selected simple-mana controls** from the same source population, giving the run **57 queued cases**.

These cases are actual card definitions. They are not observations of people playing Magic, and this run does not reconstruct games from a human transcript. The executable input is the selected source card. Keeping that distinction clear lets us say exactly what a result establishes.

The broad scan is deliberately permissive. A paragraph can mention drawing cards without drawing one itself. It can quote a token's ability or describe an effect that happens later. A match is useful weak feedback: it explains why the factory spent compute on that card. It is not yet evidence that Phase is wrong.

The stronger check has a separate job. Before testing a repair, we froze a small source grammar for complete cost and effect sentences. It derives an expected classification from the source text and the pinned rule, then aligns that interpretation with the actual syntax tree produced by Phase. Unsupported sentences and failed alignments remain inconclusive.

For Darkwater Egg, the recorded source and syntax tree align. The evaluator expects `is_mana_ability = false`; the baseline parser reports `true`. The two isolated worker executions reproduce that disagreement. The same frozen check finds violations in the other four Eggs, Chromatic Sphere, Deranged Assistant, and Millikin. The last two matter because they put library movement in the activation cost rather than the effect.

The measured development baseline is small enough to state directly:

| Development cohort | Recorded result |
| --- | --- |
| Eight source-qualified library-moving cards | Eight repeated classification violations |
| Six simple-mana controls | Six passing classifications |
| Twenty-seven other nominated cards | Inconclusive under the frozen evaluator |

The acceptance plan contains **18 frozen strong gates**: the eight development failures, the six development controls, and four held-out controls reserved for candidate evaluation. A failing gate cannot be removed to improve the score.

There is an important limitation in that split. No source-qualified library-moving card landed in holdout. The four held-out controls can check that a repair preserves those ordinary classifications. They cannot establish held-out repair performance for the family that motivated the change. The replay retains that gap alongside the positive evidence.

This is also classification assurance, with a narrow grammar and a particular rules snapshot. It does not certify runtime behavior during payment, priority, replacement effects, or resolution. A parser result can be correct while the engine later executes the ability incorrectly. Those claims need their own production-path cases and observations.

We keep the execution boundary simple. The worker receives a card definition and reports what Phase produced. It does not receive the expected classification. The evaluator runs after the worker and compares recorded output with the frozen expectation. Each measurement uses two separate processes, with their inputs, outputs, exit results, and measured wall time retained.

The build identity needs similar care. An executable can report the revision pinned by its enclosing workspace even when it was built against an overridden checkout. We record that declared identity separately from the attested source revision, source snapshot, patch, and binary hash. A comparison between baseline and candidate should identify the programs that actually ran.

Cases, evaluator source, and gate membership are fixed before the candidate is judged. Changing any of them creates a new experiment to inspect. This makes the repair task concrete: explain the measured disagreement, change the implementation, and run the original checks against the resulting binary. The candidate does not get to redefine success halfway through.

The replay boundary is designed to survive replacing Magic with another target. Rust types define versioned events, content-addressed artifacts, case ancestry, builds, feedback, plans, reviews, and decisions. A generic recorder manages immutable artifacts, atomic snapshots, bounded processes, and measured compute. A generic runtime validates and serves those records.

The domain adapter supplies the meaning: how to derive a case, invoke the target, interpret observations, and apply an acceptance policy. Here it understands Oracle text, Phase syntax trees, and a bounded part of Magic's rules. A compiler factory could use source programs, diagnostic signals, and frozen differential checks. The common layer would still record the same relationships.

That separation puts a limit on what the infrastructure claims. Matching hashes establish content identity. They do not prove that an external evaluator interpreted the rules correctly. The generic runtime's validation is distinct from rerunning the installed domain evaluator and reviewing its policy. Labeling feedback “strong” describes the authority and scope of its claim; it does not make that claim infallible.

The viewer reads the same typed records. Its pipeline comes from the [generated lifecycle graph](contracts/factory-lifecycle.mmd), rather than a second implementation of how work ought to proceed. As the replay cursor advances, cases enter the queue, executions acquire evidence, and feedback appears. The interface distinguishes weak nominations from stronger evaluations and shows the producer's recorded decision when one exists.

For the current Darkwater Egg case, a reader can open the raw Scryfall record, read the Oracle text, inspect the two parser outputs, and compare the evaluator's expected and observed classification. Source hashes and missing evidence are visible. A passing feedback record does not cause the viewer to announce that a repair has been accepted.

The same records supply attribution when a repair eventually reaches a decision. A proposed change names its motivating feedback. That feedback names executions and cases. Case ancestry leads back to source records and derivation recipes. The frozen plan and review bind the decision to a particular comparison. Reduction, when used, adds a parent-child relationship instead of replacing the original case.

That chain answers a practical question: where did this improvement come from? It can be followed through files, including an inconclusive branch or a rejected attempt. A later article can describe the result without becoming the only place its provenance exists.

We will publish the real Scryfall run as a portable replay alongside the implementation. The bundle contains the recorded events and their UTF-8 artifacts, with hashes that can be checked independently. The full source archive and executables retain separate identities. The viewer can open the bundle offline; importing it does not execute embedded evaluator code. The [software factory documentation](software-factory.md) describes how to run, inspect, and adapt the pipeline.

For now, the replay stops short of an accepted change. It contains eight measured development failures, six passing controls, 27 inconclusive development cases, a frozen candidate gate, and the work leading into repair review. That is already a useful instruction for a coding agent: account for these specific disagreements while preserving the stated checks.

The eventual patch will matter. So will the record showing which source inputs motivated it, which executable changed, what the evaluator measured, and how far the resulting claim extends.

