# Hushbringer implementation executor: stop and return

Status: STOPPED BEFORE ENGINE EDITS. The v4 plan leaves a rules-bearing scope decision unresolved. This is not a compilation/test failure or an implementation-success claim.

Checkout: /home/ubuntu/repos/phase-verifiable-loop
Branch: codex/hushbringer-simultaneous-death
HEAD: 2dec6c88915db4697706234a7ba2fcedd97b1689
Case-Id: 01edd604679d89888ad9bb3bd13ca1c531fbbdd1c65f98341e7ce2a5a57d09aa

## Concrete blocker

The plan requires standalone move_to_zone / move_to_library_at_index to capture both sides of a departure from layer-resolved worlds, while an outer simultaneous producer captures before its first move and finalizes after its last. It expressly forbids per-member layer flushes that reinterpret intermediate boards, whole-GameState clones, and widening cross-pause carriers. It does not specify how a common leaf learns that an outer synchronous capture context is active.

The baseline has no such scope signal:

- game/zones.rs:636: move_to_zone(state, object_id, to, events); game/zones.rs:1124: move_to_library_at_index. Neither takes producer context.
- zones.rs:357,395: cleanup marks layers dirty. Records around 734 and 1149 read current effective characteristics.
- game/layers.rs:2363: flush_layers consumes dirtiness and mutates the real board via evaluate_layers; it is not a read-only suppression query.
- game/functioning_abilities.rs:205,245: active_static_definitions / battlefield_active_statics read current effective static_definitions and evaluate conditions, without recomputing effective abilities/types.
- game/effects/destroy.rs:181 and resolve_all around 341-372: per-member replacement/destruction precedes stamping.
- game/zone_pipeline.rs:943: deliver_batch invokes move_object for each request. Its pending batch stores undelivered requests/completion, not a lexical layer/suppression scope.
- Search of GameState, layers.rs, zones.rs and zone_pipeline.rs found no existing layer suspension or producer nesting authority available to the leaves.

Calling flush_layers at each leaf changes later members' effective characteristics/abilities/replacement decisions inside the simultaneous action. Overwriting suppression vectors afterward cannot undo later records or decisions already made under that altered world. A hostile category is a first departing source that grants/removes abilities or modifies types of another group member.

Omitting leaf flushes instead leaves standalone after-event snapshots stale when a departing continuous-effect source changes the effective suppression abilities of a surviving permanent. A later collector flush cannot reconstruct the immediately-after value. Some(empty) is authoritative, so this is a semantic defect, not merely an optimization.

CR 603.10/603.10a, 608.2f, 611.3a-b and 613.11 are clear. The missing decision is the concrete synchronous producer/leaf scope authority, not the rules timing.

## Narrow planner decision needed

Specify and review how a leaf distinguishes a standalone move from a member of an already-captured simultaneous group. Identify exact storage/API threading, nested-group and nested-cause behavior, when layer flushes occur, and exactly-once closure for zero/single groups, completion, prevention, early return and existing pause segments. Retain the cross-pause exclusion; no context may leak into the next written instruction.

This executor did not invent a GameState field, thread-local mechanism, parameter expansion or layer refactor. The parent explicitly requested stop-and-return if no existing mechanism satisfies the reviewed boundary.

## Diff and verification

No repository source files changed, no parser/card-data changes, no commits/pushes/subagents. Final read-only git status was empty and HEAD remained pinned. Only this report is written outside the repository.

Read repository AGENTS.md/CLAUDE.md, engine-implementation-executor.md, full v4 plan and clean review, and applicable card-test, project-reference, add-trigger, add-static-ability and add-interactive-effect checklist/reference sections.

Executed: git branch --show-current; git rev-parse HEAD; git status --short. Results above. Executed tilt get uiresource clippy >/dev/null 2>&1: exit 127, Tilt unavailable, not code failure.

No formatting, clippy, engine tests, card-data generation, new runtime tests, baseline fixture executions or changed-worker harness executions ran. Parent-reported baseline build/data preparation are inherited evidence only. All implementation and runtime acceptance rows remain pending.

