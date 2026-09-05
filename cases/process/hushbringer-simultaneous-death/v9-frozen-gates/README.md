# Frozen v9 runtime verification

Case ID: `01edd604679d89888ad9bb3bd13ca1c531fbbdd1c65f98341e7ce2a5a57d09aa`.

The [freeze receipt](freeze-receipt.json) and [source manifest](source.json) identify all 2,051 source files tested after the ninth clean full plan review. The complete source archive remains on EC2 at the hash and path in [the manifest](manifest.json), including modules absent from the tracked-only patch.

The [verification receipt](verification-receipt.json) records 16,581 passing library tests, 3,067 passing integration tests, 91 passing focused tests, and successful formatting, engine Clippy and card-data generation. Generated tracked inputs were restored before the full suites. Source hashes did not change during the measured run. The [root audit](root-audit.json) independently checked all eight log hashes. The complete logs are retained here as deterministic gzip files, with both compressed and original hashes.

The explicit run of 20 ignored diagnostics produced two passes and 18 failures. These characterize known limitations; they are not part of the passing claim. The primary authored acceptance expectation remains zero Spirits.

The [library-choice source proof](library-choice-reachability.json) identifies three library-choice wrappers restricted by existing constructors and validation to Hand or Library. The [disposition](library-choice-disposition.json) applies the already-reviewed plan's scope: retain reachable controls and actual battlefield leaf obligations, and do not claim a wrapper-only mutation kill for those three branches. The independent implementation reviewer must audit that classification.

This checkpoint establishes passing runtime gates on a frozen candidate. Boundary-removal checks, independent implementation review, a clean committed worker comparison and the acceptance receipt remain separate obligations.
