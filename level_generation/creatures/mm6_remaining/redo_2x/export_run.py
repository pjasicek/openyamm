"""Export a staged creature redo using the existing native atlas/variant contract."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys

from prepare_run import REPO
from whole_animation_resolution import record_detail_policy, validate_policy
sys.path.insert(0, str(REPO / 'level_generation/creatures/mm6_peasants'))
import package_family

def asset(path, out):
    return dict(path=os.path.relpath(path, out), sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def export(project, with_viewer=True):
    ROOT = REPO / project
    OUT = ROOT / 'redo_2x'
    config = json.loads((ROOT / 'config.json').read_text())
    records = json.loads((OUT / 'registration.json').read_text())
    run = json.loads((OUT / 'run.json').read_text())
    jobs = {j['id']: j for j in run['jobs']}
    if (OUT / 'standing_01.json').exists():
        jobs['standing_01'] = json.loads((OUT / 'standing_01.json').read_text())
    generation = {}
    for name, record in records.items():
        assert len(record['translate']) == 2, f'{name}: registration translate must be an x/y pair'
        batch = record['batch']
        if record.get('empty_native_endpoint'):
            assert batch == 'native_empty_endpoints'
            source = ROOT/'native'/(name+'.png')
            entry = generation.setdefault(batch, dict(raw=asset(OUT/'raw/native_empty_endpoints.png', OUT),
                prompt=asset(OUT/'prompts/native_empty_endpoints.txt', OUT), references=[]))
            entry['references'].append(asset(source, OUT))
            target = OUT/'cleaned'/(name+'.png')
            cleaned = OUT/'cleaned/native_empty_endpoints'/(record.get('generated_frame', name)+'.png')
            if target.is_symlink() and target.resolve() != cleaned.resolve():
                target.unlink()
            if not target.exists():
                target.symlink_to(os.path.relpath(cleaned, target.parent))
            continue
        if 'retained_from' in record:
            retained = record['retained_from']
            source_root = REPO / retained['project']
            if source_root != ROOT:
                assert retained.get('user_authorization'), 'Cross-project art reuse requires explicit scope'
                assert json.loads((source_root / 'sources.json').read_text()) == json.loads(
                    (ROOT / 'sources.json').read_text()), 'Retained artwork must have identical native family sources'
                assert (source_root / 'recolor_vectors.json').read_bytes() == (ROOT / 'recolor_vectors.json').read_bytes()
                if config.get('material_module'):
                    assert (source_root / config['material_module']).read_bytes() == (
                        ROOT / config['material_module']).read_bytes(), 'Changed retained material semantics'
                for relative, digest in retained['source_metadata'].items():
                    assert asset(source_root / relative, OUT)['sha256'] == digest
            assert asset(source_root / 'registration.json', OUT)['sha256'] == retained['registration_sha256']
            original = json.loads((source_root / 'registration.json').read_text())[name]
            assert original['batch'] == batch and original['scale'] == record['scale']
            for relative, digest in retained['assets'].items():
                assert asset(source_root / relative, OUT)['sha256'] == digest
                assert asset(OUT / relative, OUT)['sha256'] == digest, 'Changed retained pixels: ' + relative
            previous = json.loads((source_root / 'generation.json').read_text())['batches'][batch]
            def retained_asset(value):
                result = asset(source_root / value['path'], OUT)
                assert result['sha256'] == value['sha256']
                return result
            generation[batch] = dict(raw=retained_asset(previous['raw']),
                                    prompt=retained_asset(previous['prompt']),
                                    references=[retained_asset(value) for value in previous['references']])
            assert (OUT / 'cleaned' / (name + '.png')).exists()
            continue
        job = jobs[batch]
        attempt = next(a for a in job['attempts'] if a.get('raw', a.get('raw_path')) == record['raw_path'])
        generation[batch] = dict(raw=asset(REPO / record['raw_path'], OUT), prompt=asset(REPO / attempt['prompt'], OUT),
                                references=[asset(REPO / p['path'], OUT) for p in attempt['references']])
        source = OUT / 'cleaned' / batch / (record.get('generated_frame', name) + '.png')
        target = OUT / 'cleaned' / (name + '.png')
        if target.is_symlink() and target.resolve() != source.resolve():
            target.unlink()
        if not target.exists():
            target.symlink_to(os.path.relpath(source, target.parent))
    (OUT / 'generation.json').write_text(json.dumps(dict(batches=generation), indent=2) + '\n')
    for name in ['sources.json', 'config.json', 'recolor_vectors.json']:
        shutil.copy2(ROOT / name, OUT / name)
    if config.get('material_module'):
        shutil.copy2(ROOT / config['material_module'], OUT / config['material_module'])
    package_family.export(config['family'], OUT, ROOT)
    path = OUT / 'manifest.json'
    manifest = json.loads(path.read_text())
    original = json.loads((ROOT / 'manifest.json').read_text())
    for key in ['logical_canvas', 'logical_pivot', 'native_frame_scale', 'animations', 'animations_by_palette']:
        assert manifest[key] == original[key], key
    # The family material module may use nonlinear native palette lookup tables.
    # Preserve that authoritative contract rather than labelling a LUT as an RGB vector.
    if original['recolor_model'] in ('masked_luminance_lut_v1', 'multi_mask_luminance_lut_v1'):
        single = original['recolor_model'] == 'masked_luminance_lut_v1'
        old_key, new_key = (('luminance_vector', 'luminance_lut') if single else
                            ('region_luminance_vectors', 'region_luminance_luts'))
        for palette, variant in original['variants'].items():
            if new_key in variant:
                generated = manifest['variants'][palette]
                assert generated[old_key] == variant[new_key], 'Changed native recolor table: ' + palette
                generated[new_key] = generated.pop(old_key)
        manifest['recolor_model'] = original['recolor_model']
        manifest['recolor'] = original['recolor']
        manifest['regions'] = original['regions']
    manifest['generated_detail'] = dict(minimum_sampling_exclusive=2,
        measured_minimum=min(min(r['effective_sampling_xy']) for r in records.values()
                             if not r.get('empty_native_endpoint')),
        registration='registration.json', calibration='calibration.json')
    exceptions = {n: r['retained_detail_exception'] for n, r in records.items() if 'retained_detail_exception' in r}
    if exceptions:
        manifest['generated_detail']['retained_detail_exceptions'] = exceptions
        manifest['generated_detail']['measured_new_art_minimum'] = min(
            min(r['effective_sampling_xy']) for r in records.values()
            if 'retained_from' not in r and not r.get('empty_native_endpoint'))
    manifest['limitations'] = [line for line in manifest['limitations'] if not line.startswith('2x export tier')]
    reuse = json.loads((OUT / 'processing.json').read_text()).get('historical_art_reuse')
    if reuse:
        manifest['historical_art_reuse'] = reuse
        manifest['limitations'].append('User-authorized reuse of earlier generated art fills ' +
            str(len(reuse['frames'])) + ' native poses. Those poses retain their historical generation layout '
            'and measured sampling; they are not new complete-sheet imagegen returns.')
    if exceptions:
        manifest['limitations'].append('User-authorized historical detail exception: ' + ', '.join(sorted(exceptions)))
    manifest['quality_status'] = 'pending_full_animation_and_variant_review'
    below_gate = sorted(name for name, record in records.items()
                        if not record.get('empty_native_endpoint') and min(record['effective_sampling_xy']) <= 2
                        and 'retained_detail_exception' not in record)
    policy = json.loads((OUT / 'processing.json').read_text()).get('whole_animation_resolution_policy')
    if policy:
        validate_policy(policy, run, original, records)
        record_detail_policy(manifest, policy, records)
    elif below_gate:
        manifest['generated_detail']['below_minimum_frames'] = below_gate
        manifest['quality_status'] = 'limited_whole_cycle_trial_below_detail_gate'
        manifest['limitations'].append('Complete native cycles retained, but actual generated sampling is below the '
            'required >2x for ' + str(len(below_gate)) + ' frames. The 2x export does not add generated detail. '
            'These are review candidates, not resolution-gate passes.')
    path.write_text(json.dumps(manifest, indent=2) + '\n')
    validation_path = OUT / 'validation.json'
    validation = json.loads(validation_path.read_text())
    validation['visual_review'] = ('See review.html and review/*.png; automated checks alone are not visual acceptance.'
                                 if with_viewer else
                                 'See review/*.png; automated checks alone are not visual acceptance.')
    validation_path.write_text(json.dumps(validation, indent=2) + '\n')
    if with_viewer:
        template = (REPO / 'level_generation/creatures/mm6_peasants/viewer.html').read_text()
        (OUT / 'review.html').write_text(template.replace('__TITLE__', config['title'] + ' redo — staged candidate')
                                       .replace('/* MANIFEST */', json.dumps(manifest, separators=(',', ':'))))
    print('Staged package (visual acceptance pending):', OUT / 'manifest.json')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('project')
    parser.add_argument('--skip-viewer', action='store_true', help='Skip the shared-template HTML export')
    args = parser.parse_args()
    export(args.project, not args.skip_viewer)
