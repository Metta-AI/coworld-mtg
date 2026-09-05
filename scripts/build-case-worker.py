#!/usr/bin/env python3
"""Preserve a worker and typed build provenance without changing the production pin."""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ROOT_FILES = ('Cargo.toml', 'Cargo.lock', 'rust-toolchain.toml')


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def source_snapshot(root):
    paths = [root / name for name in ROOT_FILES] + sorted((root / 'crates').rglob('*'))
    return {str(path.relative_to(root)): sha(path.read_bytes()) for path in paths
            if path.is_file() and 'target' not in path.relative_to(root).parts}


def copy_sources(source, destination):
    destination.mkdir()
    for name in ROOT_FILES:
        shutil.copy2(source / name, destination / name)
    shutil.copytree(source / 'crates', destination / 'crates')


def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--phase-checkout', type=Path)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=False)
    builder = sha(Path(__file__).read_bytes())
    harness = source_snapshot(ROOT)
    build = output / 'source'
    copy_sources(ROOT, build)
    shutil.copy2(build / 'Cargo.lock', build / 'Cargo.lock.input')
    command = [str(ROOT / 'scripts/cargo.sh'), 'build', '--manifest-path', str(build / 'Cargo.toml'),
               '--package', 'coworld-mtg-harness', '--target-dir', str(ROOT / 'target'),
               '--message-format=json-render-diagnostics']
    pin = json.loads((ROOT / 'phase-source.json').read_text())
    phase = {'kind': 'pinned', **pin}
    phase_files = None
    if args.phase_checkout:
        checkout = args.phase_checkout.resolve()
        phase_files = source_snapshot(checkout)
        copy_sources(checkout, output / 'phase-source')
        dirty = git(checkout, 'diff', '--binary', '--full-index', 'HEAD', '--', 'crates', *ROOT_FILES)
        patch = git(checkout, 'diff', '--binary', '--full-index', pin['revision'], '--', 'crates', *ROOT_FILES)
        (output / 'phase.patch').write_bytes(patch)
        (output / 'phase-dirty.patch').write_bytes(dirty)
        phase = {'kind': 'checkout', 'repository': pin['repository'], 'checkout': str(checkout),
                 'base_revision': pin['revision'], 'revision': git(checkout, 'rev-parse', 'HEAD').decode().strip(),
                 'source_files': phase_files, 'dirty_patch_sha256': sha(dirty), 'patch_sha256': sha(patch),
                 'worktree_clean': not git(checkout, 'status', '--porcelain', '--untracked-files=normal').strip()}
        command += ['--config', 'patch."https://github.com/nishu-builder/phase.git".engine.path=' + json.dumps(str(checkout / 'crates/engine'))]
    else:
        command += ['--locked']
    environment = dict(os.environ)
    environment['CARGO_NET_OFFLINE'] = 'true'
    with (output / 'cargo-messages.jsonl').open('w') as messages:
        subprocess.run(command, cwd=build, env=environment, stdout=messages, check=True)
    if sha(Path(__file__).read_bytes()) != builder or source_snapshot(ROOT) != harness or (phase_files is not None and source_snapshot(args.phase_checkout.resolve()) != phase_files):
        raise RuntimeError('source changed during compilation; do not certify this build')
    artifacts = [json.loads(line) for line in (output / 'cargo-messages.jsonl').read_text().splitlines()]
    executables = [item['executable'] for item in artifacts
                   if item.get('reason') == 'compiler-artifact'
                   and item.get('target', {}).get('name') == 'coworld-mtg-harness'
                   and 'bin' in item.get('target', {}).get('kind', []) and item.get('executable')]
    if len(executables) != 1:
        raise RuntimeError('Cargo did not identify exactly one harness executable')
    shutil.copy2(executables[0], output / 'worker')
    channel = (build / 'rust-toolchain.toml').read_text().split('channel = "')[1].split('"')[0]
    record = {'binary_sha256': sha((output / 'worker').read_bytes()),
              'harness_revision': git(ROOT, 'rev-parse', 'HEAD').decode().strip(),
              'harness_source_files': harness, 'phase': phase,
              'cargo_lock_sha256': sha((build / 'Cargo.lock').read_bytes()), 'command': command,
              'builder_sha256': builder,
              'build_environment': {key: environment[key] for key in
                                    ('RUSTFLAGS', 'CARGO_ENCODED_RUSTFLAGS', 'CARGO_BUILD_TARGET') if key in environment},
              'compiler': subprocess.check_output(['rustup', 'run', channel, 'rustc', '-Vv'],
                                                  cwd=build, env=environment, text=True).strip()}
    (output / 'build.json').write_text(json.dumps(record, indent=2) + '\n')
    subprocess.run([str(output / 'worker'), 'case', 'build-check', '--build', str(output)], check=True)
    print(f"Worker: {output / 'worker'}\nSHA-256: {record['binary_sha256']}")


if __name__ == '__main__':
    main()
