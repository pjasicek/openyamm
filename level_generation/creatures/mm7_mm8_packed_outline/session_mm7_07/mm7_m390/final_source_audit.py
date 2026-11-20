"""Verify this staged session without editing native or accepted asset packages."""
import importlib.util
import re
from datetime import datetime, timezone
from pathlib import Path

p = Path(__file__).with_name('session_pipeline.py')
s = importlib.util.spec_from_file_location('session', p)
m = importlib.util.module_from_spec(s)
s.loader.exec_module(m)
summary = dict(verified_utc=datetime.now(timezone.utc).isoformat(), families=[],
               native_bmps=0, native_palettes=0, native_frame_group_files=0,
               prior_metadata_files=0, returned_sheets=0, failed_submissions=0,
               unused_native_frames=0, whole_sheet_jobs=0)

for stem in m.FAMILIES:
    root = m.STAGE / ('mm7_' + stem)
    out = root / 'redo_2x'
    sources = m.read(root / 'sources.json')
    run = m.read(out / 'run.json')
    manifest = m.read(out / 'manifest.json')
    original = m.read(root / 'manifest.json')
    acceptance = m.read(out / 'review/acceptance.json')
    assert acceptance['accepted']
    assert run['accepted'] and run['status'] == 'accepted_after_static_visual_review'
    for path, key in [('assets_dev/engine/data_tables/monster_descriptors.txt', 'descriptor_table_sha256'),
                      ('level_generation/creatures/remaining_inventory.json', 'inventory_sha256')]:
        assert m.sha(m.REPO / path) == acceptance['source_integrity'][key]
        summary[key] = acceptance['source_integrity'][key]
    assert set(manifest['frames']) == set(sources['sources'])
    assert manifest['descriptor_animations'] == original['descriptor_animations']
    assert manifest['complete_native_descriptor_animations'] == original['descriptor_animations']
    assert m.sha(out / 'manifest.json') == acceptance['manifest_sha256']
    for relative, digest in acceptance['artifact_hashes'].items():
        assert m.sha(out / relative) == digest, (stem, relative)
    for record in (list(sources['sources'].values()) + list(sources['palette_sources'].values()) +
                   sources['group_sources'] + run['source_metadata']):
        assert m.sha(m.REPO / record['path']) == record['sha256'], record['path']
    native_cache = {}
    returns = failures = 0
    for job in run['jobs']:
        assert job.get('selected_raw')
        assert job['status'] == 'accepted_complete_sheet_after_visual_review'
        selected = [a for a in job['attempts'] if a['raw'] == job['selected_raw']]
        assert len(selected) == 1 and selected[0].get('review_status') != 'rejected_visual_review'
        preparations = job.get('preparation_history', []) + [job]
        for attempt in job['attempts']:
            assert m.sha(m.REPO / attempt['raw']) == attempt['sha256']
            assert m.sha(m.REPO / attempt['prompt']) == attempt['prompt_sha256']
            prompt = (m.REPO / attempt['prompt']).read_text()
            assert prompt.startswith(m.HEADER)
            assert len(attempt['references']) >= 3
            for reference in attempt['references']:
                assert m.sha(m.REPO / reference['path']) == reference['sha256']
            references = [str((m.REPO / r['path']).resolve()) for r in attempt['references'][:2]]
            preparation = next(p for p in preparations if
                [str((m.REPO / r).resolve()) for r in p['references'][:2]] == references)
            colour = m.Image.open(references[0]).convert('RGBA')
            outline = m.Image.open(references[1]).convert('RGB')
            assert colour.size == outline.size
            palette_match = re.search(r'Generate ONLY base palette (\d+)', prompt)
            palette = int(palette_match[1]) if palette_match else sources['base_palette']
            crop = [round(v * 2) for v in preparation['native_crop']]
            cell = [v * 2 for v in preparation['cell_native_size']]
            expected = m.Image.new('RGBA', tuple(cell[i] * preparation[['columns', 'rows'][i]] for i in range(2)))
            guide = m.Image.new('RGB', expected.size, 'white')
            for index, name in enumerate(job['frames']):
                key = (name, palette)
                if key not in native_cache:
                    native_cache[key] = m.native_2x(sources['sources'][name], sources, palette)[0]
                native = native_cache[key]
                part = native.crop(crop)
                rebuilt = m.Image.new('RGBA', native.size)
                rebuilt.paste(part, tuple(crop[:2]))
                assert m.np.array_equal(m.np.array(native), m.np.array(rebuilt))
                xy = (index % preparation['columns'] * cell[0], index // preparation['columns'] * cell[1])
                expected.paste(part, xy)
                inside = m.np.array(part.getchannel('A'))[::2, ::2] > 0
                edge = inside & ~m.ndimage.binary_erosion(inside, structure=m.np.ones((3, 3), bool))
                pixels = m.np.full((*inside.shape, 3), 255, m.np.uint8)
                pixels[edge] = 0
                guide.paste(m.Image.fromarray(pixels).resize(part.size, m.Image.Resampling.NEAREST), xy)
            assert m.np.array_equal(m.np.array(colour), m.np.array(expected)), (stem, job['id'], attempt['raw'], 'native')
            assert m.np.array_equal(m.np.array(outline), m.np.array(guide)), (stem, job['id'], attempt['raw'], 'outline')
            returns += 1
        failures += len(job.get('failed_submissions', []))
    row = dict(family=stem, accepted=True, native_bmps=len(sources['sources']),
               native_palettes=len(sources['palette_sources']), native_frame_group_files=len(sources['group_sources']),
               prior_metadata_files=len(run['source_metadata']), returned_sheets=returns,
               failed_submissions=failures, unused_native_frames=len(sources['unreferenced']),
               whole_sheet_jobs=len(run['jobs']), minimum_generated_sampling=manifest['generated_detail']['measured_minimum'],
               exact_native_colour_alpha_and_outline_reconstruction=True, all_hashes_unchanged=True,
               exact_native_descriptor_metadata_preserved=True)
    summary['families'].append(row)
    for key in ['native_bmps', 'native_palettes', 'native_frame_group_files', 'prior_metadata_files',
                'returned_sheets', 'failed_submissions', 'unused_native_frames', 'whole_sheet_jobs']:
        summary[key] += row[key]
    print(stem, 'verified', returns, 'complete preparations/returns', flush=True)

summary.update(accepted_families=len(summary['families']), submissions=summary['returned_sheets'] + summary['failed_submissions'],
               timed_playback_watched=False, installed=False)
m.save(m.STAGE / 'mm7_m390/final_source_integrity.json', summary)
print({key: value for key, value in summary.items() if key != 'families'})
