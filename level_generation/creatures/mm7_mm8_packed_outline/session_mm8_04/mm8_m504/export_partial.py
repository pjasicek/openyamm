"""Pack available masters with the shared exporter and retain the complete native contract.

The exporter snapshot deliberately contains no playback. The delivered partial
manifest restores the untouched full native bindings and explicitly lists gaps.
It must never be promoted to full-family acceptance.
"""
import argparse
import copy
import json
from pathlib import Path
import shutil
import sys

SESSION = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SESSION / 'mm8_m496'))
from process_session import native_package, read, sha, write


def export(family):
    root = SESSION / family
    sources = read(root / 'sources.json')
    records = read(root / 'registration.json')
    aliases = {a: c for a, c in sources['pixel_aliases'].items() if c in records}
    available = set(records) | set(aliases)
    missing = sorted(set(sources['sources']) - available)
    assert missing, 'Use the ordinary shared exporter for complete families'
    work = root / 'partial_export_work'
    work.mkdir(exist_ok=True)
    (work / 'review').mkdir(exist_ok=True)
    snapshot = copy.deepcopy(sources)
    snapshot['sources'] = {n: sources['sources'][n] for n in sorted(available)}
    snapshot['pixel_aliases'] = aliases
    snapshot['bindings'] = {}
    write(work / 'sources.json', snapshot)
    write(work / 'registration.json', records)
    shutil.copy2(root / 'material_settings.json', work / 'material_settings.json')
    for folder in ['toned_2x', 'masks_2x', 'previews', 'native_variants']:
        link = work / folder
        if not link.exists():
            link.symlink_to(root / folder, target_is_directory=True)
        assert link.resolve() == (root / folder).resolve()
    source_hash = sha(root / 'sources.json')
    native_package.ROOT = work
    native_package.run()
    assert sha(root / 'sources.json') == source_hash
    for folder in ['atlas', 'runtime_aligned_2x', 'runtime_masks_2x']:
        shutil.copytree(work / folder, root / folder, dirs_exist_ok=True)
    manifest = read(work / 'draft_manifest.json')
    manifest.update(status='partial_exports_pending_visual_review',
        animations=sources['bindings'], missing_frames=missing, full_coverage=False,
        pixel_aliases=sources['pixel_aliases'], logical_canvas=sources['logical_canvas'],
        logical_pivot=sources['logical_pivot'], placement_registration='registration.json',
        native_palette_exports=sources.get('staged_native_palettes', {}),
        generated_sampling_min=min(min(r['effective_sampling_xy']) for r in records.values()),
        review_evidence='review/partial_acceptance.json',
        partial_contract='Every original native step is retained. Missing frame references are unresolved; '
            'no substitute or new playback step is supplied. Unused art remains unbound.',
        packing_snapshot='partial_export_work/sources.json')
    manifest.pop('viewer', None)
    assert manifest['animations'] == sources['bindings']
    assert set(manifest['frames']) == available
    write(root / 'draft_manifest.json', manifest)
    checks = read(work / 'review/export_checks.json')
    checks.update(full_coverage=False, missing_frames=missing,
        all_native_animation_metadata_preserved=True,
        packing_snapshot_has_no_playback=True,
        complete_family_acceptance=False)
    write(root / 'review/export_checks.json', checks)
    print(f'{family}: {len(available)}/{len(sources["sources"])} available; {len(missing)} explicit gaps')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('family')
    export(parser.parse_args().family)
