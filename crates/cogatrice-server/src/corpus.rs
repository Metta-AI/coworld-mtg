use anyhow::{anyhow, bail, Context, Result};
use phase_bridge::{CardSpec, DeckList, PhaseRuntime, PHASE_REVISION};
use serde::Deserialize;
use sha2::{Digest, Sha256};
use std::collections::BTreeMap;
use std::env;
use std::path::{Component, Path, PathBuf};

const CORPUS_SCHEMA: &str = "coworld-mtg-corpus-v1";

#[derive(Deserialize)]
struct CorpusManifest {
    schema: String,
    phase_revision: String,
    card_count: usize,
    files: BTreeMap<String, CorpusFile>,
}

#[derive(Deserialize)]
struct CorpusFile {
    bytes: usize,
    sha256: String,
}

#[derive(Deserialize)]
struct DeckFile {
    name: String,
    cards: Vec<DeckEntry>,
}

#[derive(Deserialize)]
struct DeckEntry {
    count: usize,
    spec: CardSpec,
}

pub struct Corpus {
    root: PathBuf,
    manifest: CorpusManifest,
}

impl Corpus {
    pub fn from_env() -> Result<Self> {
        let root = env::var("COGAME_CORPUS_DIR").context("COGAME_CORPUS_DIR is required")?;
        Self::load(root)
    }

    fn load(root: impl Into<PathBuf>) -> Result<Self> {
        let root = root.into();
        let manifest_path = root.join("manifest.json");
        let manifest: CorpusManifest = serde_json::from_slice(
            &std::fs::read(&manifest_path)
                .with_context(|| format!("failed to read {}", manifest_path.display()))?,
        )?;
        if manifest.schema != CORPUS_SCHEMA {
            bail!("unsupported corpus schema {}", manifest.schema);
        }
        if manifest.phase_revision != PHASE_REVISION {
            bail!(
                "corpus uses Phase {}, but phase-bridge pins {}",
                manifest.phase_revision,
                PHASE_REVISION
            );
        }
        for required in [
            "phase-card-data.json",
            "decks/lorehold_excavation.json",
            "decks/fractal_convergence.json",
        ] {
            if !manifest.files.contains_key(required) {
                bail!("corpus manifest has no {required}");
            }
        }
        for (name, expected) in &manifest.files {
            let relative = Path::new(name);
            if relative
                .components()
                .any(|component| !matches!(component, Component::Normal(_)))
            {
                bail!("invalid corpus path {name}");
            }
            let bytes = std::fs::read(root.join(relative))
                .with_context(|| format!("failed to read corpus file {name}"))?;
            if bytes.len() != expected.bytes {
                bail!(
                    "corpus file {name} has {} bytes, expected {}",
                    bytes.len(),
                    expected.bytes
                );
            }
            let actual = hex::encode(Sha256::digest(&bytes));
            if actual != expected.sha256 {
                bail!(
                    "corpus file {name} SHA-256 mismatch: expected {}, got {actual}",
                    expected.sha256
                );
            }
        }
        Ok(Self { root, manifest })
    }

    pub fn phase_runtime(&self) -> Result<PhaseRuntime> {
        let text = std::fs::read_to_string(self.root.join("phase-card-data.json"))?;
        let runtime = PhaseRuntime::from_card_data_json(&text)?;
        if runtime.card_count() != self.manifest.card_count {
            bail!(
                "corpus loaded {} cards, expected {}",
                runtime.card_count(),
                self.manifest.card_count
            );
        }
        Ok(runtime)
    }

    pub fn load_deck(&self, id: &str) -> Result<DeckList> {
        let file_name = match id {
            "lorehold_excavation" => "lorehold_excavation.json",
            "fractal_convergence" => "fractal_convergence.json",
            _ => return Err(anyhow!("unknown deck id {id}")),
        };
        let path = self.root.join("decks").join(file_name);
        let deck: DeckFile = serde_json::from_slice(&std::fs::read(&path)?)?;
        let cards = deck
            .cards
            .into_iter()
            .flat_map(|entry| std::iter::repeat_n(entry.spec, entry.count))
            .collect();
        Ok(DeckList {
            name: deck.name,
            cards,
        })
    }
}
