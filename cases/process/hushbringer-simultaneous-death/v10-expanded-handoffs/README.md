# Independently invoked handoff and snapshot checks

This table is generated from the retained runtime outcomes. Each row passed
all baseline and restored invocations with zero ignored tests. The mutants
produced 38 intended assertion failures and 32 passing controls across 70
independently invoked cases. This is bounded evidence for review, not acceptance.

| Exact mutation | Cases per phase | Payoff/semantic failures | Snapshot failures after correct payoff | Passing mutant controls |
| --- | ---: | ---: | ---: | ---: |
| sba-check_zero_toughness | 8 | 2 | 2 | 4 |
| sba-check_lethal_damage | 8 | 2 | 4 | 2 |
| sba-check_unattached_auras | 8 | 2 | 2 | 4 |
| sba-check_role_uniqueness | 8 | 2 | 2 | 4 |
| sba-check_world_rule | 8 | 2 | 2 | 4 |
| sba-check_zero_loyalty | 8 | 2 | 2 | 4 |
| sba-check_zero_defense | 8 | 2 | 2 | 4 |
| sba-check_saga_sacrifice | 8 | 2 | 2 | 4 |
| before-snapshot-some-to-live-fallback | 3 | 2 | 0 | 1 |
| after-snapshot-some-to-live-fallback | 3 | 2 | 0 | 1 |

The eight state-based-action rows execute all eight combinations of subject
departure, observer departure and insertion order separately. Sixteen co-dying
variants lose the expected one-life payoff. Eighteen other selected variants
retain the payoff but lose the required event snapshot. Unaffected controls
remain passing. The two fallback rows distinguish an authoritative captured
snapshot, including an empty one, from a later live-state query.

The canonical executable was freshly compiled from the complete frozen v10
source. Every mutant was freshly compiled; restored runs explicitly reuse the
preserved canonical executable after exact source restoration. Full source,
runtime context, dynamic libraries, commands and logs are bound by receipts.
Mutant binary hashes were captured at compilation and execution; earlier
mutant executables were not separately retained after target reuse.

The root mechanical audit reopened all eleven full source archives, verified
2,051 files in each, reproduced each exact mutation through the pinned
formatter, and checked all 210 independent run records. A first audit attempt
used an insufficient whitespace-only formatting model; its setup correction
is retained and is not a runtime failure.

The later source snapshot appends only three battle sibling tests; its
separate lineage receipt must establish that these measured fixture bytes and
production code remain unchanged. This archive describes the source actually
compiled here, without relabeling earlier builds.

See [results.json](results.json), [root-archive-audit.json](root-archive-audit.json)
and [archive-manifest.json](archive-manifest.json). Large source archives and
the canonical executable remain on EC2, identified by hash.
