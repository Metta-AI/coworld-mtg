# Separate costs exposed a missing boundary

Case ID: `01edd604679d89888ad9bb3bd13ca1c531fbbdd1c65f98341e7ce2a5a57d09aa`.

The [runtime stop report](hushbringer-implementation-stop-v7-components.md)
records a regression introduced by the simultaneous-event repair. When two
separate sacrifice costs were deferred until mana payment, their object lists
were flattened into one group. Sacrificing Hushbringer first and Doomed Traveler
second incorrectly suppressed Traveler's trigger. The original engine created
one Spirit in this ordering; the candidate created zero.

Immediate-payment controls preserved separate groups. The deferred queue had
lost which validated cost selection each object belonged to. This prompted a
new typed boundary and a fresh planning and review cycle. The target case's
expectation was unchanged; the candidate was not accepted.

The [manifest](manifest.json) binds the exact proof, test sources and logs.
Full source archives remain on EC2 at the recorded paths and hashes. The
tracked patches omit new untracked Rust modules and are not complete source
snapshots by themselves. The extra library-choice fixture failure in active
attempt 4 is disclosed separately in the proof; later corrections do not
replace this attempt's sources or result.
