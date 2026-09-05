# Full Phase plan review: Hushbringer v7

No blocking gaps found in the full v7 plan within its explicitly bounded scope. The plan is clean for the next implementation/test iteration. This is an architectural plan review, not approval of the dirty implementation or a completed runtime/maintainer acceptance receipt. Every existing exclusion and every uncompleted verification gate remains in force.

## Reviewed identity and method

- Plan: /home/ubuntu/coworld-migration-20260904/hushbringer-plan-v7.md.
- Verified SHA-256: e94553af94d7cc577cd548fc914fc560b16d0d2fb29c247371b5c9b3da411d27.
- Original production base: 2dec6c88915db4697706234a7ba2fcedd97b1689.
- Original-source inspection used /home/ubuntu/repos/phase-hushbringer-baseline-tests. Its HEAD matches the base and its crates/engine/src production diff is empty. The active /home/ubuntu/repos/phase-verifiable-loop tree is dirty and was not treated as original-source evidence or as proof of completed gates.
- Read the complete v7 document, AGENTS.md (symlink to CLAUDE.md), CLAUDE.md, review-engine-plan, engine-planner, add-trigger, add-static-ability, card-test, add-interactive-effect, and the applicable project-reference verification instructions.
- Independently checked the baseline producer/constructor inventories and relevant suppression, matching, source-availability, delayed lifetime, zone leaf, SBA/Augment, destruction, sacrifice, choice, cost, replacement, layer-reset and serialization seams. Read the v6 fixture stop/proof and partial production/test reports as inherited evidence.
- All reads, current Oracle requests and this report write ran through ssh nishadsingh-box-4. No engine, tests, plan or harness edits; no builds/tests, commits, pushes or child agents.

## Why the architecture passes the full review

| Required dimension | Review finding |
|---|---|
| Class rather than card | The runtime seam is the existing SuppressTriggers family, existing zone clauses and dedicated death matchers. Hushbringer/Traveler/Wrath validate that seam; no name branch or fabricated named-card Oracle is proposed. The estimate of affected cards is explicitly an estimate, not a measured support count. |
| Building-block reuse | Before evaluation uses functioning battlefield statics and the existing source/filter authorities. After evaluation uses the existing record filter authority. Evaluated outcomes, rather than a saved source ID/filter later reinterpreted against a different battlefield, preserve controller, condition and effective-ability meaning. The shared suppression module and lexical owner/member helpers each have a concrete missing responsibility. |
| Analogous trace | The plan traces the existing co-departed observer path end to end and separately traces suppression, ChangesZone, Changeling/layers, Haunt, keep/sacrifice, multi-target Destroy, interactive continuation, delayed listeners, origin normalization and Augment. Baseline paths and function names match those traces. |
| Placement and boundaries | Rules work stays in engine game/types modules. Parser, card data, functioning-ability/layer authorities, delayed creation/cleanup and general event dispatch remain reference seams. No frontend/WASM/AI game logic, UI text or i18n work is introduced. |
| Idiomatic Rust and type design | The proposed optional before/after value uses existing SuppressedTriggerEvent values. Owner ID, subject incarnation, occurrence key and private token distinguish different identities instead of a global boolean or card-specific variant. Short owned containers and closure epilogues avoid unsafe, interior-mutability and retained-reference machinery. |
| Nom and variants | No parser file, grammar, effect/trigger/static enum variant or new mechanic is proposed. No nom or inventory gate is being skipped for an actual proposed parser/variant change; discovery of either returns to planning. |
| Rules | Current Oracle and active local CR text support the premise and timing distinction. The plan explicitly rejects the old misuse of 603.2g and 704.7. The self-from-anywhere exception, Haunt link semantics and separate before/after clause decisions are retained. |
| Applicable skill checklists | Existing trigger/static/interactive lifecycle phases are disposed explicitly; unchanged phases are identified. Natural choice production, working continuation deltas, tracked-set/empty-choice cases, legal-action controls, APNAP/constraint controls and fresh verification remain required. Typed fixtures are labeled as such and use normal cast/apply boundaries. |
| Verification map | The matrix names seams, production entries, observable assertions, paired positive guards, sibling/hostile fixtures and failure discrimination. Existing passing broad tests do not substitute for pending rows. Parser shape assertions and scope helper tests are supplementary. Runtime status is distinguished from parser/card support status. |
| Identity/provenance | A selected live incarnation and explicit top member binding own an exact emitted occurrence. Barriers stop independent resolver reentry from borrowing an ancestor merely by ID overlap. Finalized event data survives clone/serde while the lexical carrier cannot survive pause/return. Haunt's linked subject and delayed creation-bound source/controller are separate authorities. |
| Scope and compatibility | Producer, ordinary matcher, delayed consumer, origin variant, source-availability and serialization boundaries are explicit. Ambiguous OneOf/NotEquals clauses preserve actual ordinary-live versus delayed-ungated behavior locally to the matching clause. No compatibility count or ignored desired failure is promoted to repaired rules support. |

