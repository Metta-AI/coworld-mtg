use crate::ReplayState;
use axum::extract::{Path as AxumPath, Query, State};
use axum::http::{header, StatusCode};
use axum::response::{Html, IntoResponse, Response};
use std::collections::BTreeMap;
use std::path::{Component, Path, PathBuf};

pub(crate) async fn replay_client_asset(State(state): State<ReplayState>) -> Response {
    let has_phase_snapshots = state
        .replay
        .games
        .first()
        .and_then(|game| game.steps.first())
        .is_some_and(|step| step.state.phase_client.is_some());
    let filename = if has_phase_snapshots {
        "replay.html"
    } else {
        "legacy-replay.html"
    };
    let dist = web_dist_dir();
    if !dist.is_dir() {
        return client_placeholder(BTreeMap::new()).into_response();
    }
    serve_file(dist.join(filename)).await
}

pub(crate) async fn client_asset(
    AxumPath(path): AxumPath<String>,
    Query(params): Query<BTreeMap<String, String>>,
) -> Response {
    let dist = web_dist_dir();
    if dist.is_dir() {
        return match resolve_client_asset(&dist, &path) {
            Some(file) => serve_file(file).await,
            None => (StatusCode::NOT_FOUND, "not found").into_response(),
        };
    }
    if matches!(path.as_str(), "player" | "global" | "replay") {
        return client_placeholder(params).into_response();
    }
    (StatusCode::NOT_FOUND, "not found").into_response()
}

async fn serve_file(file: PathBuf) -> Response {
    match tokio::fs::read(&file).await {
        Ok(bytes) => ([(header::CONTENT_TYPE, content_type(&file))], bytes).into_response(),
        Err(error) if error.kind() == std::io::ErrorKind::NotFound => {
            (StatusCode::NOT_FOUND, "not found").into_response()
        }
        Err(_) => (StatusCode::INTERNAL_SERVER_ERROR, "failed to read asset").into_response(),
    }
}

fn client_placeholder(params: BTreeMap<String, String>) -> Html<String> {
    let body = serde_json::to_string_pretty(&params).unwrap_or_else(|_| "{}".to_owned());
    Html(format!(
        "<!doctype html><html><body><pre>{}</pre></body></html>",
        escape_html(&body)
    ))
}

fn web_dist_dir() -> PathBuf {
    std::env::var_os("COGAME_WEB_DIST")
        .map(PathBuf::from)
        .unwrap_or_else(|| PathBuf::from("web/dist"))
}

fn resolve_client_asset(dist: &Path, path: &str) -> Option<PathBuf> {
    let relative = match path {
        "player" | "global" | "replay" => PathBuf::from(format!("{path}.html")),
        _ => safe_relative_path(path)?,
    };
    Some(dist.join(relative))
}

fn safe_relative_path(path: &str) -> Option<PathBuf> {
    let mut out = PathBuf::new();
    for component in Path::new(path).components() {
        match component {
            Component::Normal(part) => out.push(part),
            _ => return None,
        }
    }
    (!out.as_os_str().is_empty()).then_some(out)
}

fn content_type(path: &Path) -> &'static str {
    match path.extension().and_then(|extension| extension.to_str()) {
        Some("html") => "text/html; charset=utf-8",
        Some("js") => "text/javascript; charset=utf-8",
        Some("css") => "text/css; charset=utf-8",
        Some("json") | Some("map") => "application/json; charset=utf-8",
        Some("svg") => "image/svg+xml",
        Some("png") => "image/png",
        Some("ico") => "image/x-icon",
        _ => "application/octet-stream",
    }
}

fn escape_html(text: &str) -> String {
    text.replace('&', "&amp;")
        .replace('<', "&lt;")
        .replace('>', "&gt;")
        .replace('"', "&quot;")
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn asset_paths_cannot_escape_the_distribution_directory() {
        assert_eq!(
            safe_relative_path("assets/app.js"),
            Some("assets/app.js".into())
        );
        assert_eq!(safe_relative_path("../secret"), None);
        assert_eq!(safe_relative_path("/absolute"), None);
        assert_eq!(safe_relative_path(""), None);
    }
}
