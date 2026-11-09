"""
MM9's trees, bushes and flowers on the outdoor regions as MM6-MM8 3D decorations (DECORATIONS_AND_GRASS.md step 3:
trees are never MM9's). Chosen by look from review/tree_candidates.png (2026-11-04): MM9's are northern conifers.

  MM9                       ours (weights)
  tree02, tree04 (pine with an irregular crown)       MM6 6tree18 (dark dense conifer) 2, MM7 tree60 (hemlock) 1
  tree01b (the same pine, Dark Passageway)           as tree02
  tree05 (conical spruce)                             MM8 tree29 1, MM8 tree30 1 (pines)
  tree06 (tall narrow spruce)                         MM7 tree60 1, MM8 tree30 1
  snowtree1, snowtree2 (snow-covered spruces)         MM7 tree36 (snow spruce) 2, MM6 snotre01 1, MM6 snotre05 1
  deadtree3, deadtree4 (bare black trees)             MM8 tree28 1, MM6 6tree27 1
  bush01 (fern)                                       MM7 bush03 (fern)
  bush02 (broad leaves)                               MM7 bush02 (broad leaves)
  flowers01, flowers03 (roses and daisies in grass)   MM7 flower03 (roses) 1, flower04 (cabbage roses) 1, flower10 1

Each keeps MM9's size: the MM9 model's height x the object's Scale, in 25-unit steps, as an MM9 world row
`mm9v_<ours>_<height>` binding our model at that height (rows.py); our model's other binding keys (LOD distances,
offsets) as the engine's outdoor binding has them. The species of an object is picked by its object index (stable).
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[4]
CHOICES = {
    "tree01b": [("6tree18", 2), ("tree60", 1)],
    "tree02": [("6tree18", 2), ("tree60", 1)],
    "tree04": [("6tree18", 2), ("tree60", 1)],
    "tree05": [("tree29", 1), ("tree30", 1)],
    "tree06": [("tree60", 1), ("tree30", 1)],
    "snowtree1": [("tree36", 2), ("snotre01", 1), ("snotre05", 1)],
    "snowtree2": [("tree36", 2), ("snotre01", 1), ("snotre05", 1)],
    "deadtree3": [("tree28", 1), ("6tree27", 1)],
    "deadtree4": [("tree28", 1), ("6tree27", 1)],
    "bush01": [("bush03", 1)],
    "bush02": [("bush02", 1)],
    "flowers01": [("flower03", 1), ("flower04", 1), ("flower10", 1)],
    "flowers03": [("flower03", 1), ("flower04", 1), ("flower10", 1)],
}
# MM9 model heights at scale 1 in our units (the ABC's LOD0 height x 2.56; tree01b/02/04/05/06: their props' meta,
# tree01b level_generation/props/mm9_darkpassageway_claude/work/tree01b_meta.json).
MM9_HEIGHT = {"tree01b": 1555.6, "tree02": 1707.9, "tree04": 1707.9, "tree05": 1274.0, "tree06": 990.2, "snowtree1": 525.6,
              "snowtree2": 1100.3, "deadtree3": 1102.1, "deadtree4": 1057.3, "bush01": 45.3, "bush02": 42.2,
              "flowers01": 13.8, "flowers03": 10.2}
KIND = {"tree": "tree", "snow": "tree", "dead": "tree", "bush": "bush", "flow": "flowers"}
STEP = 25.0
# How far each kind is set into the ground (roots, the base of a clump on a slope).
SINK = {"tree": 8.0, "bush": 3.0, "flowers": 1.0}


def mm9_species(model_path: str) -> str | None:
    stem = model_path.replace("\\", "/").split("/")[-1].lower().removesuffix(".abc")
    return stem if stem in CHOICES else None


def kind(species: str) -> str:
    return KIND[species[:4]]


def pick(species: str, object_index: int, region: str) -> str:
    choices = CHOICES[species]
    total = sum(w for _, w in choices)
    roll = int(hashlib.sha1(f"{region}:{object_index}".encode()).hexdigest(), 16) % total
    for name, weight in choices:
        if roll < weight:
            return name
        roll -= weight
    return choices[-1][0]


def engine_bindings() -> dict:
    data = yaml.safe_load((REPO / "assets_dev/engine/models/decorations.yml").read_text())
    return {b["name"].lower(): b for b in data["decorations"]}


def row(species: str, ours: str, scale: float, engine: dict) -> dict:
    height = max(STEP, round(MM9_HEIGHT[species] * scale / STEP) * STEP)
    name = f"mm9v_{ours}_{int(height)}"
    binding = {k: v for k, v in engine[ours.lower()].items() if k not in ("name", "height", "height_jitter")}
    binding["height"] = float(height)
    k = kind(species)
    radius = 0 if k == "flowers" else 16 if k == "bush" else int(min(64, max(20, height * 0.025)))
    return {"name": name, "hint": k, "radius": radius, "height": height, "binding": binding, "sink": SINK[k]}
