use anyhow::{anyhow, Context, Result};
use serde::{Deserialize, Serialize};
use std::env;

use crate::uri;

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct EpisodeConfig {
    pub tokens: Vec<String>,
    #[serde(default = "default_players")]
    pub players: Vec<PlayerConfig>,
    #[serde(default = "default_seed")]
    pub seed: u64,
    #[serde(default = "default_decks")]
    pub decks: Vec<String>,
    #[serde(default = "default_games_to_win")]
    pub games_to_win: u32,
    #[serde(default = "default_starting_life")]
    pub starting_life: i32,
    #[serde(default = "default_turn_cap")]
    pub turn_cap: u32,
    #[serde(default = "default_clock_s")]
    pub clock_s: f64,
    #[serde(default = "default_decision_cap_s")]
    pub decision_cap_s: f64,
    #[serde(default = "default_player_connect_timeout_s")]
    pub player_connect_timeout_s: f64,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct PlayerConfig {
    pub name: String,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct PublicEpisodeConfig {
    pub players: [PlayerConfig; 2],
    pub seed: u64,
    pub decks: [String; 2],
    pub games_to_win: u32,
    pub starting_life: i32,
    pub turn_cap: u32,
    pub clock_s: f64,
    pub decision_cap_s: f64,
    pub player_connect_timeout_s: f64,
}

impl EpisodeConfig {
    pub async fn from_env() -> Result<Self> {
        let uri = env::var("COGAME_CONFIG_URI").context("COGAME_CONFIG_URI is required")?;
        let text = uri::read_to_string(&uri).await?;
        let config = serde_json::from_str::<EpisodeConfig>(&text)
            .with_context(|| format!("failed to parse config from {uri}"))?;
        config.normalized()
    }

    pub fn public(&self) -> PublicEpisodeConfig {
        PublicEpisodeConfig {
            players: [self.players[0].clone(), self.players[1].clone()],
            seed: self.seed,
            decks: [self.decks[0].clone(), self.decks[1].clone()],
            games_to_win: self.games_to_win,
            starting_life: self.starting_life,
            turn_cap: self.turn_cap,
            clock_s: self.clock_s,
            decision_cap_s: self.decision_cap_s,
            player_connect_timeout_s: self.player_connect_timeout_s,
        }
    }

    fn normalized(mut self) -> Result<Self> {
        if self.tokens.len() < 2 {
            return Err(anyhow!("config tokens must contain two entries"));
        }
        self.tokens.truncate(2);
        while self.players.len() < 2 {
            let index = self.players.len();
            self.players.push(PlayerConfig {
                name: format!("goldfish-{index}"),
            });
        }
        self.players.truncate(2);
        while self.decks.len() < 2 {
            self.decks.push(default_decks()[self.decks.len()].clone());
        }
        self.decks.truncate(2);
        if self.games_to_win == 0 {
            self.games_to_win = default_games_to_win();
        }
        if self.starting_life <= 0 {
            self.starting_life = default_starting_life();
        }
        if self.turn_cap == 0 {
            self.turn_cap = default_turn_cap();
        }
        if self.clock_s <= 0.0 {
            self.clock_s = default_clock_s();
        }
        if self.decision_cap_s <= 0.0 {
            self.decision_cap_s = default_decision_cap_s();
        }
        if self.player_connect_timeout_s <= 0.0 {
            self.player_connect_timeout_s = default_player_connect_timeout_s();
        }
        Ok(self)
    }
}

pub fn host_port_from_env() -> (String, u16) {
    let host = env::var("COGAME_HOST").unwrap_or_else(|_| "0.0.0.0".to_owned());
    let port = env::var("COGAME_PORT")
        .ok()
        .and_then(|value| value.parse::<u16>().ok())
        .unwrap_or(8080);
    (host, port)
}

pub fn load_replay_uri() -> Option<String> {
    env::var("COGAME_LOAD_REPLAY_URI").ok()
}

pub fn results_uri() -> String {
    env::var("COGAME_RESULTS_URI").unwrap_or_else(|_| "results.json".to_owned())
}

pub fn save_replay_uri() -> String {
    env::var("COGAME_SAVE_REPLAY_URI").unwrap_or_else(|_| "replay.json".to_owned())
}

pub fn log_uri() -> Option<String> {
    env::var("COGAME_LOG_URI").ok()
}

fn default_players() -> Vec<PlayerConfig> {
    vec![
        PlayerConfig {
            name: "goldfish-0".to_owned(),
        },
        PlayerConfig {
            name: "goldfish-1".to_owned(),
        },
    ]
}

fn default_decks() -> Vec<String> {
    vec!["red_rush".to_owned(), "green_stompy".to_owned()]
}

fn default_seed() -> u64 {
    42
}

fn default_games_to_win() -> u32 {
    1
}

fn default_starting_life() -> i32 {
    20
}

fn default_turn_cap() -> u32 {
    25
}

fn default_clock_s() -> f64 {
    360.0
}

fn default_decision_cap_s() -> f64 {
    30.0
}

fn default_player_connect_timeout_s() -> f64 {
    60.0
}
