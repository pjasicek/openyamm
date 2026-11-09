"""MM5 terrain material additions, composed into the isolated global base.

The acid artwork is an unchanged MM8 bitmap. Separate aliases and a separate
tileset keep its liquid base out of the river's animated blue-water bank.
"""
import hashlib
import json
from pathlib import Path
import shutil

import yaml

PROJECT = Path(__file__).resolve().parent
ROOT = PROJECT.parents[2]
ACID_TILESET = 40
ACID_BASE = 'mm5acid'
ACID_VARIANTS = range(12, 24)
DESERT_ART = PROJECT/'implementation/art/desert_terrain'
DESERT_MASKS = [1,2,3,4,5,7,8,10,11,12,13,14]


def acid_name(variant):
    return ACID_BASE if variant == 0 else f'mm5ac{variant:02d}'


def append_rows(unique, indexed):
    # Append after existing entries so previously assigned local selectors stay stable.
    for index in range(198, 222):
        row = indexed[index]
        unique.setdefault(row[1].lower(), list(row))
    for variant in [0, *ACID_VARIANTS]:
        row = list(indexed[126 + variant])
        row[1] = acid_name(variant)
        row[4] = str(ACID_TILESET)
        row[5] = str(variant)
        unique[row[1]] = row
    for bits in DESERT_MASKS:
        key = f'mm5sd{bits:02d}'
        unique[key] = ['0',key,'0','0','41',str(bits),'0x0200']


def prepare(assets, runtime, indexed):
    texture_paths = {p.stem.lower(): p for p in (ROOT/'assets_dev/worlds/mm8/textures').iterdir()
                     if p.is_file()}
    target = runtime/'textures'
    target.mkdir(parents=True, exist_ok=True)
    provenance = []
    for variant in [0, *ACID_VARIANTS]:
        key = 'slimywtr' if variant == 0 else indexed[126 + variant][1].lower()
        source = texture_paths[key]
        destination = target/(acid_name(variant) + '.bmp')
        shutil.copy2(source, destination)
        provenance.append({'texture': acid_name(variant), 'donor': str(source.relative_to(ROOT)),
                           'sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
                           'operation': 'byte-identical copy under a world-specific texture alias'})
    desert = json.loads((DESERT_ART/'manifest.json').read_text())
    for donor in desert['donors'].values():
        assert hashlib.sha256((ROOT/donor['path']).read_bytes()).hexdigest()==donor['sha256']
    for bits in DESERT_MASKS:
        record = desert['variants'][str(bits)]
        source = DESERT_ART/record['path']
        assert hashlib.sha256(source.read_bytes()).hexdigest()==record['sha256'],source
        shutil.copy2(source,target/source.name)
        provenance.append({'texture':source.stem,'donor':str(source.relative_to(ROOT)),
                           'sha256':record['sha256'],'operation':'reviewed Blender shader bake; native sand/dirt donors',
                           'materialManifest':str((DESERT_ART/'manifest.json').relative_to(PROJECT))})
    addition = {'id': 'mm5_acid_pond', 'semantic': 'water', 'applies_to': ['terrain'],
                'match': {'texture_names': [ACID_BASE], 'texture_prefixes': ['mm5ac']},
                'terrain_transition_overlay': True}
    # No fabricated animation frames: the existing liquid material implementation
    # scrolls a static base beneath its stationary keyed shore overlay.
    fragment = PROJECT/'implementation/surface_materials_append.yml'
    fragment.write_text(yaml.safe_dump({'materials': [addition]}, sort_keys=False))
    source = ROOT/'assets_dev/engine/rendering/surface_materials.yml'
    composed = yaml.safe_load(source.read_text())
    assert all(m['id'] != addition['id'] for m in composed['materials'])
    composed['materials'].append(addition)
    destination = assets/'engine/rendering/surface_materials.yml'
    destination.parent.mkdir(parents=True, exist_ok=True)
    assert not destination.is_symlink(), destination
    destination.write_text(yaml.safe_dump(composed, sort_keys=False))
    report = {'acidTileset': ACID_TILESET, 'acidBase': ACID_BASE,
              'acidAnimation': 'existing static-liquid scrolling with stationary native shore overlays',
              'scorchedBank': {'world': 'mm8', 'base': 'voltyl', 'sourceRows': [198, 221]},
              'desertTileset':41,'desertMaterialManifest':str((DESERT_ART/'manifest.json').relative_to(PROJECT)),
              'textures': provenance, 'registryFragment': str(fragment.relative_to(PROJECT)),
              'baseSurfaceRegistrySha256': hashlib.sha256(source.read_bytes()).hexdigest(),
              'scope': 'isolated composed base; repository MM6/MM7/MM8 registries and artwork unchanged'}
    (PROJECT/'implementation/terrain_materials.json').write_text(json.dumps(report, indent=2)+'\n')