Operational note: the first attempt to write this report used an incorrectly quoted SSH heredoc and failed with a Python SyntaxError before writing. The enclosing local shell then attempted several report fragments as commands (command-not-found/no-such-file errors, and an at invocation rejected as garbled time). No intentional local command/file work was performed, but this was an accidental violation of the all-commands-through-SSH constraint. A subsequent correctly shell-quoted SSH command writes this report. No successful local file mutation was observed.

## Production-path coverage map

No implemented behavioral claim has a passing test receipt; no new test was created.

| Planned seam | Production entry | Disposition / discriminator still required |
|---|---|---|
| Leaf snapshot | move_to_zone / move_to_library_at_index | Blocked on scope; effective source changes must preserve actual before/after worlds. |
| Group snapshot | Destroy/DestroyAll, keep/sacrifice, SBA, batch delivery, ChangeZone, resumed drain, choices, scoped sacrifice, cost commit | Blocked on scope; both orders must suppress while retaining later members' starting characteristics. |
| Ordinary matcher | Scalar/disjunctive, batched, self/LKI/co-departed/off-zone/index collection | Not edited/tested; before/after and ordinary-live OneOf/NotEquals matrix pending. |
| Dedicated matchers | Haunt / death-caused Unattach | Not edited/tested; positive reached subject and surviving/co-dying Hush tests pending. |
| Registered delayed | Cast-created WheneverEvent / WhenNextEvent / alternatives / reflexive | Not edited/tested; suppression, retention, consumption and later payoff tests pending. |
| Serialization | Emitted/parked events and pending contexts | Not edited/tested; None/Some(empty), repeated IDs/indices and pause round-trip pending. |
| Exclusions | Aggregate/inherited sacrifice, legacy direct delayed, cross-pause, ambiguous origins | Zero edits preserve code; active controls and ignored desired-behavior evidence remain pending. |

No test names or revert-failing results are fabricated. The primary zero-Spirit failure is inherited baseline evidence, not a new execution.

## Maintainer-simulation matrix

| Seam / first branch | Authority / binding time | Mode / storage | Consumer | Invalidation | Hostile fixture | Serialized surface |
|---|---|---|---|---|---|---|
| Standalone leaf / actual battlefield departure | Before and immediate after | Planned evaluated ZoneChangeRecord snapshot | Zone and special matchers | Event lifetime | Effective suppressor changes after departure | Planned optional field, not added |
| Group member / nonempty loop | Owning simultaneous action | Missing scope signal is blocker | Leaf and later group members | Needs exact completion/early/pause closure | First member changes later types/abilities | Scope undecided, no field added |
| Outer group / selected candidates | Pre-first and post-last worlds | Planned owned outcomes plus bounded event slice | Finalizer / collection | Close once; no next-instruction leak | Zero/single, prevented, nested, repeated ID | Final event field only under v4 intent |
| Ordinary ambiguous clause / matching predicate | Current collector cache | Borrowed Some(cache) | Ordinary adapter | Call end | Subject first, Hush later, mixed clauses | No compatibility metadata |
| Registered delayed / matcher wrapper | Event timing plus existing creation source/controller | Existing listener and planned event field | Matching/lifetime/context path | Existing one-shot/cleanup/reflexive | Alternatives and later eligible death | Event carries snapshot |

All rows are pending proof; this is not a completed maintainer simulation.

## CR diff gate / parser honesty

No source diff, added annotations or parser edits. Zero new unverified CR annotations. Read-only verification command:

rg -n "^603.10|^603.6c|^611.3|^613.11|^704.3|^608.2[cf]|^400.7|^700.4" docs/MagicCompRules.txt

Displayed text supports the boundary argument. No parser combinator gate applies.

## Judgment, deviations and risks

Treat the missing scope authority as an architectural execution blocker, without substituting stale or mid-group layers. No unexpected checkout change or uncertain CR was found. No implementation deviation occurred. The next review must reject a primary-case-only pass hiding changed later-member characteristics or stale standalone after snapshots.

Return to planner and obtain a fresh review of the concrete scope decision before restarting implementation.
