use rand::seq::SliceRandom;
use rand::{Rng, SeedableRng};
use rand_chacha::ChaCha12Rng;

pub fn seeded(seed: u64) -> ChaCha12Rng {
    ChaCha12Rng::seed_from_u64(seed)
}

pub fn shuffle<T>(rng: &mut ChaCha12Rng, values: &mut [T]) {
    values.shuffle(rng);
}

pub fn roll_die(rng: &mut ChaCha12Rng, sides: u32) -> u32 {
    rng.gen_range(1..=sides)
}
