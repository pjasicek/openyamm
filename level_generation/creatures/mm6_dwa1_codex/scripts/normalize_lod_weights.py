"""Normalize all influence sets together, after the final body/head/shadow packaging."""
from pathlib import Path
import hashlib
import json
import sys
import numpy as np

sys.dont_write_bytecode = True
P = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(P.parents[2] / 'tools'))
from merge_head_material import read_glb, write_glb, accessor_array


def normalize_weights(document, binary):
    report = []
    for mesh in document['meshes']:
        for primitive_index, primitive in enumerate(mesh['primitives']):
            attributes = primitive['attributes']
            names = sorted(name for name in attributes if name.startswith('WEIGHTS_'))
            if not names:
                assert not any(name.startswith('JOINTS_') for name in attributes)
                continue
            assert names in (['WEIGHTS_0'], ['WEIGHTS_0', 'WEIGHTS_1'])
            arrays = []
            for name in names:
                assert name.replace('WEIGHTS_', 'JOINTS_') in attributes
                index = attributes[name]
                accessor = document['accessors'][index]
                # These Blender exports use float weights; reject a changed encoding before writing.
                assert accessor['componentType'] == 5126 and accessor['type'] == 'VEC4'
                weights = accessor_array(document, binary, index)
                assert np.isfinite(weights).all() and (weights >= 0).all()
                arrays.append(weights)
            assert len({len(weights) for weights in arrays}) == 1
            total = sum(weights.astype(np.float64).sum(axis=1) for weights in arrays)
            assert (total > 0).all(), 'Cannot normalize a vertex with no joint influence'
            before = float(np.abs(total - 1).max())
            changed = np.abs(total - 1) > 1e-6
            for name, weights in zip(names, arrays):
                weights[changed] = weights[changed].astype(np.float64) / total[changed, None]
                accessor = document['accessors'][attributes[name]]
                view = document['bufferViews'][accessor['bufferView']]
                offset = view.get('byteOffset', 0) + accessor.get('byteOffset', 0)
                stride = view.get('byteStride', 16)
                for row in np.flatnonzero(changed):
                    start = offset + int(row) * stride
                    binary[start:start + 16] = weights[row].astype('<f4').tobytes()
            after = float(np.abs(sum(w.astype(np.float64).sum(axis=1) for w in arrays) - 1).max())
            assert after < 1e-4
            report.append({'mesh': mesh.get('name'), 'primitive': primitive_index, 'sets': names,
                           'vertices': len(total), 'vertices_normalized': int(changed.sum()),
                           'max_error_before': before, 'max_error_after': after})
    assert report, 'No skinned primitives found'
    return report


def main():
    source, destination = map(Path, sys.argv[1:])
    document, binary = read_glb(source)
    report = normalize_weights(document, binary)
    write_glb(destination, document, binary)
    result = {'file': str(destination.relative_to(P)),
              'sha256': hashlib.sha256(destination.read_bytes()).hexdigest(),
              'max_error': max(row['max_error_after'] for row in report), 'primitives': report}
    (P / 'review/final_skin_weights.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
