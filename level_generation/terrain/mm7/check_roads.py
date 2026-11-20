"""Reject interior transparency and split road openings, including holes spanning joins."""
import json
import numpy as np
from scipy.ndimage import binary_fill_holes, distance_transform_edt, label
from common import *


def check_mask(a, name):
    solid = a > .5
    holes = int(np.count_nonzero(binary_fill_holes(solid) & ~solid))
    partial_interior = int(np.count_nonzero((distance_transform_edt(solid) > 4) & (a < .999)))
    assert holes == 0, (name, 'interior holes', holes)
    assert partial_interior == 0, (name, 'partial interior coverage', partial_interior)
    return dict(holes=holes, partial_interior=partial_interior)


def main():
    build = json.loads((P/'transitions/build.json').read_text())
    roads = {r['name']: r for r in build['tiles'] if r['family'] == 'roads'}
    fields = {n: np.load(P/'transitions/fields'/f'{n}.npz')['coverage'] for n in roads}
    results = {}
    edges = lambda a: dict(N=a[0], S=a[-1], E=a[:, -1], W=a[:, 0])
    for n, a in fields.items():
        results[n] = check_mask(a, n)
        assert label(a > .5)[1] == 1, (n, 'disconnected road pieces')
        for side, e in edges(a).items():
            expected = 0 if roads[n]['topology'][side] == '000' else 1
            assert label(e > .5)[1] == expected, (n, side, 'split opening')
    joins = 0
    for n, a in fields.items():
        for m, b in fields.items():
            for side, opposite, axis in [('E', 'W', 1), ('S', 'N', 0)]:
                if roads[n]['topology'][side] != roads[m]['topology'][opposite]:
                    continue
                assert np.allclose(edges(a)[side], edges(b)[opposite], atol=1e-6), (n, side, m)
                check_mask(np.concatenate([a, b], axis=axis), (n, side, m))
                joins += 1
    report = dict(passed=True, tiles=results, compatible_mask_joins=joins,
                  files={n+'.png': sha(OUT/(n+'.png')) for n in roads},
                  masks={n: sha(P/'transitions/fields'/f'{n}.npz') for n in roads})
    (P/'reports/road_masks.json').write_text(json.dumps(report, indent=2)+'\n')
    print(f'{len(roads)} solid road silhouettes; {joins} compatible mask joins pass.')


if __name__ == '__main__':
    main()
