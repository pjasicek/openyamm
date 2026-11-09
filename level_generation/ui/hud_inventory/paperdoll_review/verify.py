"""Verify the prepared review catalog covers every active pending paperdoll target."""

import hashlib
import json
from collections import Counter
from pathlib import Path
from urllib.parse import unquote

from PIL import Image


HERE = Path(__file__).resolve().parent
PREFIX = "window.PAPERDOLL_REVIEW_DATA = "


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_candidate(entry):
    if not entry.get("candidate"):
        raise ValueError(f"Target lacks a 2× candidate: {entry['id']}")
    path = HERE / unquote(entry["candidate"])
    if not path.is_file() or digest(path) != entry["candidateHash"]:
        raise ValueError(f"Candidate missing or changed: {entry['id']}")
    with Image.open(path) as image:
        if image.mode != "RGBA" or image.size != tuple(2 * value for value in entry["size"]):
            raise ValueError(f"Candidate is not exact-2× RGBA: {entry['id']}")
        if not image.getchannel("A").getbbox():
            raise ValueError(f"Empty candidate: {entry['id']}")


def main():
    source = (HERE / "catalog.js").read_text()
    if not source.startswith(PREFIX):
        raise ValueError("catalog.js is not a paperdoll catalog")
    data = json.loads(source[len(PREFIX):].removesuffix(";\n"))
    counts = Counter()
    families = Counter()
    issues = Counter()
    pending = 0
    for target in data["reviewTargets"]:
        entry = data["assets"][target["name"]]
        if not target["active"] or entry["candidateStatus"] in {"accepted", "hud_approved"}:
            continue
        pending += 1
        status = entry["candidateStatus"]
        if not status or not entry["candidate"]:
            raise ValueError(f"Active target lacks a 2× candidate: {target['id']}")
        verify_candidate(entry)
        counts[status] += 1
        families[target["treatment"]] += 1
        selected = next((option for option in entry["preparedAlternatives"]
                         if option["path"] == entry["candidate"]), None)
        if selected:
            issues.update(selected["issues"])
    equipment = {}
    for group, stats in {"melee": {"Weapon", "Weapon1or2", "Weapon2"}, "bows": {"Missile"},
                         "shields": {"Shield"}, "wands": {"WeaponW"}, "gloves": {"Gauntlets"},
                         "jewelry": {"Amulet", "Ring"}}.items():
        names = {item["icon"] for item in data["items"] if item["stat"] in stats and item["icon"]}
        for name in names:
            verify_candidate(data["assets"][name])
        equipment[group] = len(names)
    result = {"active_pending": pending, "families": dict(families), "candidate_status": dict(counts),
              "equipment_context_candidates": equipment,
              "selected_prepared_issues": dict(issues), "native_fallback": 0}
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
