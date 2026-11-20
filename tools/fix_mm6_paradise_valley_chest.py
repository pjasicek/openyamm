#!/usr/bin/env python3
"""Move outa2's western chest onto accessible, level terrain without changing its loot.

The MM8-format ODM contains world-space vertices, face planes, UVs and bounds.
Keep those records consistent; changing vertices alone leaves stale geometry metadata.
Run once to apply, or with --check to validate the installed correction. No build required.
"""

import argparse
import struct
from pathlib import Path

from export_outdoor_scene_yml import parse_outdoor_odm


MAP = Path(__file__).resolve().parents[1] / "assets_dev/worlds/mm6/maps/outa2.odm"
OLD_X = -24328
DELTA_X = 2048


def chest_offsets(data):
    def integer(offset):
        return struct.unpack_from("<i", data, offset)[0]

    if data[0x40:0x50] != bytes(16):
        raise ValueError("Expected the installed MM8-format Paradise Valley ODM")
    offset = 0xB4 + 3 * 128 * 128
    normal_count = integer(offset)
    offset += 4 + 0x30000 + normal_count * 12
    model_count = integer(offset)
    headers = offset + 4
    offset = headers + model_count * 0xBC
    for index in range(model_count):
        header = headers + index * 0xBC
        vertices = integer(header + 0x44)
        faces = integer(header + 0x4C)
        nodes = integer(header + 0x5C)
        name = data[header:header + 32].split(b"\0")[0]
        if index == 26:
            if name != b"Chest 3E_1" or vertices != 16 or faces != 11:
                raise ValueError("Unexpected chest geometry")
            return header, offset, vertices, faces
        offset += vertices * 12 + faces * (0x134 + 2 + 10) + nodes * 8
    raise ValueError("Missing chest model")


def validate(data, header, vertices, vertex_count, face_count):
    points = [struct.unpack_from("<3i", data, vertices + index * 12) for index in range(vertex_count)]
    assert struct.unpack_from("<3i", data, header + 0x70) == (OLD_X + DELTA_X, 21184, 192)
    assert min(point[0] for point in points) > -22528
    assert min(point[2] for point in points) == 160
    # All terrain vertices under the chest and its immediate approach are level.
    for row in range(21, 24):
        for column in range(19, 22):
            assert data[0xB4 + row * 128 + column] * 32 == 160
    for index in range(face_count):
        face = vertices + vertex_count * 12 + index * 0x134
        nx, ny, nz, distance = struct.unpack_from("<4i", data, face)
        count = data[face + 0x12E]
        for vertex_index in struct.unpack_from(f"<{count}H", data, face + 0x20):
            x, y, z = points[vertex_index]
            assert nx * x + ny * y + nz * z + distance == 0
        assert struct.unpack_from("<H", data, face + 0x124)[0] == 76


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--map", type=Path, default=MAP, help="Map copy to edit or validate")
    args = parser.parse_args()
    data = bytearray(args.map.read_bytes())
    header, vertices, vertex_count, face_count = chest_offsets(data)
    current_x = struct.unpack_from("<i", data, header + 0x70)[0]
    if current_x == OLD_X and not args.check:
        # Native ODM header: position, bounding box and bounding sphere centre.
        for offset in (0x70, 0x7C, 0x88, 0xAC):
            value = struct.unpack_from("<i", data, header + offset)[0]
            struct.pack_into("<i", data, header + offset, value + DELTA_X)
        for index in range(vertex_count):
            offset = vertices + index * 12
            value = struct.unpack_from("<i", data, offset)[0]
            struct.pack_into("<i", data, offset, value + DELTA_X)
        for index in range(face_count):
            face = vertices + vertex_count * 12 + index * 0x134
            nx, ny, nz, distance = struct.unpack_from("<4i", data, face)
            struct.pack_into("<i", data, face + 0x0C, distance - nx * DELTA_X)
            for offset in (0x116, 0x118):
                value = struct.unpack_from("<h", data, face + offset)[0]
                struct.pack_into("<h", data, face + offset, value + DELTA_X)
            # These axis-aligned faces use +X for south/top U, -X for north U.
            u_shift = DELTA_X if ny < 0 or nz > 0 else -DELTA_X if ny > 0 else 0
            if u_shift:
                count = data[face + 0x12E]
                # ODM stores a closing UV entry as well as the polygon vertices.
                for entry in range(count + 1):
                    offset = face + 0x48 + entry * 2
                    value = struct.unpack_from("<h", data, offset)[0]
                    struct.pack_into("<h", data, offset, value + u_shift)
                value = struct.unpack_from("<h", data, face + 0x112)[0]
                struct.pack_into("<h", data, face + 0x112, value - u_shift)
        validate(data, header, vertices, vertex_count, face_count)
        args.map.write_bytes(data)
    elif current_x != OLD_X + DELTA_X:
        raise ValueError(f"Unexpected chest X: {current_x}; correction not applied")
    validate(data, header, vertices, vertex_count, face_count)
    parse_outdoor_odm(args.map)
    print("Paradise Valley chest 2: X=-22280 Y=21184, ground Z=160; geometry and event 76 verified")


if __name__ == "__main__":
    main()
