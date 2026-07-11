use anyhow::{anyhow, Context, Result};
use futures::{SinkExt, StreamExt};
use phase_bridge::{GameAction, ViewerSnapshot};
use serde::{Deserialize, Serialize};
use serde_json::Value;
use tokio_tungstenite::tungstenite::Message;

#[derive(Clone, Debug, Default)]
pub struct GoldfishReport {
    pub hellos: Vec<HelloReport>,
    pub leaked_opponent_hand: bool,
    pub match_scores: Option<[f64; 2]>,
}

#[derive(Clone, Debug)]
pub struct HelloReport {
    pub slot: usize,
    pub deck_name: String,
    pub deck_size: usize,
}

#[derive(Debug, Deserialize)]
#[serde(tag = "type", rename_all = "snake_case")]
enum ServerFrame {
    Hello {
        slot: usize,
        seat: u8,
        decklist: phase_bridge::DeckList,
    },
    State {
        state: Box<ViewerSnapshot>,
    },
    Ack {
        cmd_id: u64,
    },
    Reject {
        cmd_id: u64,
        error: RejectError,
    },
    GameEnd,
    MatchEnd {
        scores: [f64; 2],
    },
}

#[derive(Debug, Deserialize)]
struct RejectError {
    kind: String,
    detail: String,
}

#[derive(Serialize)]
struct ClientCommand {
    cmd_id: u64,
    action: GameAction,
}

pub async fn run_url(url: &str) -> Result<GoldfishReport> {
    let (stream, _) = tokio_tungstenite::connect_async(url).await?;
    let (mut write, mut read) = stream.split();
    let mut bot = Bot::default();

    while let Some(message) = read.next().await {
        let message = message?;
        let Message::Text(text) = message else {
            continue;
        };
        let frame = serde_json::from_str::<ServerFrame>(&text).with_context(|| {
            format!(
                "invalid server frame: {}",
                text.chars().take(1000).collect::<String>()
            )
        })?;
        if let Some(action) = bot.handle_frame(frame)? {
            let text = bot.command_text(action)?;
            write.send(Message::Text(text.into())).await?;
        }
        if bot.done {
            return Ok(bot.report);
        }
    }
    Err(anyhow!("connection closed before match_end"))
}

#[derive(Default)]
struct Bot {
    seat: Option<u8>,
    latest: Option<ViewerSnapshot>,
    next_cmd_id: u64,
    awaiting_ack: bool,
    done: bool,
    report: GoldfishReport,
}

impl Bot {
    fn handle_frame(&mut self, frame: ServerFrame) -> Result<Option<GameAction>> {
        match frame {
            ServerFrame::Hello {
                slot,
                seat,
                decklist,
            } => {
                self.seat = Some(seat);
                self.report.hellos.push(HelloReport {
                    slot,
                    deck_name: decklist.name,
                    deck_size: decklist.cards.len(),
                });
            }
            ServerFrame::State { state } => {
                self.report.leaked_opponent_hand |= opponent_hand_has_known(self.seat, &state);
                self.latest = Some(*state);
            }
            ServerFrame::Ack { cmd_id } => {
                let _ = cmd_id;
                self.awaiting_ack = false;
            }
            ServerFrame::Reject { cmd_id, error } => {
                self.awaiting_ack = false;
                return Err(anyhow!(
                    "command {cmd_id} rejected: {} {}",
                    error.kind,
                    error.detail
                ));
            }
            ServerFrame::GameEnd => {
                self.latest = None;
                self.awaiting_ack = false;
            }
            ServerFrame::MatchEnd { scores } => {
                self.report.match_scores = Some(scores);
                self.done = true;
            }
        }
        Ok(self.plan())
    }

    fn plan(&self) -> Option<GameAction> {
        if self.awaiting_ack {
            return None;
        }
        choose_action(&self.latest.as_ref()?.legal_actions)
    }

    fn command_text(&mut self, action: GameAction) -> Result<String> {
        let cmd_id = self.next_cmd_id;
        self.next_cmd_id += 1;
        self.awaiting_ack = true;
        Ok(serde_json::to_string(&ClientCommand { cmd_id, action })?)
    }
}

fn choose_action(actions: &[GameAction]) -> Option<GameAction> {
    let mut candidates = actions
        .iter()
        .filter_map(|action| {
            serde_json::to_value(action)
                .ok()
                .map(|value| (action, value))
        })
        .collect::<Vec<_>>();
    candidates.sort_by_key(|(_, value)| action_rank(value));
    candidates.first().map(|(action, _)| (*action).clone())
}

fn action_rank(value: &Value) -> (u8, std::cmp::Reverse<usize>) {
    let kind = value
        .get("type")
        .and_then(Value::as_str)
        .unwrap_or_default();
    let data = value.get("data").unwrap_or(&Value::Null);
    let count = match kind {
        "DeclareAttackers" => data
            .get("attacks")
            .and_then(Value::as_array)
            .map_or(0, Vec::len),
        "DeclareBlockers" => data
            .get("assignments")
            .and_then(Value::as_array)
            .map_or(0, Vec::len),
        _ => 0,
    };
    let rank = match kind {
        "MulliganDecision" if nested_type(data.get("choice")) == Some("Keep") => 0,
        "SelectCards" => 1,
        "PlayLand" => 2,
        "CastSpell" => 3,
        "ActivateAbility" => 4,
        "DeclareAttackers" => 5,
        "DeclareBlockers" => 6,
        "PassPriority" => 8,
        _ => 7,
    };
    (rank, std::cmp::Reverse(count))
}

fn nested_type(value: Option<&Value>) -> Option<&str> {
    value?.get("type").and_then(Value::as_str)
}

fn opponent_hand_has_known(seat: Option<u8>, snapshot: &ViewerSnapshot) -> bool {
    let Some(seat) = seat else {
        return false;
    };
    snapshot
        .players
        .iter()
        .filter(|player| player.id != seat)
        .flat_map(|player| &player.hand)
        .any(|card| card.name != "Hidden Card" || !card.face_down)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn ranks_real_plays_before_priority_pass() {
        let actions = vec![
            serde_json::from_value(serde_json::json!({ "type": "PassPriority" })).unwrap(),
            serde_json::from_value(serde_json::json!({
                "type": "PlayLand",
                "data": { "object_id": 1, "card_id": 1 }
            }))
            .unwrap(),
        ];
        let chosen = serde_json::to_value(choose_action(&actions).unwrap()).unwrap();
        assert_eq!(chosen["type"], "PlayLand");
    }

    #[test]
    fn chooses_largest_attack_declaration() {
        let actions = vec![
            serde_json::from_value(serde_json::json!({
                "type": "DeclareAttackers",
                "data": { "attacks": [] }
            }))
            .unwrap(),
            serde_json::from_value(serde_json::json!({
                "type": "DeclareAttackers",
                "data": { "attacks": [[1, { "type": "Player", "data": 1 }]], "bands": [] }
            }))
            .unwrap(),
        ];
        let chosen = serde_json::to_value(choose_action(&actions).unwrap()).unwrap();
        assert_eq!(chosen["data"]["attacks"].as_array().unwrap().len(), 1);
    }
}
