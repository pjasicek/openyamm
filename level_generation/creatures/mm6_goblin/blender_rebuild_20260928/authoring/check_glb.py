"""Inspect the delivered binary, including UV/skin data and bind-surface parity between handoffs."""
import hashlib
import json
import math
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[1]
FORMATS = {5120: 'b', 5121: 'B', 5122: 'h', 5123: 'H', 5125: 'I', 5126: 'f'}
WIDTHS = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}


class Glb:
    def __init__(self, path):
        self.path = path
        self.raw = path.read_bytes()
        magic, version, size = struct.unpack_from('<4sII', self.raw)
        assert (magic, version, size) == (b'glTF', 2, len(self.raw))
        offset = 12
        while offset < size:
            length, kind = struct.unpack_from('<II', self.raw, offset)
            content = self.raw[offset + 8:offset + 8 + length]
            if kind == 0x4E4F534A:
                self.json = json.loads(content)
            elif kind == 0x004E4942:
                self.binary = content
            offset += 8 + length

    def accessor(self, index):
        acc = self.json['accessors'][index]
        view = self.json['bufferViews'][acc['bufferView']]
        fmt = '<' + FORMATS[acc['componentType']] * WIDTHS[acc['type']]
        stride = view.get('byteStride', struct.calcsize(fmt))
        start = view.get('byteOffset', 0) + acc.get('byteOffset', 0)
        result = [struct.unpack_from(fmt, self.binary, start + i * stride) for i in range(acc['count'])]
        if acc.get('normalized'):
            divisor = {5120: 127, 5121: 255, 5122: 32767, 5123: 65535}[acc['componentType']]
            result = [tuple(max(-1, v / divisor) for v in row) for row in result]
        return result

    def surfaces(self):
        result = {}
        for node in self.json['nodes']:
            if 'mesh' not in node:
                continue
            name = node.get('extras', {}).get('source_part', node['name'])
            triangles = []
            for primitive in self.json['meshes'][node['mesh']]['primitives']:
                attrs = primitive['attributes']
                positions, uv = self.accessor(attrs['POSITION']), self.accessor(attrs['TEXCOORD_0'])
                indices = [i[0] for i in self.accessor(primitive['indices'])]
                for offset in range(0, len(indices), 3):
                    tri = [tuple(round(v, 6) for v in positions[i] + uv[i]) for i in indices[offset:offset + 3]]
                    triangles.append(tuple(sorted(tri, key=lambda corner: corner[-2:])))
            result[name] = sorted(triangles, key=lambda triangle: tuple(corner[-2:] for corner in triangle))
        return result

    def audit(self, rigged):
        j = self.json
        assert len(j['scenes']) == 1, 'Unrelated Blender scene leaked into export'
        assert all('Cube' not in n.get('name', '') and 'guide' not in n.get('name', '').lower() for n in j['nodes'])
        triangles, split_vertices, influences = 0, 0, 0
        for mesh in j['meshes']:
            for primitive in mesh['primitives']:
                assert primitive.get('mode', 4) == 4
                attrs = primitive['attributes']
                pos, uv = self.accessor(attrs['POSITION']), self.accessor(attrs['TEXCOORD_0'])
                assert all(math.isfinite(v) for row in pos for v in row)
                assert all(-1e-6 <= v <= 1.000001 for row in uv for v in row)
                normals = self.accessor(attrs['NORMAL'])
                assert all(abs(sum(v * v for v in row) - 1) < .001 for row in normals)
                indices = [i[0] for i in self.accessor(primitive['indices'])]
                assert len(indices) % 3 == 0 and max(indices) < len(pos)
                triangles += len(indices) // 3
                split_vertices += len(pos)
                if rigged:
                    assert 'JOINTS_0' in attrs and 'WEIGHTS_0' in attrs
                    assert 'JOINTS_1' not in attrs
                    weights = self.accessor(attrs['WEIGHTS_0'])
                    assert all(abs(sum(w) - 1) < 1e-4 for w in weights)
                    influences = max(influences, max(sum(v > 1e-6 for v in w) for w in weights))
                    assert all(v < 72 for row in self.accessor(attrs['JOINTS_0']) for v in row)
                else:
                    assert 'JOINTS_0' not in attrs
        assert triangles <= 15000
        clips = {}
        for clip in j.get('animations', []):
            times = [t[0] for sampler in clip['samplers'] for t in self.accessor(sampler['input'])]
            assert min(times) >= 0
            clips[clip['name']] = round(max(times) - min(times), 6)
        if rigged:
            assert clips == {'standing': 2., 'walk': 1., 'attack': .75, 'hit': .75,
                             'death': .625, 'corpse': 1., 'fidget': .75}, clips
        else:
            assert not clips and not j.get('skins')
        return {'file': self.path.name, 'sha256': hashlib.sha256(self.raw).hexdigest(),
                'bytes': len(self.raw), 'triangles': triangles, 'gltf_split_vertices': split_vertices,
                'mesh_parts': len(j['meshes']), 'materials': len(j.get('materials', [])),
                'joints': len(j['skins'][0]['joints']) if j.get('skins') else 0,
                'maximum_influences': influences, 'clips_seconds': clips,
                'embedded_images': len(j.get('images', [])), 'finite_positions_normalized_normals_uv_bounds': 'pass'}


def main():
    rigged = Glb(ROOT / 'delivery/mm6_goblin_rigged.glb')
    texturing = Glb(ROOT / 'delivery/mm6_goblin_texturing.glb')
    reports = [rigged.audit(True), texturing.audit(False)]
    a, b = rigged.surfaces(), texturing.surfaces()
    assert a.keys() == b.keys(), (a.keys(), b.keys())
    maximum_difference = 0
    for key in a:
        assert len(a[key]) == len(b[key])
        for left, right in zip(a[key], b[key]):
            for va, vb in zip(left, right):
                assert va[-2:] == vb[-2:], (key, 'UV difference')
                maximum_difference = max(maximum_difference, max(abs(x - y) for x, y in zip(va[:3], vb[:3])))
    assert maximum_difference <= .000002, maximum_difference
    report = {'exports': reports, 'bind_triangles_and_uvs_match': True,
              'maximum_bind_coordinate_difference_m': maximum_difference,
              'comparison_tolerance_m': .000002,
              'weapon_park_transform': 'texturing_transforms.json', 'limit': 15000}
    (ROOT / 'delivery/glb_validation.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
