# Hushbringer v7 tests: structured partial handoff

**Status: partial; stopped for a demonstrated introduced regression; not accepted or ready to commit.** Root requested this final handoff for fresh v8 planning/review. No new mutations or production repairs were undertaken after the stop. All commands and file operations used SSH to `nishadsingh-box-4`; no local Mac writes/builds, subagents, commits, pushes or Coworld source changes.

Active `/home/ubuntu/repos/phase-verifiable-loop`, branch `codex/hushbringer-simultaneous-death`, base `2dec6c88915db4697706234a7ba2fcedd97b1689`. This executor owned only `crates/engine/tests/integration/trigger_suppression_event_timing.rs`, its existing module registration in `main.rs`, the original-source test overlay, and reports. Production peer owned all production/private test files. Its explicit authorization to touch active `src/lib.rs` changed only mtime to invalidate a stale build artifact; content hash stayed unchanged.

## Final verified results and exact evidence

- **Full active matrix:67 passed,4 failed,20 ignored** (91 named tests). Only the four deferred Composite component tests fail. Corrected natural hand-library choice passes.
- **Separate ignored desired diagnostics:2 passed,18 failed.** Passing rows are reversed aggregate payment and reversed inherited ParentTarget sacrifice. Their reached sequential order already suppresses that death; a passing order does not establish simultaneous grouping. They remain independently named diagnostics and are not promoted to repaired support.
- Prior equivalent original-source overlay: cost filter1passed/4failed; full serialized include-ignored run28passed/63failed. This older overlay still contains the failed exploratory Battlefield library-choice setup. The corrected hand-choice addition has no new baseline result from this executor.
- Exact final source: `hushbringer-v7-active-attempt-6/source.tar.gz`, SHA256 `5a83b7415c8668ee8c44595751e0139a2ca3b758b65da42870a963c930cbbb0b`; module SHA256 `9c910733be643af92021c946351b70d9e4dd6c8d8df1f92016f3980ebbaf4486`.
- Final logs: attempt6 `cargo.log` (verbose actual active library rebuild), `final-confirmation.log` and `final-confirmation.exit` (101 persisted remotely), `ignored-desired.log` (101). The first full log completed before an SSH timeout255; final confirmation resolves that transport uncertainty.
- `hushbringer-tests-v7-row-status.json` lists all91 test names/line numbers, active status, separate desired status, and prior baseline status. `hushbringer-tests-v7-source-stability.json` confirms every archived source/test file matches current bytes after the final run.
- `hushbringer-tests-v7-final-partial-module.rs`, `hushbringer-tests-v7-final-partial-main.rs`, and `hushbringer-tests-v7-final-partial-receipt.json` bind this released source and logs. Each attempt has its own source archive/manifest/receipt and a `run-results.json`; no failed attempt was overwritten.

Commands used the direct Cargo fallback authorized when Tilt was unavailable, with `PATH=/home/ubuntu/.cargo/bin:$PATH CARGO_BUILD_JOBS=4`. Final active command: `cargo test -p engine --test integration trigger_suppression_event_timing -- --nocapture --test-threads=1`. Desired diagnostics use `--ignored`. The actual rebuild used the same command plus `-vv`.

## Stop and new regression

Detailed report and exact tuple/source/log proof: `hushbringer-implementation-stop-v7-components.md` and `hushbringer-implementation-stop-v7-components-proof.json`.

A public cast uses existing `AdditionalCost::Required(AbilityCost::Composite)` with two separate one-creature Sacrifice costs, generic1 mana supplied by one colorless unit, and GainLife2. Both selections and actual commit execute; victims/spell reach Graveyard and life22. Deferred Hush-first then Traveler produces **original1 Spirit, active0, desired1**. Traveler-first produces original1/active0/desired0. Both trees join the two components in `co_departed`, incorrectly. Immediate zero-mana twins pass all four Hush/order combinations with empty peers and correct payoff.

V7 lines268/286 require closing before another component and never joining separate components. Existing `DeferredSacrificeSelection` retains only object/filter, and the pending list flattens all selections. The new commit scope wraps the whole list, converting lost component identity into an introduced payoff regression. The four active failing assertions remain intact and independently named; no compatibility waiver, parser expansion or production correction was made. Root is planning the missing component boundary in v8.

