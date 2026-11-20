"""Build the pilot map into the isolated stage (playtest/assets_dev), never into assets_dev.

  python3 source/build.py [--map S]             generate, append, update the scene, stage (removes stale lighting)
  python3 source/build.py [--map S] --bake [N]  bake the staged map's lighting (N samples, default 16), install it
  python3 source/build.py [--map S] --original  bake the unchanged map with the same tool into playtest/rebake,
                                                the fair "before" for every comparison (64 samples)

The original ODM records stay byte-identical except the attribute word of the hidden faces (Invisible added: they
keep their collision but are not drawn, clicked or baked). The new detail models are appended after every original
BModel, so all original model and face indices, events and scene records keep their meaning.
"""
import argparse
import hashlib
import json
import os
import shutil
import struct
import subprocess
import sys
from pathlib import Path

import yaml

PROJECT = Path(__file__).resolve().parents[1]
ROOT = PROJECT.parents[2]
STAGE = PROJECT / 'playtest/assets_dev'
STAGE_MAPS = STAGE / 'worlds/mm6/maps'
REBAKE = PROJECT / 'playtest/rebake/assets_dev'
sys.path.insert(0, str(ROOT / 'util'))
sys.path.insert(0, str(PROJECT / 'source'))
import map_export as odm  # noqa: E402
import maps  # noqa: E402

INVISIBLE = 0x2000
FACE_ATTRIBUTES_OFFSET = 0x1c


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def replace_file(source_bytes, destination):
    """Write through a temporary file and rename: stage files are hard links shared with assets_dev."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(destination.name + '.pilot-tmp')
    temporary.write_bytes(source_bytes)
    os.replace(temporary, destination)


def layout(data):
    count = odm.TERRAIN_SECTION_OFFSET_V8 + 3 * odm.TERRAIN_MAP_SIZE
    count += 4 + odm.CMAP1_SIZE + odm.CMAP2_SIZE + 12 * data['terrain_normal_count']
    headers = count + 4
    bodies = headers + odm.BMODEL_HEADER_SIZE * data['bmodel_count']
    ends = [bodies]
    face_offsets = []
    for model in data['bmodels']:
        start = ends[-1] + model['vertex_count'] * odm.BMODEL_VERTEX_SIZE
        face_offsets.append([start + i * odm.BMODEL_FACE_SIZE for i in range(model['face_count'])])
        ends.append(ends[-1] + model['vertex_count'] * odm.BMODEL_VERTEX_SIZE
                    + model['face_count'] * (odm.BMODEL_FACE_SIZE + odm.BMODEL_FACE_FLAGS_SIZE
                                              + odm.BMODEL_TEXTURE_NAME_SIZE)
                    + model['bsp_node_count'] * odm.BMODEL_BSP_NODE_SIZE)
    return count, headers, bodies, ends, face_offsets


def splice(base, candidate, original, generated, hidden):
    """Original bytes verbatim + the new models' headers and bodies from the native writer."""
    assert original['version'] == 8
    count, headers, bodies, ends, face_offsets = layout(original)
    new_count, new_headers, new_bodies, new_ends, _ = layout(generated)
    assert count == new_count
    old = original['bmodel_count']
    out = bytearray(base[:count] + struct.pack('<I', generated['bmodel_count']) + base[headers:bodies]
                    + candidate[new_headers + old * odm.BMODEL_HEADER_SIZE:new_bodies]
                    + base[bodies:ends[-1]] + candidate[new_ends[old]:new_ends[-1]] + base[ends[-1]:])
    shift = (generated['bmodel_count'] - old) * odm.BMODEL_HEADER_SIZE
    for model_index, faces in hidden.items():
        for face_index in faces:
            offset = face_offsets[model_index][face_index] + shift + FACE_ATTRIBUTES_OFFSET
            value = struct.unpack_from('<I', out, offset)[0]
            struct.pack_into('<I', out, offset, value | INVISIBLE)
    return bytes(out)


