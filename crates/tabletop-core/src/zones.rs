use crate::ids::SeatId;
use serde::{Deserialize, Serialize};

#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum ZoneKind {
    Library,
    Hand,
    Battlefield,
    Graveyard,
    Exile,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct ZoneRef {
    pub seat: SeatId,
    pub zone: ZoneKind,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum Phase {
    Untap,
    Upkeep,
    Draw,
    Main1,
    BeginCombat,
    DeclareAttackers,
    DeclareBlockers,
    CombatDamage,
    EndCombat,
    Main2,
    End,
}

impl ZoneKind {
    pub fn is_hidden(self) -> bool {
        matches!(self, ZoneKind::Library | ZoneKind::Hand)
    }

    pub fn is_public(self) -> bool {
        !self.is_hidden()
    }

    pub fn is_ordered(self) -> bool {
        matches!(
            self,
            ZoneKind::Library | ZoneKind::Graveyard | ZoneKind::Exile
        )
    }
}

impl Phase {
    pub fn next(self) -> Option<Phase> {
        match self {
            Phase::Untap => Some(Phase::Upkeep),
            Phase::Upkeep => Some(Phase::Draw),
            Phase::Draw => Some(Phase::Main1),
            Phase::Main1 => Some(Phase::BeginCombat),
            Phase::BeginCombat => Some(Phase::DeclareAttackers),
            Phase::DeclareAttackers => Some(Phase::DeclareBlockers),
            Phase::DeclareBlockers => Some(Phase::CombatDamage),
            Phase::CombatDamage => Some(Phase::EndCombat),
            Phase::EndCombat => Some(Phase::Main2),
            Phase::Main2 => Some(Phase::End),
            Phase::End => None,
        }
    }
}
