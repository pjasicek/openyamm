"""Export selected terrain materials at x2; mixed tiles require the later mask pass."""

import hashlib
import json
from pathlib import Path
import shutil

from PIL import Image

PROJECT = Path(__file__).resolve().parent
OUTPUT = PROJECT / 'runtime_x2'
NATIVE_BASES = {'grass': '6grastyl', 'dirt': '6dirttyl', 'volcano': '6voltyl'}


def export_runtime():
    decisions = json.loads((PROJECT / 'material_decisions.json').read_text())
    materials = OUTPUT / 'materials'
    overrides = OUTPUT / 'overrides/worlds/mm6/terrain_x2'
    materials.mkdir(parents=True, exist_ok=True)
    overrides.mkdir(parents=True, exist_ok=True)
    records = {}
    for name in ['grass', 'dirt', 'cobbles', 'volcano']:
        selected = decisions[name]
        source = PROJECT / selected['master_png']
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        if digest != selected['master_sha256']:
            raise ValueError(f'Selected {name} master changed: {source}')
        target = materials / (name + '.png')
        with Image.open(source) as image:
            if image.size != (512, 512):
                raise ValueError(f'Expected 512px authoring master: {source}')
            image.convert('RGB').resize((256, 256), Image.Resampling.LANCZOS).save(target)
        record = {
            'version': selected['version'], 'role': selected['role'],
            'source': selected['master_png'], 'source_sha256': digest,
            'png': str(target.relative_to(OUTPUT)),
            'sha256': hashlib.sha256(target.read_bytes()).hexdigest(),
        }
        if name in NATIVE_BASES:
            override = overrides / (NATIVE_BASES[name] + '.png')
            shutil.copy2(target, override)
            record['native_override'] = str(override.relative_to(OUTPUT))
        else:
            record['underlying_material'] = 'dirt'
            record['usage'] = 'Cobble material for road-mask composition only; never replace a full road tile with it.'
        records[name] = record
    manifest = {
        'world': 'mm6', 'reference_map': 'oute3.odm', 'terrain_tier': 'x2',
        'runtime_size': [256, 256], 'authoring_size': [512, 512],
        'resampling': 'Lanczos; no repainting or colour correction',
        'source_paths_relative_to': 'parent directory of runtime_x2',
        'materials': records,
        'composition': 'Compose mixed tiles and road masks at 512px, then downsample each finished tile to 256px.',
        'scope': 'Master-only export; complete connected land pack lives in ../mm6_new_sorpigal_transitions/runtime_x2',
        'incomplete': ['Water/shore work'],
    }
    (OUTPUT / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    (OUTPUT / 'README.md').write_text(f'''# Runtime terrain materials — x2

Four selected materials, exported at **256×256 RGB PNG** from the unchanged 512×512 authoring masters.

- `materials/grass.png`: grass v1.
- `materials/dirt.png`: dirt {decisions['dirt']['version']}.
- `materials/cobbles.png`: cobbles v1, for masked composition over dirt.
- `materials/volcano.png`: volcanic rock v2, retained with the earlier brightness note.

`overrides/worlds/mm6/terrain_x2/` contains only the three standalone native base replacements.
There is deliberately no full-tile cobble replacement. This is a partial base-material export, not a finished
terrain pack. Complete connected land and roads are in the sibling transition project; shoreline and water remain pending. No original runtime assets were installed
or overwritten by this export. The runtime terrain setting for these files is `x2`.

Build the final mixed tiles from the 512px masters and masks, then downsample the completed composites to 256px.
The standalone 256px cobble file is a runtime-sized material reference; use its 512px master for authoring roads.

`manifest.json` records selected versions, source and output hashes, roles and paths. Rebuild from the repository root:

```sh
python3 level_generation/terrain/mm6_new_sorpigal_master_study/export_runtime.py
```
''')
    print(f'Exported four 256px materials and three native base overrides to {OUTPUT}')
    return manifest


if __name__ == '__main__':
    export_runtime()