## Source checks that matter for this conclusion

The old ordinary collector flushes layers and builds the live suppressor cache, then rejects a whole ETB/death event before matching: game/triggers.rs:1114, :1148 and :1480–1502. Its batched expansion repeats that prefilter at :280–305. This establishes both the missing before-world authority and why removing only one whole-event gate would be incomplete.

The baseline zone clause matcher is game/trigger_matchers.rs:1058–1157; scalar origin_zones becomes OneOf and disjunctive clauses supersede scalar fields. LeavesBattlefield normalizes separately at :3427. OriginConstraint::matches_from in types/ability.rs:17921 onward supplies the existing exhaustive physical-zone predicate. The parser's origin_zones_except / parse_origin_constraint_tail at parser/oracle_trigger.rs:14749–14845 confirms that complementary OneOf sets do not encode positive-origin provenance. The plan correctly declines to manufacture such provenance.

The registered ZoneChanged matcher inventory contains the planned ChangesZone/ChangesZoneAll/LeavesBattlefield routes, ETB aliases, ETB-only EntersOrAttacks arm, Library-origin mill, destination-exile matcher, and Unattach fallback. Haunt is a distinct registered function in game/haunt.rs:125–149 with a linked subject and a recorded creature check. Its source being in Exile does not make the payoff an Any-origin arrival trigger. Native Unattached and Sacrificed cause events remain distinct from the death occurrence.

Ordinary self/LKI, co-departed and off-zone collectors reach the shared inner matcher; registered delayed WheneverEvent and WhenNextEvent alternatives at game/triggers.rs:6321–6348 bypassed the ordinary live gate. The direct delayed paths at :6252–6319 and :6354–6384 are separate bypasses. Existing check_delayed_triggers owns one-shot consumption, recurring retention and unmatched reflexive disposal. The plan repairs registered unambiguous clauses without silently adding a whole-event delayed gate or changing these lifetime authorities.

The source-availability restriction is real: game/triggers.rs:1063–1083 rejects a co-departed source before the off-zone scan at :2200 onward. Keeping a surviving noncreature Any observer and a distinct self-arrival fixture reaches the existing paths without widening this collector. General co-dying destination-functioning Any observers are explicitly outside the repaired claim. Recover controls remain required.

The baseline stamp search matches the plan's producer inventory: DestroyAll; SBA outer/five subsets; shared batch delivery; mass ChangeZone; resumed ChangeZone drain; all-eligible and player-scope sacrifices; two cost sites; four keep/sacrifice caller stamps; and two resolution-choice stamps. Targeted Destroy and targeted ChangeZone also need their newly specified boundaries despite lacking the old group stamp. The private keep/sacrifice helper computes final scoped victims before its loop, so one helper-owned boundary covers the auto/empty/APNAP/total-power/handler routes without persisting a context while choices are pending.

The sole standalone-Augment caller is the SBA iteration. game/augment.rs:168–205 uses the same replacement-aware graveyard delivery as other SBA moves. Passing the borrowed iteration token through that call is necessary to retain the co-departed observer group. The planned no-Hush exact +1 observer test is a real discriminator for omitted handoff; a Hush-zero assertion alone would not prove it.

Both zone leaves construct records before cleanup and emit after assigning turn_zone_change_index (game/zones.rs:636–936 and :1124–1218). History is cloned into record_zone_change before finalization, so deliberately leaving ledger copies None is coherent with the chosen event-only authority. The existing merge leaf flush is real and remains an explicit limit, not something a scope flag repairs.

## V7 fixture dispositions

These are acceptable bounded dispositions of demonstrated baseline failures. They do not make the new tests passed or waive their execution.

