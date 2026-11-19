"""Trim the temple wall overlapping the bell tower sill; install with a fresh lighting bake."""
import argparse
import base64
from pathlib import Path
import struct
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'util'))
from map_export import parse_odm_file


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=Path('assets_dev/worlds/mm7/maps/7out02.odm'))
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.source.resolve() == args.output.resolve():
        parser.error('Write a review copy outside the installed map')
    native = parse_odm_file(args.source)['payload']
    model = native['bmodels'][95]
    face = model['faces'][26]
    points = [tuple(model['vertices'][i][axis] for axis in 'xyz') for i in face['vertex_indices']]
    expected = [(-13242, 10688, 896), (-13242, 10704, 896), (-13242, 10752, 896),
                (-13242, 10752, 768), (-13242, 10752, 0), (-13242, 10688, 0),
                (-13242, 10688, 512), (-13242, 10688, 768)]
    if model['name'] != 'Temple3_N_1' or points != expected or face['texture_name'] != 'CHB1EL':
        raise ValueError('Unexpected temple wall geometry; inspect before applying')
    # The upper 64 x 128 rectangle is already provided by both tower models.
    for index in (94, 96):
        tower = native['bmodels'][index]
        cover = [tuple(tower['vertices'][i][axis] for axis in 'xyz')
                 for i in tower['faces'][57]['vertex_indices']]
        if cover != expected[:4] + [expected[-1]]:
            raise ValueError('Tower sill no longer covers the removed wall section')
    data = bytearray(args.source.read_bytes())
    record = base64.b64decode(face['raw_record_base64'])
    offset = data.find(record)
    if offset < 0 or data.find(record, offset + 1) >= 0:
        raise ValueError('Face record is not unique')
    for start in (0x20, 0x48, 0x70, 0x98, 0xC0, 0xE8):
        data[offset + start:offset + start + 10] = record[start + 6:start + 16]
        data[offset + start + 10:offset + start + 18] = bytes(8)
    data[offset + 0x12E] = 5
    bounds = [value for axis in range(3) for value in
              (min(point[axis] for point in points[3:]), max(point[axis] for point in points[3:]))]
    struct.pack_into('<6h', data, offset + 0x116, *bounds)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(data)
    after = parse_odm_file(args.output)['payload']
    changed = [(bi, fi) for bi, (a, b) in enumerate(zip(native['bmodels'], after['bmodels']))
               for fi, (fa, fb) in enumerate(zip(a['faces'], b['faces'])) if fa != fb]
    assert changed == [(95, 26)], changed
    fixed = after['bmodels'][95]['faces'][26]
    for field in ('vertex_indices', 'texture_us', 'texture_vs'):
        assert fixed[field] == face[field][3:]
    print(f'Trimmed model 95 face 26; preserved tower sill, face ids and UVs: {args.output}')


if __name__ == '__main__':
    main()
