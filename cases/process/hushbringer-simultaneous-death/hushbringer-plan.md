# Plan: preserve trigger-suppression timing across simultaneous departures

Plan-only artifact, prepared against `/Users/nishadsingh/repos/phase-verifiable-loop`, branch `codex/hushbringer-simultaneous-death`, base `2dec6c88915db4697706234a7ba2fcedd97b1689`. No engine code edited, builds run, tests run, or commits made. The caller owns plan review and implementation.

## Premise and rules verification

Independently fetched the current Scryfall named-card API responses on 2026-09-04 (curl with a user agent; the web tool could not open the API URL):

- [Hushbringer](https://scryfall.com/card/eld/18/hushbringer): `Flying, lifelink\nCreatures entering or dying don't cause abilities to trigger.`
- [Doomed Traveler](https://scryfall.com/card/clu/59/doomed-traveler): `When this creature dies, create a 1/1 white Spirit creature token with flying.`
- [Wrath of God](https://scryfall.com/card/cmm/70/wrath-of-god): `Destroy all creatures. They can't be regenerated.`

The [official Throne of Eldraine release notes](https://magic.wizards.com/en/news/feature/throne-eldraine-release-notes-2019-09-20), Hushbringer bullets, independently confirm suppression of creatures dying simultaneously with Hushbringer. They also explicitly distinguish graveyard triggers with “from anywhere,” including the exception for a dying creature's own self-referential from-anywhere ability. This exception is required coverage, not interchangeable with ordinary dies triggers.

Fetched current rules using the repository's `scripts/fetch-comp-rules.sh`. The script followed [Wizards' rules page](https://magic.wizards.com/en/rules) to `https://media.wizards.com/2026/downloads/MagicCompRules%2020260819.txt` and wrote the ignored local `docs/MagicCompRules.txt`. Verified the following numbers by `rg` in that file:

| Rule | Verified meaning relevant here |
|---|---|
| 603.2, 603.2c | Registration occurs when the event matches; one registration per occurrence. |
| 603.6a–b | ETB checks include newcomers with applicable continuous effects. |
| 603.6c | A “from anywhere” destination trigger is never an LTB ability merely because its event came from the battlefield. |
| 603.6d | “As enters,” “enters with,” and “enters tapped” are static effects, not triggers. |
| 603.10, 603.10a | Normal triggers use the immediate post-event world; LTB and the listed exceptional triggers look immediately before the event. |
| 611.3a–b, 613.11 | Static effects apply while functioning and can affect game rules. Their applicability must be evaluated in the appropriate world. |
| 700.4 | “Dies” means battlefield to graveyard. |
| 608.2c, 608.2f | Written instructions are ordered; a single action involving multiple objects is generally simultaneous. |
| 704.3 | One applicable SBA check is simultaneous; later fixpoint checks are separate. |
| 400.7 | A zone transition creates a new rules object despite the engine retaining an ObjectId. |
| 113.6, 113.6k | Zone of function and self/destination trigger availability matter independently of the event's physical origin. |

Do not carry the current suppression comment's interpretation of **603.2g** forward: the verified rule concerns events that did not occur because they were prevented/replaced. Hushbringer does not prevent or replace deaths. Use 603.10/603.6c and 611.3/613.11 for suppression timing. Also, existing comments calling **704.7** a general simultaneity rule are inaccurate; use verified 704.3 for that claim.

Frozen case `01edd604679d89888ad9bb3bd13ca1c531fbbdd1c65f98341e7ce2a5a57d09aa` in `coworld-mtg/tmp/verifiable-loop/campaign-002` is repeatable: both executions have evidence hash `26d06290e1d19cd412a680b9f67be09db75532274bdd7ddeff488a071c621cf7`; the only violated assertion is `simultaneous-death-suppressed`. The guards establish that Hushbringer, Traveler, and Wrath reached the graveyard. Corpus hash is `9fce132e2d1dbc5ca5376cf691a56877d8378407d1e14fb29fc16bad057f725e`.

## Root cause and owning seam

`crates/engine/src/game/triggers.rs::active_suppress_trigger_statics` (~1114) gathers only **currently functioning battlefield** suppressors. `collect_pending_triggers` flushes post-move layers, caches that list (~1480), and `event_is_suppressed_by_static_triggers_cached` then causes a whole-event `continue` (~1501). Wrath has already removed Hushbringer by then, so the suppressor is absent while Traveler's LKI trigger remains available.

The existing generic simultaneity authority is `ZoneChangeRecord.co_departed`, populated by `game/zones.rs::mark_simultaneous_departures`. `effects/destroy.rs::resolve_all` already stamps Wrath's group. The existing co-departed observer scan in `triggers.rs` (~2106) is the analogous feature. Simultaneity must continue to be established by producers, never inferred from all ZoneChanged entries in a resolution's events vector.

Two tempting patches are insufficient:

1. Reading every dead object's printed statics from a graveyard extends Hushbringer beyond its lifetime and ignores removed/granted/conditional abilities.
2. Adding co-departed suppressors to the whole-event skip incorrectly suppresses from-anywhere abilities. It also misses an earlier Traveler death followed by Hushbringer's later departure in the same resolution: the earlier event must retain the suppression that existed then.

## Pattern Coverage

This fixes event-time suppression for the `StaticMode::SuppressTriggers { source_filter, events }` family and its interaction with self/observer, scalar/disjunctive, and batched zone triggers. The family includes Hushbringer plus ETB siblings such as Torpor Orb, Hushwing Gryff, Tocatli Honor Guard, Doorkeeper Thrull, and opponent-scoped variants; approximately 5–10 printed suppressors and hundreds to thousands of affected death/ETB triggers, not a measured card-data count. The death axis currently has fewer printed sources, but no logic may branch on card name. Synthetic building-block fixtures can vary source filter, controller, and condition without inventing Oracle for a named card.

This is a runtime correctness change. No new Oracle grammar, effect, keyword, trigger mode, or static mode is required. Parser/card coverage counts should remain unchanged; runtime verification gains coverage.

## Building Blocks, Logic Placement, Rust Idioms

- Keep applicability evaluation behind `functioning_abilities::battlefield_active_statics`, including phasing, zone, condition, and layer-resolved ability removal. Reuse `layers::flush_layers` at genuine event boundaries; do not flush halfway through a simultaneous group and treat that intermediate board as the rules state.
- Reuse `FilterContext::from_source` while the source still exists in its relevant world and `matches_target_filter` / `matches_target_filter_on_zone_change_record`. The latter explicitly has source-relative properties that still consult live state, so saving only `source_id + source_filter` and evaluating later is not a complete snapshot.
- Store **evaluated suppression outcomes** at the logical event boundary, so the snapshot includes controller-relative filters, static conditions, and characteristic changes. Do not persist a borrowed FilterContext or reconstruct an old battlefield during trigger collection.
- Reuse `ZoneChangeRecord`, `SuppressedTriggerEvent`, `OriginConstraint`, `ZoneChangeClause`, `ObjectId`, `turn_zone_change_index`, and the existing deferred trigger carriers. Use a small serializable struct with `before` and `after` vectors of existing `SuppressedTriggerEvent`, not unlabelled booleans, strings, or a new Hushbringer enum variant.
- The event-boundary capture belongs to `game/zones.rs` and the existing simultaneous producers; applicability/matching belongs to a shared `game/trigger_suppression.rs` helper module; timing selection belongs beside `zone_change_clause_matches` in `game/trigger_matchers.rs`. `game/triggers.rs` consumes that shared predicate in every collection path.
- No transport, AI policy, frontend, or dormant mtgish changes. No new enum variant is proposed, so `cargo engine-inventory` and the add-engine-variant checklist are not applicable and were not run during this no-build planning task.

## Analogous Trace

Read/traced these current paths (some skill paths are stale because oracle_static is now a directory):

1. Suppression: `types/statics.rs::SuppressTriggers` → `parser/oracle_static/restriction.rs::parse_suppress_triggers` → `parser/oracle_static/dispatch.rs` → `parser/oracle_static/tests.rs` → `game/functioning_abilities.rs::battlefield_active_statics` → `game/triggers.rs::active_suppress_trigger_statics` → collection and `matching_batched_trigger_events` → standard stack placement/resolution.
2. Dies: `parser/oracle_trigger.rs` (dies and put-into-graveyard branches, origin parsing, disjunctive clauses) → `types/ability.rs::TriggerDefinition` / existing `OriginConstraint` → `game/trigger_matchers.rs::match_changes_zone`, `match_changes_zone_all`, `match_leaves_battlefield`, `zone_change_clause_matches` → `game/triggers.rs::collect_matching_triggers_inner`, LKI/self/off-zone/co-departed scans → `game/stack.rs` standard resolution → `game/scenario.rs` cast driver.
3. Simultaneous death observer: `game/effects/destroy.rs::resolve_all` → replacement handling → `game/zones.rs::move_to_zone` → `game/game_object.rs::snapshot_for_zone_change` → `ZoneChangeRecord` → `mark_simultaneous_departures` → co-departed collection in `game/triggers.rs` → tests `dies_observer_killed_in_same_sba_batch_fires_for_each_simultaneous_death` and `dies_observer_does_not_observe_sequential_departure`. Also read the cast/trigger conventions in `tests/integration/curse_co_departed_enchanted_player_trigger.rs`.
4. Required static-skill analogous trace: `database/synthesis.rs::synthesize_changeling_cda` → `types/ability.rs::ContinuousModification::AddAllCreatureTypes` → `types/layers.rs` → `game/layers.rs::gather_active_continuous_effects` and `apply_continuous_effect_to`. This confirms layer-backed characteristics should be consumed, not reimplemented in suppression.

## Implementation steps

All paths below are relative to `/Users/nishadsingh/repos/phase-verifiable-loop`.

### 1. Characterize behavior before changing it

Create `crates/engine/tests/integration/trigger_suppression_event_timing.rs` and register it in the already-read `tests/integration/main.rs`. Add the primary Wrath test and unsuppressed positive twin first. Use full, verbatim Oracle text above; use `from_oracle_text_with_keywords` for keyword-bearing fixtures as instructed by card-test. Cast through `GameScenario` + `GameRunner::cast(wrath).resolve()`, fund WWCC, inspect CastOutcome zones and Spirit count. Assert zero unimplemented effect entries and the expected functioning suppression static before casting. Reverse insertion order as a second runtime case. Record the baseline failure before implementation using the caller's permitted build workflow.

### 2. Introduce event-local before/after suppression data

Modify `types/game_state.rs::ZoneChangeRecord` with an optional, serde-defaulted `trigger_suppression` snapshot. `Some` with empty vectors means authoritatively unsuppressed, and **must not fall back to live state**; `None` identifies legacy/synthetic records whose event-time context was not captured. Define the small snapshot struct here, using existing `SuppressedTriggerEvent` values in canonical order.

Initialize the field in `game/game_object.rs::snapshot_for_zone_change` and `ZoneChangeRecord::test_minimal`. Set `None` in non-event synthetic constructors already read in `game/filter.rs::matches_target_filter_on_lki_snapshot` and `game/stack.rs::zone_change_record_from_spec`. Search all `ZoneChangeRecord {` literals and update only exhaustive constructors; struct-update test constructors inherit the default. Add round-trip/default compatibility coverage in the existing `types/events.rs` serialization tests. The Debug golden in `tests/integration/loop_shortcut.rs` must receive only the mechanically added `trigger_suppression: None` field for its non-battlefield records, preserving its historical event sequence and every other byte.

Add `game/trigger_suppression.rs`, register it in `game/mod.rs`, and move the existing active-static filtering and subject matching into it. Provide one shared evaluator usable by both live ETB checks and event snapshots. No card-name checks and no duplicate filter semantics.

### 3. Capture at actual single/group boundaries, not at eventual trigger collection

In `game/zones.rs`, add paired helpers to capture suppression for a specified set of candidate battlefield objects before an action and attach completed before/after results to **only the ZoneChanged events produced by that action**. Capture the before result against the pre-action layer-resolved board. Once that logical action finishes, evaluate the after result against the post-action functioning suppressors, using the departure record's pre-death creature characteristics where the Hushbringer ruling requires them. Filter actual events by source zone, object, and event index/range; attempted-but-prevented members get no departure snapshot.

Single `move_to_zone` / `move_to_library_at_index` departures get a one-object context. Simultaneous outer producers must capture their candidates **before the first move**, and finalize once for the whole group, overriding intermediate per-object defaults. This avoids both insertion-order dependence and querying a former controller in the graveyard. `co_departed` remains the authority for grouping, with exact event sub-slices. A group of zero or one still finalizes snapshot data; the current `group.len() < 2` shortcut may skip co-departed IDs, but must not skip capture/finalization.

Wire the same helpers at existing production boundaries already inspected:

- `game/effects/destroy.rs::resolve_all`: matching set before the replacement/move loop, finalization with `departed_subset` after it. Preserve indestructible/regeneration/replacement handling.
- `game/sba.rs::check_state_based_actions`: capture once per applicable SBA **iteration**, after the existing layer flush, and finalize the iteration's actual departures. Do not let per-category zero-toughness/lethal/legend passes become independent suppression worlds, and do not carry a context into a later fixpoint iteration.
- `game/zone_pipeline.rs::move_objects_simultaneously_then` / `deliver_batch`: all request IDs before delivery; finalize the supplied action's event slice.
- `game/effects/change_zone.rs` targeted/mass multi-object loops and `game/effects/mod.rs::drain_pending_change_zone_iteration`: capture/finalize each complete, uninterrupted logical move instruction. Preserve and characterize the existing per-segment behavior on paused paths; the cross-pause observation limitation below remains out of scope.
- `game/effects/sacrifice.rs` all-eligible fast path; `game/effects/mod.rs::perform_player_scope_sacrifices`; `game/engine_resolution_choices.rs` chosen-permanent movement: capture after selections are known and before moving them; finalize **before** resuming a subsequent instruction. The currently observed choice handler stamps after `resume_with_error_propagation`; move timing finalization ahead of that call so later instructions cannot change this event's post-state.
- `game/casting_costs.rs` existing calls to `mark_simultaneous_departures`: capture/finalize each existing simultaneous cost component independently. Never merge separate cost components merely because both have sacrifice events.

Avoid cloning whole GameStates. Evaluate each candidate once per logical boundary, and keep the no-suppressor path cheap. Shared context must be an owned value suitable for pending-state serialization, with already-evaluated outcomes, not raw static definitions that will later read live state.

**Pause boundary — explicit pre-existing limitation, out of scope:** the base documents a cross-pause simultaneous-observation gap (`triggers.rs::ltb_observer_cross_pause_co_departed_deferred`, ignored; `zone_pipeline.rs` batch docs; `effects/mod.rs` drain comments). Per the orchestrator's bounded-scope instruction, do not add an event-retention scheduler, widen continuation carriers, or repair full cross-pause simultaneity in this change. The existing paused producers stamp and collect per segment; preserve that behavior and characterize it separately. Snapshot finalization must occur before collection for every segment the existing engine regards as complete, and the new snapshot data on already-emitted records must survive serialization. This does not claim that segment boundaries are the correct full rules event. The original ignored test and its explanation remain. The unpaused Wrath, single moves, sequential instructions, and complete producer groups are the acceptance scope. If correctness of an acceptance fixture unexpectedly requires the deferred cross-pause machinery, report that scope conflict to the orchestrator instead of silently expanding implementation.
### 4. Apply suppression to matching trigger clauses

Modify `game/trigger_matchers.rs::zone_change_clause_matches` and its callers so the existing typed origin/destination information determines suppression timing for the **matching clause**. Scalar origins and `origin_zones` must use the same normalization already employed by `match_changes_zone`; do not create separate string classification or select timing from the physical event's `from` alone.

- A battlefield-origin dies/LTB clause uses the snapshot's before result.
- A graveyard-from-anywhere clause uses the after result; `OriginConstraint::Any` must not become LTB because this particular card died.
- Preserve the official self-from-anywhere exception: a dying card's ability that triggers on its own arrival from anywhere is checked as a destination/new-object ability. It must not be rejected by a death-event suppression gate. Express this using source/subject identity, the clause's typed SelfRef semantics, its origin, and destination-zone function—not a named-card exception. Add an explicit test of this rule before finalizing its implementation.
- For `zone_change_clauses`, a definition fires if any **matching and unsuppressed** clause qualifies, once for this occurrence. A suppressed death clause must not suppress another eligible clause. Preserve existing dedup and batched behavior.
- Retain current ETB causal suppression and ward-only suppression as separate unchanged semantics. Do not apply a saved death snapshot to exile, bounce, sacrifice-cause events, phase changes, or ward. The death-specific timing change does not authorize a generalized reinterpretation of all the other CR 603.10 exceptions.

In `game/triggers.rs`, remove the whole-event death `continue`; keep the event-wide ETB fast path where valid and route scalar, batched, self-LKI, co-departed, off-zone, and trigger-index shadow matching through the shared clause predicate. `matching_batched_trigger_events` must filter with the same semantics as first-match registration. Check `source_was_not_co_departed_into_zone`: its existing Recover protection cannot become a blanket rejection of destination-functioning self/from-anywhere abilities. Keep Recover-style before-event availability distinct from a new object's self-arrival ability. Do not change constraints, APNAP ordering, targeting, or stack resolution logic.

For old records with no snapshot, retain the existing live behavior as an explicitly documented legacy fallback; do not claim old already-emitted events can reconstruct missing history. All new production death events and all new regression fixtures must contain authoritative snapshots.

### 5. Verify and record the boundary of the fix

Follow the matrix below, then run formatting and the permitted engine verification workflow. Frozen harness case/corpus/checker stay unchanged for before/after comparison. A fresh rebuilt worker against the changed Phase checkout must turn the original violated assertion into satisfied twice with identical semantic evidence per revision. The original baseline worker must still fail it. Record both worker hashes; do not overwrite campaign-002.

## Verification Matrix

All negative assertions have a paired positive reach guard. Typed fixtures below are named as engine building-block fixtures, not as paraphrased named-card Oracle. Cast tests use CastOutcome and actual Oracle; helper tests supplement rather than replace them.

| Claim and seam | Production path/test | Required assertion, positive reach guard, and failure discrimination |
|---|---|---|
| Hush dies simultaneously; before snapshot / matcher | Wrath cast pipeline, both insertion orders | Hush + Traveler + Wrath in graveyard, stack settled, zero Spirit. Paired no-Hush cast produces exactly one Spirit. Original base fails zero assertion. |
| Self and observer death triggers share suppression | Wrath plus an independent surviving and a co-dying death observer | All intended victims depart; no Traveler token or observer life delta. Same observer fixture without suppressor gains life for each actual victim. This catches limiting the fix to the dying source's own ability. |
| Sequential events are separate | One typed chained effect removes Hush then Traveler; reverse order in a second case; drive via apply/scenario | Hush-first allows one Spirit; Traveler-first allows zero. Both cards demonstrably move, and the unsuppressed control creates a token. Inspect distinct co_departed groups and event indices. A resolution-wide cached suppression set fails one order. |
| From-anywhere is not LTB | Surviving typed from-anywhere graveyard observer beside a dies observer, Wrath | With Hush co-dying, from-anywhere observer fires while dies observer is blocked. Hush remaining alive blocks the creature-death-caused observer. Both observer definitions positively match/resolve without Hush. |
| Self from-anywhere exception | Typed self-from-anywhere destination-functioning trigger on the dying subject, Hush survives | Its positive effect occurs while ordinary self-dies is blocked; prove source/destination matching and no Unimplemented. This must be verified independently of the observer test. |
| Clause-local and batched decisions | Existing `zone_change_clauses` and `batched` paths through `match_changes_zone` / `matching_batched_trigger_events` | Suppressed clause alone gives no effect; an eligible sibling clause gives one effect; two eligible clauses for one occurrence still give one registration. Positive reach guard: both clauses independently match in no-suppression controls. |
| Correct controllers and conditions | Two typed suppression sources under different controllers, owner != controller victim, conditional source whose condition changes as group leaves | Only the pre-event matching subjects are suppressed, regardless of departure order. A nonmatching subject's trigger fires. Rebind/control-change between distinct events affects the next event only; earlier recorded outcome remains stable. |
| Effective abilities/types, not printed text | Layer-granted/removed suppression, phased-out source, animated noncreature victim | Active counterpart blocks; stripped/phased-out counterpart permits the same positive token/life effect. Animated victim is suppressed when a creature immediately before death; noncreature sibling is not. Positive type/ability assertions occur after layer flush and before cast. |
| Replacement and no-op branches | DestroyAll indestructible/regeneration; death redirected to exile; empty board | Guards prove attempted spell resolves and expected victim zones/survivors. Exile produces no dies trigger but a matching exile/LTB sibling triggers. Empty board has EffectResolved and normal priority. No stale suppression/group is installed for prevented members. |
| Distinct cause events unaffected | Sacrifice with both sacrifice-cause and dies listeners | Sacrifice event positive listener fires; dies listener is blocked by Hush. Torpor Orb blocks ETB but permits Traveler death. Existing ward and transform-on-reentry tests stay green. |
| SBA logical boundary | Damage sweep killing Hush + Traveler, plus successive-SBA-iteration fixture | Same-iteration death blocked; later-iteration death after Hush is gone allowed. Guard actual lethal/zero-toughness departures and count one Spirit in positive twin. Avoid conflating per-category passes with CR 704.3 iterations. |
| Pause and serialization boundary | Force replacement ordering in a mass move, serialize/deserialize parked GameState, resume | Already-emitted snapshots and exact event identity survive serialization. Verify no regression to the base's completed-segment behavior; retain the ignored cross-pause observer characterization. Unpaused parity is the desired future full-group behavior, not an asserted repaired capability in this patch. |
| Legacy compatibility | Existing GameEvent and pending-state JSON missing added fields; populated new snapshot round-trip | Old JSON loads; missing remains None. New authoritative empty snapshot stays Some(empty) and does not begin suppressing after an unrelated suppressor enters. Positive counterpart with a captured Dies suppression still blocks after the source disappears. |

For each suppression negative, inspect at least the first reached branch: snapshot present vs legacy fallback; active static iterator; event category match; matching scalar/disjunctive origin; `source_filter` result; batched dedup. No negative may be satisfied solely because a card did not parse, cast did not commit, the victim survived, a target prompt remained unanswered, or no matching trigger existed.

Run existing `suppress_triggers_*`, co-departed observer, Recover/off-zone, trigger-index audit, batched trigger, ward, and transform-on-reentry tests. Existing APNAP/once-per-turn/intervening-if tests protect unchanged constraints and stack machinery; the two-player observer fixture also checks that surviving unsuppressed sources keep normal ownership/order. Recheck the Scute Swarm/trigger throughput benchmark if the new shared predicate changes the hot candidate loop; absence of any suppressor must avoid per-candidate full-board rescans.

## Skill Checklist Disposition

Applied/read engine-planner, add-trigger, add-static-ability, card-test, and project-reference.

- Add-trigger type/condition/constraint phases: existing types suffice; no new variants.
- Event emission phase: extend event context at zone producer boundary, not a new GameEvent.
- Matcher/registry phase: extend existing registered zone matchers; no new registry entry; verify all existing aliases still reach them.
- Target extraction phase: unchanged; effects and targets are unchanged.
- Parser and parser tests phase: no grammar change; existing Hushbringer/dies/from-anywhere shape tests plus runtime fixture parse reach guards verify current representation. No accepted text with deferred semantics is added.
- Constraint tracking phase: unchanged; use existing per-event and batched dedup.
- Stack resolution phase: unchanged standard path; no raw `resolve_top` test shortcut.
- Add-static type/layer/condition/keyword-fixup phases: no new static or continuous modification; consume existing layer/functioning-ability authority.
- Add-static parser/dispatch/snapshot phases: unchanged; no parser snapshot refresh required.
- Non-continuous static consumer phase: suppression matching is the owning consumer being repaired.
- Tests/verification phases: full matrix above, no vacuous negatives, formatting plus fresh engine evidence.
- Nom Compliance: not applicable; no parser file is proposed for modification. If implementation discovers grammar work, return to planner/oracle-parser rather than inserting ad hoc string detection.
- Variant Discoverability: not applicable; no new enum variant. If implementation adds one anyway, it must first read/run add-engine-variant and consult freshly generated inventory.
- Skill self-maintenance: report stale skill references (`oracle_static.rs` moved, and some CR reference table meanings are inaccurate); do not use those table descriptions as verified law. No unrelated skill-file edits are required for this fix.

## Identity / Provenance Contract

The authority is a **single logical zone-change action**, not a card name, current graveyard object, turn-wide death list, or entire resolution. Bind pre-event suppression outcomes before any member moves, using each source's then-current controller, condition, effective ability and each subject's characteristics. Bind post-event outcomes after that action completes and before the next written instruction/SBA iteration. Store on its ZoneChangeRecord. Complete groups use their producer context; the existing paused-segment limitation remains explicitly separate and is not repaired here. Source/subject ObjectIds identify members, and `turn_zone_change_index` plus bounded producer event slice prevent a later incarnation of the same storage ID from receiving an earlier snapshot. A snapshot's lifetime follows its concrete event through collection/replay; no global lingering suppressor set is installed.

Timing selection is by the matching typed trigger clause. `co_departed` is group provenance, not proof that every possible trigger is an LTB trigger. The multi-source controller/condition fixture, both sequential orders, blink/repeated-ObjectId fixture, and old-empty-vs-new-empty round-trip test prove these bindings. Expire any temporary producer context exactly once at completion/cancellation; it may not bleed into the next move instruction. Do not invent a new cross-pause continuation contract in this bounded change.

## Serialization, validation, rollback, and limits

Adding the optional event snapshot field is additive JSON evolution: serde default and omission for None preserve loading old saves. An authoritative empty value must remain distinguishable from a missing value. No card-data AST variant or schema change, client decision logic, or mtgish mirror is needed. Engine GameEvent Debug output changes mechanically; update only the added field in the existing historical golden. Transport serialization must carry the new data without computing any rule.

The implementation caller should run `cargo fmt --all`. Follow project-reference: use fresh, terminal Tilt results for clippy/test-engine/card-data when Tilt watches the changed checkout; exit 3 from tilt-wait means unavailable/wrong checkout, not failed code. A green main-checkout build does not validate this worktree. Direct builds/tests only if Tilt is confirmed down or a separately authorized isolated workflow is available. This planning agent ran none of these commands.

Rollback discrimination: retain original frozen inputs and original worker hash. New worker must satisfy the primary case twice, preserve no-Hush positive behavior and all corpus siblings, and pass the specific per-seam positive/negative tests. Reverting event capture must fail the simultaneity/order tests; reverting clause timing must fail from-anywhere coexistence; dropping event-snapshot serde carry-through must fail its round-trip/provenance test. Do not “fix” the checker, expected assertion, Oracle text, or source corpus to manufacture a pass. Distinguish compilation failure, unavailable/stale build evidence, fixture setup failure, semantic assertion failure, and known pre-existing ignored cross-pause observer failure in the receipt.

The required no-pause bug is well established. Full cross-pause simultaneity is an adjacent existing architectural gap explicitly excluded by the orchestrator; it must not disappear into a passing primary-case claim. Preserve its existing ignored characterization and report any regression separately. No unsupported card is promoted based only on parse success.