1. Aggregate payment: the baseline aggregate handler validates unique eligible selections/power, loops sacrifices and returns through its existing continuation helper (game/engine_payment_choices.rs:1545–1638). The old fixture fails at life 20 versus desired 21 before its Spirit assertion. Moving the unconditional gain before the unless instruction supplies independent payment/group reach: life 21 at the prompt, paid final 21 versus declined final 16, actual victims/cause events and normal priority. The post-payment continuation's desired 21 is preserved separately. Grouping's desired zero in both selected orders remains independently executable and ignored as a known grouping gap. Neither failed guard nor a different successful route can be reported as reached aggregate suppression discrimination.

2. Regeneration: game/effects/regenerate.rs appends the shield only to live replacement definitions; game/layers.rs:1640 resets them from base. game/scenario.rs:926–930 seeds both live and base definitions. A seeded typed shield can therefore test the real first Destroy replacement application while the cast-created persistence diagnostic still asks for survival. Regenerated/tapped survivor, absent protected departure/CreatureDestroyed event, actual other victim, no-shield positive and cant_regenerate false/true twins prevent a vacuous guard assertion. The seeded fixture does not prove one-shot persistence, cleanup expiry, later attempts, or a real Regenerate cast.

3. Resumed explicit-target ChangeZone: the original fixture starts with no Hush and stops at two Spirits versus desired one, so it did not establish the Hush branch. The baseline resumed drain already collects/drains its tail and subsequently returns to ordinary action processing. V7 properly labels repeat scanning as an explanation requiring occurrence evidence, rather than a proven new fix. The Hush tail test still requires zero in both orders, exact two-member tail group and authoritative snapshots after natural pause/serde/resume. The identical no-Hush exactly-two fixture is narrowly labeled baseline duplicate-dispatch compatibility; desired one remains a separate diagnostic. The unpaused exact-one and later independent exact +1 controls remain mandatory. No event-vector deduplication, replay repair or broad relaxation of no-Hush counts is authorized.

I recomputed every log hash in the stop proof and the baseline overlay hash; all match:

| Artifact | Verified SHA-256 / result |
|---|---|
| hushbringer-baseline-v6.log | 3bc666ab3b9ce2b75e8034363d5b92b7d2f977b65a03bb12a1de0a1a00ed12d9; original two zero-Spirit assertions fail at one, no-Hush passes |
| hushbringer-active-tests-v6-attempt-4.log | dd0bb6077008a61d45665c467b9a8cdbdb84730af80231e2f3e8b1328a67a119; 41 passed, 3 failed, 4 ignored |
| hushbringer-baseline-expanded-v6-attempt-1.log | c0131a1d848a11e19685b1e696b3b661c84f823b17464ff6d9537a8634e36884; 15 passed, 33 failed, 0 ignored |
| Baseline expanded test overlay | ff07d4b130b01271b2bd1b5fdf4756fc0eb8013b9899c650125ba72383f0062d |

These are verified saved receipts, not tests run by this reviewer. Parameter loops with an early failure prove only their reached cases. The later active test hash is not retroactively evidence for attempt 4; v7 correctly requires new source/name/hash receipts and separate per-order diagnostic results.

## Rules and premise verification

