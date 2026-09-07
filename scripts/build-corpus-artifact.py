#!/usr/bin/env python3
"""Build a deterministic private corpus after explicit native card-data validation."""
from __future__ import annotations

import argparse
import base64
import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
import tarfile
import tempfile

SCHEMA = "coworld-mtg-corpus-v1"
PHASE_REVISION = "54227f4527a0b45b01eb3f819d262ee49b665810"
CORPUS_FILES = (
    "phase-card-data.json",
    "decks/fractal_convergence.json",
    "decks/lorehold_excavation.json",
)
VALIDATION_TIMEOUT_SECONDS = 60
ATTESTATION = (
    "The caller attests that the supplied validator was built from the declared Phase revision. "
    "Its byte hash identifies the executable; it does not independently prove its source or build."
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_identity(data: bytes) -> dict:
    return {"bytes": len(data), "sha256": sha256(data)}


class ValidationFailure(ValueError):
    def __init__(self, reason, receipt, stdout, stderr):
        super().__init__(reason)
        self.receipt, self.stdout, self.stderr = receipt, stdout, stderr


def validate_snapshot(payload: bytes, validator: Path, revision: str, directory: Path):
    validator = validator.resolve(strict=True)
    binary_hash = sha256(validator.read_bytes())
    input_path = directory / "phase-card-data.json"
    input_path.write_bytes(payload)
    reason = None
    try:
        result = subprocess.run([str(validator), "phase-card-data.json"], cwd=directory,
                                capture_output=True, timeout=VALIDATION_TIMEOUT_SECONDS)
        exit_code, stdout, stderr = result.returncode, result.stdout, result.stderr
        if exit_code:
            reason = "native validator rejected the staged card data"
    except subprocess.TimeoutExpired as error:
        exit_code, stdout, stderr = None, error.stdout or b"", error.stderr or b""
        reason = "native validator exceeded its deadline"
    except OSError:
        exit_code, stdout, stderr = None, b"", b""
        reason = "native validator could not be executed"
    try:
        input_after = sha256(input_path.read_bytes()) if not input_path.is_symlink() and input_path.is_file() else None
        binary_after = sha256(validator.read_bytes())
    except OSError:
        input_after, binary_after = None, None
    receipt = {
        "schema": "coworld-mtg-corpus-validation-v1",
        "validator_sha256": binary_hash,
        "declared_phase_revision": revision,
        "source_attribution": ATTESTATION,
        "arguments": ["phase-card-data.json"],
        "working_directory": "isolated directory containing the exact input snapshot",
        "input": {"path": "phase-card-data.json", **file_identity(payload)},
        "input_sha256_after": input_after,
        "validator_sha256_after": binary_after,
        "exit_code": exit_code,
        "stdout": {"path": "validation/stdout.txt", **file_identity(stdout)},
        "stderr": {"path": "validation/stderr.txt", **file_identity(stderr)},
        "scope": "Successful exit of the supplied native card-data validator on these exact bytes; not gameplay conformance.",
    }
    if input_after != sha256(payload):
        reason = "native validator changed or removed the staged input"
    if binary_after != binary_hash:
        reason = "validator executable changed during validation"
    if reason:
        receipt["status"] = "rejected"
        raise ValidationFailure(reason, receipt, stdout, stderr)
    receipt["status"] = "passed"
    return receipt, stdout, stderr


def build_corpus(source: Path, output: Path, validator: Path, validator_phase_revision: str):
    source, output = source.resolve(), output.absolute()
    if output.exists() or output.is_symlink():
        raise ValueError("refusing to overwrite an existing output")
    if source == output or source in output.resolve().parents:
        raise ValueError("output must be outside the source corpus")
    if not re.fullmatch("[0-9a-f]{40}", validator_phase_revision) or validator_phase_revision != PHASE_REVISION:
        raise ValueError("validator Phase revision must equal the builder's pinned PHASE_REVISION")
    # Capture all original payloads before validation. Packaging uses these exact
    # bytes even if an external process subsequently changes the source directory.
    payloads = {name: (source / name).read_bytes() for name in CORPUS_FILES}
    phase_cards = json.loads(payloads["phase-card-data.json"])
    if not isinstance(phase_cards, dict) or not phase_cards:
        raise ValueError("card data must be a nonempty card-export object")
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".corpus-build-", dir=output.parent) as temporary:
        work = Path(temporary)
        validation_dir = work / "validate"
        validation_dir.mkdir()
        receipt, stdout, stderr = validate_snapshot(
            payloads["phase-card-data.json"], validator, validator_phase_revision, validation_dir)
        payloads["validation/stdout.txt"] = stdout
        payloads["validation/stderr.txt"] = stderr
        manifest = {
            "schema": SCHEMA, "phase_revision": PHASE_REVISION, "card_count": len(phase_cards),
            "files": {name: file_identity(data) for name, data in sorted(payloads.items())},
            "validation": receipt,
        }
        payloads["manifest.json"] = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode()
        tar_path = work / "corpus.tar"
        with tarfile.open(tar_path, "w", format=tarfile.USTAR_FORMAT) as archive:
            for name, data in sorted(payloads.items()):
                info = tarfile.TarInfo(name)
                info.size, info.mode, info.mtime = len(data), 0o644, 0
                info.uid = info.gid = 0
                info.uname = info.gname = ""
                archive.addfile(info, io.BytesIO(data))
        compressed = work / "corpus.tar.zst"
        subprocess.run(["zstd", "-q", "-3", str(tar_path), "-o", str(compressed)], check=True)
        archive_identity = file_identity(compressed.read_bytes())
        with compressed.open("rb") as stream:
            os.fsync(stream.fileno())
        # Atomic, create-only publication on the same filesystem. Neither native
        # rejection nor failed compression can expose a partial final archive.
        os.link(compressed, output)
        directory_fd = os.open(output.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    return {**archive_identity, "validation": receipt}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path, help="new archive path outside the source directory")
    parser.add_argument("--validator", type=Path, required=True, help="explicit native card-data-validate executable")
    parser.add_argument("--validator-phase-revision", required=True,
                        help="caller-attested build revision; must match the builder's Phase pin")
    args = parser.parse_args()
    try:
        result = build_corpus(args.source, args.output, args.validator, args.validator_phase_revision)
    except ValidationFailure as error:
        # Preserve exact failed diagnostic bytes without creating a corpus archive.
        print(json.dumps({"status": "rejected", "validation": error.receipt,
                          "stdout_base64": base64.b64encode(error.stdout).decode("ascii"),
                          "stderr_base64": base64.b64encode(error.stderr).decode("ascii")}, sort_keys=True))
        parser.exit(1, f"Corpus validation failed: {error}\n")
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        parser.exit(1, f"Corpus packaging failed: {error}\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
