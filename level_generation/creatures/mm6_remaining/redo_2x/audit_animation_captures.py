"""Validate the browser-rendered animation captures for the accepted MM6 review scope."""

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image

from capture_viewer_animation import webp_durations


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def audit(queue_path, output_path):
    queue = json.loads(Path(queue_path).read_text())
    families = []
    total_bindings = 0
    total_distinct = 0
    for family in queue['families']:
        manifest_path = Path(family['package'])
        root = manifest_path.parent
        viewer_path = root / 'placement_review.html'
        index_path = root / 'review/browser_motion/browser_capture_index.json'
        manifest = json.loads(manifest_path.read_text())
        index = json.loads(index_path.read_text())
        assert index['manifest_sha256'] == sha256(manifest_path), family['family']
        assert index['viewer_sha256'] == sha256(viewer_path), family['family']
        atlas_paths = {path for page in manifest['pages']
                       for path in [page['base'], page['mask'], page['mask_overlay'],
                                    *page['variant_previews'].values()]}
        current_atlas_hashes = {path: sha256(root / path) for path in sorted(atlas_paths)}
        assert index['atlas_pages_sha256'] == current_atlas_hashes, (
            family['family'], 'atlas changed after browser capture')
        assert index['visual_acceptance'] is False, family['family']
        palette = next(key for key, value in manifest['variants'].items() if value.get('exact_base_bypass'))
        expected = {(name, int(view)): steps
                    for name, animation in manifest['animations_by_palette'][palette].items()
                    for view, steps in animation['views'].items() if steps}
        observed = {(binding['action'], binding['view']): binding['capture_index']
                    for binding in index['bindings']}
        assert len(observed) == len(index['bindings']) == len(expected), family['family']
        assert set(expected) == set(observed), family['family']
        signatures = {json.dumps(steps, sort_keys=True) for steps in expected.values()}
        captures = index['captures']
        assert len(captures) == index['distinct_sequence_count'] == len(signatures), family['family']
        assert set(observed.values()) == set(range(len(captures))), family['family']
        for binding, capture_index in observed.items():
            capture = captures[capture_index]
            steps = expected[binding]
            assert steps == expected[(capture['action'], capture['view'])], (family['family'], binding)
            assert capture['frames'] == [step['frame'] for step in steps], (family['family'], binding)
            assert capture['native_duration_ms'] == [step['duration_ms'] for step in steps], (
                family['family'], binding)
        for capture in captures:
            webp_path = Path(capture['webp'])
            metadata_path = Path(capture['metadata'])
            metadata = json.loads(metadata_path.read_text())
            assert sha256(webp_path) == capture['webp_sha256'] == metadata['animation_sha256']
            assert sha256(metadata_path) == capture['metadata_sha256']
            assert metadata['manifest_sha256'] == index['manifest_sha256']
            assert metadata['viewer_sha256'] == index['viewer_sha256']
            assert metadata['palette'] == palette
            assert metadata['frames'] == capture['frames']
            assert metadata['native_duration_ms'] == capture['native_duration_ms']
            encoded = webp_durations(webp_path)
            assert encoded == metadata['encoded_duration_ms']
            if encoded:
                assert sum(encoded) == sum(metadata['exported_duration_ms'])
                assert sum(encoded) == sum(round(ms) for ms in metadata['native_duration_ms'])
            else:
                assert len(capture['frames']) == 1
            animation = Image.open(webp_path)
            assert animation.n_frames == (len(encoded) or 1)
        families.append(dict(family=family['family'], index=str(index_path), index_sha256=sha256(index_path),
                             manifest_sha256=index['manifest_sha256'], viewer_sha256=index['viewer_sha256'],
                             atlas_pages_sha256=current_atlas_hashes,
                             bindings=len(expected), distinct_captures=len(captures)))
        total_bindings += len(expected)
        total_distinct += len(captures)
    result = dict(family_count=len(families), binding_count=total_bindings,
                  distinct_capture_count=total_distinct, families=families, visual_acceptance=False,
                  method='Current placement viewer canvases and native timing; frame/alias coverage and capture hashes audited')
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(dict(families=len(families), bindings=total_bindings, captures=total_distinct,
                          output=str(output_path))))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--queue', default='level_generation/creatures/mm6_remaining/ground_anchor_review/accepted/placement_queue.json')
    parser.add_argument('--output', default='level_generation/creatures/mm6_remaining/ground_anchor_review/accepted/animation_capture_inventory.json')
    args = parser.parse_args()
    audit(args.queue, args.output)
