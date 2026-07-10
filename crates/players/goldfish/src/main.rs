use anyhow::{anyhow, Result};
use clap::Parser;

#[derive(Parser)]
struct Args {
    #[arg(long)]
    url: Option<String>,
}

#[tokio::main]
async fn main() -> Result<()> {
    let args = Args::parse();
    let url = args
        .url
        .or_else(|| std::env::var("COWORLD_PLAYER_WS_URL").ok())
        .ok_or_else(|| anyhow!("--url or COWORLD_PLAYER_WS_URL is required"))?;
    goldfish::run_url(&url).await?;
    Ok(())
}
