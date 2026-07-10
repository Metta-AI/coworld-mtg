use serde::{Deserialize, Serialize};

#[derive(
    Clone, Copy, Debug, Default, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize,
)]
pub struct SeatId(pub u8);

#[derive(
    Clone, Copy, Debug, Default, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize,
)]
pub struct CardId(pub u32);

#[derive(
    Clone, Copy, Debug, Default, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize,
)]
pub struct Seq(pub u64);

impl SeatId {
    pub fn opponent(self) -> SeatId {
        SeatId(1 - self.0)
    }

    pub fn index(self) -> usize {
        usize::from(self.0)
    }

    pub fn is_valid(self) -> bool {
        self.0 < 2
    }
}
