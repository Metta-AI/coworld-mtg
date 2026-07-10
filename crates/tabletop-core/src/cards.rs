use crate::ids::{CardId, SeatId};
use crate::setup::CardSpec;
use crate::zones::{ZoneKind, ZoneRef};
use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(tag = "type", rename_all = "snake_case")]
pub enum CardAttr {
    Tapped { value: bool },
    FaceDown { value: bool },
    Attacking { value: bool },
    PtOverride { value: Option<String> },
    Annotation { value: String },
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct CardView {
    pub id: CardId,
    pub owner: SeatId,
    pub controller: SeatId,
    pub spec: CardSpec,
    pub is_token: bool,
    pub tapped: bool,
    pub face_down: bool,
    pub attacking: bool,
    pub pt_override: Option<String>,
    pub annotation: Option<String>,
    pub counters: BTreeMap<String, i32>,
    pub x: Option<i16>,
    pub y: Option<i16>,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
#[allow(clippy::large_enum_variant)]
pub enum CardRef {
    Known(CardView),
    Hidden { id: CardId },
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub(crate) struct CardInstance {
    pub id: CardId,
    pub owner: SeatId,
    pub spec: CardSpec,
    pub is_token: bool,
    pub location: ZoneRef,
    pub tapped: bool,
    pub face_down: bool,
    pub attacking: bool,
    pub pt_override: Option<String>,
    pub annotation: Option<String>,
    pub counters: BTreeMap<String, i32>,
    pub x: Option<i16>,
    pub y: Option<i16>,
}

impl CardInstance {
    pub fn new_deck_card(id: CardId, owner: SeatId, spec: CardSpec) -> Self {
        Self {
            id,
            owner,
            spec,
            is_token: false,
            location: ZoneRef {
                seat: owner,
                zone: ZoneKind::Library,
            },
            tapped: false,
            face_down: false,
            attacking: false,
            pt_override: None,
            annotation: None,
            counters: BTreeMap::new(),
            x: None,
            y: None,
        }
    }

    pub fn new_token(id: CardId, owner: SeatId, spec: CardSpec, x: i16, y: i16) -> Self {
        Self {
            id,
            owner,
            spec,
            is_token: true,
            location: ZoneRef {
                seat: owner,
                zone: ZoneKind::Battlefield,
            },
            tapped: false,
            face_down: false,
            attacking: false,
            pt_override: None,
            annotation: None,
            counters: BTreeMap::new(),
            x: Some(x),
            y: Some(y),
        }
    }

    pub fn view(&self) -> CardView {
        CardView {
            id: self.id,
            owner: self.owner,
            controller: self.location.seat,
            spec: self.spec.clone(),
            is_token: self.is_token,
            tapped: self.tapped,
            face_down: self.face_down,
            attacking: self.attacking,
            pt_override: self.pt_override.clone(),
            annotation: self.annotation.clone(),
            counters: self.counters.clone(),
            x: self.x,
            y: self.y,
        }
    }

    pub fn apply_attr(&mut self, attr: &CardAttr) {
        match attr {
            CardAttr::Tapped { value } => self.tapped = *value,
            CardAttr::FaceDown { value } => self.face_down = *value,
            CardAttr::Attacking { value } => self.attacking = *value,
            CardAttr::PtOverride { value } => self.pt_override = value.clone(),
            CardAttr::Annotation { value } => self.annotation = Some(value.clone()),
        }
    }
}
