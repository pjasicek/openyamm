"""Install the two persistent containers behind New Sorpigal's tavern, once.

Keep storage ids 2/3 so existing saved inventories follow their new locations.
The previously unused ids 0/19 take the original bridge loot definitions.
The original 90 models and all entity/spatial records remain byte-identical.
"""
import argparse
import copy
import struct
from pathlib import Path

import yaml

from export_outdoor_scene_yml import parse_outdoor_odm

ROOT = Path(__file__).resolve().parents[1]
MAP = ROOT / "assets_dev/worlds/mm6/maps/oute3.odm"
PLACEMENTS = ((28, "StorageSouth", (-6880, -9248, 160), 501),
              (28, "StorageNorth", (-6880, -8992, 160), 502),
              (57, "StorageSign", (-6880, -9536, 160), 503))


def chest_block(chest):
    return (f"    - chest_index: {chest['chest_index']}\n"
            f"      chest_type_id: {chest['chest_type_id']}\n"
            f"      flags: {chest['flags']}\n"
            f"      raw_items_hex: \"{chest['raw_items_hex']}\"\n"
            f"      inventory_matrix: {chest['inventory_matrix']}\n")


def storage_bindings(path):
    """Scene metadata owns events: native geometry event fields are cleared at load."""
    parsed = parse_outdoor_odm(path)
    lines = []
    for model_index in (90, 91, 92):
        for face in parsed["bmodels"][model_index]["faces"]:
            if face["cog_triggered_number"]:
                lines.append(f"    - bmodel_index: {model_index}\n")
                for key in ("face_index", "legacy_attributes", "cog_number", "cog_triggered_number", "cog_trigger"):
                    value = face[{"face_index": "index", "legacy_attributes": "attributes"}.get(key, key)]
                    lines.append(f"      {key}: {value}\n")
    return "".join(lines)


def sections(data):
    offset = 0xB4 + 3 * 128 * 128
    normals = struct.unpack_from("<i", data, offset)[0]
    offset += 4 + 0x30000 + normals * 12
    count = struct.unpack_from("<i", data, offset)[0]
    headers = offset + 4
    cursor = headers + count * 0xBC
    models = []
    for index in range(count):
        header = bytearray(data[headers + index * 0xBC:headers + (index + 1) * 0xBC])
        vertices = struct.unpack_from("<i", header, 0x44)[0]
        faces = struct.unpack_from("<i", header, 0x4C)[0]
        nodes = struct.unpack_from("<i", header, 0x5C)[0]
        end = cursor + vertices * 12 + faces * (0x134 + 12) + nodes * 8
        models.append((header, bytearray(data[cursor:end]), vertices, faces))
        cursor = end
    return offset, models, cursor


