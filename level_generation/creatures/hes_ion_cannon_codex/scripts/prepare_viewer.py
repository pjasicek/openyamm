#!/usr/bin/env python3
"""Prepare existing creature-review UI for seven static states; does not launch a browser."""
import copy
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT.parents[2] / "tools"))
from merge_head_material import append_accessor, read_glb, write_glb
from run_creature_review import command

CONFIG = json.loads((PROJECT / "charging_states.json").read_text())


def prepare():
    sources = [PROJECT / "export" / spec["file"] for spec in CONFIG["states"].values()]
    missing = [path.name for path in sources if not path.is_file()]
    if missing:
        raise ValueError("Awaiting final Meshy exports: " + ", ".join(missing))
    viewer = PROJECT / "review/viewer"
    models = []
    for state, source in zip(CONFIG["states"], sources):
        doc, binary = read_glb(source)
        doc = copy.deepcopy(doc)
        # The shared animation viewer needs a clip: animate an empty node only in its review copy.
        node = len(doc.setdefault("nodes", []))
        doc["nodes"].append({"name": "Review_Static", "translation": [0, 0, 0]})
        doc["scenes"][doc.get("scene", 0)]["nodes"].append(node)
        times = append_accessor(doc, binary, np.array([0, 1], dtype=np.float32),
                                {"componentType": 5126, "type": "SCALAR"}, None)
        values = append_accessor(doc, binary, np.zeros((2, 3), dtype=np.float32),
                                 {"componentType": 5126, "type": "VEC3"}, None)
        for accessor in (times, values):
            doc["bufferViews"][doc["accessors"][accessor]["bufferView"]].pop("target", None)
        doc["accessors"][times].update(min=[0], max=[1])
        doc["animations"] = [{"name": "Standing", "samplers": [{"input": times, "output": values}],
                              "channels": [{"sampler": 0, "target": {"node": node, "path": "translation"}}]}]
        target = viewer / source.name
        write_glb(target, doc, binary)
        digest = hashlib.sha256(target.read_bytes()).hexdigest()
        models.append({"id": state, "label": "Great ion cannon — " + state,
                       "revision": digest[:12], "sha256": digest, "url": target.name + "?v=" + digest[:12]})
    manifest = {"revision": "ion_cannon_static_states", "model": sources[0].name, "default_model": "rest",
                "default_clip": "Standing", "feedback": "feedback/user_feedback.json", "models": models,
                "clips": {"Standing": {"label": "Static state", "duration": 1, "mode": "loop",
                    "provenance": "Static Meshy model; viewer-only empty-node hold, no authored motion.",
                    "anchors": [{"time": 0, "label": "Frozen v1 and orthogonal masters", "phase": "Approved appearance references",
                                 "source_images": ["../../references_hd/" + name for name in
                                     ["00_three_quarter.png", "01_front.png", "03_left.png", "02_back.png", "04_right.png"]]}]}}}
    (viewer / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    for model in models:
        command(PROJECT, "check", 8912, [], model["id"])
    print("Seven viewer choices prepared; no browser opened.")


if __name__ == "__main__":
    prepare()
