# A silence that disappears too early

Hushbringer prevents creatures entering or dying from causing triggered
abilities to trigger. Doomed Traveler normally leaves a Spirit token when it
dies. Put both on the battlefield and cast Wrath of God, which destroys all
creatures. Should the Traveler leave a token?

For this death trigger, the game looks back to the moment before the creatures
died. Hushbringer was there, so the answer is no. Wizards explicitly covers
simultaneous deaths in the [Throne of Eldraine release notes](https://magic.wizards.com/en/news/feature/throne-eldraine-release-notes-2019-09-20).

We authored that rule claim as a small executable case. This example came from
rules-based scenario construction, not successful reconstruction of a recorded
game. The initial position has three cards and enough mana to cast Wrath. The
case first checks that Hushbringer, Doomed Traveler and Wrath really reached the
graveyard. Only then does it count Spirit tokens. That matters: zero tokens
would tell us little if the spell never resolved.

The pinned Phase engine produced one Spirit, twice. Replaying the same result
made the defect reproducible; it did not make the result correct. The worker
received the position and the cast operation. The expected token count lived
in the coordinator's case, with its independent rules citation.

The source investigation found the right kind of mistake for a software story:
trigger collection scanned the battlefield after the creatures had moved.
Hushbringer was gone by then. A fact about the event had been replaced by a
query against the resulting state. The repair plan captures suppression at the
event and consumes it at the appropriate trigger boundary. Different trigger
classes can use different timing, so the fix must distinguish ordinary death
triggers from triggers watching a card arrive in a graveyard from anywhere.

The controls make the claim sharper. Without Hushbringer, the Traveler creates
one token. Removing Hushbringer before casting Wrath also restores that token.
A Stonecoil Serpent cast while Hushbringer remains present still enters with its
three counters: those counters come from a replacement effect, not a trigger.
All three controls passed on the baseline. A patch that simply removes death
triggers or blocks entry effects indiscriminately would fail these neighbors.

The first independent plan review found three other paths that the proposed
change needed to cover: a dedicated haunt matcher, choose-and-sacrifice-rest
sweeps, and a separate multi-target destruction path. That review changed the
implementation obligation before anyone wrote the engine patch.

The implementation then exposed a second, sharper distinction. Wrath makes
Hushbringer and Traveler die together. Paying two separate sacrifice costs can
make Hushbringer die first and Traveler second. In that ordering, Hushbringer is
already gone when Traveler dies, so Traveler should create a Spirit. The
reverse ordering should create none.

The partial repair passed the original simultaneous-death tests but failed
this new cost case: Hushbringer-first produced zero Spirits instead of one.
The original engine produced one. Deferred payment had flattened separate
cost selections into one list, and the repair treated that list as a single
event. The [retained failed attempt](../cases/process/hushbringer-simultaneous-death/v7-component-stop/README.md)
records the exact operations, reached zones, life total, object groups and
before/after snapshots. Its failure was kept visible and sent through another
planning and review cycle. A [fresh original-engine run with an isolated build](../cases/process/hushbringer-simultaneous-death/v7-component-isolated-runtime/README.md)
confirmed the cost observations independently of the earlier shared build
directory.

This changed the design requirement: preserve which validated cost component
each selected object belongs to, then close that component's event before
starting the next. A snapshot needs both a time and a well-defined event. A
flat collection of objects cannot recover the decision that grouped them.
The case's expectation stayed fixed while the repair obligation grew.

The build workflow needed a correction too. Sharing a Cargo output directory
between the original and modified engine checkouts caused a test compile to
see an older engine type. The [build-isolation record](../cases/process/hushbringer-simultaneous-death/build-isolation/README.md)
retains the failed compile and the builder change. Both comparison workers
now require separate build directories and the same corrected builder. The
rebuilt baseline still passes nine cases and violates Hushbringer; the original
checker and case remain preserved. Build provenance belongs inside the
experiment because the executable being compared must be the one we intended
to build.

There is an unusual external corroboration. Magic Online's [February 4, 2025
patch notes](https://www.mtgo.com/news/mtgo-blog-02042025) listed a fix for the
same Hushbringer simultaneous-death symptom. We do not know whether their
implementation had the same cause. It does show that this subtlety matters in
a long-running production game, not just in a new AI-assisted engine.

The wider campaign contains ten scenarios using thirteen cards. The Linux
baseline passed nine and failed this one, with no inconclusive executions.
Other useful examples are Lightning Helix losing both damage and life gain
when its target disappears, Young Pyromancer keeping a cast-triggered token
when the spell is countered, Swords to Plowshares using the creature's power
before exile removes its counters, and Rancor returning only after actually
reaching the battlefield. These are contrasts between neighboring behaviors,
not a count of how many card names a parser recognizes.

The deletion reducer reported that the Hushbringer case was already at a fixed
point: three cards and one operation. It tried deleting the cast; the guards
then failed, so that was an inconclusive experiment rather than a smaller
reproducer. We should not describe this run as reducing a large game to three
cards. It verified that none of the permitted individual deletions preserved
this case's obligation.

The reusable product of the loop is the obligation and its evidence: an exact
input, a justified expectation, a repeated baseline failure, a reviewed repair,
and checks against nearby cases. The acceptance machinery requires a single
preserved checker to evaluate both workers. The case, corpus and expectation
cannot change between them. Acceptance is evidence about those stated cases;
it is not a proof that every game now follows every rule.

The executed before/after results and final repair scope are recorded separately
in the campaign artifacts. This narrative should only call the repair accepted
after the independent implementation review and the acceptance receipt exist.
