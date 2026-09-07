use clap::{Parser, Subcommand};
use factory_runtime::{export_bundle, new_run, serve, verify, write_json_new};
use loop_contract::ProgramTarget;
use std::net::SocketAddr;
use std::path::PathBuf;

#[derive(Parser)]
#[command(about = "Serve, verify and export software-improvement replay files")]
struct Args {
    #[command(subcommand)]
    command: Command,
}

#[derive(Subcommand)]
enum Command {
    /// Serve existing replay runs and a built viewer with GET-only endpoints.
    Serve {
        #[arg(long)]
        root: PathBuf,
        #[arg(long)]
        web_dist: PathBuf,
        #[arg(long, default_value = "127.0.0.1:8030")]
        bind: SocketAddr,
    },
    /// Audit a run directory, replay.json, or portable bundle JSON.
    Verify { input: PathBuf },
    /// Export all verified UTF-8 artifacts into a portable JSON bundle.
    Export {
        input: PathBuf,
        #[arg(long)]
        output: PathBuf,
    },
    /// Create a running replay with the canonical stage topology and no events.
    Init {
        #[arg(long)]
        run_id: String,
        #[arg(long)]
        title: String,
        #[arg(long)]
        program: String,
        #[arg(long)]
        repository: String,
        #[arg(long)]
        baseline_revision: String,
        #[arg(long)]
        output: PathBuf,
    },
}

#[tokio::main(flavor = "current_thread")]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    match Args::parse().command {
        Command::Serve {
            root,
            web_dist,
            bind,
        } => {
            println!("Replay viewer: http://{bind}/client/factory.html");
            serve(&root, &web_dist, bind).await?;
        }
        Command::Verify { input } => {
            let replay = verify(&input)?;
            println!(
                "Verified {}: {} events and {} artifacts",
                replay.run_id,
                replay.events.len(),
                replay.artifacts.len()
            );
        }
        Command::Export { input, output } => {
            let bundle = export_bundle(&input)?;
            write_json_new(&output, &bundle)?;
            println!("Exported {} to {}", bundle.replay.run_id, output.display());
        }
        Command::Init {
            run_id,
            title,
            program,
            repository,
            baseline_revision,
            output,
        } => {
            let replay = new_run(
                run_id,
                title,
                ProgramTarget {
                    name: program,
                    repository,
                    baseline_revision,
                },
            )?;
            write_json_new(&output, &replay)?;
        }
    }
    Ok(())
}