def clone(model, name, position, event):
    header, body, vertex_count, face_count = copy.deepcopy(model)
    points = [struct.unpack_from("<3i", body, index * 12) for index in range(vertex_count)]
    centre = tuple((min(p[a] for p in points) + max(p[a] for p in points)) // 2 for a in range(2))
    delta = (position[0] - centre[0], position[1] - centre[1], position[2] - min(p[2] for p in points))
    moved = [tuple(p[a] + delta[a] for a in range(3)) for p in points]
    for index, point in enumerate(moved):
        struct.pack_into("<3i", body, index * 12, *point)
    # Recompute the authoritative runtime header; several legacy headers have stale bounds.
    for offset in (0, 32):
        header[offset:offset + 32] = name.encode().ljust(32, b"\0")
    minimum = tuple(min(p[a] for p in moved) for a in range(3))
    maximum = tuple(max(p[a] for p in moved) for a in range(3))
    centre3 = tuple((minimum[a] + maximum[a]) // 2 for a in range(3))
    for offset, values in ((0x68, centre3), (0x74, minimum), (0x80, maximum), (0xA8, centre3)):
        struct.pack_into("<3i", header, offset, *values)
    radius = int(sum(((maximum[a] - minimum[a]) / 2) ** 2 for a in range(3)) ** .5) + 1
    struct.pack_into("<i", header, 0xB4, radius)
    for index in range(face_count):
        face = vertex_count * 12 + index * 0x134
        nx, ny, nz, distance = struct.unpack_from("<4i", body, face)
        struct.pack_into("<i", body, face + 12, distance - sum(n * d for n, d in zip((nx, ny, nz), delta)))
        for axis, offsets in enumerate(((0x116, 0x118), (0x11A, 0x11C), (0x11E, 0x120))):
            for offset in offsets:
                value = struct.unpack_from("<h", body, face + offset)[0]
                struct.pack_into("<h", body, face + offset, value + delta[axis])
        # UV entries/deltas are retained together: the cloned material does not slide.
        old_event = struct.unpack_from("<H", body, face + 0x124)[0]
        if old_event:
            struct.pack_into("<H", body, face + 0x124, event)
    if name == "StorageSign":
        textures = vertex_count * 12 + face_count * (0x134 + 2)
        for index in range(face_count):
            offset = textures + index * 10
            if body[offset:offset + 10].split(b"\0")[0] == b"BANK":
                body[offset:offset + 10] = b"sign128\0\0\0"
                # The native writing sign is 256x128; the bank icon used a 64x64 UV extent.
                face = vertex_count * 12 + index * 0x134
                du, dv = struct.unpack_from("<2h", body, face + 0x112)
                for vertex in range(body[face + 0x12E] + 1):
                    for uv_offset, scale, delta in ((0x48, 4, du), (0x70, 2, dv)):
                        uv = face + uv_offset + vertex * 2
                        value = struct.unpack_from("<h", body, uv)[0]
                        struct.pack_into("<h", body, uv, (value + delta) * scale)
                struct.pack_into("<2h", body, face + 0x112, 0, 0)
    return header, body, vertex_count, face_count


def validate(path):
    data = path.read_bytes()
    _, models, _ = sections(data)
    assert len(models) == 93
    parsed = parse_outdoor_odm(path)
    for index, (_, name, position, event) in enumerate(PLACEMENTS, 90):
        header, body, vertices, faces = models[index]
        assert header[:32].split(b"\0")[0].decode() == name
        assert struct.unpack_from("<i", header, 0x7C)[0] == position[2]
        assert event in {face["cog_triggered_number"] for face in parsed["bmodels"][index]["faces"]}
        for face_index in range(faces):
            face = vertices * 12 + face_index * 0x134
            nx, ny, nz, distance = struct.unpack_from("<4i", body, face)
            count = body[face + 0x12E]
            for vertex in struct.unpack_from(f"<{count}H", body, face + 0x20):
                point = struct.unpack_from("<3i", body, vertex * 12)
                assert abs(sum(n * p for n, p in zip((nx, ny, nz), point)) + distance) <= 65536
    scene = yaml.safe_load(path.with_suffix(".scene.yml").read_text(encoding="utf-8"))
    bindings = {(face["bmodel_index"], face["face_index"]): face
                for face in scene["bmodel_faces"]["interactive_faces"]}
    for index, (_, _, _, event) in enumerate(PLACEMENTS, 90):
        for face in parsed["bmodels"][index]["faces"]:
            if face["cog_triggered_number"]:
                assert bindings[index, face["index"]]["cog_triggered_number"] == event
    chests = scene["initial_state"]["chests"]
    assert len(chests) == 20
    for index in (2, 3):
        assert not any(bytes.fromhex(chests[index]["raw_items_hex"]))
    print("Verified: bridge events 76/77 -> ordinary ids 0/19; storage events 501/502 -> persistent ids 2/3")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    data = MAP.read_bytes()
    offset, models, tail = sections(data)
    if not args.check:
        if len(models) != 90:
            raise ValueError("Expected the original 90-model map; use --check after installation")
        additions = [clone(models[source], name, position, event) for source, name, position, event in PLACEMENTS]
        updated = data[:offset] + struct.pack("<i", 93)
        updated += b"".join(model[0] for model in models + additions)
        updated += b"".join(model[1] for model in models + additions) + data[tail:]
        MAP.write_bytes(updated)
        scene_path = MAP.with_suffix(".scene.yml")
        text = scene_path.read_text(encoding="utf-8")
        scene = yaml.safe_load(text)
        chests = scene["initial_state"]["chests"]
        assert len(chests) == 20
        assert all(not any(bytes.fromhex(chests[i]["raw_items_hex"])) for i in (0, 19))
        # Change only chest blocks, retaining the large exported scene verbatim elsewhere.
        for destination, source in ((0, 2), (19, 3), (2, 0), (3, 19)):
            chest = copy.deepcopy(chests[source])
            chest["chest_index"] = destination
            block = chest_block(chest)
            start = text.index(f"    - chest_index: {destination}\n", text.index("  chests:\n"))
            end = text.find("    - chest_index:", start + 1)
            if end < 0:
                end = text.index("  variables:", start)
            text = text[:start] + block + text[end:]
        text = text.replace("entities:\n", storage_bindings(MAP) + "entities:\n", 1)
        scene_path.write_text(text, encoding="utf-8", newline="\n")
    validate(MAP)


if __name__ == "__main__":
    main()
