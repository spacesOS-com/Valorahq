"""Validate the explicit release checkpoint. Never regenerate production output.

Legacy generators are quarantined; --audit-generators runs them only in a
throwaway tree and reports every drift. Snapshot deltas need a reviewed
manifest revision, not an automatic restore or acceptance flag.
"""
from pathlib import Path
import argparse, hashlib, json, shutil, subprocess, tempfile, sys
ROOT = Path(__file__).resolve().parent.parent
CHECKPOINT = ROOT / '_release/checkpoints/consumer-oct7-first-meeting-art-word-v1'

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None

def verify():
    manifest = json.loads((CHECKPOINT / 'checkpoint-files.json').read_text())
    bad = [p for p, sha in manifest.items() if digest(ROOT / p) != sha]
    public = json.loads((CHECKPOINT / 'public-output.json').read_text())
    for p, sha in public.items():
        if digest(ROOT / p) != sha and p not in bad:
            bad.append(p)
    for p in json.loads((CHECKPOINT / 'generator-drift.json').read_text())['paths']:
        if digest(CHECKPOINT / 'reviewed-output' / p) != manifest[p]:
            bad.append('reviewed-output/' + p)
    allowed = set(manifest) | {'_build/build.py', '_release', '.git'}
    unexpected = []
    for p in ROOT.rglob('*'):
        if not p.is_file():
            continue
        rel = p.relative_to(ROOT).as_posix()
        if '.git' in p.relative_to(ROOT).parts or '__pycache__' in p.parts or rel.startswith('_release/'):
            continue
        if rel not in allowed:
            unexpected.append(rel)
    if bad or unexpected:
        print(json.dumps({'status':'FAIL', 'changed_or_missing':bad, 'unapproved_extra_files':unexpected}, indent=2))
        return False
    print('PASS: exact checkpoint source/runtime and public bytes; no files generated or restored.')
    return True

def audit():
    manifest = json.loads((CHECKPOINT / 'checkpoint-files.json').read_text())
    with tempfile.TemporaryDirectory(prefix='valora-generator-audit-') as temp:
        tree = Path(temp) / 'tree'
        shutil.copytree(ROOT, tree, ignore=shutil.ignore_patterns('.git', '__pycache__'))
        result = subprocess.run([sys.executable, str(tree / '_build/generator_legacy.py')], cwd=tree, capture_output=True, text=True)
        changed = [p for p, sha in manifest.items() if digest(tree / p) != sha]
        print(json.dumps({'status':'QUARANTINED_DRIFT' if changed else 'MATCH', 'generator_exit':result.returncode, 'changed_paths':changed, 'count':len(changed), 'stdout':result.stdout, 'stderr':result.stderr}, indent=2))
        return result.returncode == 0 and not changed

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--audit-generators', action='store_true')
    args = parser.parse_args()
    if not verify():
        sys.exit(1)
    if args.audit_generators and not audit():
        sys.exit(2)
