use axum::body::{to_bytes, Body};
use axum::http::{Request, StatusCode};
use factory_runtime::{
    export_bundle, new_run, router, validate_bundle, verify, write_json_new, ReplayBundle,
};
use loop_contract::{
    digest, ArtifactHashMode, FactoryArtifact, FactoryReplay, ProgramTarget, ReplayRecording,
};
use serde_json::json;
use std::collections::BTreeMap;
use std::fs;
use std::path::{Path, PathBuf};
use tempfile::TempDir;
use tower::ServiceExt;

struct Fixture {
    _temporary: TempDir,
    root: PathBuf,
    web: PathBuf,
    run: PathBuf,
    replay: FactoryReplay,
    artifact_id: String,
}
fn fixture() -> Fixture {
    let temporary = tempfile::tempdir().unwrap();
    let root = temporary.path().join("runs");
    let web = temporary.path().join("web");
    let run = root.join("test-import");
    fs::create_dir_all(run.join("artifacts")).unwrap();
    fs::create_dir_all(web.join("assets")).unwrap();
    fs::write(
        web.join("factory.html"),
        "<!doctype html><title>Fixture viewer</title>",
    )
    .unwrap();
    fs::write(web.join("assets/app.js"), "export const fixture = true;").unwrap();
    let mut replay = new_run(
        "test-import".into(),
        "Imported parser test".into(),
        ProgramTarget {
            name: "Fixture parser".into(),
            repository: "https://example.test/parser".into(),
            baseline_revision: "fixture-v1".into(),
        },
    )
    .unwrap();
    replay.recording = ReplayRecording::Imported {
        description: "Constructed runtime test fixture; no execution history is claimed".into(),
    };
    let content = json!({"text":"café","items":[2,1]});
    let id = digest(&content).unwrap();
    let path = format!("artifacts/{id}.json");
    fs::write(
        run.join(&path),
        serde_json::to_vec_pretty(&content).unwrap(),
    )
    .unwrap();
    replay.artifacts.insert(
        id.clone(),
        FactoryArtifact {
            path,
            media_type: "application/json".into(),
            hash_mode: ArtifactHashMode::CanonicalJson,
        },
    );
    write_json_new(&run.join("replay.json"), &replay).unwrap();
    Fixture {
        _temporary: temporary,
        root,
        web,
        run,
        replay,
        artifact_id: id.to_string(),
    }
}
fn save_replay(path: &Path, replay: &FactoryReplay) {
    fs::write(
        path.join("replay.json"),
        serde_json::to_vec_pretty(replay).unwrap(),
    )
    .unwrap();
}

#[test]
fn imported_manifest_and_portable_bundle_verify_without_an_engine() {
    let fixture = fixture();
    assert_eq!(verify(&fixture.run).unwrap(), fixture.replay);
    assert_eq!(
        verify(&fixture.run.join("replay.json")).unwrap(),
        fixture.replay
    );
    let bundle = export_bundle(&fixture.run).unwrap();
    validate_bundle(&bundle).unwrap();
    let path = fixture.root.join("portable.json");
    write_json_new(&path, &bundle).unwrap();
    assert_eq!(verify(&path).unwrap(), fixture.replay);
    assert_eq!(
        export_bundle(&path).unwrap().artifact_contents,
        bundle.artifact_contents
    );
    assert!(write_json_new(&path, &bundle).is_err());
}

#[test]
fn corrupt_missing_and_extra_bundle_artifacts_are_rejected() {
    let fixture = fixture();
    let bundle = export_bundle(&fixture.run).unwrap();
    let mut corrupt = bundle.clone();
    corrupt
        .artifact_contents
        .values_mut()
        .next()
        .unwrap()
        .push('x');
    assert!(validate_bundle(&corrupt).is_err());
    let mut missing = bundle.clone();
    missing.artifact_contents.clear();
    assert!(validate_bundle(&missing).is_err());
    let mut extra = bundle;
    extra
        .artifact_contents
        .insert(loop_contract::hash_bytes(b"unlisted"), "unlisted".into());
    assert!(validate_bundle(&extra).is_err());
    let descriptor = fixture.replay.artifacts.values().next().unwrap();
    fs::write(fixture.run.join(&descriptor.path), "{\"changed\":true}").unwrap();
    assert!(verify(&fixture.run).is_err());
    assert!(export_bundle(&fixture.run).is_err());
}

#[test]
fn binary_artifact_is_verifiable_but_string_bundle_export_is_explicitly_unsupported() {
    let mut fixture = fixture();
    let bytes = vec![0xff, 0xfe, 0];
    let id = loop_contract::hash_bytes(&bytes);
    let path = format!("artifacts/{id}.bin");
    fs::write(fixture.run.join(&path), &bytes).unwrap();
    fixture.replay.artifacts.insert(
        id,
        FactoryArtifact {
            path,
            media_type: "application/octet-stream".into(),
            hash_mode: ArtifactHashMode::Bytes,
        },
    );
    save_replay(&fixture.run, &fixture.replay);
    verify(&fixture.run).unwrap();
    assert!(export_bundle(&fixture.run)
        .unwrap_err()
        .to_string()
        .contains("binary"));
}

#[test]
fn manifest_traversal_and_invalid_run_names_are_rejected() {
    let mut fixture = fixture();
    fixture.replay.artifacts.values_mut().next().unwrap().path = "../secret.json".into();
    save_replay(&fixture.run, &fixture.replay);
    assert!(verify(&fixture.run).is_err());
    assert!(factory_runtime::validate_run_id("../outside").is_err());
    assert!(factory_runtime::validate_run_id("a/b").is_err());
    assert!(factory_runtime::validate_run_id("%2e%2e").is_err());
    assert!(factory_runtime::validate_run_id("ordinary-run_1.0").is_ok());
}

