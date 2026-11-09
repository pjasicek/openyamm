"""
Portal and traversal counts per review pose of an MM9 city BLV, before and after a rebuild (CITY_STREET_COST.md,
proposal 3 "fewer, larger roof-line portals").

    python3 devdocs/mm9_rework/city_street_cost/portal_counts.py tour <city> <phase>   # writes the tour
    python3 devdocs/mm9_rework/city_street_cost/portal_counts.py run <city> <phase>    # tour + game run + counts
    python3 devdocs/mm9_rework/city_street_cost/portal_counts.py faces <city>          # portal faces of the BLV
    python3 devdocs/mm9_rework/city_street_cost/portal_counts.py table <city>          # before | after per pose
    python3 devdocs/mm9_rework/city_street_cost/portal_counts.py diff <city>           # before/after image sheet

<city> is the project name without `mm9r_` and `city` (thjorgard); <phase> a label (before, after). The tour is the
city's latest review tour (every shot: streets and interiors) at 12:00 with `portals log on`, settle 3 s, images and
the game log in output/mm9_rework/portals_1101/<city>/<phase>/. Counts are exact per pose; for each shot the last
`[PortalView]` line before its capture is taken (draw calls are a 1-second mean: the window may include the previous
pose's frames when the settle is short, so the visibility counts are the measure). The binary's md5 is recorded;
PORTAL_COUNTS_BINARY=<path> runs another copy of the game (the same binary before and after while build/ changes);
PORTAL_COUNTS_ASSETS=<root> another asset root (a hard-linked copy of the review root with the old maps put back, when
shared assets such as textures changed between the before and after runs).
"""

from __future__ import annotations

import glob
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "output/mm9_rework/portals_1101"
TOURS = {"arslegard": "v05", "drangheim": "v11", "frosgard": "v03", "guberland": "v02", "sturmford": "v03",
         "thjorgard": "v03", "thronheim": "v03"}
KEYS = ("sectors_drawn", "nodes", "portals_tested", "portals_traversed", "batches", "faces", "draw_calls")
NODE_CAP = 256                      # IndoorPortalVisibilityInput maxNodes: nodes == 256 is a cap hit


def project(city: str) -> Path:
    return ROOT / f"level_generation/projects/mm9r_{city}city"


def write_tour(city: str, phase: str) -> Path:
    source = yaml.safe_load((project(city) / f"review_tour_{TOURS[city]}.yml").read_text())
    folder = OUT / city / phase
    folder.mkdir(parents=True, exist_ok=True)
    shots = []
    for k, shot in enumerate(source["shots"]):
        shot = {key: shot[key] for key in ("name", "position", "yaw", "pitch") if key in shot}
        shot["settle_seconds"] = 3.0
        if k == 0:
            shot["time"] = "12:00"
            shot["commands"] = ["portals log on"]
        shots.append(shot)
    tour = {"output_dir": str(folder), "settle_seconds": 3.0, "exit": True, "shots": shots}
    path = folder / "tour.yml"
    path.write_text(yaml.safe_dump(tour, sort_keys=False))
    return path


def parse_line(line: str) -> dict:
    values = dict(re.findall(r"(\w+)=([^\s]+)", line))
    out = {}
    for key, value in values.items():
        try:
            out[key] = int(value)
        except ValueError:
            try:
                out[key] = float(value)
            except ValueError:
                out[key] = value
    # per sector id:faces/facesInPortals/triangles/batches/tileDraws/tileTriangles/portalsTested/...: the links
    # iterated (each node's sector's links, also past the node cap), as CITY_STREET_COST.md's "portal link tests"
    if isinstance(out.get("sectors"), str):
        out["link_tests"] = sum(int(part.split(":")[1].split("/")[6]) for part in out["sectors"].split(","))
    return out


def run(city: str, phase: str) -> None:
    tour = write_tour(city, phase)
    folder = tour.parent
    binary = Path(os.environ.get("PORTAL_COUNTS_BINARY", ROOT / "build/game/openyamm"))
    md5 = hashlib.md5(binary.read_bytes()).hexdigest()
    first = yaml.safe_load(tour.read_text())["shots"][0]
    name = f"city_{city}_portals_{phase}"
    command = ["./tools/run_game.sh", "--isolated", name, "--world", "mm9", "--map", f"{city}city.blv",
               "--assets", os.environ.get("PORTAL_COUNTS_ASSETS", str(ROOT / "output/mm9_rework/assets_dev")),
               "--position", *[str(v) for v in first["position"]], "--yaw-radians", str(first["yaw"]),
               "--pitch-degrees", "0", "--warmup", "3", "--seconds", str(30 + 4 * len(yaml.safe_load(
                   tour.read_text())["shots"])),
               "--set", f"debug.screenshot_tour_path={tour}", "--binary", str(binary)]
    env = dict(os.environ, SDL_AUDIODRIVER="dummy")
    result = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, text=True)
    (folder / "run.txt").write_text(result.stdout + result.stderr)
    logs = sorted(glob.glob(f"/tmp/openyamm-desktop-{name}-*/game.log"), key=lambda p: Path(p).stat().st_mtime)
    if not logs:
        raise SystemExit("no game log; see " + str(folder / "run.txt"))
    log = Path(logs[-1]).read_text(errors="replace")
    (folder / "game.log").write_text(log)
    counts = shot_counts(log, [s["name"] for s in yaml.safe_load(tour.read_text())["shots"]])
    (folder / "counts.json").write_text(json.dumps({"binary_md5": md5, "binary_mtime": binary.stat().st_mtime,
                                                    "blv": blv_portals(city), "shots": counts}, indent=1) + "\n")
    print(city, phase, md5, len(counts), "shots")


