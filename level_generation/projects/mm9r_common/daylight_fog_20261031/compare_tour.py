#!/usr/bin/env python3
"""
Short time-of-day comparison tours for a converted city (CITY_PLAYBOOK "Daylight and fog"): chosen views of one of the
city's existing tours, each at a few times, as a BLV tour and the same views on the old ODM import.

    compare_tour.py write <city> <name> --from v03 --views s06_palace_front,... [--times 12:00,23:30]
        -> mm9r_<city>/review_tour_<name>.yml (review/<name>/) and review_tour_<name>_original.yml
    compare_tour.py run <city> <name> [--original] [--binary build/game/openyamm] [--folder X]
        one isolated, minimized, silent game run of that tour (the review root, or the city's original root); --folder
        writes the shots to review/X instead (before / after runs of one tour)
    compare_tour.py sheet <city> <name> <time> <folder>... --out <jpg>
        one row per view: the folders' shots of that time side by side, labelled; a folder "a+b" takes b's shot where a
        has none or only the death video

The BLV and the old ODM share the frame, so the same positions serve both (each city's make_tour.py).
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[4]
PROJECTS = ROOT / "level_generation/projects"
REVIEW_ROOT = ROOT / "output/mm9_rework/assets_dev"


def tour_path(city: str, name: str, original: bool) -> Path:
    return PROJECTS / f"mm9r_{city}" / f"review_tour_{name}{'_original' if original else ''}.yml"


def write(city: str, name: str, source: str, views: list[str], times: list[str]) -> None:
    base = yaml.safe_load(tour_path(city, source, False).read_text())
    by_name = {shot["name"]: shot for shot in base["shots"]}
    missing = [view for view in views if view not in by_name]
    if missing:
        raise SystemExit(f"views not in review_tour_{source}.yml: {missing}")
    for original in (False, True):
        shots = [dict(by_name[view], name=f"{view}_{time.replace(':', '')}", time=time)
                 for time in times for view in views]
        folder = PROJECTS / f"mm9r_{city}" / "review" / f"{name}{'_original' if original else ''}"
        tour = {"output_dir": str(folder), "settle_seconds": 2.0, "exit": True, "shots": shots}
        tour_path(city, name, original).write_text(yaml.safe_dump(tour, sort_keys=False))
        print(tour_path(city, name, original))


def run(city: str, name: str, original: bool, binary: str, folder: str) -> int:
    """One game run per view (its times in a row). Written when long BLV tours ended in the death video (the tour's
    indoor clock ran during its hold; fixed 2026-11-01, CITY_PLAYBOOK "Daylight and fog"): no longer required."""
    full = yaml.safe_load(tour_path(city, name, original).read_text())
    if folder:
        full["output_dir"] = str(PROJECTS / f"mm9r_{city}" / "review" / folder)
    views = []
    for shot in full["shots"]:
        view = shot["name"].rsplit("_", 1)[0]
        if view not in views:
            views.append(view)
    worst = 0
    for index, view in enumerate(views):
        tour = dict(full, shots=[shot for shot in full["shots"] if shot["name"].rsplit("_", 1)[0] == view])
        path = PROJECTS / f"mm9r_{city}" / "work" / f"tour_{folder or name}_{index:02d}.yml"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(yaml.safe_dump(tour, sort_keys=False))
        worst = max(worst, run_one(city, tour, path, original, binary, f"{folder or name}{index:02d}"))
    return worst


def run_one(city: str, tour: dict, path: Path, original: bool, binary: str, label: str) -> int:
    first = tour["shots"][0]
    assets = ROOT / "output/mm9_rework" / f"{city}_original_root" if original else REVIEW_ROOT
    command = [sys.executable, str(ROOT / "tools/run_game.py"), f"city_{city}_{label}{'o' if original else ''}",
               "--world", "mm9", "--map", f"{city}.{'odm' if original else 'blv'}", "--assets", str(assets),
               "--binary", binary, "--position", *(str(v) for v in first["position"]),
               "--yaw-radians", str(first["yaw"]), "--pitch-degrees", "0", "--warmup", "3",
               "--seconds", str(int(12 + 6 * len(tour["shots"]))),
               "--set", f"debug.screenshot_tour_path={path}"]
    if original:
        command += ["--set", "video.view_distance=unlimited"]
    environment = dict(os.environ, SDL_AUDIODRIVER="dummy")
    return subprocess.call(command, cwd=ROOT, env=environment)


def sheet(city: str, name: str, time: str, folders: list[str], out: str) -> None:
    from PIL import Image, ImageDraw
    tour = yaml.safe_load(tour_path(city, name, False).read_text())
    stamp = time.replace(":", "")
    views = [shot["name"] for shot in tour["shots"] if shot["name"].endswith("_" + stamp)]
    width, height, label = 560, 315, 16
    canvas = Image.new("RGB", (width * len(folders), (height + label) * len(views)), (16, 16, 16))
    draw = ImageDraw.Draw(canvas)
    def death_video(image) -> bool:
        """The letterboxed death video a long BLV tour can end in (run()): black side bars, no HUD."""
        pixels = image.convert("L").resize((160, 90)).load()
        return max(pixels[x, y] for x in range(6) for y in range(90)) < 6

    for row, view in enumerate(views):
        for column, spec in enumerate(folders):
            # "a+b": the newest usable shot of a, else of b (an earlier session's folder of the same state)
            x, y = column * width, row * (height + label)
            chosen, note = None, "missing"
            for folder in spec.split("+"):
                found = sorted(Path(folder).glob(f"*-{view}.png"), key=lambda path: path.stat().st_mtime)
                if found:
                    image = Image.open(found[-1]).convert("RGB")
                    if death_video(image):
                        note = "death video (long tour)"
                        continue
                    chosen = (image, Path(folder).name)
                    break
            name = chosen[1] if chosen else Path(spec.split("+")[0]).name
            draw.text((x + 4, y + 2), f"{view[:-5]} {time} {name}", fill=(230, 230, 230))
            if chosen:
                canvas.paste(chosen[0].resize((width, height)), (x, y + label))
            else:
                draw.text((x + 8, y + label + 8), note, fill=(255, 80, 80))
    canvas.save(out, quality=88)
    print(out)


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="action", required=True)
    w = sub.add_parser("write")
    w.add_argument("city")
    w.add_argument("name")
    w.add_argument("--from", dest="source", required=True)
    w.add_argument("--views", required=True)
    w.add_argument("--times", default="12:00,23:30")
    r = sub.add_parser("run")
    r.add_argument("city")
    r.add_argument("name")
    r.add_argument("--original", action="store_true")
    r.add_argument("--binary", default=str(ROOT / "build/game/openyamm"))
    r.add_argument("--folder", default="")
    s = sub.add_parser("sheet")
    s.add_argument("city")
    s.add_argument("name")
    s.add_argument("time")
    s.add_argument("folders", nargs="+")
    s.add_argument("--out", required=True)
    arguments = parser.parse_args()
    if arguments.action == "write":
        write(arguments.city, arguments.name, arguments.source, arguments.views.split(","), arguments.times.split(","))
        return 0
    if arguments.action == "run":
        return run(arguments.city, arguments.name, arguments.original, arguments.binary, arguments.folder)
    sheet(arguments.city, arguments.name, arguments.time, arguments.folders, arguments.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
