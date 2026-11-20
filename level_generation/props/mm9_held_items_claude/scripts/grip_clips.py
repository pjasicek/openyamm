#!/usr/bin/env python3
"""A hand closed round a held item in the clips that hold it, and a model's own pose clip for a prop MM9 draws
holding one (2026-11-11).

Our MM9 bodies carry grafted five-finger hands whose fingers follow MM9's two-bone mitten loosely (finger_alias), so
a hand that holds a piece of MM9's model (Ercc's cup) stays open round it. Here the fifteen finger bones of one hand
take a fixed grip (a turn about each bone's own flexion axis, +y on the MPFB hands, from its rest) in every listed
clip. A pose clip (MM9's Ercc.ABC loops its own `sitting`, the cup at the chest; our body's `sitting` is
PeasantSeated's, hands in the lap) is added as a still clip at the first frame of the clip MM9's pose matches.

    python3 level_generation/props/mm9_held_items_claude/scripts/grip_clips.py [model ...] [--out <dir>]
                                                                                 # export/<model>.glb

Reads the installed source (assets_source/worlds/mm9/models/<model>.glb, with its sockets); install the export with
tools/install_model.py --world mm9. Rerunning starts from the installed source: the grip replaces the finger keys and
a pose clip of the same name is replaced.
"""
from __future__ import annotations

import copy
import sys
from pathlib import Path

import numpy as np

import heldlib

PROJECT = Path(__file__).resolve().parents[1]
SOURCES = heldlib.ROOT / "assets_source/worlds/mm9/models"

# Flexion (degrees about the bone's +y) of each joint of the closed hand: fingers round a goblet's stem, the thumb
# across it.
CUP_GRIP = {"Index": (38.0, 70.0, 45.0), "Middle": (42.0, 75.0, 45.0), "Ring": (46.0, 75.0, 45.0),
            "Pinky": (50.0, 70.0, 40.0), "Thumb": (20.0, 25.0, 20.0)}
# model: (hand side, grip, clips that hold the item, {pose clip: (clip whose first frame it holds, seconds)},
# {socket: its position in its hand's frame}: the item's grip in the closed hand; absolute, so a rerun on a source
# this script wrote keeps it)
GRIPS = {
    # Ercc (ErccSpeech.scr): the cup in his right hand while he sits (Ercc.ABC `sitting`: ercc01a's first frame,
    # the cup at the chest), rants (ercc01a-c), drinks and passes out (ercc02, held by ercc_out). MM9's cup01 frame
    # puts the stem against the open hand's palm (add_sockets.py: -0.0892, -0.0539, 0.0478); moved by (-2.5, -3.2,
    # -3.6) cm the stem runs through the fist, the bowl over the index finger, the foot under the little finger.
    "mm9_peasantm2": ("R", CUP_GRIP, ("ercc01a", "ercc01b", "ercc01c", "ercc02", "ercc_out"),
                      {"ercc_sitting": ("ercc01a", 2.03)}, {"Socket_Cup": (-0.1142, -0.0859, 0.0118)}),
}


def quat_mul(a, b) -> np.ndarray:
    x1, y1, z1, w1 = a
    x2, y2, z2, w2 = b
    return np.array([w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2, w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2,
                     w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2, w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2])


def flex(degrees: float) -> np.ndarray:
    half = np.radians(degrees) / 2.0
    return np.array([0.0, np.sin(half), 0.0, np.cos(half)])


class Glb:
    def __init__(self, path: Path):
        self.document, blob = heldlib.read_glb(path)
        self.blob = bytearray(blob)

    def add_accessor(self, values: np.ndarray, kind: str) -> int:
        data = values.astype(np.float32).tobytes()
        self.blob += b"\0" * (-len(self.blob) % 4)
        views = self.document["bufferViews"]
        views.append({"buffer": 0, "byteOffset": len(self.blob), "byteLength": len(data)})
        self.blob += data
        accessor = {"bufferView": len(views) - 1, "componentType": 5126, "count": int(values.shape[0]), "type": kind}
        if kind == "SCALAR":
            accessor["min"], accessor["max"] = [float(values.min())], [float(values.max())]
        self.document["accessors"].append(accessor)
        return len(self.document["accessors"]) - 1

    def write(self, path: Path) -> None:
        self.document["buffers"][0]["byteLength"] = len(self.blob) + (-len(self.blob) % 4)
        heldlib.write_glb(path, self.document, bytes(self.blob))


def grip(model: str, out_dir: Path) -> Path:
    side, curls, clips, poses, sockets = GRIPS[model]
    glb = Glb(SOURCES / f"{model}.glb")
    document = glb.document
    names = [node.get("name") for node in document["nodes"]]
    held = {}
    for finger, angles in curls.items():
        for joint, degrees in enumerate(angles, 1):
            index = names.index(f"Bip01 {side} {finger}{joint}")
            rest = document["nodes"][index].get("rotation", [0.0, 0.0, 0.0, 1.0])
            held[index] = quat_mul(rest, flex(degrees))

    def close_hand(animation: dict) -> None:
        done = set()
        for channel in animation["channels"]:
            node = channel["target"]["node"]
            if node in held and channel["target"]["path"] == "rotation":
                sampler = animation["samplers"][channel["sampler"]]
                count = document["accessors"][sampler["output"]]["count"]
                sampler["output"] = glb.add_accessor(np.tile(held[node], (count, 1)), "VEC4")
                done.add(node)
        missing = [names[node] for node in held if node not in done]
        assert not missing, (animation["name"], missing)

    for socket, position in sockets.items():
        document["nodes"][names.index(socket)]["translation"] = [float(v) for v in position]
    animations = document["animations"]
    for name in clips:
        close_hand(heldlib.glb_clip(document, name))
    for name, (source, seconds) in poses.items():
        animations[:] = [a for a in animations if a.get("name") != name]
        clip = copy.deepcopy(heldlib.glb_clip(document, source))
        times = glb.add_accessor(np.array([[0.0], [seconds]]), "SCALAR")
        for sampler in clip["samplers"]:
            values = heldlib.accessor(document, bytes(glb.blob), sampler["output"])
            kind = document["accessors"][sampler["output"]]["type"]
            sampler["input"] = times
            sampler["output"] = glb.add_accessor(np.repeat(values[:1], 2, axis=0), kind)
            sampler["interpolation"] = "LINEAR"
        clip["name"] = name
        close_hand(clip)
        animations.append(clip)
    out = out_dir / f"{model}.glb"
    glb.write(out)
    return out


def main() -> None:
    args = sys.argv[1:]
    out_dir = PROJECT / "export"
    if "--out" in args:          # a trial export elsewhere
        at = args.index("--out")
        out_dir = Path(args[at + 1])
        del args[at:at + 2]
    for model in args or list(GRIPS):
        print(grip(model, out_dir))


if __name__ == "__main__":
    main()