def shot_counts(log: str, names: list[str]) -> dict:
    """The last [PortalView] line before each shot's capture line."""
    last, out = None, {}
    pending = list(names)
    for line in log.splitlines():
        if "[PortalView]" in line:
            last = parse_line(line.split("[PortalView]", 1)[1])
            continue
        if pending and last is not None and re.search(r"(?i)(captur|screenshot).*\b\d\d-" + re.escape(pending[0])
                                                      + r"\.png", line):
            out[pending.pop(0)] = last
    return out


def blv_portals(city: str) -> dict:
    sys.path.insert(0, str(ROOT))
    from util.map_export import parse_blv_file
    root = Path(os.environ.get("PORTAL_COUNTS_ASSETS", ROOT / "output/mm9_rework/assets_dev"))
    blv = parse_blv_file(root / f"worlds/mm9/maps/{city}city.blv")["payload"]
    portals = [f for f in blv["faces"] if f["is_portal"]]
    return {"faces": len(blv["faces"]), "portal_faces": len(portals), "vertices": len(blv["vertices"]),
            "sectors": len(blv["sectors"])}


def table(city: str) -> None:
    data = {phase: json.loads((OUT / city / phase / "counts.json").read_text())
            for phase in ("before", "after") if (OUT / city / phase / "counts.json").exists()}
    for phase, d in data.items():
        print(phase, d["binary_md5"], d["blv"])
    names = list(next(iter(data.values()))["shots"])
    keys = ("sectors_drawn", "nodes", "link_tests", "portals_traversed", "batches", "draw_calls")
    print("| Pose | " + " | ".join(f"{k} (" + " / ".join(data) + ")" for k in keys) + " |")
    for name in names:
        row = [name]
        for key in keys:
            row.append(" / ".join(str(data[p]["shots"].get(name, {}).get(key, "-")) for p in data))
        print("| " + " | ".join(row) + " |")
    for phase, d in data.items():
        shots = d["shots"].values()
        print(phase, "cap hits:", sum(1 for s in shots if s.get("nodes", 0) >= NODE_CAP),
              "max nodes:", max((s.get("nodes", 0) for s in shots), default=0),
              "max link tests:", max((s.get("link_tests", 0) for s in shots), default=0))


def diff(city: str) -> None:
    import numpy as np
    from PIL import Image, ImageDraw
    before, after = OUT / city / "before", OUT / city / "after"
    rows = []
    for path in sorted(before.glob("[0-9][0-9]-*.png")):
        other = after / path.name
        if not other.exists():
            continue
        a = np.asarray(Image.open(path).convert("RGB")).astype(int)
        b = np.asarray(Image.open(other).convert("RGB")).astype(int)
        if a.shape != b.shape:
            continue
        d = np.abs(a - b).max(axis=2)
        rows.append((path.name, float((d > 24).mean() * 100), Image.open(path).convert("RGB"),
                     Image.open(other).convert("RGB"), Image.fromarray(np.uint8(np.clip(d * 4, 0, 255)))))
    w, h = 480, 270
    sheet = Image.new("RGB", (w * 3, (h + 18) * len(rows)), (20, 20, 20))
    draw = ImageDraw.Draw(sheet)
    for k, (name, share, a, b, d) in enumerate(rows):
        y = k * (h + 18)
        for j, image in enumerate((a, b, d.convert("RGB"))):
            sheet.paste(image.resize((w, h)), (j * w, y + 18))
        draw.text((4, y + 2), f"{name}  before | after | diff x4  ({share:.2f} % pixels differ > 24)", fill=(255, 255, 0))
        print(f"{name}: {share:.2f} %")
    sheet.save(OUT / city / "before_after_diff.jpg", quality=85)


if __name__ == "__main__":
    action, city = sys.argv[1], sys.argv[2]
    if action == "tour":
        print(write_tour(city, sys.argv[3]))
    elif action == "run":
        run(city, sys.argv[3])
    elif action == "faces":
        print(blv_portals(city))
    elif action == "table":
        table(city)
    elif action == "diff":
        diff(city)
