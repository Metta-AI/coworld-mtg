# A machine that can tell whether it got better

We gave a program 92 real games of Magic: The Gathering and asked which cards people had cast.

There were 1,426 listed casts in the input. The program read all 92 rows, exited successfully, and returned an empty card-frequency list.

This is a respectable software bug. It has the courtesy to be wrong without also being complicated. The interesting part was that we were building a system intended to find bugs and improve software, and this program was part of the machinery feeding it examples.

Before our machine could learn from experience, we had to establish that experience was getting into the machine.

I think this is a useful place to start talking about self-improving AI software. It puts a fairly demanding question ahead of the exciting one. Before asking how much code an agent can write, we can ask what would count as evidence that its code made anything better.

Suppose an agent changes a program, writes some tests, runs them, and reports success. This may be excellent work. It may also be a coordinated change to the program and the definition of success. Give the same agent more time and it can produce a much larger collection of mutually agreeable code, tests, and explanations.

The missing ingredient is an observation that the patch author cannot make true merely by explaining it.

Our small attempt at supplying one is [Coworld](https://github.com/Metta-AI/coworld-mtg). We use AI agents to work on a Magic rules engine and the tools around it. Magic is useful here because it offers an awkward combination: public card definitions, an explicit rulebook, and enough exceptions to make implementing the rulebook interesting. It also gives us inputs whose existence predates our desire to demonstrate that the system works.

The program with the empty answer was a CSV importer. Its inputs came from [17Lands' public game data](https://www.17lands.com/public_datasets). The particular export placed casts in numbered per-turn columns and represented cards using Arena IDs. Our importer could count the rows, but it did not extract those columns and resolve the IDs through the official mapping. Its success status described the process ending normally. It said very little about whether the requested information had survived.

Fortunately, this failure came with an unusually cooperative source of truth: the information was still sitting in the file.

We wrote a separate checker that enumerated the listed cast occurrences from the retained CSV and official mapping, then compared them with the importer's output. It preserved where each occurrence came from: the row, column, and position within a cell. That matters because a program can produce the right total while duplicating one occurrence and losing another.

The resulting experiment was small:

| Input partition | Listed casts | Old importer | Repaired importer |
| --- | ---: | --- | --- |
| First 46 games | 679 | Empty frequency list | Coverage satisfied |
| Next 46 games | 747 | Empty frequency list | Coverage satisfied |
| 16 newly acquired games | 276 | Not run | Coverage satisfied |

Each reported result was checked in two executions. The new rows were selected and frozen before candidate observations, with an operator attestation that they had been withheld from the implementer. They tested another slice of the same export format; they were no evidence about arbitrary future formats.

There was also a combined case containing the original 92 games. We kept it because it reproduced the original failure, but it overlapped the first two partitions. It reproduced the same observations rather than adding independent evidence.

After checking the required partitions and obtaining a separate review, the experiment recorded an [accepted repair](https://github.com/Metta-AI/coworld-mtg/blob/c506e3500713e13dee5f2df8c3276a6868b5da40/replays/17lands-coverage-20260907-03/replay.json).

This establishes something narrow and useful: the repaired importer preserves the listed casts and their mappings in these inputs. The dataset does not provide everything needed to reconstruct complete games, including full action order, targets, priority, and hidden state. There is no result here about whether the engine would have played those games correctly.

That restriction is part of why the experiment works. We chose a question for which the available evidence could actually supply an answer.

* * *

Jason Gross's [“Catching bugs with fractional proofs”](https://theorem.dev/blog/catching-bugs-with-fractional-proofs/) gives a more sophisticated example of this instinct. Theorem starts with a property of top-K sampling, decomposes it into smaller obligations, and tests them closer to the relevant implementation. One obligation is that approximate top-K retain the actual maximum. This makes a specific numerical failure accessible without waiting for it to manifest in a full language-model interaction.

The connection I care about is the choice of question. Reasoning about structure can lead you to a test where a failure is both easier to encounter and easier to interpret. Our work does not implement fractional proof decomposition, or establish Theorem's claims about testing efficiency. But it runs into the same practical temptation: spend more compute on a large, impressive activity before deciding which smaller fact that activity is meant to establish.

For the importer, that fact was almost embarrassingly simple. The source lists a cast; the output should preserve it.

For the rules engine, finding such a fact required more care.

We took a real [Scryfall card snapshot](https://api.scryfall.com/bulk-data/oracle_cards) and looked for abilities that both produced mana and moved cards into or out of a library. In Magic, “library” means the deck you draw from. “Mana ability” is a technical classification with consequences for timing: these abilities can resolve immediately and can be used in some situations where ordinary abilities cannot.

An ability can produce mana without qualifying for that classification. Under the [rules snapshot used in this experiment](https://media.wizards.com/2026/downloads/MagicCompRules%2020260819.txt), rule 605.1a excludes activated abilities whose costs or effects move cards to or from a library.

Darkwater Egg adds mana and draws a card. Drawing moves a card from the library into the player's hand. The engine's parser nevertheless classified its ability as a mana ability.

That gives us a manageable claim. We do not need to simulate an entire match to inspect the classification. We need the actual card text, the applicable rule, and the parser's representation of the ability.

We still have to be careful about the middle step. A text search for “draw” and “add” is good at finding things worth investigating. It is much worse at deciding which clauses belong to which ability, when an effect occurs, or whether a particular exception applies.

So we separated nomination from judgment. A broad scan produced 47 potentially relevant cards; ten simple mana controls brought the queue to 57. A narrower evaluator made judgments only where the source text fitted a frozen grammar and aligned with the engine's parsed structure. Outside that region, it returned “inconclusive.”

The development baseline contained eight classification failures. We produced and independently reviewed a change addressing the Draw part of the problem. Across two candidate executions on every card, the results were:

| Candidate result | Cards |
| --- | ---: |
| Motivating classification failures now satisfied | 6 |
| Controls satisfied | 10 |
| Known classification failures still violated | 2 |
| Inconclusive | 39 |

The two remaining failures were Deranged Assistant and Millikin, whose abilities involve milling: moving a card from the library into the graveyard, the game's discard pile. The broader plan required all eight motivating failures to be repaired, along with its control checks. The experiment therefore [rejected the candidate](https://github.com/Metta-AI/coworld-mtg/blob/c506e3500713e13dee5f2df8c3276a6868b5da40/replays/scryfall-mana-20260907-03/artifacts/11bd1d52f3d2dd823d3e72194beb7bf735fcc6d8c1cb455cec33c1ab9e6f00cb).

We separately published the [reviewed Draw component](https://github.com/nishu-builder/phase/commit/31917c0ba1c86066aaa09ae44d6f34342b03d682) as a partial engine change. At this checkpoint, Mill remained unimplemented and Coworld's runtime still used the earlier engine revision. Publication did not alter the experiment's decision.

This is the result I find more informative than a clean sweep. There was real progress, and the original question remained incompletely answered. Both facts survived.

The 39 inconclusive cases survived too. An evaluator that confidently judges everything is convenient for dashboards. An evaluator that admits where its argument stops is more useful for deciding what to do next.

Even the controls need interpretation. Four were held out, but none of the held-out cards were qualified examples of the library-moving failures. Passing them gives some evidence against breaking ordinary mana classification. It does not establish that the repair generalizes to unseen examples of the defect.

* * *

At this point a reasonable objection is that we have invented testing, with a lot of JSON.

Much of the checking really is ordinary testing. The proposed change concerns the organization around it: what an agent must leave behind when it claims to have improved a program, and which parts of that claim another process can inspect.

Take the rejected engine change. Starting at its decision, you can follow the required checks to Millikin, then inspect the recorded candidate classification and the actual card text that the evaluator used. The execution identifies the build; the build record identifies the executable and the claimed source revision. The patch also names the failures that motivated it. You can examine whether this change answered the question that prompted the work.

Those connections are part of the data structure. Typed records distinguish selecting a suspicious case, running a program, judging its output, and accepting a particular change. The viewer and recorder consume the same definitions. A parsing result and a rules-correctness judgment are different claims, with different evidence requirements.

Types cannot decide whether our reading of a Magic rule is sound. They can make us name which claim we are making and preserve the inputs someone would need to challenge it.

We call the resulting artifact a replay. In this context, it is a replay of the improvement attempt: the inputs, runs, observations, changes, and decisions. A portable file can be inspected without running any code contained in it or reconstructing the story from an agent's chat history.

This also answers a surprisingly difficult attribution question. Months later, when we want to say where an improvement came from, we should be able to follow references from the patch back to the failure and the real input that exposed it. Asking an agent to remember an appealing explanation would produce a different sort of artifact.

Our first viewer made those relationships too hard to understand. The records were more explicit than the interface was legible. That is a substantial unfinished part of the project: a reader should be able to see what changed, why it changed, and what remains uncertain without studying the serialization format.

An evidence trail that nobody can follow has limited practical value.

Another reasonable objection is that the checker can be wrong.

Yes. We wrote the coverage checker. We selected the classification grammar. Agents performed much of the implementation and review, with operator orchestration. This is not yet an unattended machine that invents its own specifications, improves itself, and certifies the result.

A separate reviewer can share the implementer's misunderstanding. A recorded executable hash identifies bytes; it does not prove which source produced them. The current build linkage includes retained evidence and caller attestations, rather than independently reproduced compilation. An operator's statement that a holdout was unexposed remains a statement about the operator.

The records make those assumptions visible and give a later reviewer something specific to inspect. They do not remove the assumptions.

A frozen evaluator is useful for the same reason a frozen experimental protocol is useful. It prevents a change in the question from disappearing into a change in the answer. The evaluator may need repair; when it does, that should become a visible change with its own evidence.

The measuring machinery supplies examples of this problem too. Our first Scryfall preparation failed because real source numbers reached an integer-only metadata encoder. No target program ran. We changed the boundary so source data could be retained as bytes without forcing it through that restricted representation. That failure belongs to the recorder's history, with a different target and a different claim from the mana-classification repair.

A software factory has plenty of software in it to improve.

* * *

There is one more objection: perhaps all this care costs more than the bug is worth.

We do not yet have a convincing cost-per-accepted-improvement result. Recording compute helps ask that question; it does not answer it automatically. Worker execution, acquisition, compilation, agent reasoning, review, and human attention are different costs, and our measurements do not cover them equally.

A [separate discovery run](https://github.com/Metta-AI/coworld-mtg/blob/c506e3500713e13dee5f2df8c3276a6868b5da40/replays/17lands-observed-cards-20260908-01/replay.json) followed cards observed in the public games into the parser and found mapping gaps and explicit limitations handling Saga cards. It supplied leads for further work, with no established gameplay discrepancy or accepted repair.

This suggests a job for an improvement loop's compute budget. Cheap signals can find promising places to look. More expensive investigation can determine whether a suspected failure is real, isolate a tractable claim, and evaluate a proposed repair. Inconclusive results identify places where the present checker cannot justify spending the next dollar as confidently as we might like.

Whether this allocation beats simpler approaches is an empirical question. The current project supplies inspectable attempts at it.

The common machinery is fairly portable. A compiler project might use source programs as cases and compare behavior against a reference for a declared language subset. A data pipeline might preserve source occurrences through a transformation, much as our importer does. A numerical library might test invariants and carefully bounded reference comparisons.

Each would need its own account of correctness. What they can share is the record of how a case became a claim, a claim motivated a change, and evidence supported or failed to support accepting that change.

That is the version of “verifiable AI software” I want to build toward. Sometimes verification will mean a formal proof. Sometimes it will mean a recomputable comparison under explicit assumptions. In either case, the claim needs to be small enough to understand, and the evidence needs to be attached to the particular program being discussed.

Our starting result was a program that looked at 1,426 listed casts and returned zero. We now have a repair, a checker, retained before-and-after observations, and a record explaining why that repair was accepted. We also have a second experiment that made progress and was rejected, and a third that has only supplied leads.

If the next version says it found 1,426 casts, the interesting question is still which ones. We should be able to show you.

I would like the same answer when an AI tells me it made a program better.
