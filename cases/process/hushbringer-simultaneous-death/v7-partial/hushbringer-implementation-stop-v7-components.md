# Hushbringer v7 bounded stop: deferred cost components

Status: **introduced regression; not accepted, not ready to commit**. This is the concrete stop/return required by `.claude/agents/engine-implementation-executor.md` when current code contradicts the reviewed plan. Root confirmed fresh v8 planning/review is required. No production code was changed by this tests executor; no compatibility waiver or alternative design was implemented.

All work used `ssh nishadsingh-box-4`. Active repository: `/home/ubuntu/repos/phase-verifiable-loop`, branch `codex/hushbringer-simultaneous-death`, original commit `2dec6c88915db4697706234a7ba2fcedd97b1689`. Original-source test overlay: `/home/ubuntu/repos/phase-hushbringer-baseline-tests`; its production diff remains empty. Plan `hushbringer-plan-v7.md` and clean full review remain unmodified; exact hashes and evidence hashes are in `hushbringer-implementation-stop-v7-components-proof.json`.

## Reached public case and observed regression

The typed spell uses existing `AdditionalCost::Required(AbilityCost::Composite { costs: [Sacrifice(specific(first),1), Sacrifice(specific(second),1)] })`, GainLife(2), and either no mana cost or generic1 supplied by one colorless mana unit. `GameRunner::cast(spell).pay_cost_with(&ordered).resolve()` drives announcement, both selections, final mana payment, commit, trigger dispatch, and resolution. Each intended creature and the spell reach Graveyard; life is22. Hushbringer and Doomed Traveler use the verified Oracle builders used by the primary regression. No manual resolver or fabricated pending state is the action under test.

| Payment / order | Desired Spirit count | Original source | Active v7 | Group metadata |
|---|---:|---:|---:|---|
| Deferred, no Hush, first/second | 1 | 1 | 1 | Both trees wrongly make the two components peers |
| Deferred, no Hush, reverse | 1 | 1 | 1 | Both trees wrongly make the two components peers |
| Deferred, Hush then Traveler | 1 | 1 | **0** | Active Traveler snapshot captures Hush from the earlier component |
| Deferred, Traveler then Hush | 0 | 1 | 0 | Active payoff repaired, but peer list still wrongly joins components |
| Immediate, all four matching tuples | 1 except Traveler-before-Hush0 | Correct | Correct | Empty peers in each component |

Active Hush-first failure is at the actual Spirit payoff assertion (`left:0`, `right:1`), independently named `separate_deferred_spell_sacrifice_cost_components_hush_first`. The three other deferred tuple tests preserve the empty-peer desired assertion, and the Traveler-first baseline test also fails the desired Spirit0 assertion. The first no-Hush tuple's early peer failure cannot hide the two Hush outcomes because they have independent test names. The immediate four-tuple test is the positive sibling.

## Exact plan/code conflict

V7 line268 requires cost loops to close before another component. Line286 requires capture of **this existing cost component's selected IDs** and says **never join separate components**.

The existing `continue_after_declared_mana_split` splits a Composite residual into current and remaining payments (active `casting_costs.rs:264`). `can_defer_spell_sacrifice_until_mana_payment` (`:1638`) permits each spell component with a nonzero remaining mana cost. `handle_sacrifice_for_cost` (`:1997`) appends each selected object to the same `pending.deferred_sacrificed_permanents`. `DeferredSacrificeSelection` (`types/game_state.rs:2301`) retains only `object_id` and `filter`; it has no component boundary. At commit, active `pay_deferred_spell_sacrifices_at_commit` (`casting_costs.rs:1795`) opens one owner around the whole flat list. Original source already stamped that whole list as co-departed. The added authoritative before snapshot now turns this pre-existing lost component identity into the Hush-first gameplay regression.

This cannot be treated as the already-approved aggregate or inherited-target grouping exclusion: it is the explicitly in-scope deferred chosen-cost boundary. It cannot be repaired by weakening expected payoffs, accepting peer merging, or skipping a tuple. A fresh plan must determine how the existing cost authority preserves separate components through deferred commit and scope any required storage/compatibility work. This executor supplies evidence only and does not choose that design.

## Immutable evidence and attempts

Every v7 material attempt has an exact `source.tar.gz`, per-file `manifest.json`, `test-module.rs`, `combined.patch`, and initial `receipt.json` in its named directory. The tracked combined diff does not include the untracked new integration module; the module is explicitly included in both archive and manifest. `hushbringer-implementation-stop-v7-components-proof.json` binds all proof source/log hashes.

- Active `hushbringer-v7-active-attempt-3/cargo.log`:66 passed,2 failed,20 ignored. First reached deferred grouping failure and a separate exploratory library target error.
- Active `hushbringer-v7-active-attempt-4/cargo.log`:66 passed,5 failed,20 ignored. Independent deferred tuples prove every outcome above. Module SHA256 `b4210811323eb15c76478db70bd974198d706ff356ee7e3d8efafca64736acd7`; source archive SHA256 `765dcac3526bf4c59ac4f96de52e20886c28d71ce2cbcead96ecefe806fb41ee`.
- Original `hushbringer-v7-baseline-attempt-1/cargo.log`: cost filter1 passed,4 failed. The completed log survived an SSH Broken pipe after test completion; do not report transport255 as the Cargo code.
- Original `hushbringer-v7-baseline-attempt-1/full-include-ignored.log`: serialized full run28 passed,63 failed,0 ignored, command101. Independent cost proof lines349–374 are not interleaved. Source archive SHA256 `214f864066635552ed4727cc4819eb7904fdfa3d78fc2311bd4b20590b5c25f1`.
- Baseline adaptation in `hushbringer-v7-baseline-overlay-transform.json` removes only unsupported new-field snapshot assertions and exactly three new-field presence checks. All semantic assertions and action setup are unchanged. JSON proof prints absent baseline snapshot asnull.
- Final active archive `hushbringer-v7-active-attempt-5` corrects only the unrelated extra library fixture to an actual two-of-three Hand-to-Library choice. No Battlefield-library-choice support is claimed: the attempted empty-target private-zone scan permits Hand/Library only, while the previous BF filter announced an ordinary target. Both failed exploratory attempts remain archived. Existing targeted Battlefield library leaf and natural hand-choice tests remain retained. Final runtime result will be recorded in the tests-v7 handoff and final receipt.

## Scope at stop

The three approved v7 A/B/C dispositions and many formerly pending runtime rows pass active attempt4; the stop does not erase that work. Twenty independently named desired known-gap diagnostics remain distinct from active requirements. No isolated seam rollback was started: exact-seam evidence is still **zero**, including the essential Augment member-handoff and added-mid-leaf-flush mutations. Root explicitly deferred all new mutation work to the fresh executor after boundary revision. A remaining real-pipeline resolver-reentry discriminator is not yet established: moving another parent candidate cannot discriminate the wrapper because member matching includes exact object/incarnation; manual helper isolation and public Devour do not establish that exact rollback.

The tests-v7 partial handoff will enumerate retained rows, pending obligations, CR/parser honesty, final module/log receipt, and peer/root-owned gates. No worker comparison, commit, acceptance, or full implementation completion is claimed.
