#[tokio::main]
async fn main() -> anyhow::Result<()> {
    cogatrice_server::run().await
}
