use anyhow::{bail, Result};
use clap::{Args, Parser, Subcommand};
use coworld_mtg_harness::{
    aggregate_results, load_manifest, materialize_corpus, mine_17lands_with_options,
    minimize_trace, replay_trace_file, run_shard, AggregateOptions, CardsCsvInput,
    Lands17InputSchema, MaterializeOptions, Mine17landsOptions, RunOptions,
};
use phase_bridge::PHASE_REVISION;
use std::path::PathBuf;

#[derive(Parser)]
#[command(name = "coworld-mtg-harness")]
#[command(about = "Reproducible direct-to-Phase MTG fidelity harness")]
struct Cli {
    #[command(subcommand)]
    command: Command,
}

#[derive(Subcommand)]
enum Command {
    /// Parse raw Scryfall JSONL with Phase; emits observations without expectations.
    OracleProbe {
        #[arg(long)]
        input: PathBuf,
        #[arg(long)]
        output: PathBuf,
    },
    /// Typed, reproducible scenario and repair evaluation loop.
    Case(coworld_mtg_harness::cases::CaseArgs),
    /// Materialize and cross-check an immutable corpus manifest.
    Materialize(MaterializeArgs),
    /// Run a deterministic, resumable legal-action shard.
    Run(RunArgs),
    /// Replay a standalone trace and verify all hard gates.
    Replay(ReplayArgs),
    /// Reduce a failing trace to its first discriminating transition.
    Minimize(MinimizeArgs),
    /// Deduplicate findings and publish a scoreboard.
    Aggregate(AggregateArgs),
    /// Mine 17Lands observations into explicitly soft workload signals.
    Mine17lands(Mine17landsArgs),
    /// Validate campaign identity and run one improvement shard.
    Improve(ImproveArgs),
    /// Fit a bounded supported projection of real 17Lands observations.
    Fit17lands(Fit17landsArgs),
}

#[derive(Args)]
struct Fit17landsArgs {
    #[arg(long)]
    manifest_uri: String,
    #[arg(long)]
    replay_data: String,
    #[arg(long)]
    replay_sha256: String,
    #[arg(long)]
    cards_csv: String,
    #[arg(long)]
    cards_csv_sha256: String,
    #[arg(long, default_value_t = 0)]
    game_index: u64,
    #[arg(long, default_value_t = 1)]
    turn_pairs: u32,
    #[arg(long, default_value_t = 10_000)]
    nodes: u64,
    #[arg(long, default_value_t = 128)]
    max_actions: usize,
    /// Explicit hypothetical filler for an unobserved opponent deck.
    #[arg(long)]
    opponent_filler: String,
    #[arg(long)]
    output_dir: PathBuf,
}

#[derive(Args)]
struct MaterializeArgs {
    #[arg(long)]
    set: String,
    #[arg(long)]
    phase_card_data: String,
    #[arg(long)]
    phase_card_data_sha256: Option<String>,
    #[arg(long)]
    mtgjson: Option<String>,
    #[arg(long)]
    mtgjson_sha256: Option<String>,
    #[arg(long)]
    mtgjson_version: Option<String>,
    #[arg(long)]
    scryfall: Option<String>,
    #[arg(long)]
    scryfall_sha256: Option<String>,
    #[arg(long)]
    scryfall_snapshot: Option<String>,
    #[arg(long = "17lands")]
    lands17: Option<String>,
    #[arg(long = "17lands-sha256")]
    lands17_sha256: Option<String>,
    #[arg(long = "17lands-dataset")]
    lands17_dataset: Option<String>,
    #[arg(long)]
    output_dir: PathBuf,
}

