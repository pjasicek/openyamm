"""Explicit one-time preview-only Air crop migration; preserve all prior generation and acceptance history."""
import argparse
import fcntl
import importlib.util
import json
import shutil
from pathlib import Path

from finalize_classification import HERE, ROOT, digest

spec = importlib.util.spec_from_file_location('hud_migration_queue', HERE / 'queue.py')
queue_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(queue_module)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true', help='Archive checkpoint and activate the reviewed native layout')
    args = parser.parse_args()
    with (HERE / 'checkpoint/state.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        queue = queue_module.Queue()
        assert not queue.state.get('layout_revision'), 'Revision already active; never restart migration'
        assert not queue.state.get('claims'), 'Finish or explicitly release actual work before migration'
        review_dir = HERE / 'review/spellbook_placement'
        review = json.loads((review_dir / 'review.json').read_text())
        assert review['owned_capture_exit_code'] == 0 and review['normal_settings_unchanged']
        for name, sha in review['evidence_sha256'].items():
            assert digest(review_dir / name) == sha, 'Native placement evidence drift'
        records = json.loads((review_dir / 'audit.json').read_text())['records']
        assert len(records) == 22
        changes = {}
        for record in records:
            assert record['agreeing_patches'] >= 3
            sibling = next(r for r in records if r['name'] == record['name'][:-1]
                           + ('b' if record['name'].endswith('a') else 'a'))
            assert record['candidate_origin'] == sibling['candidate_origin']
            target_id = 'engine--icons--' + record['name'] + '.bmp'
            target = queue.targets[target_id]
            old = target['page_dependencies'][0]['x2_draw_rect']
            x, y = record['candidate_origin']
            changes[target_id] = dict(before_x2=old, after_x2=[x * 2, y * 2, *old[2:]])
        root = HERE / 'checkpoint/layout_revisions/air_v1'
        plan = dict(revision='air_v1', targets=changes,
                    affected_accepted=[c for c in changes if queue.accepted(c)],
                    previous_state_sha256=digest(queue.state_path))
        print(json.dumps(plan, indent=2))
        if not args.apply:
            return
        assert not root.exists(), 'Preserve a previous migration attempt'
        root.mkdir(parents=True)
        shutil.copy2(queue.state_path, root / 'before-state.json')
        shutil.copy2(review_dir / 'candidate-spellbook.yml', root / 'spellbook.yml')
        shutil.copy2(Path(__file__), root / 'migration_snapshot.py')
        native = 'assets_dev/engine/ui/gameplay/spellbook.yml'
        revision = dict(plan, native_layout=native, native_layout_sha256=digest(ROOT / native),
            preview_layout=str(root / 'spellbook.yml'), preview_layout_sha256=digest(root / 'spellbook.yml'),
            evidence_hashes={str(review_dir / name): sha for name, sha in review['evidence_sha256'].items()})
        queue_module.save(root / 'revision.json', revision)
        queue.state['layout_revision'] = dict(path=str(root / 'revision.json'), sha256=digest(root / 'revision.json'))
        # Old records remain readable but affected acceptance is stale until re-reviewed at the revised crop.
        queue_module.save(queue.state_path, queue.state)
        resumed = queue_module.Queue()
        assert all(not resumed.accepted(c) for c in plan['affected_accepted'])
        assert digest(root / 'before-state.json') == plan['previous_state_sha256']


if __name__ == '__main__':
    main()
