"""Check each pilot frame against the MM6-MM8 consensus for its slot, and list what the engine shows it for.

Input: measurements.json from measure.py. Every feature is a change from the family's own frame 01, so identity
cancels out. A slot's defining features are those where at least 70 % of the reference human families change in
the same direction by more than the feature's floor. The pilot frame passes a feature when it changes the same way
by at least 35 % of the consensus median. Features the pilot changes strongly where the consensus does not are
reported as extras. Squint is not counted when closed eyes already define the slot (the model reads closed lids
as squint). A missing feature that the template family pc07 also lacks is reported as "template": the pilot
follows a real MM6-MM8 family there, not the majority. Writes verification.json and prints a table.
"""

import json
import re
from collections import defaultdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
PILOT = "mm9pc03"
MIN_DETECTED = 48

# name: (floor, label for positive change, label for negative change)
FEATURES = {
    "eyes_closed": (0.15, "eyes close", "eyes open wider"),
    "eye_wide": (0.15, "eyes widen", "eyes less wide"),
    "squint": (0.15, "squint", "less squint"),
    "gaze_up": (0.15, "gaze up", "gaze down"),
    "gaze_left": (0.15, "gaze to its left", "gaze to its right"),
    "jaw_open": (0.12, "mouth opens", "mouth closes"),
    "smile": (0.15, "smile", "less smile"),
    "frown": (0.10, "mouth corners down", "corners up"),
    "pucker": (0.15, "lips pucker/funnel", "lips relax"),
    "brow_up": (0.15, "inner brows up", "brows lower"),
    "brow_down": (0.15, "brows down (anger)", "brows relax"),
    "yaw": (6.0, "head turns (+yaw)", "head turns (-yaw)"),
    "pitch": (6.0, "head pitches (+)", "head pitches (-)"),
    "roll": (6.0, "head rolls (+)", "head rolls (-)"),
    "height": (0.08, "taller", "head lower/partly out of frame"),
    "green": (0.012, "greener skin", "less green"),
    "red": (0.015, "redder skin", "less red"),
    "saturation": (0.30, "more saturated", "desaturated (grey/stone)"),
}


def features(row, base):
    out = {}
    if "height" in FEATURES and base["head_height"]:
        out["height"] = row["head_height"] / base["head_height"] - 1
    out["green"] = row["chroma"][1] - base["chroma"][1]
    out["red"] = row["chroma"][0] - base["chroma"][0]
    out["saturation"] = row["saturation"] / max(base["saturation"], 1e-6) - 1
    if "shapes" not in row or "shapes" not in base:
        return out
    s, b = row["shapes"], base["shapes"]

    def mean(shape, *names):
        return np.mean([shape[n] for n in names])

    def gaze_left(shape):
        return (shape["eyeLookOutLeft"] + shape["eyeLookInRight"] - shape["eyeLookInLeft"]
                - shape["eyeLookOutRight"]) / 2

    pairs = {
        "eyes_closed": ("eyeBlinkLeft", "eyeBlinkRight"), "eye_wide": ("eyeWideLeft", "eyeWideRight"),
        "squint": ("eyeSquintLeft", "eyeSquintRight"), "jaw_open": ("jawOpen",),
        "smile": ("mouthSmileLeft", "mouthSmileRight"), "frown": ("mouthFrownLeft", "mouthFrownRight"),
        "pucker": ("mouthPucker", "mouthFunnel"), "brow_up": ("browInnerUp",),
        "brow_down": ("browDownLeft", "browDownRight"),
    }
    for name, keys in pairs.items():
        out[name] = mean(s, *keys) - mean(b, *keys)
    out["gaze_up"] = (mean(s, "eyeLookUpLeft", "eyeLookUpRight") - mean(s, "eyeLookDownLeft", "eyeLookDownRight")
                      - mean(b, "eyeLookUpLeft", "eyeLookUpRight") + mean(b, "eyeLookDownLeft", "eyeLookDownRight"))
    out["gaze_left"] = gaze_left(s) - gaze_left(b)
    for name in ("yaw", "pitch", "roll"):
        out[name] = row[name] - base[name]
    return out


