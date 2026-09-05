# Hushbringer plan review — revisions required

Three blocking gaps were found. The proposed event-local before/after outcomes are a sound direction, and the primary Wrath case is explained correctly, but the stated producer and matcher coverage is incomplete. A revised full plan should address the three bounded gaps below before implementation.

Reviewed the complete `/home/ubuntu/coworld-migration-20260904/hushbringer-plan.md` against Phase commit `2dec6c88915db4697706234a7ba2fcedd97b1689` in `/home/ubuntu/repos/phase-verifiable-loop`. All inspection and this report's creation ran on EC2 through `ssh nishadsingh-box-4`. No engine implementation, builds, tests, or commits were performed. The working tree was clean at the end of inspection.

## 1. [P1] The removed event-wide death gate currently protects Haunt's independent matcher

**Plan location:** step 4, lines 106–116; verification matrix.

**Evidence:**
- `crates/engine/src/game/trigger_matchers.rs:30` dispatches `TriggerMode::HauntedCreatureDies` directly to `game/haunt.rs::match_haunted_creature_dies`, rather than to `zone_change_clause_matches`.
- `crates/engine/src/game/haunt.rs:125–149` matches battlefield-to-graveyard events by the creature's recorded types and its Haunt link. It never calls the zone-clause predicate or a suppression predicate.
- `crates/engine/src/database/haunt.rs:137–150` constructs this production trigger with `trigger_zones = [Exile]`. Its origin and destination are not encoded as an ordinary battlefield-origin clause; the dedicated matcher owns those semantics.
- The off-zone collector in `game/triggers.rs:2200ff` reaches this matcher. Today the whole-event gate at approximately `triggers.rs:1501` stops it while Hushbringer is active. The plan removes that gate and specifies suppression in the ordinary clause matcher, leaving this independent route unprotected.
- Existing `game/haunt_tests.rs:431` (`haunt_payoff_fires_from_exile_when_haunted_creature_dies`) confirms this is an implemented runtime consumer, rather than a hypothetical variant.

**Consequence:** following the stated changes would introduce a regression: a haunted creature dying while Hushbringer remains on the battlefield would trigger the exiled card's Haunt payoff. The same omission would also leave the simultaneous-death form unfixed. An exiled trigger source does not make this a from-anywhere trigger; its condition is the haunted creature dying.

**Required revision:** explicitly trace and route this dedicated death matcher through the shared suppression authority with battlefield-origin/look-back timing, preserving the existing Haunt-link subject identity. Do not infer timing solely from the source's current zone or from unset scalar origin fields. Enumerate the dedicated zone-event matcher routes in the scope matrix so removing the broad gate has a complete replacement.

Add a production-path regression using an already established Haunt link and an exiled payoff source: kill the haunted subject with Hushbringer surviving, and kill it together with Hushbringer. Both suppress the payoff. A paired no-Hush run must resolve the payoff, with the link and actual death asserted as reach guards. The existing standalone Haunt positive test is useful supplementary coverage but does not exercise the proposed gate. Include a sequential Hush-first positive if this matcher is given a separate timing adapter. Coverage/card-data status remains unchanged.

## 2. [P2] Existing choose-and-sacrifice-rest groups are omitted from capture wiring

**Plan location:** step 3's producer list, lines 92–99.

**Evidence:**
- `crates/engine/src/game/effects/choose_and_sacrifice_rest.rs::sacrifice_unchosen` collects the complete `to_sacrifice` set at lines 544–556, then moves members through `sacrifice_permanent` individually at lines 558–577.
- Four existing complete-group producers call this helper and stamp their event slice: `choose_and_sacrifice_rest.rs:129`, `:171`, `:307`, and `:417`. These include automatic category choices, the terminal APNAP sweep, and total-power keep choices.
- `engine_resolution_choices.rs:4546` stamps the CategoryChoice route before trigger dispatch as well. This is a separate route from the EffectZoneChoice chosen-permanent handler around line 3862 discussed explicitly by the plan.
- `zones.rs::stamp_simultaneous_from_slice` currently only sets `co_departed` after movement. Extending ordinary single-object movement with snapshots cannot retrospectively recover the pre-sweep suppressor state at this post-movement stamp.

**Consequence:** Hushbringer and Traveler sacrificed in one completed keep-some/sacrifice-the-rest sweep still receive sequential one-object snapshots unless the outer producer captures first. When Hushbringer is earlier in the sweep, Traveler becomes authoritatively unsuppressed; reversing the order changes the outcome. This contradicts the plan's complete-group acceptance scope and preserves the same failure class outside DestroyAll.

**Required revision:** name this module and all complete entry/selection branches in the producer inventory. Prefer capturing once around the shared `sacrifice_unchosen` sweep, after the kept set and scoped players are known and before its first actual sacrifice, with exactly one completed-group finalization before a continuation/trigger scan. Audit both `mark_simultaneous_departures` and `stamp_simultaneous_from_slice` callers; an inventory of the former alone misses these existing authorities.

Add cast/apply coverage for a completed CategoryChoice sweep that keeps a third creature while sacrificing Hushbringer and Traveler in both insertion orders. Assert the kept object survives, both intended victims move, no Spirit appears, and the no-Hush twin produces a Spirit. Exercise an automatic/terminal branch and the total-power branch, or demonstrate in the revised trace that all now share the same capture/finalization seam and supply an appropriate reach test for each bypass. Preserve scoped-player and sacrifice-cause behavior.

