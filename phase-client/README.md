# Phase client Coworld overlay

These files are copied onto the exact Phase revision pinned by
`phase-bridge`. The overlay replaces Phase's multiplayer `WebSocketAdapter`
at build time and boots `GamePage` directly, without Phase's lobby, local WASM
engine, deck storage, matchmaking, service worker, or telemetry.

The overlay must stay narrow: transport, Coworld chrome, entry points, and
replay adaptation belong here; battlefield and prompt components remain owned
by Phase.

Current replays buffer at their first recorded event and stay paused until the
finite stream completes. The Coworld chrome owns the bottom transport dock,
recorded-time playback, speed selection, and event/turn/game navigation. Its
keyboard contract is Space for play/pause, Left/Right for events,
Shift+Left/Right for turns, and Page Up/Page Down for games.
