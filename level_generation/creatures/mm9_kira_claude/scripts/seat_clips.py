#!/usr/bin/env python3
"""Kira's seated Argument clips lowered onto her chair (2026-11-11).

KIRA.abc's sitting animations (Sit, Applause, Sc2_KIRA5 ... Sc2_KIRA14) keep her standing hips: MM9 draws her pelvis at
her box centre, 92 units over the stage floor, her thighs' underside 81 over it, the chair's seat at 56 (Chair.abc).
Our clips carry that (pelvis 0.90, toes 0.34 over the origin), and the stage actor stands on the hall's floor, so she
hovered in front of her chair in the council cinematic. The actor cannot go under the floor (the cinematic's moves put
an actor on its floor), so the clips come down instead: their root (`Scene Root`) by SEATED_DROP game units, her thighs
then on mm9_deco_chair's seat (its top 0.683 of 1.46 at 119.3 high: 55.8). Sc2_KIRA16b (she stands up) keeps the drop
until her hips rise (RISE_START) and ends it at STOOD_DROP, which puts her feet (0.36 over the origin) on the floor for
the walk that follows.

Runs on the installed source (after add_sockets.py, whose sockets it keeps) and writes export/mm9_kira_seated.glb:

    python3 level_generation/creatures/mm9_kira_claude/scripts/seat_clips.py
    python3 tools/install_model.py --world mm9 --name mm9_kira.glb level_generation/creatures/mm9_kira_claude/export/mm9_kira_seated.glb

A clip already lowered (its extras `seat_drop`) is left alone, so a rerun changes nothing.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "level_generation/props/mm9_held_items_claude/scripts"))
import heldlib  # noqa: E402

SOURCE = ROOT / "assets_source/worlds/mm9/models/mm9_kira.glb"
OUT = Path(__file__).resolve().parents[1] / "export/mm9_kira_seated.glb"
BINDING_SCALE = 100.0           # actors.yml MM9 251: game units per model unit
SEATED_DROP = 24.0              # game units: thighs' underside 79 over the origin onto the 55.8 seat
STOOD_DROP = 35.0               # game units: Sc2_KIRA16b's last frame, feet 36 over the origin onto the floor
SEATED = ("Sit", "Applause", "Sc2_KIRA5", "Sc2_Kira7", "Sc2_Kira9b", "Sc2_KIRA12", "Sc2_KIRA14")
RISE = ("Sc2_KIRA16b", 1.5)     # the stand-up and the time her hips start to rise


def world_matrix(document: dict, index: int) -> np.ndarray:
    parents = {child: i for i, node in enumerate(document["nodes"]) for child in node.get("children", [])}
    matrix = np.eye(4)
    chain = []
    while index in parents:
        index = parents[index]
        chain.append(index)
    for i in reversed(chain):
        node = document["nodes"][i]
        local = heldlib.trs(node.get("translation", [0, 0, 0]), node.get("rotation", [0, 0, 0, 1]),
                            node.get("scale", [1, 1, 1]))
        matrix = matrix @ local
    return matrix


def main() -> int:
    document, blob = heldlib.read_glb(SOURCE)
    blob = bytearray(blob)
    names = [node.get("name") for node in document["nodes"]]
    root = names.index("Scene Root")
    # A drop straight down in the model, in the root's parent frame (its translation keys' frame)
    parent = world_matrix(document, root)
    down = np.linalg.inv(parent[:3, :3]) @ np.array([0.0, -1.0 / BINDING_SCALE, 0.0])
    plan = {name: (lambda t: np.full_like(t, SEATED_DROP)) for name in SEATED}
    rise_clip, rise_start = RISE

    def rise(times: np.ndarray) -> np.ndarray:
        end = float(times.max())
        f = np.clip((times - rise_start) / max(end - rise_start, 1e-6), 0.0, 1.0)
        return SEATED_DROP + (STOOD_DROP - SEATED_DROP) * f

    plan[rise_clip] = rise
    done = []
    for clip in document["animations"]:
        if clip["name"] not in plan or "seat_drop" in clip.get("extras", {}):
            continue
        channel = next(c for c in clip["channels"]
                       if c["target"]["node"] == root and c["target"]["path"] == "translation")
        sampler = clip["samplers"][channel["sampler"]]
        times = heldlib.accessor(document, bytes(blob), sampler["input"]).reshape(-1).astype(np.float64)
        values = heldlib.accessor(document, bytes(blob), sampler["output"]).astype(np.float64).reshape(-1, 3)
        values = values + plan[clip["name"]](times)[:, None] * down[None, :]
        # new key data (accessors may be shared between clips)
        while len(blob) % 4:
            blob.append(0)
        raw = values.astype(np.float32).tobytes()
        document["bufferViews"].append({"buffer": 0, "byteOffset": len(blob), "byteLength": len(raw)})
        blob.extend(raw)
        document["accessors"].append({"bufferView": len(document["bufferViews"]) - 1, "componentType": 5126,
                                      "count": len(values), "type": "VEC3"})
        sampler["output"] = len(document["accessors"]) - 1
        clip.setdefault("extras", {})["seat_drop"] = [SEATED_DROP, STOOD_DROP] if clip["name"] == rise_clip \
            else SEATED_DROP
        done.append(clip["name"])
    document["buffers"][0]["byteLength"] = len(blob)
    heldlib.write_glb(OUT, document, bytes(blob))
    print(f"lowered {done or 'nothing (already lowered)'} -> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
