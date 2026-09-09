# SOS source-observation fixture

These fixtures support bounded trajectory fitting against real, previously inspected 17Lands observations. They contain no Phase execution result, rules expectation, acceptance verdict, or unseen holdout.

Source: [17Lands public datasets](https://www.17lands.com/public_datasets), [SOS Premier Draft replay archive](https://17lands-public.s3.amazonaws.com/analysis_data/replay_data/replay_data_public.SOS.PremierDraft.csv.gz), [official card mapping](https://17lands-public.s3.amazonaws.com/analysis_data/cards/cards.csv), and [ability mapping](https://17lands-public.s3.amazonaws.com/analysis_data/cards/abilities.csv). Source data is credited to 17Lands under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Selection, projection and interpretation are by Coworld MTG. 17Lands does not endorse this work.

## Files and selection

- source/sos-games-2-3-11.csv preserves the exact original header and complete raw rows at zero-based archive indices 2, 3 and 11. The rows have 2,629 columns. Original compressed archive bytes were independently rehashed; the archive itself is excluded.
- source/sos-first-turns-2-3-11.csv is a derived field-preserving projection: identifying fields, on_play, both mulligan counts, candidate/opening hands, all deck columns, and both first-local-turn column families. Later turns, totals, won and num_turns are omitted. It is a partial view, not a claim that each game ended after two turns.
- source/cards-selected.csv preserves exact official mapping rows for the opening/first-turn observations plus the 14 formerly unresolved Arena IDs. This is a subset with its own hash, not the full official map. Use the original full mapping hash when supplying the full mapping.
- source/abilities-selected.csv is a reserialized official-field projection. Ability IDs occupy a different namespace from card IDs.
- expected-observations.json preserves raw fields and separates turn owner from observed player. Blank remains blank; scalar blanks are unknown.
- selection-manifest.json records source hashes, exact source-row offsets/hashes, known selection bias and attribution. inventory.json hashes these retained files.
- historical-anomaly.json retains the old duplicate hand-count anchor and the actual zero-node unresolved-ID outcome. Its expected milestones describe source normalization, not an engine result.
- source/documentation-reference.json retains primary URLs, hashes and schema facts. Application JavaScript and Python helper source are omitted; their software redistribution license was not independently established by this audit.

Rows 2 and 3 are the earliest inspected examples with explicit zero mulligans for both players and no first-local-turn cast or ability records, for on_play=True and False respectively. Row 11 is an already observed extraction contradiction. Selection used source fields before any new runtime outcomes.

## Chronology

| Source row | on_play | First boundary | Second boundary |
| --- | --- | --- | --- |
| 2 | True | user_turn_1: Island played; user hand 6; opponent hand 7 | oppo_turn_1: Plains played; user hand 6; opponent hand 7 |
| 3 | False | oppo_turn_1: Fields of Strife played; user hand 7; opponent hand 6 | user_turn_1: Deduce recorded as drawn, Forest played; user hand 7; opponent hand 6 |
| 11 | True | user_turn_1: Terramorphic Expanse played; opponent hand 7 | oppo_turn_1: Island played and Exhibition Tidecaller cast; opponent hand 6; user ability 88024 recorded |

The first two boundaries follow on_play and the separate user/opponent local-turn prefixes. Every observation of either player's state stays attached to its original turn-owner boundary. This does not supply an order for actions within a turn.

The old game 11 extractor grouped opponent hand counts 7 and 6 into the same seat-1, turn-1 anchor. They are distinct source moments. The retained game 11 run stopped on unresolved card IDs at zero nodes, so this is an invalid extracted requirement identified by inspection, not a contradiction observed during engine execution. Ability 88024 maps to a sacrifice/search/shuffle ability in the official ability file. That observation also prevents treating a library ordering inferred from later draws as a recorded initial order.

## Setup and limits

All three rows explicitly record zero mulligans for both players, seven opening-hand IDs, and 40 positive user deck counts. The user opening hand is an observed multiset; the retained pipe ordering is not a proven library order. For the player going second, row3 records a single first-turn drawn card, Deduce. A witness may choose a compatible library prefix, but must label that choice as a reconstruction.

There are no opponent deck columns or opponent opening-hand identities. Opponent deck filler, opening cards and library order must remain unknown or be explicitly hypothetical. Extra future observed opponent cards must not silently become a certified starting deck.

The official replay helper distinguishes named user-hand lists from numeric opponent-hand counts. It does not document complete ordering across within-turn field families. Preserve multiplicity, missing values and the distinction between card and ability IDs. Do not assume blank zones prove empty zones or absent numbers equal zero.

All 14 previously unresolved IDs map uniquely to official names now. This includes six basic-land printings, Sylvan Library, four Prepare spell names, and three token names. This proves ID-to-name availability only; token characteristics and Prepare face identity still need explicit runtime mapping.

The first milestone is a compatible witness for the supported first-turn observations in rows 2 and 3, with explicit hidden-state assumptions. Row11 checks separated boundaries and should retain an unsupported boundary if the ability observation cannot be modeled. Budget exhaustion or rejected unsupported data cannot establish that an observed game is impossible.

## Reproduction and historical limits

The local source archive hash is db2e760e872e931b3d58238fa4cebff6647e48d178341dc5d21e642546ed4d3e. The original download recipe and fitting result retained the URL/hash association; original archive HTTP headers and retrieval time were not available in this audit. The official mapping and helper metadata retain their own dated acquisition identities.

The public landing-page prose says replay data has one row per turn. This retained file demonstrably has one wide row per game; use its actual header and the official replay_dtypes.py patterns. No new engine probe or full archive download was performed while preparing these fixtures.

