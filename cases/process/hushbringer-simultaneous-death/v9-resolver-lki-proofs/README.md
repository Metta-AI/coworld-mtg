# Resolver and last-known-information checks

The [report](report.md) records five exact isolated mutations on the frozen
v9 candidate: the resolver barrier, entered-object exit history, battlefield
incarnation, bounce controller and Oversimplify controller.

Fifteen before invocations and fifteen freshly rebuilt restored invocations
passed. Mutants reached ten intended assertion failures; five independently
invoked controls passed. The report identifies additional nested controls and
which later assertions were not reached after a panic. It does not turn a
logged value or an unexecuted later assertion into a passing test.

The [receipt](receipt.json) and [audited results](audited-results.json) bind
source, fixtures, compiler outputs, commands and observations. This smaller
archive retains patches, receipts and complete compressed logs. All 354 files
in the original [source-artifact index](source-artifacts.json) were rehashed
before archiving; large source/runtime archives remain on EC2 at the paths in
the [archive manifest](manifest.json).

These checks belong to frozen v9. They are bounded execution evidence, not
independent implementation approval or an acceptance decision.