This finding requires no cross-pause event-retention machinery. Choices before the first sacrifice can complete normally; replacement pauses during the sweep retain the plan's documented limitation.

## 3. [P2] Multi-target Destroy bypasses the proposed DestroyAll boundary

**Plan location:** step 3, line 94, plus the claim to repair complete producer groups.

**Evidence:**
- `crates/engine/src/game/effects/mod.rs:3145` routes `Effect::Destroy` to `destroy::resolve`; `:3164` routes `DestroyAll` separately to `destroy::resolve_all`.
- `crates/engine/src/game/effects/destroy.rs:217–225` loops all targets of one Destroy effect, calling `destroy_single_object` for each. It neither calls `resolve_all` nor the simultaneous batch helper.
- The plan lists only `destroy::resolve_all`. Its new single-object snapshots would therefore record the later target after an earlier Hushbringer target has already departed.
- CR 608.2f, independently verified in the current rules file, makes a single action involving several objects simultaneous in the ordinary case. This is a printed category: the current Scryfall Oracle response for [Curtains' Call](https://scryfall.com/card/otc/130/curtains-call) contains a two-target destruction instruction. The code's independent multi-target handler establishes the concrete engine reachability.

**Consequence:** a single unpaused multi-target Destroy targeting Hushbringer and Traveler remains target-order dependent despite fixing Wrath. This is another immediate consumer of the same reusable suppression boundary, not a request to add a new mechanic.

**Required revision:** include `destroy::resolve`'s full target action in the capture/finalization design, with one pre-action context over candidate targets and an event-bounded completion over actual departures. Preserve the self-reference case, per-target legality, indestructibility, regeneration, replacements, and the existing pause limitation. Group one Destroy instruction; do not join distinct chained Destroy instructions or separate cost components.

Add a cast-pipeline regression for a two-target Destroy with both target orders (verbatim current Oracle if using a named card, or a clearly labeled typed building-block fixture), plus no-Hush positive and a prevented/indestructible-member sibling. Assert actual deaths and the Spirit count, and retain the existing sequential-instruction tests to distinguish one multi-target action from two separate actions. Reverting this producer capture should fail the target-order regression. Runtime coverage improves; card-data support counts stay unchanged.

## Checks that passed

- **Card and rules premise:** independently fetched current Scryfall Oracle text for Hushbringer, Doomed Traveler, Wrath of God, and the multi-target destruction example. Independently read the Hushbringer section of the [official Throne of Eldraine release notes](https://magic.wizards.com/en/news/feature/throne-eldraine-release-notes-2019-09-20). It supports simultaneous suppression, the from-anywhere distinctions, the self-arrival exception, pre-death creature characteristics, and unaffected sacrifice-cause triggers.
- **CR verification:** the ignored rules file was absent after migration. Ran the repository's fetch script remotely, which downloaded Wizards' current `MagicCompRules 20260819.txt` into `docs/MagicCompRules.txt`. Verified the plan's rule families against that text, including 603.2/603.2c, 603.6a–d, 603.10/603.10a, 611.3a–b, 613.11, 700.4, 608.2c/608.2f, 704.3, 400.7, and 113.6/113.6k. Also verified 603.2g and 704.7: the plan correctly rejects their existing inaccurate use. Haunt's 702.55a–c was verified for finding 1.
- **Root cause and reusable design:** the active-static list is collected after battlefield departures, while Traveler's death ability remains discoverable through LKI/off-zone collection. Recording evaluated outcomes at producer boundaries addresses source conditions, controller-relative filters, and sequential events without reviving dead statics. This is a class-level repair.
- **Reuse and layering:** the plan appropriately keeps runtime logic in game modules, reuses functioning-static/layer/filter authorities, and does not require new parser grammar, trigger/static variants, transport logic, or frontend logic.
- **Typed data and compatibility:** an optional, serde-defaulted before/after outcome structure distinguishes missing legacy context from authoritative empty outcomes. The identity/event-index contract and prohibition on resolution-wide grouping are sound.
- **Verification approach:** the primary Wrath cast, unsuppressed positive twin, reversed order, clause/batch cases, controller/condition fixtures, replacements, serialization, and immutable frozen-harness inputs are appropriate. The missing seams above need their own additions.
- **Skills:** read the remote AGENTS.md symlink/CLAUDE.md, review-engine-plan, add-trigger, add-static-ability, and card-test instructions. No parser or new-variant checklist is required for the stated design. Stale skill references do not justify unrelated edits.

## Residual assumptions and bounded limits

The explicit pre-existing cross-pause simultaneous-observer limitation remains excluded. This review does not require widening continuation carriers, introducing a retained-event scheduler, or making the ignored cross-pause test pass.

The turn ledger receives a clone of ZoneChangeRecord before event finalization (`zones.rs:917–919`, `restrictions.rs:522–530`). Its existing consumers use it for data-driven history queries, not trigger collection. I did not treat synchronizing unused suppression metadata there as a gameplay blocker; implementation should state whether those non-dispatched ledger copies intentionally retain None or are synchronized, without adding a speculative replay subsystem.

No runtime result is claimed by this review. Baseline/fixed frozen-worker evidence and the plan's full verification matrix remain implementation gates owned by the caller. Re-review the entire revised plan after the three gaps are addressed.
