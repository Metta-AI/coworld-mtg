# Recorded-game discovery

The fitting factory starts from recorded games. It freezes a source cohort, asks the native fitter to explain the selected observations through legal engine actions, and records obstacles for a separate investigation. The source-to-issue links are generated from execution receipts.

The current adapter is [fit17lands_factory.py](../scripts/fit17lands_factory.py). It uses the existing FactoryReplay lifecycle, artifact store, process supervision and viewer. The native fitter supplies typed constraints and results; the adapter does not create card-specific expected outcomes.

## What a run contains

Each game keeps its original archive row number, exact source bytes, official card mapping, selected observation scope, reconstructed setup, search bounds and worker identity. Each execution retains its constraints, result, output logs and measured wall time. A missing result, including an externally terminated worker, remains a recorded execution obstacle.

The investigation queue groups identical diagnostic signatures while retaining every originating game, source column and result. Grouping is a triage aid: two similar symptoms have not thereby been proved to share a root cause.

A matched result means the search found a trajectory for the enforced projections under its assumptions. A budget stop means the search ran out of resources. An unsupported observation means that part of the recording has not been checked. An input issue means reconstruction did not proceed. All of these appear in the replay; none is silently removed from the workload.

The frozen SOS cohort includes the first 20 source rows and uses two turns from each player. All were previously inspected; the evaluation role is not a claim of unseen holdout data. Nine contain mulligans that the first reconstruction does not handle. The runtime uses a full pinned card export, but a resolved card name is not a complete implementation-support certificate.

## Run the pipeline

Build the Coworld harness and factory runtime, retaining the harness build receipt. The worker must have access to the matching runtime corpus. Public replay artifacts do not contain that corpus.

Prepare a recording from the committed cohort and the exact runtime manifest:

    python3 scripts/fit17lands_factory.py prepare \
      --cohort fixtures/17lands/sos-cohort-20/cohort.json \
      --input-manifest /path/to/manifest.json \
      --baseline-revision FULL_BASELINE_COMMIT \
      --run-id my-17lands-discovery \
      --run-dir /path/to/runs/my-17lands-discovery \
      --runtime /path/to/factory-runtime \
      --deadline-seconds 60

Execute one supervised worker at a time:

    python3 scripts/fit17lands_factory.py execute \
      --label baseline \
      --input-manifest /path/to/manifest.json \
      --worker /path/to/retained-baseline-worker \
      --build-attestation /path/to/build.json \
      --run-dir /path/to/runs/my-17lands-discovery \
      --runtime /path/to/factory-runtime

The preparation freezes the cohort, mapping, manifest and bounds. Each completed case publishes another report into the same live replay. The default memory limit is 8 GiB per worker. The native search also has node and path-length limits. An external deadline terminates the worker's own process group and preserves its logs; it does not prove that the search space was exhausted.

A build receipt uses schema coworld-guided-fit-build-v1 and binds the source revision, before/after source hashes, command, environment, binary hash and successful build result. This is a compilation attestation, not an independent reproducible-build proof. The first retained receipt is documented in [the earlier measurements](artifacts/17lands-guided-fit-20260908/README.md).

## Investigate and propose a change

Choose issue IDs from a complete baseline report. Write a separate diagnosis that distinguishes the observation which raised the issue from the evidence supporting the proposed fix. For example, an unresolved source ID calls for identity work; a search deadline alone does not establish an engine defect.

Create a committed candidate in an isolated checkout, then retain the exact full patch:

    git diff --binary --full-index FULL_BASELINE_COMMIT FULL_CANDIDATE_COMMIT \
      > /path/to/candidate.patch

Record the proposed change and its origins:

    python3 scripts/fit17lands_factory.py propose \
      --report-id BASELINE_REPORT_ARTIFACT_ID \
      --issue-id DISCOVERED_ISSUE_ID \
      --patch /path/to/candidate.patch \
      --diagnosis /path/to/diagnosis.md \
      --description "Describe the diagnosed problem and resulting behavior" \
      --component observation_adapter \
      --candidate-repository /path/to/candidate-checkout \
      --candidate-revision FULL_CANDIDATE_COMMIT \
      --run-dir /path/to/runs/my-17lands-discovery \
      --runtime /path/to/factory-runtime

Repeat the issue-id option for multiple origins. The command checks the patch against the actual baseline-to-candidate commit diff and derives the motivating feedback and source-case links.

Run the candidate with the same execute command, changing the label, worker and build receipt and adding the returned change-id. The runtime manifest, cohort and declared bounds remain frozen. A different corpus or observation horizon requires a separate run.

## Compare and review

    python3 scripts/fit17lands_factory.py compare \
      --baseline-report-id BASELINE_REPORT_ARTIFACT_ID \
      --candidate-report-id CANDIDATE_REPORT_ARTIFACT_ID \
      --change-id PATCH_ARTIFACT_ID \
      --run-dir /path/to/runs/my-17lands-discovery \
      --runtime /path/to/factory-runtime

The comparison lists changed statuses, present/absent issue signatures, observation coverage and changed constraints or reconstruction. Removing a constraint cannot silently count as an improvement. A disappearing diagnostic is a measurement to investigate; this adapter deliberately records comparison_only rather than issuing an acceptance decision.

The broader factory's reviewed acceptance machinery remains available for separately established properties. This first fitting adapter does not automate the diagnosis, write engine patches or promote weak observational evidence into a strong rules judgment.

Verify and close a finished recording:

    python3 scripts/fit17lands_factory.py verify \
      --run-dir /path/to/runs/my-17lands-discovery \
      --runtime /path/to/factory-runtime

    python3 scripts/fit17lands_factory.py finish \
      --run-dir /path/to/runs/my-17lands-discovery \
      --runtime /path/to/factory-runtime

Verification recomputes report contents and attribution from retained worker receipts and checks the generic replay structure. It does not rerun the engine. Use the recorder/adapter version retained by the run when checking historical recordings.

Serve the run directory with factory-runtime and open client/factory.html?run=my-17lands-discovery. The fitting view shows recorded observations beside engine projections, the selected path, unchecked fields, assumptions and issue origins. Older receipts without a trace remain readable and are explicitly labeled as missing that explanation.

## What generalizes

The shared core records sources, cases, builds, executions, feedback, changes, checks and decisions. It supervises processes and retains exact content identities without knowing Magic rules. The 17Lands adapter supplies the source selection, observation projection, trajectory search and interpretation of its diagnostics.

Another software factory needs its own observable milestones and compatibility procedure. The same evidence structure can retain a compiler input and diagnostic, a service request sequence and visible responses, or a simulator trajectory with hidden state. Each domain must distinguish unknown observations, unsupported behavior, exhausted search and established failures. The recorder cannot decide those semantics on its behalf.

The remaining MTG work is fuller identity/support checks, mulligan and hidden-state reconstruction, better search, and source-grounded semantics for additional observation fields. These are measurable obstacles in the queue, rather than prerequisites for recording the first discovery runs.
