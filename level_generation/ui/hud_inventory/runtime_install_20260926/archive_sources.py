"""Move verified originals outside mounted assets, retaining all source hashes and provenance."""
import fcntl
import hashlib
import json
import sys
from pathlib import Path

OUT = Path(__file__).resolve().parent
HUD = OUT.parent
ROOT = HUD.parents[2]
sys.path.insert(0, str(HUD))
from queue import Queue, save


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    with (HUD / 'checkpoint/state.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        installed = json.loads((OUT / 'installed.json').read_text())
        assert all(sha(ROOT / r['path']) == r['sha256'] for r in installed['records'])
        manifest = OUT / 'source_archive.json'
        if not manifest.exists():
            audit = json.loads((HUD / 'finalization_20260926/icon_coverage.json').read_text())
            files = {}
            roots = ['engine/icons', 'worlds/mm6/icons', 'worlds/mm7/icons', 'worlds/mm8/icons']
            for row in audit['files']:
                path = Path(row['source'])
                if not any(str(path).startswith('assets_dev/' + r + '/') for r in roots):
                    continue
                assert sha(ROOT / path) == row['source_sha256'], path
                archive = Path('assets_legacy/icons_20260926') / path.relative_to('assets_dev')
                files[str(path)] = dict(archive=str(archive), sha256=row['source_sha256'],
                                       disposition=row['status'], target=row['target'])
            actual = {str(p.relative_to(ROOT)) for r in roots for p in (ROOT / 'assets_dev' / r).rglob('*') if p.is_file()}
            assert set(files) == actual, 'Original census changed'
            save(manifest, dict(schema='openyamm-icon-source-archive-v1', roots=roots, files=files,
                authorization='User authorized archiving original engine and unused world icon folders, 2026-09-26',
                mm9='Retained in its own native world package; excluded from this restoration migration.'))
        data = json.loads(manifest.read_text())
        for root in data['roots']:
            source = ROOT / 'assets_dev' / root
            destination = ROOT / 'assets_legacy/icons_20260926' / root
            if source.exists():
                assert not destination.exists(), destination
                destination.parent.mkdir(parents=True, exist_ok=True)
                source.rename(destination)
            assert destination.is_dir()
        assert all(sha(ROOT / r['archive']) == r['sha256'] for r in data['files'].values())
        q = Queue()
        q.state['native_source_archive'] = dict(path=str(manifest.relative_to(ROOT)), sha256=sha(manifest))
        save(q.state_path, q.state)
        print(json.dumps(dict(archived=len(data['files']), roots=data['roots'], ledger_sha256=sha(q.state_path))))


if __name__ == '__main__':
    main()
