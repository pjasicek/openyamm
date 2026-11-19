"""Remove the coplanar overlap at Tularean Forest's Dock4c_E; requires a subsequent lighting bake.

Writes a review copy only. Install it with its successfully regenerated lighting/recipe pair.
"""
import argparse
import base64
from pathlib import Path
import struct
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'util'))
from map_export import parse_odm_file


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=Path('assets_dev/worlds/mm7/maps/7out04.odm'))
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.source.resolve() == args.output.resolve():
        parser.error('Write a review copy outside the installed map')
    model = parse_odm_file(args.source)['payload']['bmodels'][114]
    face = model['faces'][58]
    points = [tuple(model['vertices'][index][axis] for axis in 'xyz') for index in face['vertex_indices']]
    expected = [(-14080, -5888, 1344), (-14592, -6400, 1344), (-14336, -7040, 1344),
                (-14080, -7296, 1344), (-13568, -7168, 1344)]
    if model['name'] != 'Dock4c_E' or points != expected or face['texture_name'] != '7trimd':
        raise ValueError('Unexpected dock geometry; inspect before applying this repair')
    # The triangle formed by the first, second and last vertices is already fully covered by face 57.
    # Removing its tip retains the remaining quad, the original UVs, face ids and all event bindings.
    covering = model['faces'][57]['vertex_indices']
    if not all(index in covering for index in (face['vertex_indices'][0], face['vertex_indices'][1],
                                              face['vertex_indices'][-1])):
        raise ValueError('The adjacent face no longer covers the overlap')
    data = bytearray(args.source.read_bytes())
    record = base64.b64decode(face['raw_record_base64'])
    offset = data.find(record)
    if offset < 0 or data.find(record, offset + 1) >= 0:
        raise ValueError('Face record is not unique')
    # Native vertex ids, UVs and the three legacy per-vertex displacement arrays.
    for start in (0x20, 0x48, 0x70, 0x98, 0xC0, 0xE8):
        data[offset + start:offset + start + 8] = record[start + 2:start + 10]
        data[offset + start + 8:offset + start + 10] = b'\0\0'
    data[offset + 0x12E] = 4
    bounds = [value for axis in range(3) for value in
              (min(point[axis] for point in points[1:]), max(point[axis] for point in points[1:]))]
    struct.pack_into('<6h', data, offset + 0x116, *bounds)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(data)
    repaired = parse_odm_file(args.output)['payload']['bmodels'][114]['faces'][58]
    assert repaired['vertex_indices'] == face['vertex_indices'][1:]
    assert repaired['texture_us'] == face['texture_us'][1:]
    assert repaired['texture_vs'] == face['texture_vs'][1:]
    print(f'Repaired Dock4c_E face 58: removed overlap with face 57; wrote {args.output}')


if __name__ == '__main__':
    main()
