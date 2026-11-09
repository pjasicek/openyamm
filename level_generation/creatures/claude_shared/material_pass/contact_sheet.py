#!/usr/bin/env python3
"""Contact sheets for the material pass batch: per model, old (backup_pre_material_pass/) and new (batch/), front
view, under the neutral key light ("sun": white sun and sky world) and the dim indoor light (warm torch, dark room)
of render_material_views.py, eight models per page.
Each GLB is prepared first: the default (tier A) material's region ramps are baked into its base colour image with
the shader's maths (tier_textures.py), since Blender does not apply them; the importer's materials are kept and
their Specular IOR Level wired from openyamm_specular (and the red channel with the mask).
Usage: contact_sheet.py [name ...]   (default: every processed model in batch/batch_results.json)
Writes batch/contact_sheet_NN.png; renders are cached in batch/contact_work/."""
import io
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import region_variants as RV  # noqa: E402
import tier_textures as TT  # noqa: E402

OUT = HERE / 'batch'
WORK = OUT / 'contact_work'
BACKUP = HERE / 'backup_pre_material_pass'
SIZE, LABEL, PER_PAGE, COLUMNS = 300, 20, 8, 2
CELLS = (('old', 'sun', 'old, key'), ('new', 'sun', 'new, key'), ('old', 'indoor', 'old, indoor'),
         ('new', 'indoor', 'new, indoor'))


def prepare(source, prefix):
    doc, binary = RV.read_glb(source)
    binary = bytes(binary)
    defaults = {p.get('material') for m in doc['meshes'] for p in m['primitives']} - {None}
    baked = set()
    for index in sorted(defaults):
        material = doc['materials'][index]
        pbr, extras = material.get('pbrMetallicRoughness', {}), material.get('extras', {})
        if 'baseColorTexture' not in pbr or not extras.get('openyamm_region_ramps'):
            continue
        image_index = doc['textures'][pbr['baseColorTexture']['index']]['source']
        if image_index in baked:
            continue
        baked.add(image_index)

        def load(texture):
            entry = doc['images'][doc['textures'][texture]['source']]
            view = doc['bufferViews'][entry['bufferView']]
            start = view.get('byteOffset', 0)
            return Image.open(io.BytesIO(binary[start:start + view['byteLength']]))
        base = load(pbr['baseColorTexture']['index'])
        alpha = base.getchannel('A') if base.mode == 'RGBA' else None
        rgb = np.asarray(base.convert('RGB'), np.float64) / 255
        bands = load(extras['openyamm_region_mask']['index']).convert('RGBA').split()
        size = base.size
        mask = np.stack([np.asarray(b if b.size == size else b.resize(size, Image.BILINEAR), np.float64) / 255
                         for b in bands], -1)
        image = Image.fromarray((np.clip(TT.apply(rgb, mask, extras['openyamm_region_ramps']), 0, 1) * 255
                                 + 0.5).astype(np.uint8))
        if alpha is not None:
            image.putalpha(alpha)
        buffer = io.BytesIO()
        image.save(buffer, 'PNG')
        data = buffer.getvalue()
        binary += b'\0' * (-len(binary) % 4)
        doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(data)})
        binary += data
        doc['images'][image_index]['bufferView'] = len(doc['bufferViews']) - 1
        doc['images'][image_index]['mimeType'] = 'image/png'
    doc, binary = RV._compact(doc, binary)
    RV.write_glb(f'{prefix}.glb', doc, binary)
    patch = {m['name']: {'specular': float(m.get('extras', {}).get('openyamm_specular', 1.0)),
                         'specular_mask': bool(m.get('extras', {}).get('openyamm_specular_mask', False))}
             for m in doc['materials']}
    job = {'glb': f'{prefix}.glb', 'patch_materials': patch, 'lights': ['sun', 'indoor'], 'views': ['front'],
           'out_prefix': prefix, 'size': SIZE, 'front': '-y'}
    Path(f'{prefix}_job.json').write_text(json.dumps(job, indent=1))
    return f'{prefix}_job.json'


def render(name):
    for label, source in (('old', BACKUP / f'{name}.glb'), ('new', OUT / f'{name}.glb')):
        prefix = WORK / f'{name}_{label}'
        if Path(f'{prefix}_indoor_front.png').exists() and Path(f'{prefix}_indoor_front.png').stat().st_mtime \
                > source.stat().st_mtime:
            continue
        job = prepare(source, str(prefix))
        subprocess.run(['blender', '--background', '--python', str(HERE / 'render_material_views.py'), '--', job],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        Path(f'{prefix}.glb').unlink()


def main():
    WORK.mkdir(parents=True, exist_ok=True)
    results = json.loads((OUT / 'batch_results.json').read_text())
    names = sys.argv[1:] or [r['name'] for r in results if r['status'].startswith('processed')]
    info = {r['name']: r for r in results}
    for name in names:
        print('RENDER', name, flush=True)
        render(name)
    block_w, block_h = SIZE * len(CELLS), SIZE + 2 * LABEL
    for page in range(0, len(names), PER_PAGE):
        chunk = names[page:page + PER_PAGE]
        rows = (len(chunk) + COLUMNS - 1) // COLUMNS
        sheet = Image.new('RGB', (block_w * COLUMNS + 8 * (COLUMNS - 1), block_h * rows), (16, 16, 16))
        draw = ImageDraw.Draw(sheet)
        for i, name in enumerate(chunk):
            x, y = (i % COLUMNS) * (block_w + 8), (i // COLUMNS) * block_h
            keep = '; '.join(f"keep {', '.join(v)}" for v in info.get(name, {}).get('keep', {}).values() if v)
            flags = '  FLAG: ' + '; '.join(info[name]['flags']) if info.get(name, {}).get('flags') else ''
            draw.text((x + 4, y + 3), f'{name}  {keep}{flags}', fill=(255, 220, 120) if not flags else (255, 120, 90))
            for c, (label, light, text) in enumerate(CELLS):
                cell = Image.open(WORK / f'{name}_{label}_{light}_front.png').convert('RGB')
                sheet.paste(cell, (x + c * SIZE, y + 2 * LABEL))
                draw.text((x + c * SIZE + 4, y + LABEL + 3), text, fill=(200, 200, 200))
        path = OUT / f'contact_sheet_{page // PER_PAGE + 1:02d}.png'
        sheet.save(path)
        print('WROTE', path)


if __name__ == '__main__':
    main()