#[derive(Args, Clone)]
struct RunArgs {
    #[arg(long)]
    manifest_uri: String,
    #[arg(long, default_value = ".private/corpus/decks/lorehold_excavation.json")]
    deck_a: PathBuf,
    #[arg(long, default_value = ".private/corpus/decks/fractal_convergence.json")]
    deck_b: PathBuf,
    #[arg(long)]
    output_dir: PathBuf,
    #[arg(long)]
    run_id: Option<String>,
    #[arg(long, default_value_t = 0)]
    seed_start: u64,
    #[arg(long)]
    seed_count: u64,
    #[arg(long, default_value_t = 2_000)]
    action_budget: u64,
    #[arg(long, default_value_t = 100)]
    checkpoint_every: u64,
    #[arg(long, default_value_t = 1_073_741_824)]
    max_trace_bytes: u64,
    #[arg(long)]
    resume: bool,
}

#[derive(Args)]
struct ReplayArgs {
    #[arg(long)]
    manifest_uri: String,
    #[arg(long)]
    trace: PathBuf,
}

#[derive(Args)]
struct MinimizeArgs {
    #[arg(long)]
    manifest_uri: String,
    #[arg(long)]
    trace: PathBuf,
    #[arg(long)]
    output: PathBuf,
}

#[derive(Args)]
struct AggregateArgs {
    #[arg(long, required = true)]
    run_dir: Vec<PathBuf>,
    #[arg(long)]
    output: PathBuf,
}

#[derive(Args)]
struct Mine17landsArgs {
    #[arg(long)]
    manifest_uri: String,
    #[arg(long)]
    output: PathBuf,
    #[arg(long)]
    row_limit: Option<u64>,
    /// Resolve observed Arena cast IDs in the public wide replay schema.
    #[arg(long, value_enum, default_value = "auto")]
    input_schema: Lands17InputSchema,
    #[arg(long, requires = "cards_csv_sha256")]
    cards_csv: Option<String>,
    #[arg(long, requires = "cards_csv")]
    cards_csv_sha256: Option<String>,
}

#[derive(Args)]
struct ImproveArgs {
    #[arg(long)]
    set: String,
    #[arg(long)]
    phase_rev: String,
    #[arg(long)]
    manifest_uri: String,
    #[arg(long, default_value_t = 0)]
    seed_start: u64,
    #[arg(long)]
    seed_count: u64,
    #[arg(long)]
    checkpoint_uri: PathBuf,
    #[arg(long)]
    run_id: Option<String>,
    #[arg(long, default_value = ".private/corpus/decks/lorehold_excavation.json")]
    deck_a: PathBuf,
    #[arg(long, default_value = ".private/corpus/decks/fractal_convergence.json")]
    deck_b: PathBuf,
    #[arg(long, default_value_t = 2_000)]
    action_budget: u64,
    #[arg(long, default_value_t = 100)]
    checkpoint_every: u64,
    #[arg(long, default_value_t = 1_073_741_824)]
    max_trace_bytes: u64,
    #[arg(long)]
    resume: bool,
}

