# Guided fitting measurements, 8 September 2026

Three previously inspected [17Lands SOS source rows](../../../fixtures/17lands/sos-first-turns/README.md) were run twice through the guided fitter at [201aa8a](https://github.com/Metta-AI/coworld-mtg/commit/201aa8a139db9819911ca9b4e1d9bb02465fb5f1). The [derived summary](summary.json) links the raw results.

| Original source row | Search nodes | Witness actions | Supported turn fields checked | Unsupported turn fields |
| --- | ---: | ---: | ---: | ---: |
| 2 | 22 | 22 | 14 | 8 |
| 3 | 22 | 22 | 15 | 8 |
| 11 | 31 | 30 | 16 | 9 |

Each run matched the supported observations at two player-turn boundaries. Four player-specific milestone keys describe those two moments. **None has complete observation coverage:** combat-damage and mana-spent fields remain unsupported; row 11 also contains an unsupported ability observation. Blank cells remain unknown.

All six processes exited successfully. The repetitions produced identical constraints and identical results except elapsed time. Search and setup took roughly 0.6–1.0 seconds; complete processes took roughly nine seconds including runtime input loading. No engine-error candidate or timeout was observed. These selected excerpts do not measure full-game search difficulty or constitute a holdout.

The witness uses one explicitly reconstructed library and hypothetical opponent deck. Matching names does not establish unique token/face characteristics or complete effect support. [The input manifest](inputs/manifest.json) identifies the private export; its cross-validation fields were not measured and its placeholder zeroes are not corpus statistics. Private definitions and executable bytes remain on EC2.

The result and constraints files are native typed fitter outputs. The process receipts record commands, limits and exits; [repeat comparison](repeat-comparison.json), [build receipt](build-final/build.json), and [checks](checks.json) preserve the associated evidence. Check logs are retained by their original basenames. Build provenance is caller-attested with source hashes, not a reproducible-build proof.

This collection is not yet a factory replay or viewer integration. See the [active plan](../../17lands-discovery-plan.md) for that next milestone. Source attribution and selection details remain in the fixture. [The inventory](inventory.json) hashes every retained file in this collection.
