"""Independent full-coverage, placement, palette and generation-provenance checks."""
import json
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
from process import ROOT, queue, save, spill
from process_compact import contact, translate
import materials


def run(final=False):
    source = json.loads((ROOT / 'sources.json').read_text())
    manifest = json.loads((ROOT / 'draft_manifest.json').read_text())
    registration = json.loads((ROOT / 'registration.json').read_text())
    jobs = json.loads((ROOT / 'compact_jobs.json').read_text())['jobs']
    settings = json.loads((ROOT / 'material_settings.json').read_text())
    aliases = source['pixel_aliases']
    assert set(manifest['frames']) == set(registration) | set(aliases)
    assert set(manifest['missing_frames']) == set(source['sources'])-set(manifest['frames'])
    if final:
        assert not manifest['missing_frames'] and len(registration) == 160
        assert all(j['status'] in ['accepted_visual', 'accepted_identity'] for j in jobs.values())
    assert not set(registration) & set(aliases)
    assert manifest['animations'] == source['bindings']
    for record in [*source['sources'].values(), *source['palette_sources'].values(),
                   *source['source_tables'], source['descriptor_table']]:
        assert queue.sha(queue.REPO / record['path']) == record['sha256'], record['path']
    counts = {'frames': 0, 'variants': 0, 'contacts': 0}
    for name, record in registration.items():
        job = jobs[record['batch']]
        assert record['generated_pixels_per_native_pixel'] >= 2
        assert min(record['raw_sampling_xy']) >= 2
        assert record['shared_calibration'] == job['frozen_calibration']
        assert job['status'] in ['accepted_visual', 'accepted_identity', 'accepted_subset', 'processed_unreviewed']
        assert name not in job.get('rejected_frames', {}), ('Selected rejected art', name)
        for item in [job['generation']['raw'], job['generation']['prompt'], *job['generation']['references']]:
            assert queue.sha(ROOT / item['path']) == item['sha256'], item['path']
        raw = Image.open(ROOT / record['raw']).convert('RGBA').crop(record['raw_cell'])
        if record.get('extraction_mask'):
            item = record['extraction_mask']
            assert queue.sha(ROOT / item['path']) == item['sha256']
            pixels = np.array(raw)
            pixels[np.asarray(Image.open(ROOT / item['path'])) == 0] = 0
            raw = Image.fromarray(pixels)
        cleaned = Image.open(ROOT / 'cleaned' / (name + '.png')).convert('RGBA')
        assert np.array_equal(np.asarray(raw)[:,:,3],np.asarray(cleaned)[:,:,3]),('Alpha changed',name)
        from process_compact import grade
        base = np.asarray(Image.open(ROOT / 'toned_2x' / (name + '.png')))
        tone = json.loads((ROOT / 'tone_settings.json').read_text())['multiplier']
        assert np.array_equal(base, grade(Image.open(ROOT / 'registered_2x' / (name + '.png')), tone, name)), ('Tone/local correction replay', name)
        mask = np.asarray(Image.open(ROOT / 'masks_2x' / (name + '.png')))
        aligned = Image.open(ROOT / 'registered_2x' / (name + '.png')).convert('RGBA')
        shift = record['integer_translation_2x']
        padding = record.get('working_padding_px', 0)
        padded = Image.new('RGBA', (576 + 2 * padding, 576 + 2 * padding))
        padded.paste(aligned, (padding, padding))
        assert np.array_equal(translate(translate(padded, [-x for x in shift]), shift), padded)
        if 'reviewed_isolated_residue' in record:
            repair = record['reviewed_isolated_residue']
            before = np.array(Image.open(ROOT / 'checkpoints/residue' / (name + '_before.png')))
            selected = np.asarray(Image.open(ROOT / 'checkpoints/residue' / (name + '_mask.png'))) > 0
            assert int(selected.sum()) == repair['pixel_count']
            assert int(before[:, :, 3][selected].max()) <= repair['alpha_max'] == 1
            labels, _ = ndi.label(before[:, :, 3] > 0)
            for component in np.unique(labels[selected]):
                assert not np.any((labels == component) & ~selected)
            before[selected] = 0
            replayed = translate(Image.fromarray(before), shift)
            padding = record.get('working_padding_px', 0)
            cropped = replayed.crop((padding, padding, padding + 576, padding + 576))
            reconstructed = Image.new('RGBA', replayed.size)
            reconstructed.paste(cropped, (padding, padding))
            assert np.array_equal(reconstructed, replayed)
            assert np.array_equal(cropped, aligned)
        landmark = contact(aligned, job['action'] == 'd')
        assert abs(landmark[0] - record['native_landmark'][0]) <= .5
        assert landmark[1] == record['native_landmark'][1]
        counts['contacts'] += 1
        for palette in materials.PALETTES:
            variant = np.asarray(Image.open(ROOT / 'previews' / (name + '_' + str(palette) + '.png')))
            assert np.array_equal(variant[:, :, 3], base[:, :, 3])
            assert np.array_equal(variant[mask == 0], base[mask == 0])
            if palette == settings['base_palette']:
                assert np.array_equal(base, variant)
            else:
                active = mask > 0
                tiny = Image.fromarray(base[active][:, None, :])
                expected = np.asarray(materials.recolor(tiny, mask[active][:, None], palette, settings))[:, 0, :]
                assert np.array_equal(expected, variant[active])
            counts['variants'] += 1
        counts['frames'] += 1
    counts['unique_generated_frames'] = counts['frames']
    for name, canonical in aliases.items():
        assert source['sources'][name]['pixel_hash'] == source['sources'][canonical]['pixel_hash']
        assert manifest['frames'][name]['pixel_alias_of'] == canonical
        for field in ['page', 'atlas_xywh', 'crop_origin_px', 'aligned_canvas_origin_px', 'logical_size']:
            assert manifest['frames'][name][field] == manifest['frames'][canonical][field]
        for palette in materials.PALETTES:
            assert np.array_equal(queue.native(ROOT, name, palette), queue.native(ROOT, canonical, palette))
            assert np.array_equal(Image.open(ROOT / f'previews/{name}_{palette}.png'),
                                  Image.open(ROOT / f'previews/{canonical}_{palette}.png'))
            counts['variants'] += 1
        counts['frames'] += 1
    edges = json.loads((ROOT / 'review/edge_audit.json').read_text())
    reviewed = json.loads((ROOT / 'review/edge_review_exceptions.json').read_text())
    for name, stages in edges.items():
        for stage, result in stages.items():
            if result['max_score'] > 12:
                exception = reviewed.get(name, {})
                limit = exception.get(stage, {})
                assert queue.sha(ROOT / 'toned_2x' / (name + '.png')) == exception.get('master_sha256')
                assert result['position'] == limit.get('position')
                assert result['max_score'] <= limit.get('max_score', 12), (name, stage, result)
                assert result['candidates_above_12'] == 1
    save(ROOT / ('review/delivery_checks.json' if final else 'review/partial_checks.json'), {'status': 'passed' if final else 'partial_checks_passed', 'family_validated': False, **counts,
        'missing_frames': manifest['missing_frames'],
        'unreviewed_jobs': [k for k,j in jobs.items() if j['status'] not in ['accepted_visual','accepted_identity']],
        'supplied_alpha_preserved':True,
        'reviewed_material_edge_exceptions': reviewed,
        'generation_sampling_min': min(r['generated_pixels_per_native_pixel'] for r in registration.values()),
        'generation_sampling_max': max(r['generated_pixels_per_native_pixel'] for r in registration.values()),
        'all_native_sources_and_bindings_exact': True, 'selected_art_provenance_exact': True,
        'native_contacts_within_half_pixel': True, 'inverse_translations_exact': True,
        'all_palette_math_and_protected_pixels_exact': True, 'all_cleaned_aligned_atlas_edges_pass': True,
        'variant_edge_policy': 'Protected contours are byte-exact base colors; masked contours use the verified native blue/red transform, not base chroma limits.'})
    print(counts)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(); parser.add_argument('--final', action='store_true')
    run(final=parser.parse_args().final)
