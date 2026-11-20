"""Validate the owned exports and save reproducible geometry/texture receipts."""
from collections import Counter
import hashlib
import io
import json
from pathlib import Path
import sys

import numpy as np
from PIL import Image

PROJECT = Path(__file__).resolve().parents[1]
REPO = PROJECT.parents[2]
sys.path.insert(0, str(REPO / 'level_generation/decorations/mm8_3d/animated/scripts'))
import check_winding as winding


def verify(path):
    document, binary = winding.read_glb(path)
    positions, triangle_count, degenerate, boundary = [], 0, 0, 0
    min_uv, max_uv = 1, 0
    opposed_normals=0
    for mesh in document['meshes']:
        edges = Counter()
        for primitive in mesh['primitives']:
            attributes = primitive['attributes']
            points = winding.array(document, binary, attributes['POSITION'])
            assert np.isfinite(points).all(), path
            positions.append(points)
            uv = winding.array(document, binary, attributes['TEXCOORD_0'])
            assert np.isfinite(uv).all(), path
            min_uv, max_uv = min(min_uv, float(uv.min())), max(max_uv, float(uv.max()))
            triangles = winding.array(document, binary, primitive['indices']).reshape(-1, 3)
            triangle_count += len(triangles)
            a, b, c = points[triangles[:, 0]], points[triangles[:, 1]], points[triangles[:, 2]]
            areas = np.linalg.norm(np.cross(b - a, c - a), axis=1) / 2
            normals=winding.array(document,binary,attributes['NORMAL'])
            dots=np.sum(np.cross(b-a,c-a)*normals[triangles].mean(axis=1),axis=1)
            opposed_normals+=int(np.sum(dots < -1e-8))
            degenerate += int(np.sum(areas < 1e-10))
            keys = [tuple(p) for p in points]
            for tri in triangles:
                for n in range(3):
                    edges[tuple(sorted((keys[tri[n]], keys[tri[(n + 1) % 3]])))] += 1
        boundary += sum(n == 1 for n in edges.values())
    assert degenerate == 0, (path.name, 'degenerate triangles', degenerate)
    assert -1e-6 <= min_uv <= max_uv <= 1.000001, (path.name, min_uv, max_uv)
    assert triangle_count < 15000, path
    assert opposed_normals==0,(path.name,'opposed exported normals',opposed_normals)
    assert boundary==0,(path.name,'open edges',boundary)
    points = np.concatenate(positions)
    low, high = points.min(axis=0), points.max(axis=0)
    # glTF is Y-up; the horizontal footprint is X/Z.
    assert abs(low[1]) < 1e-5, (path.name, low)
    assert max(abs((low + high)[[0, 2]])) < 1e-5, (path.name, low, high)
    assert abs(max((high - low)[[0, 2]]) - 1) < 1e-5, path
    sizes=[];image_pixels={}
    for number,image in enumerate(document.get('images', [])):
        assert 'bufferView' in image, (path.name, 'unembedded image', image)
        assert image['mimeType'] == 'image/png', (path.name, image)
        view=document['bufferViews'][image['bufferView']];offset=view.get('byteOffset',0)
        pixels=Image.open(io.BytesIO(binary[offset:offset+view['byteLength']]))
        image_pixels[number]=np.array(pixels.convert('RGB'))
        sizes.append(list(pixels.size))
        assert all(n>0 and n&(n-1)==0 and n<=1024 for n in pixels.size),(path.name,pixels.size)
    assert len(document['materials'])==1,(path.name,'unexpected material draws')
    pbr=document['materials'][0]['pbrMetallicRoughness']
    base=image_pixels[document['textures'][pbr['baseColorTexture']['index']]['source']]
    assert base.min()>=30 and base.max()<=243,(path.name,'albedo range',base.min(),base.max())
    mr=image_pixels[document['textures'][pbr['metallicRoughnessTexture']['index']]['source']]
    assert set(np.unique(mr[:,:,2])).issubset({0,255}),(path.name,'non-binary metal mask')
    normal_info=document['materials'][0]['normalTexture']
    normal=image_pixels[document['textures'][normal_info['index']]['source']]
    assert float(normal[:,:,:2].std())>.5,(path.name,'flat normal map')
    assert int(normal[:,:,2].min())>127,(path.name,'inverted normal hemisphere')
    assert winding.check(path) == 0, path
    return {'export': str(path.relative_to(PROJECT)), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
            'triangles': triangle_count, 'degenerate_triangles': degenerate, 'boundary_edges': boundary,
            'uv_range': [min_uv, max_uv], 'gltf_bounds': [low.tolist(), high.tolist()],
            'embedded_pngs': len(document.get('images', [])), 'texture_sizes':sizes,'opposed_normals':opposed_normals,
            'winding_passed': True,'normal_map':True,'normal_scale':normal_info.get('scale',1)}


def main():
    owned = {i['icon'] for i in json.loads((PROJECT / 'ownership.json').read_text())}
    files=[]
    for icon in sorted(owned):
        meshy=PROJECT/'work/meshy'/f'{icon}_export.glb'
        files.append(meshy if meshy.exists() else PROJECT/'work/blender'/f'{icon}_export.glb')
    assert len(files)==5 and all(f.exists() for f in files)
    receipts = []
    for path in files:
        assert path.name.removesuffix('_export.glb') in owned
        receipts.append(verify(path))
    (PROJECT / 'review/validation.json').write_text(json.dumps(receipts, indent=2) + '\n')
    print(f'PASS: {len(receipts)} owned exports, {sum(r["triangles"] for r in receipts)} triangles')


if __name__ == '__main__':
    main()
