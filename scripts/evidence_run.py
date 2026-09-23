"""Register and verify a NEW offline calculation; never bless old results.

Acceptance fixed before the first use (20 Sep 2026): every declared input
and every Python source in src/ and scripts/ must retain its exact SHA-256
from registration to completion and verification; every output byte and the
output file set must match. Any discrepancy fails. No numeric/model gate is
changed by this wrapper. A manifest proves byte provenance, not that all
physical dependencies were declared, that the model is accurate, or that a
legacy result was produced by current code.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import platform
import subprocess
from pathlib import Path
from datetime import datetime, timezone


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def _json(path, obj):
    Path(path).write_text(json.dumps(obj, indent=2, allow_nan=False) + '\n',
                          encoding='utf-8')


def _now():
    return datetime.now(timezone.utc).isoformat()


def _runtime():
    versions = {}
    for package in ('numpy', 'scipy', 'pandas', 'netCDF4', 'pytest'):
        try:
            versions[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            versions[package] = None
    return {'python': platform.python_version(), 'platform': platform.platform(),
            'distributions': versions}


def _git(root):
    def run(*args):
        p = subprocess.run(['git', '-C', str(root), *args], capture_output=True)
        return p.stdout.decode('utf-8', errors='replace').strip() if p.returncode == 0 else None
    diff = run('diff', '--binary', 'HEAD')
    return {'head': run('rev-parse', 'HEAD'), 'branch': run('branch', '--show-current'),
            'tracked_diff_sha256': None if diff is None else hashlib.sha256(diff.encode()).hexdigest(),
            'note': 'Individual source hashes include untracked Python files; HEAD alone is not the code identity.'}


def source_files(root):
    root = Path(root).resolve()
    files = []
    for folder in ('src', 'scripts'):
        files.extend(p.resolve() for p in (root / folder).rglob('*.py'))
    files.extend((root / name).resolve() for name in ('requirements.txt', 'pytest.ini')
                 if (root / name).is_file())
    return sorted(set(files))


class EvidenceRun:
    """Output directory must be new; registration is written BEFORE calculation."""
    def __init__(self, root, output, *, inputs, configuration, method):
        self.root = Path(root).resolve()
        self.output = Path(output).resolve()
        if not self.output.is_relative_to(self.root):
            raise ValueError('Output must be inside the isolated repository')
        if self.output.exists():
            raise FileExistsError('Refusing to replace an existing evidence run')
        code = source_files(self.root)
        declared = [Path(p).resolve() for p in inputs]
        if any(not p.is_file() for p in code + declared):
            raise ValueError('Every declared input must be an existing file')
        if any(p.is_relative_to(self.output) for p in code + declared):
            raise ValueError('Input cannot be inside its new output directory')
        self.registration = {
            'schema': 'mizan-evidence-run-v1', 'registered_at_utc': _now(),
            'root': str(self.root), 'method': method,
            'configuration': configuration, 'runtime': _runtime(), 'git': _git(self.root),
            'source_set': [str(p) for p in code],
            'inputs_sha256': {str(p): digest(p) for p in sorted(set(code + declared))},
            'qualification': 'OFFLINE_DEVELOPMENT_ONLY', 'write_enabled': False,
            'limitations': [
                'Source and input identity is checked; physical accuracy is not certified.',
                'Dependency completeness is a reviewed declaration, not inferred by tracing Python.',
                'External executables/databases need explicit input registration when used.',
                'Historical artifacts are inputs only and are not retroactively proven fresh.'],
        }
        # Validate JSON before creating a directory that implies a registered run.
        json.dumps(self.registration, allow_nan=False)
        self.output.mkdir(parents=True)
        _json(self.output / 'registration.json', self.registration)
        self.registration_hash = digest(self.output / 'registration.json')

    def finish(self, *, model_status, result_summary):
        if (self.output / 'manifest.json').exists():
            raise FileExistsError('An evidence run can only be sealed once')
        changed = _input_errors(self.registration)
        if digest(self.output / 'registration.json') != self.registration_hash:
            changed.append('REGISTRATION_CHANGED')
        outputs = {str(p.relative_to(self.output)): digest(p)
                   for p in sorted(self.output.rglob('*')) if p.is_file()
                   and str(p.relative_to(self.output)) not in ('registration.json', 'manifest.json')}
        if not outputs:
            changed.append('NO_OUTPUTS')
        manifest = {
            'schema': 'mizan-evidence-run-v1', 'completed_at_utc': _now(),
            'registration_sha256': self.registration_hash,
            'provenance_status': 'FAIL' if changed else 'PASS',
            'provenance_errors': changed, 'model_status': model_status,
            'result_summary': result_summary, 'outputs_sha256': outputs,
            'write_enabled': False,
        }
        _json(self.output / 'manifest.json', manifest)
        if changed:
            raise RuntimeError('Evidence run inputs changed: ' + '; '.join(changed))
        return manifest


def _input_errors(registration):
    errors = []
    root = Path(registration['root'])
    if [str(p) for p in source_files(root)] != registration['source_set']:
        errors.append('SOURCE_FILE_SET_CHANGED')
    for name, expected in registration['inputs_sha256'].items():
        p = Path(name)
        if not p.is_file():
            errors.append('INPUT_MISSING: ' + name)
        elif digest(p) != expected:
            errors.append('INPUT_CHANGED: ' + name)
    return errors


def verify_run(output):
    output = Path(output).resolve()
    try:
        manifest = json.loads((output / 'manifest.json').read_text(encoding='utf-8'))
        registration = json.loads((output / 'registration.json').read_text(encoding='utf-8'))
        errors = _input_errors(registration)
        if manifest.get('provenance_status') != 'PASS':
            errors.append('RUN_WAS_NOT_SUCCESSFULLY_SEALED')
        if digest(output / 'registration.json') != manifest['registration_sha256']:
            errors.append('REGISTRATION_CHANGED')
        actual = {str(p.relative_to(output)) for p in output.rglob('*') if p.is_file()
                  and str(p.relative_to(output)) not in ('registration.json', 'manifest.json')}
        if actual != set(manifest['outputs_sha256']):
            errors.append('OUTPUT_FILE_SET_CHANGED')
        for name, expected in manifest['outputs_sha256'].items():
            p = (output / name).resolve()
            if not p.is_relative_to(output):
                errors.append('OUTPUT_PATH_ESCAPE: ' + name)
            elif not p.is_file() or digest(p) != expected:
                errors.append('OUTPUT_CHANGED_OR_MISSING: ' + name)
        return {'status': 'FAIL' if errors else 'PASS', 'errors': errors,
                'scope': 'byte identity of this registered offline run; not model validation',
                'model_status': manifest.get('model_status'), 'write_enabled': False}
    except (OSError, ValueError, KeyError, TypeError) as exc:
        return {'status': 'FAIL', 'errors': ['INVALID_EVIDENCE: ' + str(exc)],
                'write_enabled': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path, help='Existing registered run to verify')
    args = parser.parse_args()
    result = verify_run(args.output)
    print(json.dumps(result, indent=2, allow_nan=False))
    return 0 if result['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
