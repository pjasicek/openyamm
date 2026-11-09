"""Compile the isolated rim experiment with nearby authored context and unchanged native terrain."""
import configparser
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

from PIL import Image

PROJECT = Path(__file__).resolve().parent
ROOT = PROJECT.parents[2]
OUTPUT = PROJECT/'review/rim_geometry_study_v5'
STAGE = Path('/tmp/openyamm-mm5-rim-geometry-study')
CANONICAL = Path('/tmp/openyamm-mm5-castleview')


def write(path, value):
    path.write_text(json.dumps(value, indent=2)+'\n')


def build():
    marker = STAGE/'rim-study.json'
    if STAGE.exists():
        assert json.loads(marker.read_text())['owner'] == 'mm5_castleview_kalindra'
    else:
        STAGE.mkdir()
        write(marker, {'owner': 'mm5_castleview_kalindra', 'purpose': 'Isolated rim experiment, not final world'})
        assets = STAGE/'assets_dev'
        assets.mkdir()
        shutil.copytree(CANONICAL/'assets_dev/engine', assets/'engine', symlinks=True)
        (assets/'worlds').mkdir()
        for world in ['mm5', 'mm7', 'mm8']:
            shutil.copytree(CANONICAL/'assets_dev/worlds'/world, assets/'worlds'/world, symlinks=True)
    assets = STAGE/'assets_dev'
    settings = configparser.ConfigParser()
    settings.read(CANONICAL/'settings.ini')
    settings['assets']['root'] = str(assets)
    with (STAGE/'settings.ini').open('w') as stream:
        settings.write(stream)
    Image.new('RGBA', (128, 128), (0, 0, 0, 0)).save(assets/'worlds/mm5/textures/mm5void.png')
    source = OUTPUT/'native_source'
    source.mkdir(exist_ok=True)
    (source/'models').mkdir(exist_ok=True)
    geometry = json.loads((OUTPUT/'mm5_sw.geometry.yml').read_text())
    rim_count = len(geometry['bmodels'])
    baseline = json.loads((PROJECT/'implementation/source/mm5_sw.geometry.yml').read_text())
    semantic = json.loads((PROJECT/'implementation/source/mm5_sw.semantic.json').read_text())
    context = {'reger', 'reger_crossing', 'source_4_2_7'}
    indices = [m['index'] for m in semantic['bmodels'] if m['assembly'] in context]
    geometry['bmodels'].extend(baseline['bmodels'][i] for i in indices)
    hashes = {}
    for i, model in enumerate(geometry['bmodels']):
        original = Path(model['source']['asset_path'])
        target = source/'models'/original.name
        shutil.copy2(original, target)
        hashes[target.name] = hashlib.sha256(target.read_bytes()).hexdigest()
        model['runtime_bmodel_index'] = i
        model['source']['asset_path'] = str(target)
    write(source/'mm5_sw.geometry.yml', geometry)
    scene = json.loads((PROJECT/'implementation/source/mm5_sw.scene.yml').read_text())
    overrides = json.loads((OUTPUT/'face_overrides.json').read_text())
    scene['bmodel_faces']['interactive_faces'] = overrides
    write(source/'mm5_sw.scene.yml', scene)
    for suffix in ['map.yml', 'terrain.yml']:
        shutil.copy2(PROJECT/'implementation/source'/('mm5_sw.'+suffix), source/('mm5_sw.'+suffix))
    with (OUTPUT/'native_build.log').open('w') as log:
        subprocess.run([str(ROOT/'build/editor/openyamm-editor'), '--asset-root', str(assets), '--world', 'mm5',
                        '--headless-build-map', str(source/'mm5_sw.map.yml')], stdout=log,
                       stderr=subprocess.STDOUT, check=True)
    for suffix in ['odm', 'scene.yml']:
        shutil.copy2(source/('mm5_sw.'+suffix), assets/'worlds/mm5/maps'/('mm5_sw.'+suffix))
    sys.path.insert(0, str(ROOT/'util'))
    from map_export import parse_odm_file
    native_path = assets/'worlds/mm5/maps/mm5_sw.odm'
    native = parse_odm_file(native_path)['payload']
    terrain = json.loads((source/'mm5_sw.terrain.yml').read_text())
    for field in ['height_map', 'tile_map', 'attribute_map']:
        assert bytes(native[field]) == bytes.fromhex(terrain[field+'_hex'])
    for override in overrides:
        face = native['bmodels'][override['bmodel_index']]['faces'][override['face_index']]
        expected = override['legacy_attributes']
        assert face['attributes'] & (0x20002004) == expected
        assert face['cog_triggered_number'] == 0
    assert not native['spawns'] and not scene['initial_state']['actors']
    report = {'status': 'Isolated native rim compiled; game visual/movement review pending',
              'stage': str(STAGE), 'nativeSha256': hashlib.sha256(native_path.read_bytes()).hexdigest(),
              'baselineNativeSha256': json.loads((PROJECT/'review/native/build.json').read_text())['nativeSha256'],
              'rimModels': rim_count, 'contextModels': len(indices), 'nativeModels': len(native['bmodels']),
              'boundaryFaces': sum(o['legacy_attributes'] == 0x2000 for o in overrides),
              'spillFaces': sum(o['legacy_attributes'] == 0x20000004 for o in overrides),
              'terrainArraysUnchanged': True, 'sourceObjSha256': hashes,
              'contextAssemblies': sorted(context), 'actors': 0, 'spawns': 0,
              'limits': ['Only rim and named nearby BModels are compiled; this is not a full-region completion build.',
                         'Existing scenery is retained; no new actors or gameplay effects.',
                         'Readback flags do not establish actual blocking or visual quality.']}
    write(OUTPUT/'native_build.json', report)
    print({k: v for k, v in report.items() if k not in ['sourceObjSha256', 'limits']})


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--review-version', default='rim_geometry_study_v5')
    OUTPUT = PROJECT/'review'/parser.parse_args().review_version
    build()
