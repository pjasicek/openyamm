#!/usr/bin/env python3
"""Read MM9 FXF/SPR/DTX evidence without importing OpenMM9 or modifying source assets."""

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import struct


class Reader:
    def __init__(self, data):
        self.data = data
        self.offset = 0

    def take(self, size):
        end = self.offset + size
        if size < 0 or end > len(self.data):
            raise ValueError(f"Truncated input at {self.offset:#x}, requested {size} bytes")
        value = self.data[self.offset:end]
        self.offset = end
        return value

    def unpack(self, layout):
        return struct.unpack(layout, self.take(struct.calcsize(layout)))

    def text(self, size):
        return self.take(size).split(b"\0", 1)[0].decode("ascii")

    def finish(self):
        if self.offset != len(self.data):
            raise ValueError(f"Unconsumed input at {self.offset:#x}/{len(self.data):#x}")


def fingerprint(path):
    data = path.read_bytes()
    return {"path": str(path), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def read_fxf(path):
    """Layout checked against cshell.dll 678700ff:100a32f0; retain exact float32 values."""
    reader = Reader(path.read_bytes())
    groups = []
    for _ in range(reader.unpack("<I")[0]):
        offset = reader.offset
        count = reader.unpack("<I")[0]
        group = {"offset": offset, "name": reader.text(128), "phase_ms": reader.unpack("<I")[0], "keys": []}
        for _ in range(count):
            key = {"offset": reader.offset, "component_ref": reader.text(128)}
            key["id"], key["linked"], key["linked_id"] = reader.unpack("<3I")
            key["linked_node"] = reader.text(32)
            values = reader.unpack("<ffIIffI")
            for name, value in zip(("start", "end", "repeat", "track", "min_scale", "max_scale"), values):
                key[name] = value
            properties = []
            for _ in range(values[-1]):
                prop = {"offset": reader.offset, "name": reader.text(reader.unpack("<B")[0])}
                kind = reader.unpack("<I")[0]
                prop["type"] = kind
                if kind in (0, 3, 7):
                    prop["value"] = reader.text(128)
                    if kind == 3:
                        fields = prop["value"].split(",")
                        prop["numeric_selection"] = int(fields[0])
                        index = prop["numeric_selection"] + 1
                        prop["stored_editor_label"] = fields[index] if 0 < index < len(fields) else None
                elif kind in (1, 2):
                    prop["value"] = reader.unpack("<i" if kind == 1 else "<f")[0]
                elif kind in (4, 5):
                    prop["value"] = list(reader.unpack("<3f" if kind == 4 else "<4f"))
                elif kind == 6:
                    time, packed = reader.unpack("<fI")
                    channels = [(packed >> shift) & 255 for shift in (0, 8, 16, 24)]
                    prop["value"] = {"time": time, "packed": packed, "rgb_transparency": channels}
                else:
                    # The examined native loader has cases 0..7, not the guessed type 8 in OpenMM9.
                    raise ValueError(f"Unsupported native property type {kind} at {prop['offset']:#x}")
                properties.append(prop)
            key["properties"] = properties
            key["end_offset"] = reader.offset
            group["keys"].append(key)
        group["end_offset"] = reader.offset
        groups.append(group)
    reader.finish()
    return groups


def read_sprite(path):
    """lithtech.exe 4e9ddd2b:4667a1, five u32 fields followed by u16-length paths."""
    reader = Reader(path.read_bytes())
    count, fps, keyed, translucent, color_key = reader.unpack("<5I")
    frames = [reader.text(reader.unpack("<H")[0]) for _ in range(count)]
    reader.finish()
    return {"fingerprint": fingerprint(path), "frame_count": count, "fps": fps,
            "frame_ms": 1000 // fps, "cycle_ms": count * (1000 // fps),
            "keyed": keyed, "translucent": translucent, "color_key": color_key, "frames": frames}


def read_dtx_header(path):
    reader = Reader(path.read_bytes())
    resource, version, width, height, mips, sections, internal, user = reader.unpack("<Ii4H2I")
    extra = reader.take(12)
    command = reader.text(128)
    if resource != 0 or version != -5:
        raise ValueError(f"Unexpected DTX header in {path}")
    return {"fingerprint": fingerprint(path), "version": version, "width": width, "height": height,
            "mips": mips, "sections": sections, "internal_flags": internal, "user_flags": user,
            "extra_hex": extra.hex(), "bpp_identifier": extra[2], "command": command}


def asset_index(extracted):
    index = {}
    # Each extracted archive adds one directory above the engine-relative path.
    for archive in ("SPRITES", "SPRITETEXTURES", "SOUNDS", "MODELS", "SKINS"):
        root = extracted / archive
        if not root.is_dir():
            continue
        for path in root.rglob("*"):
            if path.is_file():
                name = path.relative_to(root).as_posix().lower()
                if name in index:
                    raise ValueError(f"Ambiguous engine asset path {name}")
                index[name] = path
    return index


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original-root", type=Path, required=True, help="OpenMM9/reference directory")
    parser.add_argument("--effect", default="spell-column of fire")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    extracted = args.original_root / "extracted"
    fxf = extracted / "CLIENTFX/CLIENTFX/SPELLS.fxf"
    groups = read_fxf(fxf)
    group = next(group for group in groups if group["name"] == args.effect)
    index = asset_index(extracted)
    assets = {}
    mismatches = []
    native_emissions = ("Point", "Plane", "Sphere", "PlaneIn", "PlaneOut", "Cone", "Circle")
    for effect in groups:
        for key in effect["keys"]:
            for prop in key["properties"]:
                if prop["name"] == "EmissionType" and prop["type"] == 3:
                    numeric = prop["numeric_selection"]
                    native = native_emissions[numeric]
                    if native != prop["stored_editor_label"]:
                        mismatches.append({"effect": effect["name"], "key": key["id"], "offset": prop["offset"],
                                           "numeric": numeric, "stored_label": prop["stored_editor_label"],
                                           "native_branch": native})
    for key in group["keys"]:
        for prop in key["properties"]:
            if prop["type"] != 7 or prop["value"].endswith("|..."):
                continue
            name = prop["value"].split("|", 1)[1].replace("\\", "/").lower()
            path = index[name]
            if path.suffix.lower() == ".spr":
                sprite = read_sprite(path)
                sprite["textures"] = [read_dtx_header(index[frame.replace("\\", "/").lower()])
                                      for frame in sprite["frames"]]
                assets[name] = sprite
            else:
                assets[name] = {"fingerprint": fingerprint(path)}
    component_counts = Counter(key["component_ref"].split(";", 1)[0]
                               for effect in groups for key in effect["keys"])
    report = {"fxf": fingerprint(fxf), "group_count": len(groups),
              "key_count": sum(len(effect["keys"]) for effect in groups),
              "component_counts": dict(component_counts), "effect": group,
              "emission_label_mismatches": mismatches, "assets": assets}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"groups": report["group_count"], "keys": report["key_count"],
                      "components": report["component_counts"], "emission_label_mismatches": len(mismatches),
                      "effect": group["name"], "assets": len(assets), "output": str(args.output)}, indent=2))


if __name__ == "__main__":
    main()
