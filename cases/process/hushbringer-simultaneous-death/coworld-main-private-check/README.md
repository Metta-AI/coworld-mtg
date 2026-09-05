# Private corpus and browser validation on published main

The earlier main integration check skipped private-corpus and browser tests
because the private corpus was not materialized in the publication checkout.
The existing archive was subsequently retrieved from its content-addressed
S3 location and verified against corpus.lock.json. All three card/deck payloads
match the original experiment corpus; its manifest names the current main pin.

On published Coworld revision 2895ad02 with Phase b5f46858, the complete Rust
workspace tests with private-corpus-tests passed and both browser tests passed.
Tracked source remained unchanged. This validates the currently published
harness and existing Phase pin; it is separate from fixed-checker repair
acceptance and from a future dependency update.

The [receipt](receipt.json) binds commands, environment, corpus identity and
logs. The [manifest](manifest.json) preserves original and compressed hashes.
The private card/deck archive stays on EC2 and is not copied into this record.
Existing local AWS authentication streamed the archive directly into EC2;
there was no local build, local artifact file or credential copy.

The server requires its corpus manifest to match its Phase revision. Publishing
the eventual repaired engine therefore also requires a new deterministic
corpus archive and matching lock, followed by validation of that new pin.
