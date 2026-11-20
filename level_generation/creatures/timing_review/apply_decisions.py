#!/usr/bin/env python3
"""Apply the timing review's picks: billboard contact frames and 3D impact markers.

    level_generation/creatures/timing_review/apply_decisions.py [--write]

Without --write it prints what would change. With it, contact frames and attack sound delays go to
assets_dev/engine/rendering/sprite_attack_timing.yml (every sprite sharing the picked frames; "at the end" and a zero
delay remove them) and each reviewed 3D impact becomes the `animation.events` impact of every role bound to that clip in every
descriptor of the model in assets_dev/worlds/<world>/models/actors.yml (comments and layout are kept). A marker that
was only confirmed changes nothing. Sockets picked for a model (`fx|<model>`) replace `animation.sockets` and the ranged
attack's and cast's `glow`, `release`, `glow_scale` and `color` in every descriptor of the model, and the melee attack's
`glow`, `glow_scale` and `color` (a melee glow needs its colour; it has no release); impacts and named `effects` stay.
Rerun build_review_data.py afterwards.
"""
import argparse
import json
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[3]
TOOL = Path(__file__).resolve().parent
TIMING = ROOT / "assets_dev/engine/rendering/sprite_attack_timing.yml"
TIMING_HEADER = """# Attack timing of monster attack sprites.
# contact_frame: the 0-based frame that first shows the blow, the missile leaving or the spell's release; the game
#   applies the attack as that frame appears and the action still lasts the whole animation. Without it the attack
#   applies when the animation has played, as MM8 does (re_mm8/ACTOR_ATTACK_TIMING.md).
# sound_delay: seconds after the attack starts that its attack sound plays; without it the sound plays as it starts.
# Picked in level_generation/creatures/timing_review/ and written by its apply_decisions.py.
"""
ROLE_ORDER = ["attack_melee", "attack_ranged", "cast"]


def timingChanges(decisions, timings, spritesBySignature):
    updated = {name: dict(timing) for name, timing in timings.items()}
    for key, decision in decisions.items():
        if not key.startswith("sprite|"):
            continue
        # Every sprite showing the picked frames, also tiers added to the signature after the pick was made.
        for name in sorted(set(decision.get("sprites", [])) | spritesBySignature.get(key[len("sprite|"):], set())):
            timing = updated.setdefault(name, {})
            if "frame" in decision:
                timing.pop("contact_frame", None)
                if decision["frame"] is not None:
                    timing["contact_frame"] = int(decision["frame"])
            if "soundDelay" in decision:
                timing.pop("sound_delay", None)
                if decision["soundDelay"]:
                    timing["sound_delay"] = round(float(decision["soundDelay"]), 3)
    return {name: timing for name, timing in updated.items() if timing}


def formatTiming(timing):
    fields = [f"contact_frame: {timing['contact_frame']}"] if "contact_frame" in timing else []
    if "sound_delay" in timing:
        fields.append(f"sound_delay: {formatImpact(timing['sound_delay'])}")
    return "{" + ", ".join(fields) + "}"


def formatImpact(value):
    return f"{value:.3f}".rstrip("0").rstrip(".")


def setEventImpact(lines, start, end, role, impact):
    """Set `role`'s impact inside the descriptor block lines[start:end]; return a description of the edit."""
    events = next((i for i in range(start, end) if lines[i] == "    events:"), None)
    if events is not None:
        # Entries are flow mappings (`role: {impact: 1, ...}`) or block mappings (`role:` then deeper `key: value`).
        located = []
        i = events + 1
        while i < end and lines[i].startswith("      "):
            match = re.match(r"^      (\w+):\s*(\{.*\})?\s*$", lines[i])
            if not match:
                raise SystemExit(f"unsupported events entry: {lines[i].strip()}")
            lineIndex = i
            children = []
            i += 1
            while not match.group(2) and i < end and lines[i].startswith("        "):
                children.append(i)
                i += 1
            located.append((lineIndex, match.group(1), match.group(2), children))
        for lineIndex, name, flow, children in located:
            if name != role:
                continue
            old = lines[lineIndex] if flow else "; ".join(lines[c].strip() for c in children)
            if flow:
                body = flow[1:-1]
                if re.search(r"impact:\s*[-\d.e]+", body):
                    body = re.sub(r"impact:\s*[-\d.e]+", f"impact: {formatImpact(impact)}", body, count=1)
                else:
                    body = f"impact: {formatImpact(impact)}, " + body.strip()
                lines[lineIndex] = f"      {role}: {{{body.strip()}}}"
                new = lines[lineIndex]
            else:
                child = next((c for c in children if re.match(r"^        impact:", lines[c])), None)
                if child is None:
                    lines.insert(lineIndex + 1, f"        impact: {formatImpact(impact)}")
                else:
                    lines[child] = f"        impact: {formatImpact(impact)}"
                new = "; ".join(lines[c].strip() for c in range(lineIndex + 1, lineIndex + 1 + max(1, len(children))))
            return f"{old.strip()}  ->  {new.strip()}" if old.strip() != new.strip() else None
        # Insert in role order.
        position = events + 1
        for lineIndex, name, flow, children in located:
            if ROLE_ORDER.index(name) < ROLE_ORDER.index(role):
                position = (children[-1] if children else lineIndex) + 1
        lines.insert(position, f"      {role}: {{impact: {formatImpact(impact)}}}")
        return f"added {lines[position].strip()}"
    animation = next((i for i in range(start, end) if lines[i] == "  animation:"), None)
    if animation is None:
        raise SystemExit("descriptor without an animation block")
    position = animation + 1
    while position < end and (lines[position].startswith("    ") or lines[position].strip().startswith("#")):
        position += 1
    lines[position:position] = ["    events:", f"      {role}: {{impact: {formatImpact(impact)}}}"]
    return f"added events with {role}: {{impact: {formatImpact(impact)}}}"


