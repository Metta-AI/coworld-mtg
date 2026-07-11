use anyhow::{anyhow, Result};
use phase_bridge::{CardSpec, DeckList};
use serde::Deserialize;

#[derive(Deserialize)]
struct DeckFile {
    name: String,
    cards: Vec<DeckEntry>,
}

#[derive(Deserialize)]
struct DeckEntry {
    count: usize,
    spec: CardSpec,
}

pub fn load_deck(id: &str) -> Result<DeckList> {
    let text = match id {
        "red_rush" => include_str!("../../../decks/red_rush.json"),
        "green_stompy" => include_str!("../../../decks/green_stompy.json"),
        _ => return Err(anyhow!("unknown deck id {id}")),
    };
    parse_deck(text)
}

fn parse_deck(text: &str) -> Result<DeckList> {
    let deck = serde_json::from_str::<DeckFile>(text)?;
    let mut cards = Vec::new();
    for entry in deck.cards {
        cards.extend(std::iter::repeat_n(entry.spec, entry.count));
    }
    Ok(DeckList {
        name: deck.name,
        cards,
    })
}
