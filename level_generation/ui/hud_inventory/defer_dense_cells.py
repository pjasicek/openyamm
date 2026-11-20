"""Record explicit per-cell visual failures from retained dense returns, without accepting artwork."""
import argparse
import fcntl
import json
from pathlib import Path

from review_dense_sheet import BATCH, HERE, ROOT, digest, queue_module, read


def apply_review(path):
    review = read(path)
    folder = BATCH / review['bundle']
    manifest = read(folder / 'manifest.json')
    sheet = next(s for s in manifest['sheets'] if s['id'] == review['sheet'])
    assert digest(folder / sheet['layout']) == sheet['layout_sha256']
    layout = read(folder / sheet['layout'])
    members = {c['id']: c for c in layout['cells']}
    receipt = read(folder / 'outputs/progress.json')['sheets'][review['sheet']]
    raw = folder / receipt['raw_path']
    assert digest(raw) == receipt['raw_sha256'] == review['raw_sha256'], 'Stale raw review'
    assert review['cells'] and all(c in members for c in review['cells'])
    assert review['review_images'], 'Retain actual visual comparison evidence'
    evidence = {str(Path(p).resolve()): digest(Path(p)) for p in review['review_images']}
    with (HERE / 'checkpoint/state.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        q = queue_module.Queue()
        for cell, notes in review['cells'].items():
            assert isinstance(notes, str) and notes.strip(), 'Explicit observed defect required per cell'
            assert not q.accepted(cell), 'Preserve accepted siblings'
            assert members[cell]['member'] == q.members[cell][1], 'Cell contract changed'
            assert digest(ROOT / members[cell]['member']['source_path']) == members[cell]['source_sha256']
            assignment = q.state['external_assignments'][cell]
            assert assignment['bundle'] == review['bundle'] and assignment['dense_sheet'] == review['sheet']
        for cell, notes in review['cells'].items():
            current = q.state['cells'].setdefault(cell, {})
            current.update(status='deferred', reason=notes, dense_visual_review=dict(
                path=str(path.resolve()), sha256=digest(path), evidence_hashes=evidence,
                raw=str(raw.resolve()), raw_sha256=review['raw_sha256']))
            q.state['external_assignments'][cell].update(status='returned', raw_sha256=review['raw_sha256'])
        queue_module.save(q.state_path, q.state)
    return dict(deferred=len(review['cells']), accepted=0, staged=0)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('review', type=Path)
    print(json.dumps(apply_review(parser.parse_args().review)))
