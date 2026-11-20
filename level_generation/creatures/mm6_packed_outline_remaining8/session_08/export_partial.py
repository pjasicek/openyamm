"""Stage available art without claiming completion of a blocked native sheet.

Uses the shared exporter for pixels, masks, palettes and provenance. The full
native contract is preserved separately; unavailable reviewer views are empty
and explicitly labelled. This session utility never edits shared tools.
"""
import copy
import hashlib
import json
from pathlib import Path
import sys

from PIL import Image, ImageDraw

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / 'level_generation/creatures/mm6_remaining/redo_2x'))
import export_run
from whole_animation_resolution import record_detail_policy, validate_policy


def read(path):
    return json.loads(path.read_text())


def write(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def export_partial(project):
    root = (REPO / project).resolve()
    out = root / 'redo_2x'
    original = read(root / 'manifest.json')
    source = read(root / 'sources.json')
    records = read(out / 'registration.json')
    missing = sorted(set(source['sources']) - set(records))
    run = read(out / 'run.json')
    blocked = [job for job in run['jobs'] if not job.get('selected_raw')]
    assert missing and set(missing) == {name for job in blocked for name in job['frames']}
    assert all(job['status'] == 'blocked_imagegen_safety' for job in blocked)
    package = export_run.package_family
    original_export, original_load = package.export, package.load
    original_animation, original_contacts = package.animation, package.make_contacts

    def partial_load(family, source_root):
        path, config, inventory = original_load(family, source_root)
        inventory = copy.deepcopy(inventory)
        inventory['sources'] = {name: item for name, item in inventory['sources'].items() if name in records}
        inventory['pixel_aliases'] = {name: item for name, item in inventory['pixel_aliases'].items()
                                      if name in records}
        return path, config, inventory

    def partial_animation(group, action, frames):
        animation = original_animation(group, action, source['sources'])
        unavailable = [view for view, steps in animation['views'].items()
                       if any(step['frame'] not in frames for step in steps)]
        if unavailable:
            animation['blocked_views'] = unavailable
            for view in unavailable:
                animation['views'][view] = []
        return animation

    def edge_contact(output, config, inventory, registration, aligned, tiles, masks, audit, animations, vectors):
        ranked = sorted(audit, key=lambda name: audit[name]['atlas_extracted']['max_score'], reverse=True)[:12]
        sheet = Image.new('RGB', (1680, 380), (55, 55, 55))
        draw = ImageDraw.Draw(sheet)
        for index, name in enumerate(ranked):
            x, y = audit[name]['atlas_extracted']['position']
            crop = tiles[name].crop((x-16, y-16, x+16, y+16)).resize((128, 128), Image.Resampling.NEAREST)
            for column, background in enumerate([(35, 35, 35), (240, 240, 240)]):
                patch = Image.new('RGBA', crop.size, (*background, 255))
                patch.alpha_composite(crop)
                sheet.paste(patch.convert('RGB'), (index % 6 * 280 + column * 132, index // 6 * 190 + 30))
            draw.text((index % 6 * 280 + 2, index // 6 * 190 + 8), name, fill='white')
        sheet.save(output / 'review/edge_current.png')

    class PartialPixelsExported(Exception):
        pass

    def partial_pixels(family, output, source_root):
        staged_source = read(output / 'sources.json')
        staged_source['sources'] = {name: item for name, item in staged_source['sources'].items()
                                    if name in records}
        staged_source['partial_coverage'] = dict(expected=len(source['sources']), missing_frames=missing)
        write(output / 'sources.json', staged_source)
        original_export(family, output, source_root)
        raise PartialPixelsExported()

    package.load, package.animation, package.make_contacts = partial_load, partial_animation, edge_contact
    package.export = partial_pixels
    try:
        export_run.export(project, False)
    except PartialPixelsExported:
        pass
    finally:
        package.export, package.load = original_export, original_load
        package.animation, package.make_contacts = original_animation, original_contacts
    manifest = read(out / 'manifest.json')
    for key in ('logical_canvas', 'logical_pivot', 'native_frame_scale'):
        assert manifest[key] == original[key]
    for palette, actions in original['animations_by_palette'].items():
        for action, native in actions.items():
            actual = manifest['animations_by_palette'][palette][action]
            for view, steps in native['views'].items():
                if any(step['frame'] in missing for step in steps):
                    assert actual['views'][view] == [] and view in actual['blocked_views']
                else:
                    assert actual['views'][view] == steps
    policy = read(out / 'processing.json')['whole_animation_resolution_policy']
    validate_policy(policy, run, original, records)
    manifest['generated_detail'] = dict(measured_minimum=min(min(row['effective_sampling_xy'])
                                                          for row in records.values()),
                                        registration='registration.json', calibration='calibration.json')
    record_detail_policy(manifest, policy, records)
    manifest['quality_status'] = 'partial_staged_blocked_sheet'
    manifest['partial_coverage'] = dict(expected_frames=len(source['sources']), exported_frames=len(records),
                                      missing_frames=missing, blocked_jobs=[job['id'] for job in blocked],
                                      native_contract='native_contract.json', acceptance_frozen=False)
    manifest['limitations'].append('Partial family: blocked native sheets remain absent. Empty reviewer views '
                                   'are blocked restoration slots, not native no-image sentinels.')
    write(out / 'native_contract.json', original)
    write(out / 'manifest.json', manifest)
    validation = read(out / 'validation.json')
    validation['complete_native_coverage'] = False
    validation['expected_source_files'] = len(source['sources'])
    validation['missing_frames'] = missing
    validation['available_native_sequences_preserved'] = validation.pop('per_palette_native_sequences_preserved')
    validation['visual_review'] = 'Partial art awaiting explicit available-pose review; family acceptance is blocked.'
    write(out / 'validation.json', validation)
    template = (REPO / 'level_generation/creatures/mm6_peasants/viewer.html').read_text()
    template = template.replace("'Native no-image action'", "a.blocked_views?.includes($('view').value)?"
                                "'Restoration blocked: native sheet absent':'Native no-image action'")
    template = template.replace('review/standing_variants.png', 'review/all_variants_0.png')
    title = read(root / 'config.json')['title'] + ' — PARTIAL, rear standing sheet blocked'
    (out / 'review.html').write_text(template.replace('__TITLE__', title)
                                   .replace('/* MANIFEST */', json.dumps(manifest, separators=(',', ':'))))
    print(json.dumps(manifest['partial_coverage']))


if __name__ == '__main__':
    export_partial(sys.argv[1])
