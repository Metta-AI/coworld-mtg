use anyhow::{anyhow, Result};
use clap::Parser;

#[derive(Parser)]
struct Args {
    #[arg(long)]
    url: Option<String>,
}

const WORKER_STACK_SIZE: usize = 4 * 1024 * 1024;

fn main() -> Result<()> {
    tokio::runtime::Builder::new_multi_thread()
        .thread_stack_size(WORKER_STACK_SIZE)
        .enable_all()
        .build()?
        .block_on(async {
            let args = Args::parse();
            let url = args
                .url
                .or_else(|| std::env::var("COWORLD_PLAYER_WS_URL").ok())
                .ok_or_else(|| anyhow!("--url or COWORLD_PLAYER_WS_URL is required"))?;
            goldfish::run_url(&url).await?;
            Ok(())
        })
}
