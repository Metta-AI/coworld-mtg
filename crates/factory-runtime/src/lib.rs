//! Read-only replay serving and portable evidence export, independent of any target engine.
use axum::body::Body;
use axum::extract::{Path as RoutePath, Request, State};
use axum::http::{header, HeaderValue, Method, StatusCode};
use axum::middleware::{self, Next};
use axum::response::{IntoResponse, Redirect, Response};
use axum::routing::get;
use axum::{Json, Router};
use loop_contract::{
    ContentHash, FactoryReplay, FactoryRunStatus, FactoryVersion, ProgramTarget, ReplayRecording,
};
use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;
use std::fs;
use std::io::Write;
use std::net::SocketAddr;
use std::path::{Component, Path, PathBuf};

#[derive(Debug, thiserror::Error)]
pub enum Error {
    #[error("{0}")]
    Invalid(String),
    #[error("{0}")]
    Io(#[from] std::io::Error),
    #[error("{0}")]
    Json(#[from] serde_json::Error),
}
pub type Result<T> = std::result::Result<T, Error>;

#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ReplayBundle {
    pub replay: FactoryReplay,
    /// Artifact strings are exact UTF-8 file contents, not reserialized JSON values.
    pub artifact_contents: BTreeMap<ContentHash, String>,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct RunSummary {
    pub run_id: String,
    pub title: String,
    pub status: FactoryRunStatus,
    pub recording: ReplayRecording,
}
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct RunList {
    pub runs: Vec<RunSummary>,
}

pub fn new_run(run_id: String, title: String, target: ProgramTarget) -> Result<FactoryReplay> {
    validate_run_id(&run_id)?;
    let replay = FactoryReplay {
        version: FactoryVersion::V1,
        run_id,
        title,
        target,
        recording: ReplayRecording::Live,
        status: FactoryRunStatus::Running,
        stages: loop_contract::factory_stages(),
        artifacts: BTreeMap::new(),
        events: vec![],
    };
    replay.validate().map_err(Error::Invalid)?;
    Ok(replay)
}

/// Write a new output, refusing to replace an existing replay or bundle.
pub fn write_json_new(path: &Path, value: &impl Serialize) -> Result<()> {
    let bytes = serde_json::to_vec_pretty(value)?;
    let mut file = fs::OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(path)?;
    file.write_all(&bytes)?;
    file.write_all(b"\n")?;
    file.sync_all()?;
    Ok(())
}

pub fn validate_run_id(id: &str) -> Result<()> {
    if id.is_empty()
        || id == "."
        || id == ".."
        || !id
            .bytes()
            .all(|c| c.is_ascii_alphanumeric() || b"-_.".contains(&c))
    {
        return Err(Error::Invalid(
            "run ID must be a single portable directory name".into(),
        ));
    }
    Ok(())
}

fn directory(path: &Path) -> Result<PathBuf> {
    let meta = fs::symlink_metadata(path)?;
    if meta.file_type().is_symlink() || !meta.is_dir() {
        return Err(Error::Invalid(
            "replay and viewer roots must be real directories".into(),
        ));
    }
    Ok(fs::canonicalize(path)?)
}

/// Check every component before opening a local file. Request paths cannot escape
/// their configured root, traverse a symlink, or address a device/directory.
fn safe_file(root: &Path, relative: &Path) -> Result<PathBuf> {
    let mut resolved = root.to_path_buf();
    if relative.as_os_str().is_empty() {
        return Err(Error::Invalid("empty file path".into()));
    }
    for component in relative.components() {
        let Component::Normal(name) = component else {
            return Err(Error::Invalid(
                "file paths must stay within their configured root".into(),
            ));
        };
        resolved.push(name);
        if fs::symlink_metadata(&resolved)?.file_type().is_symlink() {
            return Err(Error::Invalid(
                "symlinked replay or viewer files are not served".into(),
            ));
        }
    }
    if !fs::metadata(&resolved)?.is_file() || !fs::canonicalize(&resolved)?.starts_with(root) {
        return Err(Error::Invalid(
            "requested path is not a regular file within its root".into(),
        ));
    }
    Ok(resolved)
}

fn read_manifest(root: &Path) -> Result<FactoryReplay> {
    let replay: FactoryReplay =
        serde_json::from_slice(&fs::read(safe_file(root, Path::new("replay.json"))?)?)?;
    replay.validate().map_err(Error::Invalid)?;
    Ok(replay)
}

fn run_directory(root: &Path, id: &str) -> Result<PathBuf> {
    validate_run_id(id)?;
    let path = directory(&root.join(id))?;
    if !path.starts_with(root) {
        return Err(Error::Invalid(
            "run directory escaped its configured root".into(),
        ));
    }
    Ok(path)
}

fn load_manifest(root: &Path, id: &str) -> Result<(PathBuf, FactoryReplay)> {
    let run = run_directory(root, id)?;
    let replay = read_manifest(&run)?;
    if replay.run_id != id {
        return Err(Error::Invalid(
            "URL run ID differs from the manifest run ID".into(),
        ));
    }
    Ok((run, replay))
}

fn read_artifact(root: &Path, replay: &FactoryReplay, id: &ContentHash) -> Result<Vec<u8>> {
    let descriptor = replay
        .artifacts
        .get(id)
        .ok_or_else(|| Error::Invalid("artifact is not listed in this replay".into()))?;
    let bytes = fs::read(safe_file(root, Path::new(&descriptor.path))?)?;
    replay.verify_artifact(id, &bytes).map_err(Error::Invalid)?;
    Ok(bytes)
}

fn collect_artifacts(
    root: &Path,
    replay: &FactoryReplay,
) -> Result<BTreeMap<ContentHash, Vec<u8>>> {
    replay
        .artifacts
        .keys()
        .map(|id| Ok((id.clone(), read_artifact(root, replay, id)?)))
        .collect()
}

pub fn validate_bundle(bundle: &ReplayBundle) -> Result<()> {
    if bundle.artifact_contents.len() != bundle.replay.artifacts.len() {
        return Err(Error::Invalid(
            "bundle must contain exactly the manifest's artifacts".into(),
        ));
    }
    let contents = bundle
        .artifact_contents
        .iter()
        .map(|(id, value)| (id.clone(), value.as_bytes().to_vec()))
        .collect();
    bundle
        .replay
        .validate_artifacts(&contents)
        .map_err(Error::Invalid)
}

/// Input may be a run directory, replay.json, or a portable bundle JSON file.
pub fn verify(input: &Path) -> Result<FactoryReplay> {
    if fs::symlink_metadata(input)?.file_type().is_symlink() {
        return Err(Error::Invalid(
            "symlinked replay inputs are not read".into(),
        ));
    }
    if input.is_dir() {
        let root = directory(input)?;
        let replay = read_manifest(&root)?;
        let contents = collect_artifacts(&root, &replay)?;
        replay
            .validate_artifacts(&contents)
            .map_err(Error::Invalid)?;
        return Ok(replay);
    }
    let parent = input
        .parent()
        .filter(|p| !p.as_os_str().is_empty())
        .unwrap_or(Path::new("."));
    let root = directory(parent)?;
    let name = input
        .file_name()
        .ok_or_else(|| Error::Invalid("input file name is missing".into()))?;
    let bytes = fs::read(safe_file(&root, Path::new(name))?)?;
    let value: serde_json::Value = serde_json::from_slice(&bytes)?;
    if value.get("replay").is_some() {
        let bundle: ReplayBundle = serde_json::from_value(value)?;
        validate_bundle(&bundle)?;
        Ok(bundle.replay)
    } else {
        let replay: FactoryReplay = serde_json::from_value(value)?;
        replay.validate().map_err(Error::Invalid)?;
        let contents = collect_artifacts(&root, &replay)?;
        replay
            .validate_artifacts(&contents)
            .map_err(Error::Invalid)?;
        Ok(replay)
    }
}

pub fn export_bundle(input: &Path) -> Result<ReplayBundle> {
    let replay = verify(input)?;
    if input.is_file() {
        let value: serde_json::Value = serde_json::from_slice(&fs::read(input)?)?;
        if value.get("replay").is_some() {
            let bundle: ReplayBundle = serde_json::from_value(value)?;
            validate_bundle(&bundle)?;
            return Ok(bundle);
        }
    }
    let root = if input.is_dir() {
        directory(input)?
    } else {
        directory(
            input
                .parent()
                .filter(|p| !p.as_os_str().is_empty())
                .unwrap_or(Path::new(".")),
        )?
    };
    let contents = collect_artifacts(&root, &replay)?;
    let mut artifact_contents = BTreeMap::new();
    for (id, bytes) in contents {
        let text = String::from_utf8(bytes).map_err(|_| {
            Error::Invalid(format!(
                "artifact {id} is binary; portable string bundles require UTF-8"
            ))
        })?;
        artifact_contents.insert(id, text);
    }
    Ok(ReplayBundle {
        replay,
        artifact_contents,
    })
}

#[derive(Clone)]
struct ServerState {
    root: PathBuf,
    web_dist: PathBuf,
}

/// Construct the same GET-only router used by `serve`, also usable by embedders/tests.
pub fn router(root: &Path, web_dist: &Path) -> Result<Router> {
    let state = ServerState {
        root: directory(root)?,
        web_dist: directory(web_dist)?,
    };
    Ok(Router::new()
        .route(
            "/",
            get(|| async { Redirect::temporary("/client/factory.html") }),
        )
        .route("/factory-api/runs", get(list_runs))
        .route("/factory-api/runs/{id}/replay.json", get(manifest))
        .route("/factory-api/runs/{id}/artifacts/{hash}", get(artifact))
        .route(
            "/client",
            get(|| async { Redirect::temporary("/client/factory.html") }),
        )
        .route(
            "/client/",
            get(|| async { Redirect::temporary("/client/factory.html") }),
        )
        .route("/client/{*path}", get(client_asset))
        .with_state(state)
        .layer(middleware::from_fn(only_get)))
}

pub async fn serve(root: &Path, web_dist: &Path, bind: SocketAddr) -> Result<()> {
    let app = router(root, web_dist)?;
    let listener = tokio::net::TcpListener::bind(bind).await?;
    axum::serve(listener, app)
        .with_graceful_shutdown(async {
            let _ = tokio::signal::ctrl_c().await;
        })
        .await?;
    Ok(())
}

async fn only_get(request: Request, next: Next) -> Response {
    if request.method() != Method::GET {
        return (
            StatusCode::METHOD_NOT_ALLOWED,
            [(header::ALLOW, "GET")],
            "Only GET is supported",
        )
            .into_response();
    }
    let mut response = next.run(request).await;
    response.headers_mut().insert(
        header::X_CONTENT_TYPE_OPTIONS,
        HeaderValue::from_static("nosniff"),
    );
    response
        .headers_mut()
        .insert(header::CACHE_CONTROL, HeaderValue::from_static("no-store"));
    response
}

impl IntoResponse for Error {
    fn into_response(self) -> Response {
        let (status, message) = match self {
            Self::Io(error) if error.kind() == std::io::ErrorKind::NotFound => (
                StatusCode::NOT_FOUND,
                "Replay or artifact file was not found".to_string(),
            ),
            Self::Io(_) => (
                StatusCode::INTERNAL_SERVER_ERROR,
                "Replay file could not be read".to_string(),
            ),
            Self::Json(error) => (
                StatusCode::UNPROCESSABLE_ENTITY,
                format!("Invalid replay JSON: {error}"),
            ),
            Self::Invalid(message) => (StatusCode::UNPROCESSABLE_ENTITY, message),
        };
        (status, Json(serde_json::json!({"error":message}))).into_response()
    }
}

async fn blocking<T: Send + 'static>(
    work: impl FnOnce() -> Result<T> + Send + 'static,
) -> Result<T> {
    tokio::task::spawn_blocking(work)
        .await
        .map_err(|_| Error::Invalid("replay file reader stopped unexpectedly".into()))?
}

async fn list_runs(State(state): State<ServerState>) -> Result<Json<RunList>> {
    blocking(move || {
        let mut runs = Vec::new();
        for entry in fs::read_dir(&state.root)? {
            let entry = entry?;
            if !entry.file_type()?.is_dir() {
                continue;
            }
            let Some(id) = entry.file_name().to_str().map(str::to_string) else {
                continue;
            };
            if validate_run_id(&id).is_err() || !entry.path().join("replay.json").try_exists()? {
                continue;
            }
            let (_, replay) = load_manifest(&state.root, &id)?;
            runs.push(RunSummary {
                run_id: replay.run_id,
                title: replay.title,
                status: replay.status,
                recording: replay.recording,
            });
        }
        runs.sort_by(|a, b| a.run_id.cmp(&b.run_id));
        Ok(Json(RunList { runs }))
    })
    .await
}

async fn manifest(
    State(state): State<ServerState>,
    RoutePath(id): RoutePath<String>,
) -> Result<Json<FactoryReplay>> {
    blocking(move || Ok(Json(load_manifest(&state.root, &id)?.1))).await
}

async fn artifact(
    State(state): State<ServerState>,
    RoutePath((id, hash)): RoutePath<(String, String)>,
) -> Result<Response> {
    blocking(move || {
        let hash = ContentHash::try_from(hash).map_err(Error::Invalid)?;
        let (run, replay) = load_manifest(&state.root, &id)?;
        let bytes = read_artifact(&run, &replay, &hash)?;
        let media_type = HeaderValue::from_str(&replay.artifacts[&hash].media_type)
            .map_err(|_| Error::Invalid("artifact media type is invalid".into()))?;
        Ok(([(header::CONTENT_TYPE, media_type)], Body::from(bytes)).into_response())
    })
    .await
}

async fn client_asset(
    State(state): State<ServerState>,
    RoutePath(path): RoutePath<String>,
) -> Result<Response> {
    blocking(move || {
        if path.contains('\\') {
            return Err(Error::Invalid("invalid viewer asset path".into()));
        }
        let file = safe_file(&state.web_dist, Path::new(&path))?;
        let media_type = match file.extension().and_then(|s| s.to_str()) {
            Some("html") => "text/html; charset=utf-8",
            Some("js" | "mjs") => "text/javascript; charset=utf-8",
            Some("css") => "text/css; charset=utf-8",
            Some("json" | "map") => "application/json",
            Some("svg") => "image/svg+xml",
            Some("png") => "image/png",
            Some("jpg" | "jpeg") => "image/jpeg",
            Some("gif") => "image/gif",
            Some("webp") => "image/webp",
            Some("ico") => "image/x-icon",
            Some("woff") => "font/woff",
            Some("woff2") => "font/woff2",
            Some("ttf") => "font/ttf",
            Some("wasm") => "application/wasm",
            _ => "application/octet-stream",
        };
        Ok(([(header::CONTENT_TYPE, media_type)], fs::read(file)?).into_response())
    })
    .await
}