def update_scene(text, compiled, base_count, hidden):
    """Hide the original faces (legacy_attributes) and add one record per new face, before `entities:`."""
    lines = text.split('\n')
    current = None
    changed = 0
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith('- bmodel_index: '):
            current = [int(stripped.split(': ')[1]), None]
        elif current is not None and stripped.startswith('face_index: ') and line.startswith('      '):
            current[1] = int(stripped.split(': ')[1])
        elif current is not None and stripped.startswith('legacy_attributes: ') and line.startswith('      '):
            model, face = current
            if face in hidden.get(model, ()):
                value = int(stripped.split(': ')[1]) | INVISIBLE
                lines[i] = line[:line.index('legacy_attributes: ')] + f'legacy_attributes: {value}'
                changed += 1
            current = None
        elif not line.startswith(' '):
            current = None
    expected = sum(len(v) for v in hidden.values())
    assert changed == expected, (changed, expected)
    records = []
    for model in compiled['bmodels'][base_count:]:
        for face in model['faces']:
            records.append(f"    - bmodel_index: {model['index']}\n      face_index: {face['index']}\n"
                           f"      legacy_attributes: {face['attributes']}\n      cog_number: 0\n"
                           f"      cog_triggered_number: {face['cog_triggered_number']}\n      cog_trigger: 0\n")
    result = '\n'.join(lines)
    assert result.count('\nentities:\n') == 1
    result = result.replace('\nentities:\n', '\n' + ''.join(records) + 'entities:\n')
    scene = yaml.load(result, Loader=yaml.CSafeLoader)
    faces = scene['bmodel_faces']['interactive_faces']
    assert sum(1 for f in faces if f['bmodel_index'] >= base_count) == sum(
        len(m['faces']) for m in compiled['bmodels'][base_count:])
    return result


def cook_project_textures():
    """The project's own textures (source/make_textures.py) cooked into the stage only."""
    sources = PROJECT / 'textures/root'
    stems = sorted(p.stem for p in (sources / 'worlds/mm6/textures_x4').glob('*.png'))
    only = [arg for stem in stems for arg in ('--only', f'mm6/{stem}')]
    if not stems:
        return
    subprocess.run(['python3', str(ROOT / 'tools/cook_surface_textures.py'), '--sources', str(sources),
                    '--output', str(STAGE), '--world', 'mm6', *only], check=True)
    subprocess.run(['python3', str(ROOT / 'tools/surface_materials.py'), 'cook', '--sources', str(sources),
                    '--output', str(STAGE), '--world', 'mm6', *only], check=True)


def stage(path=STAGE):
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(['cp', '-al', str(ROOT / 'assets_dev'), str(path)], check=True)


def profile_of(stem):
    """The map's bake profile: the shared profile file when there is one, else the one its installed bake used."""
    path = ROOT / 'tools/lighting/baked_outdoors/profiles' / f'mm6_{stem}.yml'
    if path.exists():
        return yaml.safe_load(path.read_text())
    return json.loads((ROOT / 'assets_dev/worlds/mm6/maps' / f'{stem}.bake.json').read_text())['profile']


