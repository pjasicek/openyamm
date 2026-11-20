"""Collect final owned hashes, scoped cook receipts and completed native tours into the handoff."""
import hashlib
import json
from pathlib import Path
import shutil
import sys

import yaml
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parents[1]
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from link_static_model_lods import read_glb


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    owned = read(HERE / 'ownership.json')
    ledger = read(HERE / 'ledger.json')
    validation = read(HERE / 'receipts/validation.json')
    installed = read(HERE / 'receipts/installed.json')
    designs = read(HERE / 'designs.json')
    acceptance = read(HERE / 'review/acceptance.json')
    assert len(owned) == len(installed) == len(validation) == 56
    assert all(len(groups) == 1 for groups in read(HERE / 'receipts/assembly.json').values())
    assert len(read(HERE / 'receipts/reimport.json')) == 56
    binary = read(HERE / 'receipts/final_native_binary.json')['sha256']
    native = {}
    accepted_runs = read(HERE / 'review/accepted_native_runs.json')
    for accepted_name, folder_name in accepted_runs.items():
        folder = Path(folder_name)
        run = read(folder / 'run.json')
        if run['status'] != 'completed':
            continue
        assert run['exit_code'] == 0 and run['binary_sha256'] == binary
        setting = next(s for s in run['request']['set'] if s.startswith('debug.screenshot_tour_path='))
        tour = Path(setting.split('=', 1)[1])
        name = tour.stem.removesuffix('_tour')
        assert name == accepted_name
        spec = yaml.safe_load(tour.read_text())
        images = [Path(spec['output_dir']) / f'{i + 1:02}-{shot["name"]}.png'
                  for i, shot in enumerate(spec['shots'])]
        assert all(f.exists() for f in images), name
        log = (folder / 'game.log').read_text()
        assert 'vendor=0x10de' in log and 'Renderer: OpenGL 3.3' in log
        for row in owned:
            assert not any(row['binding']['model'] in line and 'failed' in line.lower() for line in log.splitlines())
        destination = HERE / 'receipts/native' / name
        destination.mkdir(parents=True, exist_ok=True)
        for file in ['run.json', 'game.log']:
            shutil.copyfile(folder / file, destination / file)
        shutil.copyfile(tour, destination / 'tour.yml')
        native[name] = {'run': str(folder), 'receipt': str(destination.relative_to(HERE)),
                        'images': [str(f.relative_to(HERE)) for f in images], 'status': 'completed',
                        'image_sha256': {str(f.relative_to(HERE)): sha(f) for f in images},
                        'review': 'Visible solid components, identifiable colours, grounded silhouettes; metal readable in dim interiors.'}
        sheet = Image.new('RGB', (1440, ((len(images) + 1) // 2) * 405))
        draw = ImageDraw.Draw(sheet)
        for i, path in enumerate(images):
            im = Image.open(path)
            im.thumbnail((720, 405))
            x, y = i % 2 * 720, i // 2 * 405
            sheet.paste(im, (x, y))
            draw.text((x + 5, y + 5), path.stem, fill='white')
        sheet.save(HERE / f'review/native_{name}_contact.png')
    expected = {'coverage'} | {f'{kind}_{i}' for kind in ['indoor', 'outdoor'] for i in range(1, 6)}
    assert set(native) == expected, (set(native), expected)
    assert sum(len(r['images']) for r in native.values()) == 110
    coverage = read(HERE / 'review/native_coverage.json')['coverage']
    textures, groups, proposals = set(), {}, []
    bindings = {r['icon']: r for r in yaml.safe_load((ROOT / 'assets_dev/engine/world_items/items.yml').read_text())['items']}
    for index, row in enumerate(owned):
        icon = row['icon']
        export = HERE / ledger[icon]['source_export']
        source = ROOT / 'assets_source' / row['binding']['model']
        runtime = ROOT / 'assets_dev' / row['binding']['model']
        assert sha(export) == sha(source) == validation[icon]['sha256'] == acceptance[icon]['export_sha256']
        assert sha(runtime) == installed[icon]['runtime_sha256']
        assert sha(HERE / f'references/baseline/item_{icon}.glb') == ledger[icon]['baseline_sha256']
        assert all(bindings[icon][key] == value for key, value in row['binding'].items())
        doc, unused = read_glb(runtime)
        for im in doc['images']:
            texture = runtime.parent / im['uri']
            assert texture.exists()
            textures.add(texture)
        group_key = tuple(designs[icon][key] for key in ['construction', 'design', 'surface', 'trim'])
        groups.setdefault(group_key, []).append(icon)
        group_name = next(name for name, icons in coverage.items() if icon in icons)
        coverage_image = next(s for s in native['coverage']['images'] if group_name + '.png' in s)
        ledger[icon].update({'status': 'installed', 'defects': [], 'native_coverage': coverage_image,
                            'source_icon': row['icon_reference'], 'physical_assembly': 'one supported assembly',
                            'nominal_texels_per_metre': round(512 * 133.333333 / row['binding']['length']),
                            'native_reviews': [key for key, value in native.items()
                                               if any('/' + icon + '-' in s or '-' + icon + '-' in s for s in value['images'])]})
        low, high = validation[icon]['bounds_gltf']
        scale = row['binding']['length']
        bounds = [low[0] * scale, -high[2] * scale, low[1] * scale,
                  high[0] * scale, -low[2] * scale, high[1] * scale]
        proposals.append({**row['binding'], 'bounds': [round(n, 4) for n in bounds]})
    (HERE / 'ledger.json').write_text(json.dumps(ledger, indent=2) + '\n')
    (HERE / 'proposed_bindings_with_bounds.json').write_text(json.dumps({
        'note': 'Coordinator merge only; lengths and model/icon bindings unchanged. Engine-axis bounds from final LOD0.',
        'items': proposals}, indent=2) + '\n')
    handoff = {'status': 'installed_wip_worker_scope_complete', 'icons': 56,
               'families': {'bows_and_crossbows': 36, 'blasters': 5, 'wands': 15},
               'route': 'Blender component construction + built-in imagegen unlit UV atlas + semantic mixed PBR',
               'distinct_design_material_configurations': len(groups),
               'reused_matching_variants': [g for g in groups.values() if len(g) > 1],
               'base_triangles': sum(d['triangles'] for d in designs.values()),
               'max_base_triangles': max(d['triangles'] for d in designs.values()),
               'lod_chains': sum(len(d['lod_triangles']) > 1 for d in designs.values()),
               'one_material_per_model': True, 'texture_dimensions': [2048, 2048],
               'unique_runtime_textures': [{'path': str(p.relative_to(ROOT)), 'bytes': p.stat().st_size} for p in sorted(textures)],
               'source_glb_bytes': sum(r['source_bytes'] for r in installed.values()),
               'runtime_glb_bytes': sum(r['runtime_bytes'] for r in installed.values()),
               'meshy_identity': 'engine:weapons-ranged-magic', 'meshy_jobs': [], 'meshy_credits': 0,
               'imagegen_calls': 1, 'imagegen_prompt': 'textures/PROMPT.txt',
               'native_runs': native, 'native_captures': 110, 'representatives_in_both_world_types': 25,
               'native_binary': read(HERE / 'receipts/final_native_binary.json'),
               'suggested_length_changes': [], 'coordinator_bounds_updates': 'proposed_bindings_with_bounds.json',
               'binding_changes_applied_by_worker': False, 'renderer_material_deviations': [],
               'remaining_asset_defects': [], 'failures': [],
               'limits': ['Android cook/device rendering was outside this desktop worker validation.',
                          'Coordinator owns merging refreshed bounds into the shared manifest.',
                          'WIP only; no release promotion or global builds/cooks by this worker.'],
               'ledger': 'ledger.json', 'validation': 'receipts/validation.json', 'installs': 'receipts/installed.json'}
    (HERE / 'handoff.json').write_text(json.dumps(handoff, indent=2) + '\n')
    print('Handoff ready: 56 installed, 110 native captures, all final hashes and owned bindings preserved')


if __name__ == '__main__':
    main()
