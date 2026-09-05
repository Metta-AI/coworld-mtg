# Original cost behavior confirmed with an isolated build

This run removes the build-sharing uncertainty from the earlier cost
observations. The original engine was compiled in its own target directory.
The exact earlier test overlay was unchanged, and production source had no
diff from the original revision.

Deferred Hushbringer-first still produced one Spirit, while the partial repair
produced zero. Traveler-first produced one on the original engine even though
the rule requires zero. Both original deferred selections shared incorrect
peer groups. All four immediate-payment controls remained correct. The
suite result was one pass and four failures, with exact output retained.

The [manifest](manifest.json) binds the command, receipt, log and already
retained test source. This supplements the historical logs without relabeling
or replacing them.