def bake(stem, settings, output, assets, samples):
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)
    profile = output / 'profile.json'
    profile.write_text(json.dumps(settings, indent=2) + '\n')
    with open(output / 'blender.log', 'w') as log:
        subprocess.run(['blender', '--background', '--factory-startup', '--python-exit-code', '1', '--python',
                        str(ROOT / 'tools/lighting/bake_outdoor.py'), '--',
                        '--profile', str(profile),
                        '--output', str(output), '--assets', str(assets), '--sources', str(ROOT / 'assets_source'),
                        '--sources', str(PROJECT / 'textures/root'),
                        '--samples', str(samples)], cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--map', default='oute3')
    parser.add_argument('--bake', type=int, nargs='?', const=16)
    parser.add_argument('--original', action='store_true')
    parser.add_argument('--kit', help='prototype: the silhouette kit on these BModels only (comma-separated)')
    args = parser.parse_args()
    stem = args.map
    BUILD = maps.build(stem)
    BUILD.mkdir(parents=True, exist_ok=True)
    if args.original:
        stage(REBAKE)
        bake(stem, profile_of(stem), BUILD / 'rebake_original', REBAKE, 64)
        for suffix in ('.lighting', '.bake.json'):
            replace_file((BUILD / 'rebake_original' / (stem + suffix)).read_bytes(),
                         REBAKE / 'worlds/mm6/maps' / (stem + suffix))
        print('Re-baked the unchanged map into', REBAKE)
        return
    if args.bake:
        # The map's own profile, with a finer lightmap for the detail models.
        settings = profile_of(stem)
        plan = json.loads((BUILD / 'plan.json').read_text())
        settings['model_units_per_texel'] = {b['model_name'] + '_geo': b['units_per_texel'] for b in plan['buildings']}
        # Review bakes clamp the rare over-range texels (light leaking into a recess) instead of failing; the counts
        # are in bake/stats and the raw pages in bake/*.npy (trace them with source/find_texels.py).
        settings['clamp_rgbm'] = True
        bake(stem, settings, BUILD / 'bake', STAGE, args.bake)
        for suffix in ('.lighting', '.bake.json'):
            replace_file((BUILD / 'bake' / (stem + suffix)).read_bytes(), STAGE_MAPS / (stem + suffix))
        print('Installed the bake into the stage.')
        return
    venv_python = PROJECT / 'venv/bin/python'
    subprocess.run([str(venv_python), str(PROJECT / 'source/generate.py'), '--map', stem]
                   + (['--kit', args.kit] if args.kit else []), check=True)
    plan = json.loads((BUILD / 'plan.json').read_text())
    base_path = ROOT / plan['map']
    tool = BUILD / 'odmtool'
    subprocess.run(['c++', '-std=c++20', '-O2', '-I', str(ROOT), str(PROJECT / 'source/odmtool.cpp'),
                    str(ROOT / 'game/outdoor/OutdoorMapData.cpp'), '-o', str(tool)], check=True)
    candidate = BUILD / 'candidate.odm'
    subprocess.run([str(tool), 'append', str(base_path), str(BUILD / 'models.txt'), str(candidate)], check=True)
    original = odm.parse_odm_file(base_path)['payload']
    generated = odm.parse_odm_file(candidate)['payload']
    hidden = {b['bmodel']: b['hidden_faces'] for b in plan['buildings']}
    result = splice(base_path.read_bytes(), candidate.read_bytes(), original, generated, hidden)
    (BUILD / f'{stem}.odm').write_bytes(result)
    compiled = odm.parse_odm_file(BUILD / f'{stem}.odm')['payload']
    # Every original record is unchanged apart from the hidden faces' Invisible bit.
    for model_old, model_new in zip(original['bmodels'], compiled['bmodels']):
        assert model_old['vertices'] == model_new['vertices']
        for face_old, face_new in zip(model_old['faces'], model_new['faces']):
            expected = face_old['attributes'] | (INVISIBLE if face_old['index'] in hidden.get(model_old['index'], ())
                                                 else 0)
            assert face_new['attributes'] == expected
            for key in ('vertex_indices', 'texture_us', 'texture_vs', 'texture_name', 'cog_triggered_number'):
                assert face_old[key] == face_new[key]
    assert compiled['entities'] == original['entities']
    scene = update_scene(base_path.with_suffix('.scene.yml').read_text(), compiled, len(original['bmodels']), hidden)
    (BUILD / f'{stem}.scene.yml').write_text(scene)
    stage()
    replace_file((BUILD / f'{stem}.odm').read_bytes(), STAGE_MAPS / f'{stem}.odm')
    replace_file(scene.encode(), STAGE_MAPS / f'{stem}.scene.yml')
    for suffix in ('.lighting', '.bake.json'):
        (STAGE_MAPS / (stem + suffix)).unlink(missing_ok=True)
    cook_project_textures()
    report = {'base_map_sha256': digest(base_path), 'map_sha256': digest(BUILD / f'{stem}.odm'),
              'scene_sha256': digest(BUILD / f'{stem}.scene.yml'), 'buildings': plan['buildings']}
    (BUILD / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print('Staged', STAGE_MAPS / f'{stem}.odm', '(lighting removed: bake, then --lighting)')


if __name__ == '__main__':
    main()
