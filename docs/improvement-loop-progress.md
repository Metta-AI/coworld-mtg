# Verifiable improvement loop: implementation checkpoint

Checkpoint: 2026-09-05. The loop has its first accepted repair:
[Hushbringer simultaneous death](../cases/evidence/hushbringer-simultaneous-death/case-note.md).
The original worker creates one Spirit; the newly compiled, reviewed repair
creates none. All seven planned regressions and two separately selected
holdouts pass under the preserved checker. The acceptance command generated
the attribution record and readable case note from those exact results.

The reusable harness is on main. Rust types generate strict JSON schemas and
architecture/message-flow diagrams. The execution worker receives a scenario;
the coordinator retains the expectation. Reachability guards distinguish an
unreached condition from a real rule violation. Repeated runs, bounded
reduction, isolated builds and a frozen acceptance plan make the claim and
its evidence inspectable. The [case guide](verifiable-cases.md) documents the
commands and artifacts.

Acceptance binds the originating case, rules support, baseline and candidate
source/build identities, exact checker, independently approved review, repair
patch and neighboring case results. It writes acceptance.json last.
The [evidence catalog](../cases/evidence/README.md) now contains one accepted
repair. Repair planning and implementation remain agent-orchestrated; the
execution, checking and attribution commands are implemented in the CLI.

Ten authored scenarios exercise thirteen cards. They cover Lightning Helix
losing its target, Swords to Plowshares remembering power after exile,
Young Pyromancer after a countered spell, Rancor's actual battlefield history,
and Hushbringer's interaction with death triggers and entry replacements.
All twenty baseline/candidate bundles and forty repeated executions were
independently verified. Supplemental final-worker runs confirm both Hushbringer
object orders and the no-Hushbringer control.

The repair captures event-time trigger suppression and preserves the identity
of simultaneous events and separate sacrifice-cost components. It passes
three full independent implementation reviews after resolving their findings.
The reviewed executable/test source passes 196 focused checks, 16,586 library
tests, 3,172 integration tests and 15 binary tests. Engine Clippy, formatting
and card generation passed. The final source differs from that broad-suite
snapshot only in one corrected comment citation; the final worker was actually
compiled from clean commit fa0ebfe88db224ebd32624bb96ef033d338c2d8c.

The [process history](../cases/process/hushbringer-simultaneous-death/README.md)
retains how the work improved its own checks. An intermediate repair confused
separate sacrifice costs; shared Cargo targets produced stale build evidence;
old unit tests missed eight removed state-based-action handoffs; independently
named variants prevented an early panic from hiding later controls. Native
library-choice tests, rule-citation checks and factual coverage-map corrections
closed later review findings. All 67 targeted mutations retain measured
discriminators: 56 public runtime, ten private/helper/schema and one defensive
Battle contract. Preparing publication also added the corpus lock to the
Phase pin checker, with a CLI regression that fails on the old checker.

The [case study](case-study-hushbringer.md) develops these findings into a blog
narrative. The initial case was authored and already small; bounded reduction
confirmed that its permitted individual deletions did not preserve the failure.
It was not a recorded game reduced to three cards. All ten named engine limits
remain explicit. Twenty desired diagnostic cases stay ignored in the normal
suite; an explicit run yields two passes and eighteen failures. No universal
Magic-correctness, parser-coverage or throughput claim follows.

All implementation, builds and evidence live on the EC2 machine reached with
ssh nishadsingh-box-4. Migration verified 3,902 files before local cleanup and
freed 12,964,511,744 bytes on the Mac. The [workspace guide](ec2-workspace.md)
records the retained locations.

Remaining publication work is to verify the clean automatic integration with
newer Phase commits, publish that engine revision, and update Coworld's Phase
pin together with its matching private corpus archive. The integration is
running its full checks in a separate checkout. Existing published harness
source already passed the Rust private-corpus suite and both browser tests;
those checks will run again for the new production pin.