def blockEnd(lines, start, indent):
    """End (exclusive) of the key at lines[start]: the deeper lines below it, and list items at its own indent."""
    i = start + 1
    while i < len(lines):
        stripped = lines[i].strip()
        lead = len(lines[i]) - len(lines[i].lstrip(" "))
        if stripped and not (lead > indent or (lead == indent and stripped.startswith("- "))):
            break
        i += 1
    while i > start + 1 and not lines[i - 1].strip():
        i -= 1
    return i


def formatSocket(value):
    if isinstance(value, str):
        return value
    offset = ", ".join(formatNumber(component) for component in value["offset"])
    return f"{{node: {value['node']}, offset: [{offset}]}}"


def formatNumber(value):
    return f"{value:.4f}".rstrip("0").rstrip(".") if isinstance(value, float) else str(value)


def setCharge(lines, start, end, decision, roles):
    """Write the model's picked sockets and the roles' charge keys into the descriptor block lines[start:end]."""
    animation = next((i for i in range(start, end) if lines[i] == "  animation:"), None)
    if animation is None:
        return []
    animationEnd = blockEnd(lines, animation, 2)
    sockets = decision.get("sockets") or {}
    for role, spec in (decision.get("roles") or {}).items():
        for name in list(spec.get("glow") or []) + ([spec["release"]] if spec.get("release") else []):
            if name not in sockets:
                raise SystemExit(f"{decision['model']} {role}: socket {name} is not among the picked sockets")
    socketLines = ["    sockets:" if sockets else "    sockets: {}"]
    socketLines += [f"      {name}: {formatSocket(value)}" for name, value in sockets.items()]
    changes = []
    current = next((i for i in range(animation + 1, animationEnd) if re.match(r"^    sockets:", lines[i])), None)
    if current is None:
        lines[animation + 1:animation + 1] = socketLines
    elif lines[current:blockEnd(lines, current, 4)] != socketLines:
        lines[current:blockEnd(lines, current, 4)] = socketLines
    else:
        socketLines = None
    if socketLines:
        changes.append(f"sockets {', '.join(sockets) or 'none'}")
    for role in ROLE_ORDER:
        if role not in roles or role not in (decision.get("roles") or {}):
            continue
        spec = decision["roles"][role]
        if role == "attack_melee" and spec.get("glow") and not spec.get("color"):
            raise SystemExit(f"{decision['model']} attack_melee: a melee glow needs a colour (the game refuses it)")
        animationEnd = blockEnd(lines, animation, 2)
        events = next((i for i in range(animation + 1, animationEnd) if lines[i] == "    events:"), None)
        if events is None:
            lines.insert(animationEnd, "    events:")
            events = animationEnd
        eventsEnd = blockEnd(lines, events, 4)
        entry = next((i for i in range(events + 1, eventsEnd) if re.match(rf"^      {role}:", lines[i])), None)
        entryEnd = blockEnd(lines, entry, 6) if entry is not None else eventsEnd
        old = (yaml.safe_load("\n".join(line[6:] for line in lines[entry:entryEnd])) or {}).get(role) or {} \
            if entry is not None else {}
        if role == "attack_melee" and not spec.get("glow") and not {"glow", "glow_scale", "color"} & set(old):
            continue  # No melee glow picked or installed: leave the marker entry as it is.
        items = [("impact", old["impact"])] if "impact" in old else []
        if spec.get("glow"):
            items.append(("glow", "[" + ", ".join(spec["glow"]) + "]"))
        if spec.get("release") and role != "attack_melee":
            items.append(("release", spec["release"]))
        if spec.get("glowScale") not in (None, 1, 1.0):
            items.append(("glow_scale", formatNumber(float(spec["glowScale"]))))
        if spec.get("color"):
            items.append(("color", "[" + ", ".join(str(int(c)) for c in spec["color"]) + "]"))
        rendered = []
        if old.get("effects"):
            rendered = [f"      {role}:"] + [f"        {key}: {value}" for key, value in items] + ["        effects:"]
            rendered += [f"          {element}: {effect}" for element, effect in old["effects"].items()]
        elif items:
            rendered = [f"      {role}: {{" + ", ".join(f"{key}: {value}" for key, value in items) + "}"]
        current = lines[entry:entryEnd] if entry is not None else []
        if rendered != current:
            lines[entry if entry is not None else eventsEnd:entryEnd] = rendered
            changes.append(f"{role}: {' / '.join(line.strip() for line in rendered) or 'removed'}")
    return changes


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--world", default="mm6")
    parser.add_argument("--write", action="store_true", help="write the files (default: print the changes)")
    args = parser.parse_args()
    decisionsPath = TOOL / "decisions.json"
    decisions = json.loads(decisionsPath.read_text()) if decisionsPath.exists() else {}

    reviewData = json.loads((TOOL / "data" / args.world / "review_data.json").read_text())
    spritesBySignature = {}
    for model in reviewData["models"]:
        for descriptor in model["descriptors"]:
            for sprite in descriptor["sprites"].values():
                if sprite:
                    spritesBySignature.setdefault(sprite["signature"], set()).add(sprite["name"])

    timings = (yaml.safe_load(TIMING.read_text()) or {}).get("sprites") or {} if TIMING.exists() else {}
    updatedTimings = timingChanges(decisions, timings, spritesBySignature)
    for name in sorted(set(timings) | set(updatedTimings)):
        if timings.get(name) != updatedTimings.get(name):
            print(f"timing {name}: {timings.get(name, {})} -> {updatedTimings.get(name, {})}")

    # Roles each descriptor plays in game (build_review_data.py); an unused role only keeps a marker it already has.
    usedRoles = {(descriptor["name"], role) for model in reviewData["models"] for descriptor in model["descriptors"]
                 for role, binding in descriptor["roles"].items() if binding["used"]}
    actorsPath = ROOT / f"assets_dev/worlds/{args.world}/models/actors.yml"
    actors = yaml.safe_load(actorsPath.read_text())["actors"]
    lines = actorsPath.read_text().split("\n")
    starts = [i for i, line in enumerate(lines) if line.startswith("- descriptor: ")]
    edits = 0
    for key, decision in sorted(decisions.items()):
        if not key.startswith("clip|"):
            continue
        _, modelName, clip = key.split("|", 2)
        if decision.get("warp"):
            # Its marker moves with the retime; retime_clip.py and a reinstall come first.
            print(f"{modelName} {clip}: warp preview {decision['warp']} not baked yet; marker left as installed")
            continue
        if not isinstance(decision.get("impact"), (int, float)):
            continue
        for actor in actors:
            if Path(actor["model"]).name != modelName:
                continue
            clips = actor.get("clips") or {}
            animation = actor.get("animation") or {}
            bound = {"attack_melee": clips.get("attack_melee"), "attack_ranged": clips.get("attack_ranged"),
                     "cast": animation.get("cast")}
            events = animation.get("events") or {}
            for role in ROLE_ORDER:
                if bound[role] != clip or ((actor["descriptor"], role) not in usedRoles and role not in events):
                    continue
                starts = [i for i, line in enumerate(lines) if line.startswith("- descriptor: ")]
                start = next(i for i in starts
                             if lines[i].split("#")[0].rstrip() == f"- descriptor: {actor['descriptor']}")
                end = next((i for i in starts if i > start), len(lines))
                change = setEventImpact(lines, start, end, role, decision["impact"])
                if change:
                    edits += 1
                    print(f"{actor['descriptor']} {role}: {change}")

    for key, decision in sorted(decisions.items()):
        if not key.startswith("fx|"):
            continue
        for actor in actors:
            if Path(actor["model"]).name != decision["model"]:
                continue
            roles = {role for role in ("attack_melee", "attack_ranged") if (actor.get("clips") or {}).get(role)}
            roles |= {"cast"} if (actor.get("animation") or {}).get("cast") else set()
            starts = [i for i, line in enumerate(lines) if line.startswith("- descriptor: ")]
            start = next(i for i in starts
                         if lines[i].split("#")[0].rstrip() == f"- descriptor: {actor['descriptor']}")
            end = next((i for i in starts if i > start), len(lines))
            for change in setCharge(lines, start, end, decision, roles):
                edits += 1
                print(f"{actor['descriptor']} {change}")

    if not args.write:
        print("dry run; pass --write to apply")
        return
    body = "".join(f"  {name}: {formatTiming(timing)}\n" for name, timing in sorted(updatedTimings.items()))
    TIMING.write_text(TIMING_HEADER + "sprites:" + (" {}\n" if not body else "\n" + body))
    if edits:
        actorsPath.write_text("\n".join(lines))
    print(f"wrote {TIMING.relative_to(ROOT)}" + (f" and {edits} marker/socket edits in {actorsPath.relative_to(ROOT)}"
                                                 if edits else ""))


if __name__ == "__main__":
    main()
