# Battle-protector member handoff: bounded production reachability finding

The exact released mutation sba-check_battle_protector removes only zones::with_departure_member in the zero-legal-protector departure arm. That arm is not reachable through a coherent, nonterminal game using the shipped format presets inspected below. This is a bounded source finding, not a runtime mutation kill, proof about every representable GameState/configuration, or permission to remove the wrapper. Its exact measured mutation result remains in the nineteen-row campaign.

Frozen source authority: hushbringer-v9-execution/frozen-candidate-v9/source.json, SHA256 46ac753dff4229b2b2841a86b5334f2595c4b76bef4be8a4941dd76756f5f803, 2,051 files. All inspection used SSH to nishadsingh-box-4. Active source is untouched.

## Required first branches

1. game/sba.rs::check_state_based_actions (52) creates one iteration owner. Its player-loss block calls eliminate_players_simultaneously and immediately returns false on WaitingFor::GameOver. Other engine elimination paths run the same terminal-state authority.
2. check_battle_protector (1649) considers phased-in live Battlefield objects with Battle core type. A legal existing protector or an attacked battle short-circuits.
3. Non-Siege battles always form legal_choices = vec![controller]; they cannot enter the empty-choice arm. A Siege forms choices from players::opponents(state, controller), then filters state.eliminated_players. Only legal_choices.len() == 0 reaches the assigned physical handoff.
4. players.rs::opponents (160) uses seat order, is_opponent and is_alive; is_alive (11) reads player existence and player.is_eliminated. topology.rs::is_opponent (76) requires distinct players and different team_id. No range-of-influence or Star-style neighbor filter is present.
5. Ordinary elimination updates both authorities: elimination.rs around 394 sets player.is_eliminated = true and around 397 adds to eliminated_players. eliminate_players_simultaneously calls check_game_over at 86 before returning.

## Shipped topology and terminal relation

- FormatConfig::topology (types/format.rs 509) exposes IndividualSeats, FixedTeams and OneVsMany. The shipped FixedTeams format is TwoHeadedGiant; its constructor (842 onward) sets team_based true. Archenemy is OneVsMany.
- IndividualSeats gives each seat a distinct TeamId (topology.rs 9). No living opponents means at most one living player. elimination::check_game_over (647–703) ends the game at living.len() <= 1.
- TwoHeadedGiant maps seats to two-player teams. No living opposing team means at most one living team. The same terminal function explicitly checks living team count for TwoHeadedGiant shared resources.
- Archenemy gives the archenemy and heroes two distinct sides. The terminal function ends the game when either side has no living player.
- Coherent elimination of the last legal opposing protector therefore ends a shipped game before this SBA branch can perform a new battle departure. The handoff cannot be proven by a normal ongoing-game action fixture under those premises.

## Existing fixture does not prove public reachability

tests/integration/rules/battle.rs::battle_with_no_legal_protector_goes_to_graveyard (350) seeds a two-player Siege with illegal self protector, adds P1 only to state.eliminated_players, and directly calls sba::check_state_based_actions. P1's player.is_eliminated remains false. Consequently opponents initially sees a living opponent and the second eliminated-list filter removes it. This low-level inconsistent fixture reaches the defensive zero-choice path, but submits no public elimination and proves no coherent action path.

The assigned old filter game::sba::tests does not include that integration test. Even running the raw-SBA test would only check destination, with no ownership/snapshot/payoff assertion, and would not replace the required production proof.

## Representable-configuration qualification

FormatConfig::topology permits its generic team_based fallback to produce FixedTeams for other GameFormat values. The terminal-state special case is keyed to TwoHeadedGiant shared resources. Manually setting team_based true on an unrelated format could leave multiple same-team survivors with no opponents while the terminal check only counts players. That is a separate topology/terminal compatibility issue, not a shipped coherent scenario proved here. It must not be silently adopted to manufacture a runtime kill. Nor may a fixture set inconsistent elimination fields or inject pending state.

## Plan disposition needed

Full v9 requires threading the owner through every SBA sub-check (implementation 3b/3d and producer table) and complete per-seam runtime/revert proof. Its concrete SBA rows describe logical iteration grouping and Augment; no explicit zero-protector exception was found. Retain this defensive wrapper and the full eight other handoff obligations. A fresh full plan/review must explicitly dispose the bounded impossibility and prescribe evidence for the defensive branch. This executor does not waive it, remove code, broaden topology, or claim an unexecuted mutant passes.

Main executor independently audited the same three topology variants and reported this bounded conclusion. The finding remains qualified to shipped coherent configurations.

