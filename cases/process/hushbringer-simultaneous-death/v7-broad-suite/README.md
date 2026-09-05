# Broader checks caught four more failing tests

The active library run passed 16,574 tests and failed three. The separate
integration run passed 3,042 and failed five: the four deferred-component
tests and an existing Oversimplify test. Both runs verified that source bytes
remained unchanged.

All four newly failing pre-existing tests passed on the original engine using
its own build target. They exercise exit-time power, incarnation identity,
controller information and Oversimplify's per-player counter totals. The
fixtures directly assign derived power or controller fields, which the new
event boundary refreshes. That is an investigation finding, not permission
to lower their expected results or waive their regression checks. Their
disposition belongs in the reviewed repair plan.

The [manifest](manifest.json) binds the command scripts, receipts, baseline
logs and exact failure excerpts. Complete active logs remain on EC2 at the
recorded paths and hashes. Neither run establishes acceptance.
