# Existing tests passed while an event handoff was missing

These are eight foundational mutation experiments on frozen v9 production
with the first isolated public-test overlay. They concern zero toughness,
lethal damage, unattached Auras, Role uniqueness, the World rule, zero loyalty,
zero defense and Saga sacrifice.

For each experiment, only its member-handoff wrapper was removed. All 119
existing state-based-action unit tests still passed. The new public scenario
reached the departure and failed at its observer payoff: life remained 20
instead of becoming 21. The candidate before mutation and after restoration
passed. The [results](sba-eight-foundational-results.json), exact test overlay,
individual outcomes and complete failing public logs are retained here.

These are synthetic typed engine fixtures, not new real-card parser support.
The original test loops through eight tuples in one invocation. The mutant
stops at the first failing tuple, so later reversed-order and control tuples
were not executed on that mutant. The results state this limit explicitly.
V10 requires independent tuple invocations and further branch/incarnation,
record and follow-up checks. These artifacts do not certify those later tests,
the battle-protector branch, the complete implementation or acceptance.

The per-outcome build records bind full source archives, compiler artifacts
and logs retained on EC2. The [manifest](manifest.json) binds this smaller
repository archive; it does not duplicate those large compiler/source archives.
