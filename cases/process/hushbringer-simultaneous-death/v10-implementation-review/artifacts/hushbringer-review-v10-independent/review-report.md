# Independent implementation review: Hushbringer v10

Maintainer-Simulation Gate: FAIL

CR Annotation Gate: FAIL

## Findings

**[MED] Required native library-choice runtime coverage remains incomplete.** The changed natural-choice handler at `crates/engine/src/game/engine_resolution_choices.rs:3534` contains separate Bottom, NthFromTop and Top branches. Final source mapping honestly assigns no verified public tests to Bottom/NthFromTop and leaves Top order/rejection/Library-origin controls unresolved. The Top fixture at `crates/engine/tests/integration/trigger_suppression_event_timing.rs:4097` proves selected zones, event shape and nondeath payoff, but not library vector order or rejection. Existing Brainstorm public coverage proves part of Top ordering; the direct Nth resolver test bypasses the changed choice handler. Add or identify natural public-choice fixtures for the missing arms and controls, then bind exact results to the map. Private-zone subjects correctly have no owned departure; this does not need a fabricated mutation kill. Complete evidence: `native-library-map-finding.json`.

**[LOW] Moved and adjacent CR annotations cite unrelated or nonexistent rules.** Correct all five groups in `cr-findings.json`: source-zone selection (`effects/change_zone.rs:1560`); regeneration choice (`sba.rs:189`); Role uniqueness (`sba.rs:1340`); Battle protector rules (`sba.rs:1639` and listed nearby lines); and the broader inherited zero-defense guard (`sba.rs:263`, 1548, 1574, 1590). Role uniqueness is 704.5z, and cited Battle subparts 310.11a/310.8a do not exist in the checked-in rules. The zero-defense comments must distinguish Siege rules from inherited broader behavior without silently extending repair scope. Audit every new or moved annotation, including verbatim moves, and affected nearby comments. The author novelty-only audit is explicitly incomplete.

## Scope and source binding

The complete approved 868-line plan, applicable review/implementation instructions, tracked production diff, both untracked modules, full integration module and final appended Battle fixtures were reviewed. Final manifest is `885baf9780651ece1b38291acbcfa2ab2cb766defd3fe49671ace1ca40a73d0b`, archive `5578959239ea2420af4c260decd5381ad778f6ce69722d86ec9eead594627f2b`. All 2,051 archive members and actual final checkout files were independently verified, and all checkout files rehashed after the final handoff. Only the final Battle helper and three controls were appended to the prior module; its complete prior bytes and the other 2,050 files are unchanged. Final author handoff is `hushbringer-implementation-v10.md`, SHA `36e76c24a18559f997e06ecffd3a2e5b2d0bef044dfa56634181559b9c29e5ec`.

All operations were on EC2 through SSH. This reviewer made no production/test edits, builds, commits, pushes or child delegations. The conclusion applies to the fixed-base Phase candidate, not a future main merge or Coworld acceptance.

## Original reported bug: independent runtime

The original pinned worker, SHA `e4e8cb9d6024592745a0da533bcd86001c8115184a1ddcf0163c1f3f04494d98`, produced one Spirit for Hush-first, Traveler-first and no-Hush requests. Its retained source/build receipt, frozen harness files, original Phase pin, actual working directory/environment and loader were bound. Observations confirm required graveyards but do not expose stack or priority.

The preserved candidate integration binary, SHA `77db7d40780a2199d0a51f159869476c09ce8971ad07282ba95d88ae895f7917`, independently passed each of the three exact primary tests: zero Spirits for both simultaneous Hush orders and exactly one without Hush. Each selected exactly one test with zero ignored. Their guards check full Oracle implementation, functioning suppression, expected zones, empty stack and restored priority. The binary was compiled on source 3016; its production and primary test bytes are independently proven identical in final 885b. It is not described as a final-source compilation. Receipts: `original-runtime/receipt.json` and `candidate-runtime/receipt.json`.

## Coverage and evidence audit

The actual production path map was independently audited: 51 call sites, zero unmapped, 67 distinct mutation rows, 11 typed common-boundary rows, and 83 actual record constructors. First branches, authority selection, binding time, live/snapshot worlds, storage, consumers, invalidation and serialization were checked against production. Zero unmapped paths does not satisfy the missing native-library runtime obligations, so the maintainer gate fails. No additional production behavior defect was identified within the reviewed repair scope.

All 141 final added/moved CR-bearing lines and affected nearby comments were checked. Final appended Battle citations are valid. Parser honesty is confirmed: no parser/database/coverage implementation is promoted, typed fixtures are not parser support proof, and the 20 desired diagnostics remain limitations.

The 67 mutation seams are 56 public runtime, 10 private/schema/helper and one defensive Battle contract. Repeated stronger runs do not inflate counts. Private and defensive evidence is not represented as public behavior. Exact assertion failures, unaffected controls, canonical binary reuse and first-panic limits were reviewed. The added-mid-leaf full mutant matrix aborted; its separately retained focused completion is not a full-suite pass. The reviewer independently verified 476 immutable path/hash associations and canonical/final source archives; root per-mutation archive-content verification remains attributed evidence.

## Final verification qualifications

Source-bound final receipts show 16,586 engine-library passes, 3,163 integration passes, 15 binary passes, five cross-source behavior guards, engine Clippy and formatting passing. Suppression coverage is 187 passes/20 ignored, with three independently named final Battle controls passing. Docs executed zero tests with seven ignored. Explicit desired diagnostics are two passes/18 failures. Workspace Clippy fails on the inherited missing SetFullControl match arm; relevant files were independently confirmed byte-identical to the original base, but this reviewer did not run an original workspace build. None of these failed or unexecuted checks is labeled clean.

Historical Scute input is unavailable, so the five behavior guards establish no throughput claim. Card generation passed before the final test-only append and unchanged production/data applicability is qualified; no final-source generator rerun is claimed. Broader cross-pause, aggregate, inherited-target, ambiguous-origin, nested-layer, co-dying off-zone, regeneration-persistence and resumed duplicate-dispatch limits remain explicit.

The machine-readable report and receipt bind all final maps, source artifacts, runtime receipts, findings and verification evidence.
