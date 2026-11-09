"""Keep the painted weapon identity; make steel, paint, ivory and indicator-lens PBR regions explicit."""
import io
import json
from pathlib import Path
import sys

import numpy as np
from PIL import Image

P = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(P.parents[2] / 'tools'))
from build_actor_lods import read_glb, write_glb
from normal_map_convention import convert
from prepare_actor_glb import omit_mesh_nodes
sys.path.insert(0, str(P.parents[2] / 'level_generation/decorations/mm8_3d/animated/scripts'))
from check_winding import array


def uv_positions(doc, binary):
    result = np.full((1024, 1024, 3), np.nan)
    for mesh in doc['meshes']:
        for pr in mesh['primitives']:
            points = array(doc, binary, pr['attributes']['POSITION'])
            uv = array(doc, binary, pr['attributes']['TEXCOORD_0']) * 1023
            for tri in array(doc, binary, pr['indices']).reshape(-1, 3):
                a, b, c = uv[tri]
                lo = np.maximum(np.floor(np.min(uv[tri], axis=0)).astype(int), 0)
                hi = np.minimum(np.ceil(np.max(uv[tri], axis=0)).astype(int), 1023)
                yy, xx = np.mgrid[lo[1]:hi[1]+1, lo[0]:hi[0]+1]
                delta = np.stack([xx, yy], -1) - a
                u, v = b-a, c-a
                den = u[0]*v[1] - u[1]*v[0]
                if abs(den) < 1e-8:
                    continue
                w1 = (delta[..., 0]*v[1] - delta[..., 1]*v[0]) / den
                w2 = (u[0]*delta[..., 1] - u[1]*delta[..., 0]) / den
                w0 = 1-w1-w2
                mask = (w0 >= -1e-4) & (w1 >= -1e-4) & (w2 >= -1e-4)
                interpolated = w0[..., None]*points[tri[0]] + w1[..., None]*points[tri[1]] + w2[..., None]*points[tri[2]]
                result[yy[mask], xx[mask]] = interpolated[mask]
    assert np.isfinite(result).any()
    return result


def main():
    owned = {r['icon'] for r in json.loads((P / 'ownership.json').read_text())}
    for icon in sys.argv[1:] or sorted(owned):
        assert icon in owned
        doc, binary = read_glb(P / 'work/meshy' / f'{icon}_raw.glb')
        assert len(doc['materials']) == 1
        mat = doc['materials'][0]
        pbr = mat['pbrMetallicRoughness']
        slots = {'base': pbr['baseColorTexture']['index'], 'mr': pbr['metallicRoughnessTexture']['index'],
                 'normal': mat['normalTexture']['index']}
        pixels = {}
        for role, texture in slots.items():
            index = doc['textures'][texture]['source']
            image = doc['images'][index]
            view = doc['bufferViews'][image['bufferView']]
            offset = view.get('byteOffset', 0)
            im = Image.open(io.BytesIO(binary[offset:offset+view['byteLength']])).convert('RGB')
            pixels[role] = np.array(im.resize((1024, 1024), Image.Resampling.LANCZOS))
        base = pixels['base'] = np.clip(pixels['base'], 30, 243)
        r, g, b = [base[..., i].astype(float) for i in range(3)]
        red = (r > g*1.35) & (r > b*1.3) & (g < b*1.8)
        lens = ((g > r*1.25) & (g > b*1.08)) | ((b > r*1.3) & (b > g*.95))
        nonmetal = red | lens
        ivory = np.zeros(red.shape, bool)
        if icon == 'raygun1':
            positions = uv_positions(doc, binary)
            along = -positions[..., 2]
            low, high = np.nanmin(along), np.nanmax(along)
            # The ivory is the off-axis lower grip, not the neutral silver barrel.
            ivory = (along < low + .27*(high-low)) & (positions[..., 0] > .045) & (r > 100) & (g > 95) & (b > 70) & (r/b < 1.65)
            nonmetal |= ivory
        mr = pixels['mr']
        mr[..., 0] = 255
        mr[..., 2] = np.where(nonmetal, 0, 255)
        mr[..., 1] = np.clip(mr[..., 1], 110, 185)
        mr[..., 1][red | ivory] = 165
        mr[..., 1][lens] = 95
        payload = bytearray(binary)
        for role, texture in slots.items():
            image = doc['images'][doc['textures'][texture]['source']]
            output = io.BytesIO()
            Image.fromarray(pixels[role]).save(output, format='PNG')
            png = output.getvalue()
            payload.extend(b'\0' * (-len(payload) % 4))
            image.update({'bufferView': len(doc['bufferViews']), 'mimeType': 'image/png', 'name': icon+'_'+role})
            doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(payload), 'byteLength': len(png)})
            payload.extend(png)
        mat['doubleSided'] = False
        pbr['metallicFactor'] = pbr['roughnessFactor'] = 1
        mat['normalTexture']['scale'] = .75
        export = P / 'work/meshy' / f'{icon}_export.glb'
        write_glb(export, doc, bytes(payload))
        convention = convert(export, export, threshold=.05)
        doc, binary = read_glb(export)
        write_glb(export, doc, omit_mesh_nodes(doc, binary, []))
        receipt = {'icon': icon, 'maps': 3, 'size': 1024, 'metallic': 'binary steel/brass vs paint/ivory/lenses',
                   'dielectric_texels': int(nonmetal.sum()), 'ivory_texels': int(ivory.sum()),
                   'lens_texels': int(lens.sum()), 'normal_convention': convention}
        (P / 'receipts' / f'{icon}_pbr.json').write_text(json.dumps(receipt, indent=2) + '\n')
        print('PBR', icon, receipt, flush=True)


if __name__ == '__main__':
    main()
