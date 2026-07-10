use anyhow::{Context, Result};
use std::path::{Path, PathBuf};

pub async fn read_to_string(uri: &str) -> Result<String> {
    if is_http(uri) {
        return Ok(reqwest::get(uri)
            .await
            .with_context(|| format!("GET {uri} failed"))?
            .error_for_status()
            .with_context(|| format!("GET {uri} returned an error status"))?
            .text()
            .await?);
    }
    tokio::fs::read_to_string(path_for_uri(uri))
        .await
        .with_context(|| format!("failed to read {uri}"))
}

pub async fn write_bytes(uri: &str, bytes: Vec<u8>) -> Result<()> {
    if is_http(uri) {
        reqwest::Client::new()
            .put(uri)
            .body(bytes)
            .send()
            .await
            .with_context(|| format!("PUT {uri} failed"))?
            .error_for_status()
            .with_context(|| format!("PUT {uri} returned an error status"))?;
        return Ok(());
    }
    let path = path_for_uri(uri);
    if let Some(parent) = path.parent() {
        if !parent.as_os_str().is_empty() {
            tokio::fs::create_dir_all(parent).await?;
        }
    }
    tokio::fs::write(&path, bytes)
        .await
        .with_context(|| format!("failed to write {}", path.display()))
}

pub async fn write_json<T: serde::Serialize>(uri: &str, value: &T) -> Result<()> {
    write_bytes(uri, serde_json::to_vec_pretty(value)?).await
}

pub async fn write_text(uri: &str, value: &str) -> Result<()> {
    write_bytes(uri, value.as_bytes().to_vec()).await
}

fn is_http(uri: &str) -> bool {
    uri.starts_with("http://") || uri.starts_with("https://")
}

fn path_for_uri(uri: &str) -> PathBuf {
    if let Some(rest) = uri.strip_prefix("file://") {
        return Path::new(rest).to_path_buf();
    }
    Path::new(uri).to_path_buf()
}