## Retained v6/v7 rows and approved dispositions

All original50 test rows remain represented. The only old test name removed is `resumed_change_zone_segment_captures_hush_and_traveler_after_natural_pause`, replaced by the three explicit v7 resumed/compatibility/unpaused rows and two desired-once diagnostics. All other original test names remain; regeneration/aggregate bodies changed only by reviewed v7 dispositions.

| Reviewed disposition | Reached active result | Separate desired diagnostic |
|---|---|---|
| A aggregate unless payment | Predecessor gain reaches life21; paid skips loss; decline16; real WardSacrificeChoice, invalid duplicate/empty/underthreshold and valid retry; no-Hush1, surviving-Hush single Traveler0 | Original following gain still fails20vs21; desired full group0 fails Hush-first, reversed order passes |
| B regeneration authority | Seeded existing shield first-application matrix16tuples: actual Regenerated, protected tapped/survives, no false death; prohibited regeneration actually dies; indestructible controls retained | Four actual cast-created shield lifetime cases fail protected-zone desired assertion after shield installation reach guard |
| C resumed ChangeZone | Real first-target ReplacementChoice, serde, remaining two-tail moves; authoritative exact records/peers emitted once; Hush0 both orders; narrow no-Hush2 compatibility; later unrelated Traveler+1 | Both desired resumed no-Hush1 cases fail2vs1; unpaused no-Hush remains exactly1 |

## Production-path coverage map

The v6 report's full path and maintainer tables remain explicitly bound for retained original rows; this table updates their status and adds v7 paths. **Every exact seam rollback is still pending: zero were executed.** Whole-original-source failures are not isolated seam evidence. A passing active loop proves every tuple ran; a failing baseline loop only proves the first failed tuple unless independently named.