Fresh remote Scryfall named-card responses matched all four plan Oracle strings: [Hushbringer](https://scryfall.com/card/eld/18/hushbringer), [Doomed Traveler](https://scryfall.com/card/clu/59/doomed-traveler), [Wrath of God](https://scryfall.com/card/cmm/70/wrath-of-god), and [Curtains' Call](https://scryfall.com/card/otc/130/curtains-call). Hushbringer's Wizards-sourced rulings independently confirm simultaneous-death suppression and the self-from-anywhere exception.

Verified the plan's cited rule set in active /home/ubuntu/repos/phase-verifiable-loop/docs/MagicCompRules.txt: 101.4; 113.6/113.6k; 118.12a; 400.7; 603.2/603.2c/603.2g; 603.6a–d; 603.7a–b/603.7d–e; 603.10/603.10a/603.10c; 603.12; 608.2b–c/608.2f; 611.3a–b; 613.11; 614.6/614.8; 616.1; 700.4; 701.8a–c; 701.19a/701.19c; 701.21a; 702.12b; 702.55a–c; 704.3; 704.7.

The local text supports before-world LTB versus ordinary immediate-after checking, written-instruction and group boundaries, delayed/reflexive distinctions, destruction/replacement/sacrifice authority and the desired exactly-once diagnostic. It does not justify the retained compatibility bugs. The plan's correction of stale 603.2g/704.7 explanations is appropriate. Stale add-trigger/add-static rule tables are not being used as verified law.

## Execution details already required by the plan

Two concrete checks deserve explicit attention during implementation review; they are consequences of existing v7 invariants, not new authority or scope:

- game/engine_resolution_choices.rs:4789–4797 action_result_outcome uses mem::take(events). The existing pause branches call it inside movement logic. An owner epilogue must run before that extraction/publication, just as it must precede continuation and collection. Returning an already-extracted ActionResult from inside the owner closure would violate the plan's append-only vector/claimed-key contract. Preserve the pause result while deferring the extraction until after close; do not ignore missing keys or treat a cleared vector as an empty group. The cost simulation's state/event replacement at game/casting_costs.rs:1728–1729 is before the planned sacrifice scope, as the plan states.
- The constructor sweep also finds existing full test literals in game/derived_views.rs and integration/issue_3277_captain_nghathrod_eliminated_opponent.rs, issue_5332_gandalf_trigger_doubling.rs, and madame_null_integration.rs, in addition to the named game_object/filter/stack/default sites. These fit only the manifest's narrow concrete-constructor exception and need the additive None initialization. They do not authorize behavioral edits in those files. Struct-update literals inherit the existing default; the loop_shortcut historical Debug string changes only mechanically.

Neither detail warrants a revised architecture: the plan already requires complete constructors and finalization before publication/return. They must be verified in the actual implementation and fresh pause/serde evidence.

## Acceptance and exclusions remain unchanged

The partial v6 reports explicitly leave work open. V7 retains that work: public unpaused shared batch delivery; all touched EffectZoneChoice arms including PayCost; separate sacrifice cost components and post-choice later-Hush timing; merge/independent-child characterization; standalone and library after-world inverse/positive controls; dedicated attack/ETB/mill/exile controls; expanded ambiguous delayed alternatives/reflexive and desired diagnostics; exclusion filtering/controller/retry siblings; two simultaneous source authorities and actual rebinding; private lifecycle/serde/normalization; isolated per-seam revert discrimination; full required engine/card-data/format evidence; and the frozen-worker run. Passing 41 existing rows does not close those gates.

The frozen Coworld acceptance plan still names case 01edd604679d89888ad9bb3bd13ca1c531fbbdd1c65f98341e7ce2a5a57d09aa, seven regression cases and two holdouts. I read its author-written case and campaign-002 receipt. That receipt records:

- Corpus: 9fce132e2d1dbc5ca5376cf691a56877d8378407d1e14fb29fc16bad057f725e.
- Baseline worker: 3991738fb3994b13a556795c93f54a6f8531f8ba06ce8c998d9f02576ad004e8.
- Checker: c1d4ad75fa5112869954f5973e585534d09e78db9cb07d6d492465ebb8f25fa6.
- Identical baseline semantic evidence twice: 26d06290e1d19cd412a680b9f67be09db75532274bdd7ddeff488a071c621cf7.
- Sole violated assertion: simultaneous-death-suppressed, with actual-death and spell-finished guards.

A freshly rebuilt changed worker must pass the unchanged original case twice and preserve the frozen siblings/checker/corpus. Original worker failure remains part of the receipt. No worker run was performed in this review.

Preserved exclusions: aggregate and inherited-target completed grouping; legacy direct delayed suppression; full cross-pause grouping; death-capable ambiguous/restricted origins; intrinsic merge and independent nested layer worlds; general co-dying off-zone Any source availability; aggregate post-payment continuation; cast-created regeneration persistence; and the exact resumed duplicate-dispatch branch. Existing occurrence-selection policy for registered delayed listeners is unchanged. These exclusions are not parser/card/runtime support promotions.

Residual assumptions are execution gates: corrected fixtures must reach their intended branches, all new Hush suppression/positive controls must pass, per-seam reverts must demonstrate their specified failures, and fresh terminal verification must correspond to the changed remote checkout. Any new semantic conflict outside the precise existing exceptions returns to the caller/planner. No assertion may be weakened by analogy to an adjacent known gap.

Verdict: full v7 plan review clean within these exclusions and gates; implementation and acceptance remain unfinished.
