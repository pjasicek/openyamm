#!/usr/bin/env python3
"""
Review captures and sheets of the MM9 lightmap transfer rollout (devdocs/mm9_rework/MM9_LIGHTMAP_TRANSFER.md, "Rollout").

    python3 level_generation/projects/mm9r_common/lightmap_rollout.py capture <stem> before|transfer [--kind real|review]
    python3 level_generation/projects/mm9r_common/lightmap_rollout.py sheet <stem>

`before` runs against output/mm9_rework/lightmap_rollout_before (a hard-linked snapshot of the review root taken before
the rollout: the old BLVs with their Cycles bakes), `transfer` against the review root. Each kind is one desktop run
(`SDL_AUDIODRIVER=dummy tools/run_game.sh --isolated lmroll_<stem>_<n>`, unlimited view distance) of a tour built from
the map's own tours: `real` the views of the user's real MM9 screenshots, `review` the map's latest review tour
(`review_tour_vNN.yml`). Shots go to <project>/review/lmroll_<variant>_<kind>/.

`sheet` writes <project>/review/lmroll_real.jpg (real | before | transfer) and lmroll_review_pNN.jpg (before |
transfer), and <project>/work/lightmap_transfer/luma.json: per view the luma of the real-shot box (real_shots.py: the
real frame's x 20-78 %, y 5-88 % mapped to our view, HUD masked), and the views under DARK luma in the transfer.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

import yaml
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
from real_shots import REAL_DIR, describe, measure  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
PROJECTS = ROOT / "level_generation/projects"
ROOTS = {"before": ROOT / "output/mm9_rework/lightmap_rollout_before", "transfer": ROOT / "output/mm9_rework/assets_dev"}
DARK = 10.0
TILE = (480, 270)
# real shot -> (tour file, shot name); the shot of the same view in our tours (real_measure.py's choices)
REAL = {
    "yanmirsfort": ("review_tour_real01.yml", [("yanmirsfort_real_1.png", "y1_great_hall_south"),
                                               ("yanmirsfort_real_1.png", "y1_alt_west"),
                                               ("yanmirsfort_real_2.png", "y2_great_hall_southwest"),
                                               ("yanmirsfort_real_2.png", "y2_alt_northeast")]),
    "klusoshouse": ("review_tour_real11.yml", [("klusoshouse_real_1_corridor_guard.png", "r1_corridor_guard"),
                                               ("klusoshouse_real_2_doorway.png", "r2_doorway"),
                                               ("klusoshouse_real_3_dark_room_props.png", "r3_dark_room_props"),
                                               ("klusoshouse_real_4_count_room.png", "r4_count_room")]),
    "dungeonofsecrets": ("review_tour_real03.yml",
                         [("dungeonofsecrets_real_1_corridor.png", "d1_west_corridor"),
                          ("dungeonofsecrets_real_2_purple_room.png", "d2_pool_room_w"),
                          ("dungeonofsecrets_real_3_doorway.png", "d3a_hub_door_s10"),
                          ("dungeonofsecrets_real_4_corridor_purple.png", "d4_s04_corridor_w")]),
    "verhoffinruins": ("review_tour_v09.yml", [(str(PROJECTS / "mm9r_verhoffinruins/review/mm9_real_spawn.png"),
                                                "a01_start_stair")]),
    "dragonstadium": ("review_tour_real01.yml", [("dragonstadium_real_1_floor.png", "s1_floor_southwest"),
                                                 ("dragonstadium_real_1_floor.png", "s1_alt_closer")]),
}


def project_dir(stem: str) -> Path:
    return PROJECTS / f"mm9r_{stem}"


def review_tour(stem: str) -> Path:
    found = []
    for path in project_dir(stem).glob("review_tour_v*.yml"):
        match = re.fullmatch(r"review_tour_v(\d+)\.yml", path.name)
        if match:
            found.append((int(match.group(1)), path))
    if not found:
        raise SystemExit(f"{stem}: no review_tour_vNN.yml")
    return max(found)[1]


def source_tour(stem: str, kind: str) -> tuple[Path, list | None]:
    if kind == "real":
        name, pairs = REAL[stem]
        return project_dir(stem) / name, [shot for _, shot in pairs]
    return review_tour(stem), None


def capture(stem: str, variant: str, kind: str, index: int) -> Path:
    source, names = source_tour(stem, kind)
    tour = yaml.safe_load(source.read_text())
    shots = tour["shots"] if names is None else [s for s in tour["shots"] if s["name"] in names]
    out = project_dir(stem) / "review" / f"lmroll_{variant}_{kind}"
    out.mkdir(parents=True, exist_ok=True)
    tour_path = project_dir(stem) / "work/lightmap_transfer" / f"tour_{variant}_{kind}.yml"
    tour_path.parent.mkdir(parents=True, exist_ok=True)
    tour_path.write_text(yaml.safe_dump({"output_dir": str(out), "settle_seconds": tour.get("settle_seconds", 1.5),
                                         "exit": True, "shots": shots}, sort_keys=False))
    first = shots[0]
    command = ["./tools/run_game.sh", "--isolated", f"lmroll_{stem}_{index}", "--world", "mm9", "--map", f"{stem}.blv",
               "--assets", str(ROOTS[variant]), "--position", *[str(v) for v in first["position"]],
               "--yaw-radians", str(first["yaw"]), "--pitch-degrees", "0", "--warmup", "4",
               "--seconds", str(int(40 + 4 * len(shots))), "--set", "video.view_distance=unlimited",
               "--set", f"debug.screenshot_tour_path={tour_path}"]
    log = project_dir(stem) / "work/lightmap_transfer" / f"run_{variant}_{kind}.log"
    environment = dict(os.environ, SDL_AUDIODRIVER="dummy")
    with log.open("w") as stream:
        process = subprocess.Popen(command, cwd=ROOT, env=environment, stdout=stream, stderr=subprocess.STDOUT)
        while process.poll() is None:            # our own run's PID only
            time.sleep(2)
    count = len(list(out.glob("*.png")))
    print(f"{stem} {variant} {kind}: {count}/{len(shots)} shots in {out} (exit {process.returncode})")
    return out


def shot(folder: Path, name: str) -> Path | None:
    matches = sorted(folder.glob(f"*-{name}.png"))
    return matches[0] if matches else None


def tile(image: Image.Image, draw, path: Path | None, x: int, y: int, label: str) -> None:
    if path is not None and path.exists():
        image.paste(Image.open(path).convert("RGB").resize(TILE), (x, y + 30))
    draw.text((x + 4, y + 2), label[:90], fill=(235, 235, 235))


def sheet(stem: str) -> dict:
    review = project_dir(stem) / "review"
    result = {"map": stem, "real": [], "review": [], "dark_threshold": DARK}
    if stem in REAL:
        rows = REAL[stem][1]
        image = Image.new("RGB", (TILE[0] * 3, (TILE[1] + 30) * len(rows)), (12, 12, 16))
        draw = ImageDraw.Draw(image)
        for row, (real_name, name) in enumerate(rows):
            real = Path(real_name) if "/" in real_name else REAL_DIR / real_name
            entry = {"real": real.name, "shot": name}
            luma_real, rgb_real = measure(real, True)
            entry["real_luma"] = round(luma_real, 1)
            tile(image, draw, real, 0, row * (TILE[1] + 30), f"REAL {real.stem}: {describe(luma_real, rgb_real)}")
            for col, variant in enumerate(("before", "transfer"), 1):
                path = shot(review / f"lmroll_{variant}_real", name)
                if path is None:
                    continue
                luma, rgb = measure(path, False)
                entry[variant] = {"luma": round(luma, 1), "rgb": [round(float(v)) for v in rgb],
                                  "ratio": round(luma / luma_real, 2)}
                tile(image, draw, path, col * TILE[0], row * (TILE[1] + 30),
                     f"{variant} {name}: {describe(luma, rgb)} x{luma / luma_real:.2f}")
            result["real"].append(entry)
        image.save(review / "lmroll_real.jpg", quality=88)
    before, after = review / "lmroll_before_review", review / "lmroll_transfer_review"
    names = sorted({p.stem.split("-", 1)[1] for p in after.glob("*.png")} | {p.stem.split("-", 1)[1]
                                                                             for p in before.glob("*.png")})
    order = {p.stem.split("-", 1)[1]: p.stem for p in list(before.glob("*.png")) + list(after.glob("*.png"))}
    names.sort(key=lambda n: order[n])
    per_page = 8
    for page in range(0, len(names), per_page):
        chunk = names[page:page + per_page]
        image = Image.new("RGB", (TILE[0] * 2, (TILE[1] + 30) * len(chunk)), (12, 12, 16))
        draw = ImageDraw.Draw(image)
        for row, name in enumerate(chunk):
            entry = {"shot": name}
            for col, (variant, folder) in enumerate((("before", before), ("transfer", after))):
                path = shot(folder, name)
                if path is None:
                    continue
                luma, rgb = measure(path, False)
                entry[variant] = round(luma, 1)
                tile(image, draw, path, col * TILE[0], row * (TILE[1] + 30), f"{variant} {name}: {describe(luma, rgb)}")
            result["review"].append(entry)
        image.save(review / f"lmroll_review_p{page // per_page + 1:02d}.jpg", quality=85)
    views = [e for e in result["review"] if "transfer" in e and "before" in e]
    if views:
        result["review_mean_before"] = round(sum(e["before"] for e in views) / len(views), 1)
        result["review_mean_transfer"] = round(sum(e["transfer"] for e in views) / len(views), 1)
    result["dark_views_transfer"] = [e["shot"] for e in result["review"] if e.get("transfer", 99) < DARK]
    result["dark_views_before"] = [e["shot"] for e in result["review"] if e.get("before", 99) < DARK]
    out = project_dir(stem) / "work/lightmap_transfer/luma.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=1) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k != "review"}, indent=1))
    return result


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="command", required=True)
    c = sub.add_parser("capture")
    c.add_argument("stem")
    c.add_argument("variant", choices=("before", "transfer"))
    c.add_argument("--kind", choices=("real", "review"), action="append")
    c.add_argument("--index", type=int, default=1)
    s = sub.add_parser("sheet")
    s.add_argument("stem")
    args = ap.parse_args()
    if args.command == "capture":
        kinds = args.kind or (["real", "review"] if args.stem in REAL else ["review"])
        for offset, kind in enumerate(kinds):
            capture(args.stem, args.variant, kind, args.index * 10 + offset)
    else:
        sheet(args.stem)
    return 0


if __name__ == "__main__":
    sys.exit(main())
