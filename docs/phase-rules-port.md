# Phase rules-engine port

## Decision

Coworld MTG uses the open-source Phase engine as its rules authority. Production
builds pin the maintained [nishu-builder fork](https://github.com/nishu-builder/phase),
while [phase-rs/phase](https://github.com/phase-rs/phase) remains the upstream
project. The previous `tabletop-core` model is a useful
Cockatrice-style event table, but it cannot become real Magic by incrementally
adding checks: priority, casting, costs, continuous effects, layers, state-based
actions, triggers, replacement effects, and combat all depend on one another.

The Phase engine dependency is pinned to fork commit
`3391a770ef35d4fa7717e7343841fd6e6ca4aec6`, under Phase's MIT/Apache-2.0
license.
`crates/phase-bridge` is the only Coworld MTG layer allowed to invoke it. Host,
replay, browser, and policy code consume viewer-filtered state and exact legal
`GameAction` values; they must not reproduce legality.

## Why Phase

The alternatives evaluated were Forge and XMage. Both are established Magic
implementations, but both are Java applications and would require a second
runtime plus a translation service. Phase is Rust-native, exposes pure game
state and reducer APIs, supports native and WASM clients, and already models:

- turn structure, priority, the stack, and automatic phase progression;
- land plays, spell/ability timing, targets, costs, mana production and payment;
- attacker/blocker declarations and combat-damage assignment;
- state-based actions, continuous-effect layers, triggers, and replacements;
- London mulligans, hidden information, multiplayer viewer filtering, and
  exact per-viewer legal actions;
- parsed Oracle rules for a broad card corpus and an existing AI action surface.

This is still an open-source rules implementation, not a claim of perfect
coverage. Unsupported cards and parser gaps must be surfaced at deck-import
time and tracked against the pinned Phase revision. They must never silently
fall back to honor-system play.

## Scryfall boundary

Scryfall is authoritative card metadata, not an executable Magic rules engine.
The integration therefore has two distinct data paths:

1. Phase's generated card export supplies parsed rules and stores each card's
   Scryfall Oracle ID. Deck names are resolved against this export before a game
   can start.
2. Scryfall bulk data supplies canonical card/printing metadata and image URIs
   for presentation and deck import. Bulk snapshots should be cached and
   content-addressed; the server must not issue one API request per card.

An imported deck is accepted only if every entry resolves to a Phase card face.
The UI may use a Scryfall printing for art, but rules identity remains the
Scryfall Oracle ID embedded in the Phase face. Printing identity and Oracle
identity must not be conflated for split, transform, modal double-faced, or
rebalanced digital cards.

## Mechanics contract

The engine owns all state changes. A player submits one of the exact legal
actions produced for their filtered view. An action cannot name an arbitrary
card, choose an unavailable target, spend nonexistent mana, bypass priority, or
mark a creature as attacking outside the declaration step.

Required invariants:

- Opponent hands and ordered libraries are absent from player and spectator
  projections; replay omniscience is produced only after the episode.
- Every accepted command is byte-for-byte equivalent to a currently legal
  Phase action for that submitting seat.
- Simultaneous decisions such as London mulligans expose independent legal
  actions to every pending seat.
- The Phase state is the replay source of truth. Human-readable event text is a
  projection of engine events, never a second state machine.
- Mana display, payable costs, attack/block choices, target selectors, stack
  objects, and pending prompts are derived from engine state/legal actions.
- An engine `GameOver` state determines the result. Clock forfeits and explicit
  concessions are host-level terminal inputs and must be recorded distinctly.

## Completed migration

1. `phase-bridge` proves deck resolution, redaction, mulligans,
   legal actions, submission, deterministic state serialization, and outcomes.
2. The player protocol uses Phase
   `GameAction`; send viewer-filtered state, legal actions, effective spell
   costs, and per-object action groups in every decision snapshot.
3. The browser renders engine zones, mana pools, the stack, priority, pending
   prompts, legal action controls, and name-resolved Scryfall art for the
   bundled decks without putting card logic in TypeScript.
4. Replays record full authoritative projections, accepted Phase actions, and
   engine events. Old `move_cards` streams are no longer supported.
5. Scripted players select from the supplied legal action
   list. A policy may rank actions but may not invent one.
6. The legacy tabletop authority and free-form protocol have been removed.

## Current validation

The adapter test uses a compact fixture derived from the pinned Phase export.
Both bundled 40-card decks resolve completely, receive seven-card hidden hands,
enter Phase's simultaneous London mulligan state, and submit exact legal keep
actions. Real WebSocket episodes additionally exercise Phase state/action
transport, hidden-information checks, scoring, timeout concessions, and replay
looping.
