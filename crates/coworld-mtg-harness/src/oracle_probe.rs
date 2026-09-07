//! Expectation-free JSONL adapter for inspecting a Scryfall snapshot with Phase.
use anyhow::{bail, Context, Result};
use phase_bridge::inspect_oracle_card;
use serde_json::Value;
use std::fs::{File, OpenOptions};
use std::io::{BufRead, BufReader, BufWriter, Read, Write};
use std::path::Path;

pub fn inspect_file(input: &Path, output: &Path) -> Result<()> {
    let source = File::open(input).context("open Oracle probe input")?;
    let destination = OpenOptions::new()
        .create_new(true)
        .write(true)
        .open(output)
        .context("Oracle probe output must be new")?;
    let mut writer = BufWriter::new(destination);
    let mut reader = BufReader::new(source);
    let mut line = Vec::new();
    let mut index = 0;
    loop {
        line.clear();
        let bytes = Read::by_ref(&mut reader)
            .take(2 * 1024 * 1024 + 1)
            .read_until(b'\n', &mut line)?;
        if bytes == 0 {
            break;
        }
        index += 1;
        if bytes > 2 * 1024 * 1024 {
            bail!("record {index} exceeds the two-megabyte input limit");
        }
        let record: Value =
            serde_json::from_slice(&line).with_context(|| format!("invalid record {index}"))?;
        let result = std::thread::Builder::new()
            .name(format!("oracle-inspection-{index}"))
            .stack_size(32 * 1024 * 1024)
            .spawn(move || inspect_oracle_card(record))?
            .join()
            .map_err(|_| anyhow::anyhow!("Phase parser panicked on record {index}"))?;
        serde_json::to_writer(&mut writer, &result)?;
        writer.write_all(b"\n")?;
        writer.flush()?;
    }
    Ok(())
}
