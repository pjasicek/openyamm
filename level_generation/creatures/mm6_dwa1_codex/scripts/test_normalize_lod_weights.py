"""The regression is a valid first set plus additional LOD influences in WEIGHTS_1."""
import sys
sys.dont_write_bytecode = True
import numpy as np
from normalize_lod_weights import normalize_weights


def fixture(first, second):
    arrays = [np.asarray(first, dtype='<f4'), np.asarray(second, dtype='<f4')]
    size = arrays[0].nbytes
    document = {'meshes': [{'name': 'LOD_Shadow', 'primitives': [{'attributes': {
        'WEIGHTS_0': 0, 'WEIGHTS_1': 1, 'JOINTS_0': 2, 'JOINTS_1': 3}}]}],
        'accessors': [{'bufferView': i, 'count': len(array), 'type': 'VEC4', 'componentType': 5126}
                      for i, array in enumerate(arrays)],
        'bufferViews': [{'byteOffset': i * size, 'byteLength': size} for i in range(2)]}
    return document, bytearray(arrays[0].tobytes() + arrays[1].tobytes() + b'unchanged payload')


d, b = fixture([[.6, .4, 0, 0], [.3, .2, 0, 0]], [[.2, 0, 0, 0], [.4, .1, 0, 0]])
original = bytes(b)
r = normalize_weights(d, b)
assert r[0]['vertices_normalized'] == 1 and r[0]['max_error_before'] > .19
first = np.frombuffer(b, dtype='<f4', count=8).reshape(2, 4)
second = np.frombuffer(b, dtype='<f4', count=8, offset=32).reshape(2, 4)
assert np.allclose(first[0], [.5, 1 / 3, 0, 0]) and np.allclose(second[0], [1 / 6, 0, 0, 0])
assert np.max(abs(first.astype(float).sum(1) + second.astype(float).sum(1) - 1)) < 1e-4
assert b[16:32] == original[16:32] and b[48:] == original[48:]
fixed = bytes(b)
normalize_weights(d, b)
assert bytes(b) == fixed, 'Normalization must be idempotent'
for value in [0, -1, float('nan')]:
    d, b = fixture([[value, 0, 0, 0]], [[0, 0, 0, 0]])
    try:
        normalize_weights(d, b)
    except AssertionError:
        pass
    else:
        raise AssertionError('Invalid weights accepted')
print('WEIGHTS_0 + WEIGHTS_1 regression, untouched data, idempotence and invalid-input checks: PASS')