| Behavior / changed seam | Concrete public entry and first branch | Runtime fixtures and result / unresolved discrimination |
|---|---|---|
| DestroyAll owner | Oracle Wrath cast, nonempty matching creature vector | Three original Oracle tests pass, exact0both Hush orders/1no-Hush; exact wrapper mutation pending |
| Targeted Destroy owner | Typed cast with two validated targets; guarded destroy_single_object | Two-target/indestructible/seeded-regeneration/redirect siblings pass; separate instructions remain separate; exact rollback pending |
| Targeted/mass ChangeZone | Cast explicit target loop or matching-set sweep | Original complete-producers and co-departed observer fixtures pass; exact each-producer rollback pending |
| All-eligible/player-scope Sacrifice | Cast count admits all eligible / completed scoped selections | Original complete-producers pass, actual zones/groups/payoff; each seam rollback pending |
| Keep sweep owner | Natural CategoryChoice, KeepWithinTotalPowerChoice, auto/empty routes -> sacrifice_unchosen | Original controls plus opponent-only scope, owner!=controller, keep and out-of-scope survivors pass |
| SBA per iteration | Actual damage/zero-toughness checks after apply | Normal complete producers, first-granter type/trigger preservation and next-iteration fresh world pass; no extra leaf-flush mutation yet |
| Augment owner handoff | Cast grants Augment; lethal observer then standalone Augment in same SBA | Both orders/no-Hush+1/Hush0 and no-grant/nonlethal controls pass. Removing only Augment handoff MUST still be proven to fail+1 and peers |
| Shared batch delivery | Public non-pausing BounceAll->Graveyard -> deliver_batch | Both orders/no-Hush1, exact peer groups, continuation gain2 pass; natural paused batch compatibility retained; helper bound to peer private tests |
| Resumed targeted iteration | Real first-target redirect choice -> drain_pending_change_zone_iteration | Tail Hush0/record identity/serde and narrow no-Hush2 pass; exact drain-owner rollback pending |
| EffectZoneChoice Sacrifice | Cast count2 of3 -> actual SelectCards | Existing choice/serde/retry plus actual chained later-Hush departure pass; chosen group closes before later instruction |
| EffectZoneChoice ChangeZone/BounceAll | Actual SelectCards corresponding arm | Both orders, selected-only victims, spare survivor, gain2,0/1Spirit pass; individual arm mutations pending |
| EffectZoneChoice PayCost | EffectPayCost exile2of3 with existing exile->Graveyard replacement | Natural EffectZoneChoice is_cost_payment, selected group and continuation pass; not confused with WaitingFor::PayCost |
| EffectZoneChoice library / library leaf | Natural Hand private-zone choice / targeted BF PutAtLibraryPosition | Original one-card and corrected two-of-three hand choices pass, exact nondeath observer+1, selected cards/unchosen survivor; targeted BF leaf and dynamic inverses pass. No BF-library-choice support claimed |
| Deferred one-component sacrifice cost | Cast selected Sacrifice2, final mana commit | Original multi-object and chosen-retry tests pass; new separate Composite component cases FAIL as stop above |
| Immediate cost handler | Real PayCost SelectCards spell/activation with rejection/retry | Existing8tuples and separate immediate Composite components pass; exact handler rollback pending |
| Standalone normal/library leaf after world | Actual scalar Sacrifice or targeted library move; departing grant/removal source | Dynamic grant/removal inverse+positive twins pass; peer immediate-return private test6 passes normal/library fourtuples without post-return flush |
| Merge/nested limitations | Real alternate Mutate cast -> ChooseMutateMergeSide, then grouped departure | Component routing/union keywords/zones/incarnation/non-BF component record controls pass; subject-first grant-payoff twin passes. Named merged intrinsic-flush desired later-member characteristic fails on original/active. Public Devour remains positive |
| Resolver reentry barrier | General resolve_ability_chain masks borrowed member | Private nested identity/barrier tests bound to peer. Exact production-reaching wrapper discriminator remains UNPROVEN; moving another candidate misses exact-id binding even without wrapper and is insufficient |
| Ordinary clause timing | Actual BF->GY events, EqualsBF versus Any clause, specific subject/destination | Before/after differences, Some(empty), duplicate disjunction, selfAny destination exception, identity reuse, wrong origin/subject and eligible sibling controls pass; exact matcher/collector mutations pending |
| Ambiguous origin compatibility | OneOf/NotEquals-other clauses through ordinary or registered delayed matching | Ordinary live collection and delayed ungated compatibility pass across no/surviving/co-dying Hush; not inferred before/after support |
| Delayed lifetime/alternatives/reflexive | Actual CreateDelayedTrigger cast and later matching event | Existing source/controller, one-shot/recurring, expiry, native sacrifice/exile and new primary/or alternative/co-death/unrelated/reflexive-empty rows pass; ambiguity desired suppression fails |
| Haunt/Unattach adapters | Linked haunted death / attachment fallback death plus native Unattached | Existing linked subject, missing-link, sequential/codie/no-Hush payoff, native cause and cleanup guards pass; each exact adapter rollback pending |
| Excluded aggregate/inherited/direct delayed | Natural unless selections / ParentTarget / five legacy direct condition routes | Retry/decline/current-controller/unauthorized nonanaphoric/identity/nondeath/lifetime siblings pass; separately named desired tests retain actual limits |
| Nondeath dedicated routes | Actual mill/exile, attack declaration, ETB | Milled/MilledOnce/MilledAll/Exiled, EntersOrAttacks attack, ETB-only suppression allows death, redirected LTB/exile positives pass |
| Effective suppression filters | Existing typed statics, actual control/combat/relation changes | Two simultaneous controllers, actual control rebind between events, owner!=controller, conditional, removed/phased/granted, attack-only and equipment-relative filters pass |

## Maintainer simulation matrix

Each row binds authority and timing explicitly. These are runtime observations/read traces, not substitute mutation proof.