def slot_usage():
    """Slot -> list of what shows it, from the frame table, face animations and the idle picker."""
    enum_text = (ROOT / "game/tables/PortraitEnums.h").read_text()
    block = enum_text[enum_text.index("enum class PortraitId"):]
    block = block[:block.index("};")]
    names = {int(v): k for k, v in re.findall(r"(\w+)\s*=\s*(\d+)", block)}
    by_portrait = defaultdict(list)
    current = None
    for line in (ROOT / "assets_dev/engine/data_tables/portrait_frame_data.txt").read_text().splitlines()[3:]:
        cells = line.split("\t")
        if len(cells) < 5 or not cells[0].strip().isdigit():
            continue
        portrait, texture = int(cells[0]), int(cells[1])
        if portrait != 0:
            current = portrait
        by_portrait[current].append(texture)
    events = defaultdict(list)
    for line in (ROOT / "assets_dev/engine/data_tables/face_animations.txt").read_text().splitlines()[1:]:
        cells = line.split("\t")
        if len(cells) >= 3:
            for expression in cells[2].split(","):
                events[expression.strip()].append(cells[1])
    idle_text = (ROOT / "game/gameplay/GameplayScreenRuntime.cpp").read_text()
    idle_block = idle_text[idle_text.index("PortraitId pickIdlePortrait"):]
    idle_block = idle_block[:idle_block.index("\n}\n")]
    idle = set(re.findall(r"PortraitId::(\w+)", idle_block))
    usage = defaultdict(list)
    for portrait, textures in by_portrait.items():
        name = names.get(portrait, str(portrait))
        role = name
        if len(set(textures)) > 1:
            role += " (animation " + ",".join(map(str, textures)) + ")"
        tags = events.get(name, [])
        if name in idle:
            tags = ["idle"] + tags
        if tags:
            role += ": " + ", ".join(tags)
        for texture in sorted(set(textures)):
            usage[texture].append(role)
    return usage


def main():
    data = json.loads((HERE / "measurements.json").read_text())
    mapping = json.loads((HERE / "mapping.json").read_text())
    references = [f for f, rows in data.items()
                  if f != PILOT and sum("shapes" in r for r in rows.values()) >= MIN_DETECTED]
    usage = slot_usage()
    report = {"reference_families": references, "slots": {}}
    print(f"{len(references)} reference families\n")
    for number in range(1, 57):
        key = f"{number:02d}"
        reference = defaultdict(list)
        for family in references:
            for name, value in features(data[family][key], data[family]["01"]).items():
                reference[name].append(value)
        pilot = features(data[PILOT][key], data[PILOT]["01"])
        template = features(data["pc07"][key], data["pc07"]["01"])
        defining, extras = [], []
        closed_eyes = False
        for name, (floor, positive, negative) in FEATURES.items():
            values = np.array(reference.get(name, []))
            if len(values) < 10:
                continue
            median = float(np.median(values))
            agree = float(np.mean(np.sign(values) == np.sign(median)) if median else 0)
            strong = abs(median) > floor and float(np.mean(np.abs(values) > floor)) >= .5 and agree >= .7
            value = pilot.get(name)
            if strong and name == "squint" and closed_eyes:
                continue
            if strong:
                closed_eyes = closed_eyes or (name == "eyes_closed" and median > 0)
                label = positive if median > 0 else negative

                def shows(v):
                    return v is not None and np.sign(v) == np.sign(median) and abs(v) >= .35 * abs(median)

                defining.append({"feature": name, "label": label, "consensus": round(median, 3),
                                 "agreement": round(agree, 2), "pilot": None if value is None else round(value, 3),
                                 "pc07": None if template.get(name) is None else round(template[name], 3),
                                 "ok": bool(shows(value)), "pc07_ok": bool(shows(template.get(name)))})
            elif value is not None and abs(value) > 2.5 * floor and abs(value) > abs(median) + 2 * floor:
                label = positive if value > 0 else negative
                extras.append({"feature": name, "label": label, "pilot": round(value, 3),
                               "consensus": round(median, 3)})
        missing_all = [d for d in defining if not d["ok"]]
        status = ("no-face" if "shapes" not in data[PILOT][key] and number != 1 else
                  "pass" if not missing_all and not extras else
                  "check" if not missing_all else
                  "template" if all(not d["pc07_ok"] for d in missing_all) else "mismatch")
        report["slots"][key] = {"meaning": mapping[str(number)]["meaning"], "used_for": usage.get(number, []),
                                "status": status, "defining": defining, "extras": extras}
        missing = [d["label"] for d in defining if not d["ok"]]
        line = f"{key} {status:8} {mapping[str(number)]['meaning'][:34]:34}"
        line += " | wants: " + (", ".join(d["label"] for d in defining) or "-")
        if missing:
            line += " | MISSING: " + ", ".join(missing)
        if extras:
            line += " | EXTRA: " + ", ".join(e["label"] for e in extras)
        print(line)
    (HERE / "verification.json").write_text(json.dumps(report, indent=1) + "\n")


if __name__ == "__main__":
    main()
