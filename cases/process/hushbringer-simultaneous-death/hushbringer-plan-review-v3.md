# Hushbringer plan v3 review

One blocking plan gap remains. No other blocking gaps were found in this full review.

Reviewed `/home/ubuntu/coworld-migration-20260904/hushbringer-plan-v3.md` against `/home/ubuntu/repos/phase-verifiable-loop` at `2dec6c88915db4697706234a7ba2fcedd97b1689`, using the remote `.claude/skills/review-engine-plan/SKILL.md`, AGENTS.md/CLAUDE.md, and the applicable trigger/static/card-test/interactive planning guidance. All inspection and this artifact write used `ssh nishadsingh-box-4`. No implementation, builds, tests, commits, or subagents were performed. The behavior described below is derived from source, not a new runtime result.

## 1. [P2] Bound the mixed-origin timing rule; OneOf does not establish explicit battlefield-origin provenance

**Plan location:** lines 175–179, with coverage implications for lines 189, 197, 247, and 300.

The plan says that a matching `OneOf` Battlefield member uses the before-event suppression outcome. Existing `OriginConstraint::OneOf` does not establish that the original clause explicitly named a battlefield departure:

- `types/ability.rs:17921–17958` defines `Any`, `Equals`, `NotEquals`, and `OneOf` as zone-set predicates.
- `parser/oracle_trigger.rs:14807–14834` explicitly lowers “from anywhere other than <multiple zones>” to `OneOf(origin_zones_except(...))`. The complement can contain Battlefield.
- The graveyard clause path reuses that helper through `parse_put_into_graveyard_origin` and `parse_zone_change_clause` (`oracle_trigger.rs:14745–14747, 14934–14955`). This is not exclusively a cast-origin type.
- `ZoneChangeClause` (`types/ability.rs:17968–17988`) stores the resulting predicate but no positive-versus-negated origin provenance. The shared scalar/clause matcher (`trigger_matchers.rs:1058–1156`) currently only tests the predicate.
- The existing complementary-`OneOf` convention is also documented by `oracle_trigger_tests.rs:355–373` and `trigger_matchers.rs:7064`. The printed “Name Sticker” Goblin example is an ETB consumer and is not itself a death regression.

Consequently, the proposed unconditional `OneOf` timing rule cannot distinguish an explicit battlefield-origin clause from a from-anywhere clause whose exclusions happen to leave Battlefield in the represented set. CR 603.6c explicitly excludes from-anywhere graveyard triggers from LTB classification; CR 603.10 then selects the post-event world. Under the baseline ordinary collector, Hushbringer co-dying with the subject leaves no live suppressor, so a matching surviving from-anywhere observer is allowed. Applying the plan's before-event rule to its complementary `OneOf` representation would instead block it. That is a prospective regression caused by the new classification, rather than a request to fix the pre-existing representation ambiguity. The timing disposition of the fourth reachable variant, `NotEquals`, is also unstated.

**Smallest required revision:** explicitly enumerate `Any`, `Equals`, `NotEquals`, and mixed `OneOf` at the touched death-matching boundary. Remove the assertion that `OneOf` alone proves explicit battlefield-origin timing. The focused fix may preserve the existing behavior of ambiguous mixed-origin forms, identify their pre-existing representation/timing limitation, and exclude them from the repaired event-time guarantee. It need not add parser metadata, a new AST variant, or a parser repair. If explicit mixed-origin LTB support is retained as an acceptance claim, the plan must provide an authority that actually distinguishes it.

Add a production cast/apply no-regression characterization for an ambiguous complementary-`OneOf` death-capable observer: Hushbringer and its filtered subject co-die; both deaths and the positive observer payoff are reached. Pair it with a surviving-Hush control and a no-Hush positive. Include the `NotEquals(Battlefield)` non-death sibling with a matching non-battlefield-origin positive, and state the disposition for other `NotEquals` values that can match a death. These fixtures should preserve honestly characterized behavior and must not promote ambiguous forms to fully supported event-time semantics.

## Findings resolved or accepted

The v3 delayed-consumer work addresses the prior material gap. The source confirms that `WheneverEvent` and both `WhenNextEvent` alternatives call registered matchers (`triggers.rs:6321–6348`). The matrix now covers suppressed first occurrences, later eligible occurrences, one-shot consumption, recurring retention, same-occurrence alternatives, source/controller binding, cleanup, and reflexive disposal through normal production entry points. The direct delayed routes at `triggers.rs:6252–6319, 6354–6384` bypass the shared matcher at baseline; their explicit exclusions and active working controls are honest.

The aggregate unless-payment loop (`engine_payment_choices.rs:1574–1598`) and inherited-target sacrifice loop (`effects/sacrifice.rs:344–402`) already lack group boundaries. Their separate characterized exclusions are acceptable for this bounded fix. They do not require batching repairs. The pre-existing cross-pause limitation is separately identified and remains outside acceptance.

The plan otherwise supplies reusable event-local outcomes, evaluated source/controller/filter authority, Some(empty) versus None semantics, constructor/serialization obligations, bounded event identities, producer ownership, dedicated Haunt and Unattach adapters, ordinary/batched/shadow collector consistency, and meaningful positive/negative production coverage. The cited simultaneity, trigger timing, delayed lifetime, Haunt, sacrifice, destruction, replacement, and serialization-related rules were checked against the remote rules file. Current Scryfall Hushbringer Oracle text and rulings independently confirm the core premise, simultaneous-death rule, sacrifice-cause distinction, and self-from-anywhere exception.

## Residual implementation assumptions

The implementation must obey the existing plan's prohibition on intermediate per-member layer flushes being treated as complete simultaneous worlds; outer finalization must not change unrelated LKI or action semantics. Captured outcomes must remain attached to the intended event incarnation and survive existing deferred/serialized carriers. Fresh tests and frozen-worker comparison remain required implementation evidence; this architectural review supplies none of that runtime evidence.

After the bounded origin-scope clarification, the caller should request a fresh full review of the revised plan.