| Entry / first branch | Authority and binding time | Storage / consumer / invalidation | Hostile fixture and serialization consequence |
|---|---|---|---|
| Destroy/change/Sacrifice/keep nonempty vectors | Existing validated victims; owner begins before first move | Private frame/member token claims exact ObjectId+incarnation+event index; snapshots on emitted records; close before next instruction | Reverse order/no-Hush/guarded nondepartures; no new choice carrier |
| SBA iteration / Augment subset | Layer-resolved iteration candidates; Augment borrows same owner | Owner closes once per iteration, exact peers consumed by off-BF observer; next iteration binds fresh world | Augment subject-specific+1 and successive-SBA controls; token never serialized |
| Batch deliver / resumed tail | Existing requests/remaining list at current synchronous invocation | Completed segment closes before completion/collection; pending continuation stores existing state only | Natural redirect pause/serde, exact tail record indices, later unrelated death; cross-pause full-group limit retained |
| EffectZoneChoice validated SelectCards | Current chosen cards/payer; capture after validation | Close before resume_with_error_propagation; existing tracked-set publication remains consumer authority | Invalid retry, selected/unselected, chained Hush; prior tracked-producer plus empty-choice sibling STILL PENDING |
| Deferred Composite | Announcement separates components, then pending flat list loses identity | Current entire-list owner at commit violates component lifetime; snapshot persists wrong before world | Hush-first introduced0vs1; fresh plan required for any storage/protocol change |
| Immediate component | Current selection/current controller at payment | Handler scope closes before finish_pending_cost_or_cast/next cost | Four order/Hush tuples, activation/spell rollback, owner graveyard pass; no new serialized field |
| Standalone leaf | Actual BF departure with no borrowed owner; before at entry/after at leaf return | Some authoritative snapshot including empty; no event means nothing attached; borrowed leaf cannot flush | Grant/removal inverse normal/library; private immediate-return6th gate; event field additive/default omitted whenNone |
| Independent nested resolver | Explicit barrier, not candidate overlap or call depth | Nested capturing ancestor prevents false fresh world; childNone cannot rewrite parent keys | Private helper identity/reuse/empty parent, public Devour; exact wrapper mutation not proven |
| Merged leaf | Existing merge component/routing authority inside normal parent member | Existing intrinsic flush stays; non-BF component events excluded from peers | Real mutate controls/desired type loss; no merge/layer repair or parser promotion |
| Ordinary clause matcher | Matched clause and event's subject/filter/origin | EqualsBF readsbefore, Any readsafter; self exception follows destination; authoritativeSome prevents live fallback | Clause-local alternatives, Someempty/reused storage id; snapshot travels with event clone/replay |
| Delayed creation/match | Source/controller/payoff bound at real creation; suppression selected per later occurrence | Existing listener owns lifetime; eligible one-shot consumes, recurring retains; unmatched reflexive disposed | Suppressed then eligible event, alternative once, cleanup and unrelated identity; no latched suppression on listener |
| Ambiguous/direct excluded consumer | Existing matched OneOf/NotEquals or legacy direct mode | Ordinary live versus registered ungated compatibility retained; legacy bypass unchanged | Primary/or/reflexive/co-death variants and five desired legacy diagnostics; no inferred provenance field |
| Haunt/Unattach | Existing linked subject/attached relation selected before shared death predicate | Uses matched record's before; native cause retains native authority | Linked subject and native sibling payoff reach guards; no link protocol change |
| Effective filter evaluation | Current controller, conditions, combat and attachment relation at event boundary | Captured outcome values, not a cloned/restored board; later control/relationship does not rewrite history | Two-source controllers, actual rebind, attacking filter, attachment relation, stripped/phased source pass |
| Private GameState carrier | Synchronous closure stack and allocator only | Balanced before/after normal/error/pause, empty at outer close; serde-skipped defaults on restore | Peer six private tests include actual natural pause pre-serde memory inspection; public roundtrip cannot alone prove in-memory emptiness |

## Explicit unfinished obligations

1. Fresh v8 repair of deferred component identity and all four failing tuples, including genuine introduced Hush-first regression. No active failure may be ignored as compatibility.
2. **All exact isolated source rollback/mutation proofs remain undone.** Include every producer, individual EffectZoneChoice arm, matcher/adapter, finalization, Someempty/serde, Augment-only token handoff, and added member-flush failure with negative/sibling controls. Root deferred these to the final-source executor.
3. Real-pipeline resolver wrapper-only discriminator remains unproven; do not label another-candidate move or helper-only test as proof. Use current exact ObjectId/incarnation matching trace.
4. Earlier tracked-set producer plus empty-choice sibling at moved EffectZoneChoice boundary remains pending. Existing tracked publication is not fully discriminated by current gain-only continuations.
5. Complementary OneOf parser SHAPE convention guard remains pending; typed runtime fixtures do not prove parser output shape. No parser/card support claim is made.
6. Original-source/new-source per-case evidence needs future isolated-target confirmation where required. Older full baseline loops stop at first failure and were built in shared target; they are historical evidence with the cache limitation below. Root separately reports a freshly isolated original worker9pass/1target failure; that worker receipt is root-owned, not this executor's integration gate.
7. Full engine test, existing guard suites/benchmark, scoped/full Clippy disposition, final card-data, fresh implementation review, final clean worker comparison/acceptance and commit remain peer/root-owned. Do not infer pass from the integration matrix.