#[tokio::main]
async fn main() -> Result<()> {
    let cli = Cli::parse();
    match cli.command {
        Command::OracleProbe { input, output } => {
            coworld_mtg_harness::oracle_probe::inspect_file(&input, &output)?
        }
        Command::Fit17lands(args) => {
            use coworld_mtg_harness::fitting::{fit_17lands, FitLimits, FitOptions};
            let result = fit_17lands(FitOptions {
                manifest_uri: args.manifest_uri,
                replay_data: args.replay_data,
                replay_sha256: args.replay_sha256,
                cards_csv: args.cards_csv,
                cards_csv_sha256: args.cards_csv_sha256,
                game_index: args.game_index,
                turn_pairs: args.turn_pairs,
                opponent_filler: args.opponent_filler,
                output_dir: args.output_dir,
                limits: FitLimits {
                    nodes: args.nodes,
                    max_actions: args.max_actions,
                },
            })
            .await?;
            println!("{}", serde_json::to_string_pretty(&result)?);
        }
        Command::Case(args) => coworld_mtg_harness::cases::dispatch(args)?,
        Command::Materialize(args) => {
            let manifest = materialize_corpus(&MaterializeOptions {
                set: args.set,
                phase_card_data: args.phase_card_data,
                phase_sha256: args.phase_card_data_sha256,
                mtgjson: args.mtgjson,
                mtgjson_sha256: args.mtgjson_sha256,
                mtgjson_version: args.mtgjson_version,
                scryfall: args.scryfall,
                scryfall_sha256: args.scryfall_sha256,
                scryfall_snapshot: args.scryfall_snapshot,
                lands17: args.lands17,
                lands17_sha256: args.lands17_sha256,
                lands17_dataset: args.lands17_dataset,
                output_dir: args.output_dir,
            })
            .await?;
            println!("{}", serde_json::to_string_pretty(&manifest)?);
        }
        Command::Run(args) => {
            let result = run_shard(&run_options(args)).await?;
            println!("{}", serde_json::to_string_pretty(&result)?);
        }
        Command::Replay(args) => {
            let trace = replay_trace_file(&args.manifest_uri, &args.trace).await?;
            println!(
                "verified seed {} with {} transitions",
                trace.seed,
                trace.transitions.len()
            );
        }
        Command::Minimize(args) => {
            let trace = minimize_trace(&args.manifest_uri, &args.trace, &args.output).await?;
            println!(
                "wrote {} transitions to {}",
                trace.transitions.len(),
                args.output.display()
            );
        }
        Command::Aggregate(args) => {
            let scoreboard = aggregate_results(&AggregateOptions {
                run_dirs: args.run_dir,
                output: args.output,
            })?;
            println!("{}", serde_json::to_string_pretty(&scoreboard)?);
        }
        Command::Mine17lands(args) => {
            let report = mine_17lands_with_options(
                &args.manifest_uri,
                &args.output,
                args.row_limit,
                &Mine17landsOptions {
                    input_schema: args.input_schema,
                    cards_csv: args
                        .cards_csv
                        .zip(args.cards_csv_sha256)
                        .map(|(source, sha256)| CardsCsvInput { source, sha256 }),
                },
            )
            .await?;
            println!("{}", serde_json::to_string_pretty(&report)?);
        }
        Command::Improve(args) => {
            let manifest = load_manifest(&args.manifest_uri).await?;
            if manifest.set != args.set {
                bail!(
                    "requested set {} does not match manifest set {}",
                    args.set,
                    manifest.set
                );
            }
            if args.phase_rev != PHASE_REVISION {
                bail!(
                    "requested Phase revision {} does not match pinned {}",
                    args.phase_rev,
                    PHASE_REVISION
                );
            }
            let run = RunArgs {
                manifest_uri: args.manifest_uri,
                deck_a: args.deck_a,
                deck_b: args.deck_b,
                output_dir: args.checkpoint_uri,
                run_id: Some(args.run_id.unwrap_or_else(|| {
                    format!("{}-{}-{}", args.set, args.seed_start, args.seed_count)
                })),
                seed_start: args.seed_start,
                seed_count: args.seed_count,
                action_budget: args.action_budget,
                checkpoint_every: args.checkpoint_every,
                max_trace_bytes: args.max_trace_bytes,
                resume: args.resume,
            };
            let result = run_shard(&run_options(run)).await?;
            println!("{}", serde_json::to_string_pretty(&result)?);
        }
    }
    Ok(())
}

fn run_options(args: RunArgs) -> RunOptions {
    RunOptions {
        manifest_uri: args.manifest_uri,
        deck_paths: [args.deck_a, args.deck_b],
        output_dir: args.output_dir,
        run_id: args
            .run_id
            .unwrap_or_else(|| format!("run-{}-{}", args.seed_start, args.seed_count)),
        seed_start: args.seed_start,
        seed_count: args.seed_count,
        action_budget_per_game: args.action_budget,
        checkpoint_every: args.checkpoint_every,
        max_trace_bytes: args.max_trace_bytes,
        resume: args.resume,
    }
}
