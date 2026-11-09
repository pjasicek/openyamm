"""Build isolated terrain revisions through the editor while retaining verified native BModels.

Only the terrain changes here. The baseline ODM hash and every source OBJ are
verified before reusing geometry. A full source rebuild remains the delivery gate.
"""
import configparser
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

PROJECT = Path(__file__).resolve().parent
ROOT = PROJECT.parents[2]
OUTPUT = PROJECT/'review/desert_materials_v2'
STAGE = Path('/tmp/openyamm-mm5-desert-material-study')
CANONICAL = Path('/tmp/openyamm-mm5-castleview')


def write(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,indent=2)+'\n')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build():
    from build_native import table_rows,save_rows,TERRAIN_BASE
    from terrain_tiles import assign
    marker = STAGE/'terrain-study.json'
    if STAGE.exists():
        assert json.loads(marker.read_text())['project']=='mm5_castleview_kalindra'
    else:
        STAGE.mkdir()
        write(marker,{'project':'mm5_castleview_kalindra','purpose':'isolated desert material study'})
        assets = STAGE/'assets_dev'
        assets.mkdir()
        shutil.copytree(CANONICAL/'assets_dev/engine',assets/'engine',symlinks=True)
        (assets/'worlds').mkdir()
        for world in ['mm5','mm7','mm8']:
            shutil.copytree(CANONICAL/'assets_dev/worlds'/world,assets/'worlds'/world,symlinks=True)
    assets = STAGE/'assets_dev'
    settings = configparser.ConfigParser()
    settings.read(CANONICAL/'settings.ini')
    settings['assets']['root'] = str(assets)
    with (STAGE/'settings.ini').open('w') as stream:
        settings.write(stream)
    baseline = PROJECT/'implementation/runtime/worlds/mm5/maps/mm5_sw.odm'
    evidence = json.loads((PROJECT/'review/native/build.json').read_text())
    assert sha(baseline)==evidence['nativeSha256'],'Native baseline no longer matches its build evidence'
    geometry = json.loads((PROJECT/'implementation/source/mm5_sw.geometry.yml').read_text())
    for model in geometry['bmodels']:
        path = Path(model['source']['asset_path'])
        assert sha(path)==evidence['sourceObjSha256'][path.name],('Unbuilt geometry change',path)
    source = OUTPUT/'source'
    (source/'implementation').mkdir(parents=True,exist_ok=True)
    for folder in ['landscape']:
        link = source/folder
        if not link.exists():
            link.symlink_to((PROJECT/folder).resolve(),target_is_directory=True)
    for file in ['roads.json','architecture.json']:
        shutil.copy2(PROJECT/'implementation'/file,source/'implementation'/file)
    rows = table_rows(CANONICAL/'assets_dev/engine/data_tables/terrain_tile_data.txt')
    indexed = {int(row[0]):row for row in rows[1:] if row[0].isdigit()}
    palette = json.loads((PROJECT/'implementation/terrain_palette.json').read_text())['localTileByTexture']
    manifest = json.loads((OUTPUT/'manifest.json').read_text())
    for mask,record in manifest['variants'].items():
        if int(mask) in (0,15):
            continue
        key = f'mm5sd{int(mask):02d}'
        offset = palette[key]-90 if key in palette else len(palette)
        assert offset<144
        palette[key] = 90+offset
        row = indexed[TERRAIN_BASE+offset]
        assert row[1] in ('',key),row
        row[1:] = [key,'0','0','41',mask,'0x0200']
        texture = OUTPUT/record['path']
        assert sha(texture)==record['sha256']
        shutil.copy2(texture,assets/'worlds/mm5/textures'/texture.name)
    save_rows(assets/'engine/data_tables/terrain_tile_data.txt',rows)
    native_tiles = assign(palette,indexed,project=source)
    terrain = json.loads((PROJECT/'implementation/source/mm5_sw.terrain.yml').read_text())
    terrain['tile_map_hex'] = native_tiles.hex().upper()
    write(source/'mm5_sw.terrain.yml',terrain)
    for suffix in ['map.yml','scene.yml','geometry.yml']:
        shutil.copy2(PROJECT/'implementation/source'/('mm5_sw.'+suffix),source/('mm5_sw.'+suffix))
    # The editor explicitly supports loading existing native geometry and applying
    # terrain metadata. No binary offsets or ad-hoc ODM patcher are used.
    shutil.copy2(baseline,source/'mm5_sw.odm')
    with (OUTPUT/'native_build.log').open('w') as log:
        subprocess.run([str(ROOT/'build/editor/openyamm-editor'),'--asset-root',str(assets),'--world','mm5',
                        '--headless-build-map',str((source/'mm5_sw.map.yml').resolve())],
                       stdout=log,stderr=subprocess.STDOUT,check=True)
    sys.path.insert(0,str(ROOT/'util'))
    from map_export import parse_odm_file
    old = parse_odm_file(baseline)['payload']
    new = parse_odm_file(source/'mm5_sw.odm')['payload']
    for key in ['bmodels','entities','spawns','height_map','attribute_map']:
        assert new[key]==old[key],('Unexpected terrain-study change',key)
    assert bytes(new['tile_map'])==native_tiles
    for suffix in ['odm','scene.yml']:
        shutil.copy2(source/('mm5_sw.'+suffix),assets/'worlds/mm5/maps'/('mm5_sw.'+suffix))
    write(OUTPUT/'palette.json',palette)
    write(OUTPUT/'native_build.json',{'status':'isolated full-context terrain study; native visuals pending',
          'stage':str(STAGE),'nativeSha256':sha(source/'mm5_sw.odm'),
          'baselineNativeSha256':evidence['nativeSha256'],'bmodels':len(new['bmodels']),
          'reusedGeometry':'all source OBJ hashes verified; all native BModel records unchanged',
          'unchanged':['bmodels','entities','spawns','height_map','attribute_map'],
          'tileArrayMatchesSource':True,'paletteSlots':len(palette),'newDesertTextures':12,
          'limits':['geometry retained from verified native baseline; final delivery requires fresh full source build',
                    'source material artwork checks do not establish native appearance']})
    print('Isolated full-context native terrain study built:',STAGE)


if __name__=='__main__':
    build()