## Build provenance correction and retained attempts

Attempt1 is a fixture ownership compile error; attempt2 reached61pass/3fixture failures/20ignored; attempt3 reached66pass/2fail/20ignored; attempt4 independently exposed four deferred tuples and retained the extra library fixture failure. Attempt5 is a compile-only **stale shared-target original-library mismatch**: active integration referenced trigger_suppression while linked original ZoneChangeRecord lacked it. No source field was removed. Attempt6 forced active lib.rs mtime dirty, and verbose rustc invocation records `CARGO_MANIFEST_DIR=/home/ubuntu/repos/phase-verifiable-loop/crates/engine`; final current-byte matrix is67/4/20.

Root requires **distinct target directories for active, original-source and mutation worktrees from now on**. Active remains its own `target`; the baseline overlay must never again use active/target. One warm mutation target may be reused only inside one isolated mutation worktree with exact restores/source records. The prior shared-target baseline run is not relabeled as a newly isolated build. Root will separately certify clean workers.

Each v7 attempt retains exact full source and logs. The v6 historical attempt4 active source had only hashes, not exact retained bytes; the v6 report already discloses that retention gap. This final snapshot is not substituted for any earlier source.

## Formatting, CR, parser honesty and peer binding

Owned module/main rustfmt checks and combined `git diff --check` passed after final source; main check used skip_children to respect ownership. `hushbringer-tests-cr-audit-v7.txt` verifies all23 annotated CR numbers against current `docs/MagicCompRules.txt`, zero missing. Rules were read for their annotated purposes during fixture work. No comment cites a known compatibility defect as correct rules behavior.

Named Oracle claims are limited to the exact Hushbringer/Doomed Traveler/Wrath fixtures, with Hush keyword-aware parsing and actual Wrath WWCC payment. Other cards are explicitly typed existing building blocks. No parser production file changed, no card-data/coverage promotion, no card-specific engine patch. The extra attempted BF library-choice fixture was not production-reachable as set up: empty-target private-zone scan allows Hand/Library, while its BF filter announces a target. It was corrected to a natural two-of-three hand choice; archived failures remain separate, and no BF-choice support is certified.

Production peer `/root/hushbringer_impl_production_v6` retains source/private/full-gate ownership until its own final handoff. Bind `hushbringer-implementation-production-v6.md` and its forthcoming v7 partial report, rather than copying pending rows as passes. Peer communicated private6 passed6/6 in `hushbringer-production-private-v7-attempt-3.log`, including immediate normal/library leaf-return grant/removal inverses. Earlier workspace Clippy failed unchanged manabrew-compat missing SetFullControl after environmental prerequisites were installed; scoped engine Clippy, isolated original compat reproduction and card-data were in peer's queue at this handoff. Full engine is explicitly deferred while active four failures remain.

## Ownership release

This executor releases the active integration module/main and original-source test-only overlay to root/the fresh v8 executor. Cargo was explicitly handed to the production peer after final confirmation and desired diagnostics. No source writes, Cargo, mutations, commits or pushes will follow this handoff. The four active deferred-component failures remain visible; all20 desired diagnostics retain individual identities. This is a structured partial return for a revised plan, not completion of the original implementation task.

Final peer gate update: private6 passed; scoped engine all-target Clippy passed; original manabrew failure reproduced in its own target (expected101); card-data exit0 with exact token/subtype restoration; final fmt/diff checks passed. Peer2051-file source manifest SHA256 `0301cf3cce5276bedb0ef6c68451c6ec81adf3cf3877cc1bad099a4c5aba9263`. Bind production final partial report/receipt for commands/logs; full engine remains deferred.
