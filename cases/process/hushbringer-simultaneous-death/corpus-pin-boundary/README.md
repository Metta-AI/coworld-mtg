# Engine and corpus revision agreement

Preparing publication of this repair exposed a missing preflight check.
The server requires its private corpus manifest to match the compiled Phase
revision. The existing pin checker compared build surfaces but omitted
corpus.lock.json, so it accepted a deliberately stale corpus revision.

The checker now includes that lock. A regression runs the actual command
against the shipped pin surfaces: a consistent corpus passes and a stale
revision fails. Reverting only the checker makes that regression fail.
The [receipt](receipt.json) and logs retain both observations and the passing
Python suite. This is a publication check attributed to the originating case;
the original frozen acceptance experiment is unchanged.
