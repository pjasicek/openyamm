#!/usr/bin/env python3
"""Manifest of the gait rollout's composite viewer (index.html here): every MM6-MM8 3D actor model whose locomotion
binding or clip set changed against git HEAD (the 2026-10-31 sprint pilot and gait rollout).

Per model: the installed source GLB, its attachments, its clips (new ones marked: absent from the GLB at the
assets_source submodule's HEAD), the binding groups (descriptors sharing one old and one new walk/run/sprint binding)
and, per descriptor, the in-game playback rates before and after (gait_audit.py: Standard wandering and chasing, MAW
wandering and chasing).

    python3 level_generation/creatures/gait_rollout_20261031/viewer/build_manifest.py
"""
import json
import struct
import subprocess
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
ROLLOUT = HERE.parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROLLOUT.parent / "claude_shared/postprocess"))
sys.path.insert(0, str(ROLLOUT.parent / "claude_shared/floor"))
import gait_audit  # noqa: E402

WORLDS = ("mm6", "mm7", "mm8")
KEYS = ("run", "stride_length", "run_stride_length", "sprint", "sprint_stride_length", "gait_rate")
PILOT = {"mm6_ogr.glb", "mm6_kni.glb", "mm6_rat.glb", "mm7_m382.glb", "mm8_m452.glb"}


def glb_json(data):
    length = struct.unpack("<I", data[12:16])[0]
    return json.loads(data[20:20 + length])


def clip_names(data):
    return [animation.get("name", "") for animation in glb_json(data).get("animations", [])]


def clip_durations(data):
    """Clip name -> length in seconds (the latest keyframe time of its channels)."""
    gltf = glb_json(data)
    length = struct.unpack("<I", data[12:16])[0]
    binary_start = 20 + length + 8
    result = {}
    for animation in gltf.get("animations", []):
        end = 0.0
        for sampler in animation["samplers"]:
            accessor = gltf["accessors"][sampler["input"]]
            if "max" in accessor:
                end = max(end, float(accessor["max"][0]))
            else:
                view = gltf["bufferViews"][accessor["bufferView"]]
                offset = binary_start + view.get("byteOffset", 0) + accessor.get("byteOffset", 0)
                count = accessor["count"]
                end = max(end, struct.unpack_from("<f", data, offset + 4 * (count - 1))[0])
        result[animation.get("name", "")] = round(end, 4)
    return result


def head_file(repo, path):
    result = subprocess.run(["git", "-C", str(repo), "show", f"HEAD:{path}"], capture_output=True)
    return result.stdout if result.returncode == 0 else None


def binding(actor):
    animation = actor.get("animation") or {}
    result = {"walk": actor["clips"]["walking"]}
    result.update({key: animation[key] for key in KEYS if key in animation})
    return result


def rates(world, actors, ruleset):
    """descriptor -> {state: [clip, played rate, slide]} for the actors given."""
    result = {}
    for row in gait_audit.audit(world, None, actors, ruleset):
        result[row["descriptor"]] = {state["state"]: [state["clip"], state["rate"], state["slide"]]
                                     for state in row["rows"]}
    return result


def main():
    packages = json.loads((ROLLOUT / "packages.json").read_text())
    package_of = {key.split("/")[1]: pid for pid, keys in packages.items() for key in keys}
    models = {}
    for world in WORLDS:
        path = f"assets_dev/worlds/{world}/models/actors.yml"
        new_actors = yaml.safe_load((ROOT / path).read_text())["actors"]
        old_actors = {a["descriptor"]: a for a in yaml.safe_load(head_file(ROOT, path))["actors"]}
        changed = [a for a in new_actors if "stride_length" in (a.get("animation") or {})
                   and a["descriptor"] in old_actors
                   and binding(a) != binding(old_actors[a["descriptor"]])]
        changed_models = {a["model"] for a in changed}
        # Models whose clip set changed though no binding did (none expected) are picked up below too.
        for actor in new_actors:
            if "stride_length" not in (actor.get("animation") or {}):
                continue
            source = ROOT / "assets_source" / actor["model"]
            if actor["model"] not in changed_models:
                head = head_file(ROOT / "assets_source", actor["model"])
                if head is None or clip_names(head) == clip_names(source.read_bytes()):
                    continue
                changed_models.add(actor["model"])
        old_list = [old_actors.get(a["descriptor"], a) for a in new_actors]
        old_rates = {r: rates(world, old_list, r) for r in ("standard", "maw")}
        new_rates = {r: rates(world, new_actors, r) for r in ("standard", "maw")}
        for actor in new_actors:
            if actor["model"] not in changed_models:
                continue
            name = actor["descriptor"]
            entry = models.get(actor["model"])
            if entry is None:
                data = (ROOT / "assets_source" / actor["model"]).read_bytes()
                head = head_file(ROOT / "assets_source", actor["model"])
                old_clips = set(clip_names(head)) if head else set()
                glb = Path(actor["model"]).name
                entry = models[actor["model"]] = {
                    "id": glb.removesuffix(".glb"),
                    "path": actor["model"],
                    "label": name.rsplit(" ", 1)[0] if name[-1:].isalpha() and name[-2:-1] == " " else name,
                    "worlds": [],
                    "packages": ([["pilot"] if glb in PILOT else []][0] + ([package_of[glb]] if glb in package_of else []))
                    or ["binding only"],
                    "attachments": [{"path": a["model"], "node": a["node"]} for a in actor.get("attachments", [])],
                    "clips": {clip: {"duration": duration, "new": clip not in old_clips}
                              for clip, duration in clip_durations(data).items()},
                    "groups": [],
                    "tiers": [],
                }
            if world not in entry["worlds"]:
                entry["worlds"].append(world)
            old, new = binding(old_actors[name]), binding(actor)
            group = next((g for g in entry["groups"] if g["old"] == old and g["new"] == new), None)
            if group is None:
                group = {"old": old, "new": new, "descriptors": []}
                entry["groups"].append(group)
            group["descriptors"].append(f"{world}: {name}")
            tier = {"world": world, "descriptor": name, "group": entry["groups"].index(group)}
            for ruleset in ("standard", "maw"):
                for state in ("wander", "chase"):
                    before = old_rates[ruleset].get(name, {}).get(state)
                    after = new_rates[ruleset].get(name, {}).get(state)
                    tier[f"{ruleset}_{state}"] = [before, after]
            entry["tiers"].append(tier)
    result = sorted(models.values(), key=lambda m: (m["worlds"][0], m["label"]))
    (HERE / "manifest.json").write_text(json.dumps({"models": result}, indent=1))
    new_clips = sum(1 for m in result for c in m["clips"].values() if c["new"])
    print(f"{len(result)} models, {new_clips} new clips, "
          f"{sum(len(m['tiers']) for m in result)} descriptors -> {HERE / 'manifest.json'}")


if __name__ == "__main__":
    main()
