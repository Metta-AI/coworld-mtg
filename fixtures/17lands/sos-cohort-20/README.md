# SOS cohort: first 20 recorded games

This is a frozen source workload for bounded Phase trajectory fitting. It contains the first 20 complete rows of the retained SOS Premier Draft public replay archive, in original order, with no filtering by mulligans, card identities, support, outcomes or observed engine behavior.

All 20 rows were previously inspected as part of the historical first-25-row investigation. Source rows 2, 3 and 11 overlap the smaller development fixture. The remaining 17 rows have the evaluation role; they are not unseen holdouts. The source contains 11 games with both mulligan counts zero, seven with one opponent mulligan, and two with one user mulligan. Those nine games remain in the workload even if the current fitter cannot reconstruct them.

cohort.json is the entry point. Its game_index values index games.csv, while source_row_index preserves the archive index. Paths in the manifest resolve relative to the manifest. source_row_sha256 and decompressed_byte_offset identify the original record bytes. games.csv retains the exact original header, quoting, field values and line endings; each row has 2,629 columns. cards.csv retains the full official Arena-ID mapping.

The declared initial workload uses two turn pairs, 10,000 search nodes, at most 128 actions, and an explicitly hypothetical Plains filler for unknown opponent cards. These settings do not prove a hidden setup is correct or establish that a failed search exhausted all games compatible with the source. The source rows include all later fields; the runner must report which selected observations it enforces, cannot support, or treats as unknown.

This fixture contains no engine results. Missing or blank input stays distinguishable from zero. An unresolved identity, unsupported mulligan, unsupported observation, exhausted budget or partial match remains a reportable outcome. Source expectations and engine results must be retained separately.

## Provenance and attribution

Source data: [17Lands public datasets](https://www.17lands.com/public_datasets), under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).

- [SOS Premier Draft replay archive](https://17lands-public.s3.amazonaws.com/analysis_data/replay_data/replay_data_public.SOS.PremierDraft.csv.gz): SHA256 db2e760e872e931b3d58238fa4cebff6647e48d178341dc5d21e642546ed4d3e.
- [Official card mapping](https://17lands-public.s3.amazonaws.com/analysis_data/cards/cards.csv): SHA256 cda7b580a951bcd8cbdf725275a5627e94c79b81c8cfc61e5244eac374ba2153.
- Exact selected CSV: SHA256 746224a63538b15e949b91ddd939423a7e884bb01d2c49dce72757ff0a109012.

The retained archive was rehashed before and after extraction. Its historical URL association is retained as an attestation; original HTTP headers and retrieval time were unavailable. The preparer does not download data or invent a retrieval date. Mapping source identity comes from the existing retained official artifact.

Selection and provenance are by Coworld MTG. Modifications consist of selecting complete rows and deriving the manifest, roles and hashes; original CSV values are unchanged. 17Lands does not endorse this work. The full compressed archive, private runtime corpus and private sessions are excluded.

## Prepare again

From the repository root, run the following with the retained archive and official mapping paths. A new output directory is required; existing evidence is immutable.

    python3 scripts/prepare_17lands_cohort.py \
      --archive /path/to/17lands-replay.SOS.PremierDraft.csv.gz \
      --archive-sha256 db2e760e872e931b3d58238fa4cebff6647e48d178341dc5d21e642546ed4d3e \
      --source-url https://17lands-public.s3.amazonaws.com/analysis_data/replay_data/replay_data_public.SOS.PremierDraft.csv.gz \
      --cards-csv /path/to/cards.csv \
      --cards-sha256 cda7b580a951bcd8cbdf725275a5627e94c79b81c8cfc61e5244eac374ba2153 \
      --output-dir /path/to/new-cohort \
      --count 20 --development-row 2 --development-row 3 --development-row 11 \
      --previously-inspected-prefix 25 \
      --turn-pairs 2 --nodes 10000 --max-actions 128 --opponent-filler Plains

