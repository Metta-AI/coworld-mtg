//! Export the shared schema registry without building the engine adapter.
fn main() -> Result<(), Box<dyn std::error::Error>> {
    let directory = std::path::PathBuf::from(
        std::env::args()
            .nth(1)
            .ok_or("usage: export_contracts OUTPUT_DIRECTORY")?,
    );
    std::fs::create_dir_all(&directory)?;
    for (name, contents) in loop_contract::contract_artifacts() {
        std::fs::write(directory.join(name), contents)?;
    }
    Ok(())
}
