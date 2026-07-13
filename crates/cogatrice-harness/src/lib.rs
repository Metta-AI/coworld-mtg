//! Reproducible, direct-to-Phase fidelity harness for Cogatrice.
//!
//! This crate owns orchestration, artifacts, replay, and invariants. It never
//! interprets card text or implements a Magic rule; every submitted action is
//! selected from Phase's exact legal-action surface through `phase-bridge`.

mod aggregate;
mod corpus;
mod io;
mod model;
mod runner;
mod soft_signals;

pub use aggregate::{aggregate_results, AggregateOptions};
pub use corpus::{load_manifest, materialize_corpus, MaterializeOptions};
pub use model::*;
pub use runner::{minimize_trace, replay_trace_file, run_shard, RunOptions};
pub use soft_signals::mine_17lands;
