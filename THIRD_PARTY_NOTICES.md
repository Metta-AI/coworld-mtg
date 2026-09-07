# Third-party notices

Coworld MTG is unofficial Fan Content permitted under the Wizards of the Coast Fan Content Policy. It is not
approved or endorsed by Wizards. Portions of the materials used are property of Wizards of the Coast.
© Wizards of the Coast LLC.

The private runtime corpus includes deck data derived from the 17Lands SOS PremierDraft public dataset. 17Lands
public datasets are made available under the Creative Commons Attribution 4.0 International license. 17Lands does
not endorse this project or its findings.

The public repository distributes bounded slices of the 17Lands MSH PremierDraft wide-replay CSV, the official
Arena card mapping from `cards.csv`, and an authentic first-game fixture. Source attribution and byte identities
are retained with the [17Lands factory replay](replays/17lands-coverage-20260907-03/replay.json) and
[fixture provenance](crates/coworld-mtg-harness/tests/fixtures/17lands-msh-replay-v1/source-manifest.json).
These [17Lands public datasets](https://www.17lands.com/public_datasets) are available under
[Creative Commons Attribution 4.0 International](https://creativecommons.org/licenses/by/4.0/).
Modifications include bounded downloading, decompression, CSV row slicing and partitioning, and a mapping-row
subset for the first-game fixture; retained original field values are unchanged. 17Lands does not endorse this
project, the repair, or its findings. The records support the stated ingestion checks, not a full gameplay replay.

The public repository does not distribute the generated private runtime card database, private deck lists,
full Scryfall bulk archive or MTGJSON runtime data. Authorized builds materialize the pinned private corpus
described by `corpus.lock.json`.
Public source slices and fixtures do not publish that full corpus or its private deck data.
