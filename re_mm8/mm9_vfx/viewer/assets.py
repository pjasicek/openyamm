"""Read-only preview decoders. No imports from OpenMM9 or third-party model readers."""

import binascii
from functools import lru_cache
import hashlib
from pathlib import Path
import struct
import sys
import zlib

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from inspect_assets import Reader, asset_index, read_fxf, read_sprite
from authored import load_authored


def png(width, height, rgba):
    def chunk(tag, data):
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", binascii.crc32(tag + data))

    rows = b"".join(b"\0" + rgba[y * width * 4:(y + 1) * width * 4] for y in range(height))
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">2I5B", width, height, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(rows, 3)) + chunk(b"IEND", b""))


def decode_dtx(data):
    """Version -5 top mip. Identifier zero is native legacy BGRA32, not a palette."""
    reader = Reader(data)
    resource, version, width, height, mips, sections, flags, user = reader.unpack("<Ii4H2I")
    extra = reader.take(12)
    reader.take(128)
    kind = extra[2]
    if resource != 0 or version != -5 or not (0 < width <= 8192 and 0 < height <= 8192):
        raise ValueError("Unsupported DTX header")
    result = bytearray(width * height * 4)
    if kind in (0, 3):
        source = reader.take(len(result))
        result[0::4], result[1::4], result[2::4], result[3::4] = (
            source[2::4], source[1::4], source[0::4], source[3::4])
    elif kind in (4, 5, 6):
        for y in range(0, height, 4):
            for x in range(0, width, 4):
                alpha = reader.take(8) if kind != 4 else None
                c0, c1, indices = reader.unpack("<HHI")
                colors = []
                for c in (c0, c1):
                    r, g, b = (c >> 11) & 31, (c >> 5) & 63, c & 31
                    colors.append(((r << 3) | (r >> 2), (g << 2) | (g >> 4), (b << 3) | (b >> 2), 255))
                if c0 > c1 or kind != 4:
                    colors.extend(tuple((colors[0][c] * (3 - i) + colors[1][c] * i) // 3
                                        for c in range(4)) for i in (1, 2))
                else:
                    colors += [tuple((colors[0][c] + colors[1][c]) // 2 for c in range(4)), (0, 0, 0, 0)]
                if kind == 6:
                    a0, a1 = alpha[:2]
                    count = 7 if a0 > a1 else 5
                    alphas = [a0, a1] + [((count - i) * a0 + i * a1) // count for i in range(1, count)]
                    if count == 5:
                        alphas += [0, 255]
                    alpha_bits = int.from_bytes(alpha[2:], "little")
                for i in range(16):
                    px, py = x + i % 4, y + i // 4
                    color = list(colors[(indices >> (2 * i)) & 3])
                    if kind == 5:
                        color[3] = ((int.from_bytes(alpha, "little") >> (4 * i)) & 15) * 17
                    elif kind == 6:
                        color[3] = alphas[(alpha_bits >> (3 * i)) & 7]
                    if px < width and py < height:
                        offset = (py * width + px) * 4
                        result[offset:offset + 4] = bytes(color)
    else:
        raise ValueError(f"Unsupported DTX pixel format {kind}")
    return width, height, result


def inverse_matrix(values):
    rows = [list(values[i * 4:i * 4 + 4]) + [float(i == j) for j in range(4)] for i in range(4)]
    for col in range(4):
        pivot = max(range(col, 4), key=lambda row: abs(rows[row][col]))
        rows[col], rows[pivot] = rows[pivot], rows[col]
        divisor = rows[col][col]
        if abs(divisor) < 1e-12:
            raise ValueError("Singular ABC bind matrix")
        rows[col] = [v / divisor for v in rows[col]]
        for row in range(4):
            if row != col:
                amount = rows[row][col]
                rows[row] = [a - amount * b for a, b in zip(rows[row], rows[col])]
    return [rows[row][col + 4] for col in range(4) for row in range(4)]


def read_abc(path):
    """ABC v9–13: highest LOD, skeleton and first animation, in native Y-up units.

    Section layouts cross-checked against local format readers; this decoder is newly authored.
    Model animation is a preview implementation, not a verified original-engine tracker.
    """
    reader = Reader(path.read_bytes())

    def string():
        return reader.text(reader.unpack("<H")[0])

    sections, next_offset = {}, 0
    while next_offset != -1:
        if next_offset in sections.values() or not 0 <= next_offset < len(reader.data):
            raise ValueError("Invalid ABC section chain")
        reader.offset = next_offset
        name = string()
        next_offset = reader.unpack("<i")[0]
        if name in sections:
            raise ValueError("Repeated ABC section")
        sections[name] = reader.offset
    reader.offset = sections["Header"]
    version = reader.unpack("<I")[0]
    if version not in (9, 10, 11, 12, 13):
        raise ValueError(f"Unsupported ABC version {version}")
    reader.take(8)
    node_count = reader.unpack("<I")[0]
    reader.take(20)
    lod_count = reader.unpack("<I")[0]
    reader.take(20 if version >= 13 else 16)
    command = string()
    reader.offset = sections["Pieces"]
    _, piece_count = reader.unpack("<2I")
    pieces = []
    for _ in range(piece_count):
        material = reader.unpack("<H")[0]
        reader.take(12 if version > 9 else 8)
        reader.take(2)
        name = string()
        for lod in range(lod_count):
            faces = []
            for _ in range(reader.unpack("<I")[0]):
                faces.append([list(reader.unpack("<ffH")) for _ in range(3)])
            vertices = []
            for _ in range(reader.unpack("<I")[0]):
                weight_count, _ = reader.unpack("<2H")
                weights = []
                for _ in range(weight_count):
                    node, x, y, z, bias = reader.unpack("<I4f")
                    weights.append([node, bias])
                position = list(reader.unpack("<3f"))
                reader.take(12)
                vertices.append({"position": position, "weights": weights})
            if lod == 0:
                pieces.append({"name": name, "material": material, "faces": faces, "vertices": vertices})
    reader.offset = sections["Nodes"]
    nodes, ancestors = [], []
    for _ in range(node_count):
        while ancestors and ancestors[-1][1] == 0:
            ancestors.pop()
        parent = ancestors[-1][0] if ancestors else -1
        if ancestors:
            ancestors[-1][1] -= 1
        name = string()
        index, flags = reader.unpack("<Hb")
        bind = reader.unpack("<16f")
        children = reader.unpack("<I")[0]
        nodes.append({"name": name, "index": index, "parent": parent, "inverseBind": inverse_matrix(bind),
                      "bind": [bind[row * 4 + col] for col in range(4) for row in range(4)]})
        if children:
            ancestors.append([len(nodes) - 1, children])
    animation = None
    if "Animation" in sections:
        reader.offset = sections["Animation"]
        count = reader.unpack("<I")[0]
        if count:
            reader.take(12)
            name = string()
            reader.take(8 if version >= 12 else 4)
            frame_count = reader.unpack("<I")[0]
            times = []
            for _ in range(frame_count):
                times.append(reader.unpack("<I")[0])
                string()
            tracks = []
            for _ in range(node_count):
                if version == 13:
                    reader.take(4)
                frames = []
                for _ in range(frame_count):
                    frames.append(list(reader.unpack("<7f")))
                    if version == 13:
                        reader.take(8)
                tracks.append(frames)
            animation = {"name": name, "times": times, "tracks": tracks}
    return {"version": version, "command": command, "pieces": pieces, "nodes": nodes, "animation": animation}


class Assets:
    def __init__(self, reference):
        self.reference = reference
        self.index = asset_index(reference / "extracted")
        source = reference / "extracted/CLIENTFX/CLIENTFX/SPELLS.fxf"
        groups = read_fxf(source)
        self.sprites = {}
        self.groups = groups
        self.hash = hashlib.sha256(source.read_bytes()).hexdigest()
        self.problems = {}
        for group in groups:
            problems = []
            for key in group["keys"]:
                for prop in key["properties"]:
                    if prop["type"] != 7 or prop["value"].endswith("|..."):
                        continue
                    ref = prop["value"].split("|", 1)[1].replace("\\", "/").lower()
                    if ref not in self.index:
                        problems.append(f"Missing asset: {ref}")
                    elif ref.endswith(".spr") and ref not in self.sprites:
                        sprite = read_sprite(self.index[ref])
                        sprite.pop("fingerprint")
                        sprite["frames"] = [frame.replace("\\", "/").lower() for frame in sprite["frames"]]
                        self.sprites[ref] = sprite
                        problems.extend(f"Missing frame: {f}" for f in sprite["frames"] if f not in self.index)
            self.problems[group["name"]] = sorted(set(problems))

        authored, sprites, self.authored_textures = load_authored()
        self.groups = authored + self.groups
        self.sprites.update(sprites)
        self.problems.update({effect["name"]: [] for effect in authored})

    def catalog(self):
        return {"effects": self.groups, "sprites": self.sprites, "problems": self.problems,
                "sourceHash": self.hash}

    @lru_cache(maxsize=512)
    def texture(self, name):
        if name in self.authored_textures:
            return self.authored_textures[name].read_bytes()
        return png(*decode_dtx(self.index[name].read_bytes()))

    @lru_cache(maxsize=24)
    def model(self, name):
        return read_abc(self.index[name])
