use anyhow::{bail, Context, Result};
use flate2::read::MultiGzDecoder;
use serde::Serialize;
use serde_json::Value;
use sha2::{Digest, Sha256};
use std::fs;
use std::io::Read;
use std::path::{Path, PathBuf};

pub async fn read_resource(uri: &str) -> Result<Vec<u8>> {
    let display_uri = sanitized_resource_uri(uri);
    if uri.starts_with("http://") || uri.starts_with("https://") {
        let response = reqwest::get(uri)
            .await
            .with_context(|| format!("download {display_uri}"))?
            .error_for_status()
            .with_context(|| format!("download {display_uri}"))?;
        return Ok(response.bytes().await?.to_vec());
    }
    if let Some(path) = uri.strip_prefix("file://") {
        return fs::read(path).with_context(|| format!("read {path}"));
    }
    if uri.contains("://") {
        bail!(
            "unsupported URI scheme in {display_uri}; use a local/file path or an immutable HTTP URL"
        );
    }
    fs::read(uri).with_context(|| format!("read {uri}"))
}

pub fn sanitized_resource_uri(uri: &str) -> String {
    if let Ok(mut parsed) = reqwest::Url::parse(uri) {
        let _ = parsed.set_username("");
        let _ = parsed.set_password(None);
        parsed.set_query(None);
        parsed.set_fragment(None);
        parsed.to_string()
    } else {
        uri.to_owned()
    }
}

pub fn sha256(bytes: &[u8]) -> String {
    hex::encode(Sha256::digest(bytes))
}

pub fn verify_hash(label: &str, bytes: &[u8], expected: Option<&str>) -> Result<String> {
    let actual = sha256(bytes);
    if let Some(expected) = expected {
        if !actual.eq_ignore_ascii_case(expected) {
            bail!("{label} sha256 mismatch: expected {expected}, got {actual}");
        }
    }
    Ok(actual)
}

pub fn decoded_json_bytes(raw: &[u8]) -> Result<Vec<u8>> {
    if raw.starts_with(&[0x1f, 0x8b]) {
        let mut decoder = MultiGzDecoder::new(raw);
        let mut decoded = Vec::new();
        decoder.read_to_end(&mut decoded)?;
        Ok(decoded)
    } else {
        Ok(raw.to_vec())
    }
}

pub fn canonical_json<T: Serialize>(value: &T) -> Result<Vec<u8>> {
    let mut value = serde_json::to_value(value)?;
    canonicalize(&mut value);
    Ok(serde_json::to_vec(&value)?)
}

pub fn canonical_hash<T: Serialize>(value: &T) -> Result<String> {
    Ok(sha256(&canonical_json(value)?))
}

fn canonicalize(value: &mut Value) {
    match value {
        Value::Array(values) => values.iter_mut().for_each(canonicalize),
        Value::Object(map) => {
            let old = std::mem::take(map);
            let mut entries = old.into_iter().collect::<Vec<_>>();
            entries.sort_by(|a, b| a.0.cmp(&b.0));
            for (key, mut child) in entries {
                canonicalize(&mut child);
                map.insert(key, child);
            }
        }
        _ => {}
    }
}

pub fn write_json_atomic(path: &Path, value: &impl Serialize) -> Result<()> {
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent)?;
    }
    let temporary = path.with_extension("tmp");
    fs::write(&temporary, serde_json::to_vec_pretty(value)?)?;
    fs::rename(&temporary, path)?;
    Ok(())
}

pub fn resolve_relative_resource(manifest_uri: &str, stored_path: &str) -> String {
    if stored_path.starts_with("http://")
        || stored_path.starts_with("https://")
        || stored_path.starts_with("file://")
        || Path::new(stored_path).is_absolute()
    {
        return stored_path.to_owned();
    }
    if manifest_uri.starts_with("http://") || manifest_uri.starts_with("https://") {
        if let Ok(base) = reqwest::Url::parse(manifest_uri) {
            if let Ok(joined) = base.join(stored_path) {
                return joined.to_string();
            }
        }
    }
    let manifest_path = manifest_uri.strip_prefix("file://").unwrap_or(manifest_uri);
    PathBuf::from(manifest_path)
        .parent()
        .unwrap_or_else(|| Path::new("."))
        .join(stored_path)
        .to_string_lossy()
        .into_owned()
}

#[cfg(test)]
mod tests {
    use super::sanitized_resource_uri;

    #[test]
    fn strips_credentials_from_persisted_remote_uris() {
        let value = sanitized_resource_uri(
            "https://worker:secret@example.com/bulk/cards.json?signature=private#fragment",
        );
        assert_eq!(value, "https://example.com/bulk/cards.json");
    }
}
