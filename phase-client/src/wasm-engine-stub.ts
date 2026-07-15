const unavailable = (): never => {
  throw new Error("The Coworld Phase client does not ship a browser rules engine");
};

export default async function init(): Promise<never> {
  return unavailable();
}

export const ping = unavailable;
export const take_last_panic_message = unavailable;
export const initialize_game = unavailable;
export const submit_action = unavailable;
export const get_game_state = unavailable;
export const get_filtered_game_state = unavailable;
export const get_ai_action = unavailable;
export const get_ai_scored_candidates = unavailable;
export const select_action_from_scores = unavailable;
export const get_legal_actions_js = unavailable;
export const get_legal_actions_for_viewer_js = unavailable;
export const get_viewer_snapshot_js = unavailable;
export const restore_game_state = unavailable;
export const resume_multiplayer_host_state = unavailable;
export const load_card_database = unavailable;
export const build_ai_card_subset = unavailable;
export const evaluate_deck_compatibility_js = unavailable;
export const apply_seat_mutation = unavailable;
export const project_seat_view = unavailable;
export const export_game_state_json = unavailable;
export const clear_game_state = unavailable;
export const set_multiplayer_mode = unavailable;
export const resolve_all = unavailable;
export const estimate_bracket_for_deck = unavailable;
export const has_replay_recording = unavailable;
export const export_replay_log = unavailable;
export const load_replay_for_playback = unavailable;
export const replay_length_js = unavailable;
export const replay_header_js = unavailable;
export const replay_seek_js = unavailable;
export const clear_replay_playback = unavailable;