#[tokio::test]
async fn serves_recorded_metadata_verified_artifacts_and_viewer_assets() {
    let fixture = fixture();
    let app = router(&fixture.root, &fixture.web).unwrap();
    for (url, content_type) in [
        ("/factory-api/runs".to_string(), "application/json"),
        (
            "/factory-api/runs/test-import/replay.json".to_string(),
            "application/json",
        ),
        (
            format!(
                "/factory-api/runs/test-import/artifacts/{}",
                fixture.artifact_id
            ),
            "application/json",
        ),
        (
            "/client/factory.html".to_string(),
            "text/html; charset=utf-8",
        ),
        (
            "/client/assets/app.js".to_string(),
            "text/javascript; charset=utf-8",
        ),
    ] {
        let response = app
            .clone()
            .oneshot(Request::builder().uri(&url).body(Body::empty()).unwrap())
            .await
            .unwrap();
        assert_eq!(response.status(), StatusCode::OK, "{url}");
        assert_eq!(response.headers()["content-type"], content_type);
        assert_eq!(response.headers()["x-content-type-options"], "nosniff");
        let body = to_bytes(response.into_body(), usize::MAX).await.unwrap();
        if url == "/factory-api/runs" {
            let list: factory_runtime::RunList = serde_json::from_slice(&body).unwrap();
            assert_eq!(list.runs[0].run_id, "test-import");
            assert!(matches!(
                list.runs[0].recording,
                ReplayRecording::Imported { .. }
            ));
        }
    }
    for method in ["POST", "PUT", "DELETE", "HEAD"] {
        let response = app
            .clone()
            .oneshot(
                Request::builder()
                    .method(method)
                    .uri("/factory-api/runs")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();
        assert_eq!(response.status(), StatusCode::METHOD_NOT_ALLOWED);
        assert_eq!(response.headers()["allow"], "GET");
    }
}

#[tokio::test]
async fn server_rejects_url_identity_mismatch_corruption_and_traversal() {
    let mut fixture = fixture();
    let app = router(&fixture.root, &fixture.web).unwrap();
    let descriptor = fixture.replay.artifacts.values().next().unwrap();
    fs::write(fixture.run.join(&descriptor.path), "corrupt").unwrap();
    let response = app
        .clone()
        .oneshot(
            Request::builder()
                .uri(format!(
                    "/factory-api/runs/test-import/artifacts/{}",
                    fixture.artifact_id
                ))
                .body(Body::empty())
                .unwrap(),
        )
        .await
        .unwrap();
    assert_eq!(response.status(), StatusCode::UNPROCESSABLE_ENTITY);
    fixture.replay.run_id = "different-run".into();
    save_replay(&fixture.run, &fixture.replay);
    let response = app
        .clone()
        .oneshot(
            Request::builder()
                .uri("/factory-api/runs/test-import/replay.json")
                .body(Body::empty())
                .unwrap(),
        )
        .await
        .unwrap();
    assert_eq!(response.status(), StatusCode::UNPROCESSABLE_ENTITY);
    for path in [
        "/client/../runs/test-import/replay.json",
        "/client/%2e%2e/runs/test-import/replay.json",
        "/factory-api/runs/%2e%2e/replay.json",
    ] {
        let response = app
            .clone()
            .oneshot(Request::builder().uri(path).body(Body::empty()).unwrap())
            .await
            .unwrap();
        assert_ne!(response.status(), StatusCode::OK, "{path}");
    }
}

#[cfg(unix)]
#[tokio::test]
async fn symlinked_artifact_parent_run_and_viewer_files_are_not_served() {
    use std::os::unix::fs::symlink;
    let fixture = fixture();
    let descriptor = fixture.replay.artifacts.values().next().unwrap();
    let original = fixture.run.join(&descriptor.path);
    let external = fixture.root.join("external.json");
    fs::rename(&original, &external).unwrap();
    symlink(&external, &original).unwrap();
    assert!(verify(&fixture.run).is_err());
    let app = router(&fixture.root, &fixture.web).unwrap();
    symlink(&external, fixture.web.join("linked.json")).unwrap();
    symlink(&fixture.run, fixture.root.join("linked-run")).unwrap();
    for path in [
        format!(
            "/factory-api/runs/test-import/artifacts/{}",
            fixture.artifact_id
        ),
        "/factory-api/runs/linked-run/replay.json".into(),
        "/client/linked.json".into(),
    ] {
        let response = app
            .clone()
            .oneshot(Request::builder().uri(&path).body(Body::empty()).unwrap())
            .await
            .unwrap();
        assert_eq!(
            response.status(),
            StatusCode::UNPROCESSABLE_ENTITY,
            "{path}"
        );
    }
    fs::remove_file(&original).unwrap();
    fs::remove_dir(fixture.run.join("artifacts")).unwrap();
    symlink(&fixture.root, fixture.run.join("artifacts")).unwrap();
    assert!(verify(&fixture.run).is_err());
}

#[test]
fn bundles_do_not_allow_unknown_top_level_fields() {
    let invalid = json!({"replay":{},"artifact_contents":{},"acceptance":"invented"});
    assert!(serde_json::from_value::<ReplayBundle>(invalid).is_err());
    let fixture = fixture();
    let missing = ReplayBundle {
        replay: fixture.replay,
        artifact_contents: BTreeMap::new(),
    };
    assert!(validate_bundle(&missing).is_err());
}
