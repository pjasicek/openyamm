#!/usr/bin/env python3
"""
One lighting-tour run of the 2026-10-31 re-light: the shots of an existing tour YAML into <project>/review/<name>_<mode>
(original: the old import from output/mm9_rework/assets_original at unlimited view distance; unbaked: the BLV with
lightmaps off; baked: the BLV as installed). Waits for its own game process; log in <project>/work/relight/.

    python3 level_generation/projects/mm9r_common/relight_tour.py level_generation/projects/mm9r_<map> SOURCE_TOUR.yml \
        NAME original|unbaked|baked [--seconds N] [--set key=value ...]
"""
import argparse
import os
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[3]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("project", type=Path)
    ap.add_argument("tour", type=Path)
    ap.add_argument("name")
    ap.add_argument("mode", choices=("original", "unbaked", "baked"))
    ap.add_argument("--seconds", type=int)
    ap.add_argument("--set", action="append", default=[])
    args = ap.parse_args()
    project = args.project.resolve()
    stem = yaml.safe_load((project / "overrides.yml").read_text())["map"]["stem"]
    tour = yaml.safe_load(args.tour.read_text())
    out_dir = project / "review" / f"{args.name}_{args.mode}"
    tour["output_dir"] = str(out_dir)
    tour["exit"] = True
    tour_path = project / "work/relight" / f"tour_{args.name}_{args.mode}.yml"
    tour_path.parent.mkdir(parents=True, exist_ok=True)
    tour_path.write_text(yaml.safe_dump(tour, sort_keys=False))
    first = tour["shots"][0]
    seconds = args.seconds or int(30 + 4 * len(tour["shots"]))
    if args.mode == "original":
        assets, mapname, extra = "assets_original", f"{stem}.odm", ["--set", "video.view_distance=unlimited"]
    else:
        assets, mapname, extra = "assets_dev", f"{stem}.blv", []
        if args.mode == "unbaked":
            extra = ["--set", "video.lightmaps=false"]
    for item in args.set:
        extra += ["--set", item]
    command = ["./tools/run_game.sh", "--isolated", f"{stem}_{args.name}_{args.mode}", "--world", "mm9",
               "--map", mapname, "--assets", str(ROOT / "output/mm9_rework" / assets),
               "--position", *(str(v) for v in first["position"]), "--yaw-radians", str(first["yaw"]),
               "--pitch-degrees", "0", "--warmup", "3", "--seconds", str(seconds), *extra,
               "--set", f"debug.screenshot_tour_path={tour_path}"]
    log = project / "work/relight" / f"run_{args.name}_{args.mode}.log"
    env = dict(os.environ, SDL_AUDIODRIVER="dummy")
    with log.open("w") as handle:
        rc = subprocess.run(command, cwd=ROOT, env=env, stdout=handle, stderr=subprocess.STDOUT).returncode
    shots = len(list(out_dir.glob("*.png"))) if out_dir.exists() else 0
    print(f"{args.name} {args.mode}: rc {rc}, {shots}/{len(tour['shots'])} shots in {out_dir}")
    return 0 if shots == len(tour["shots"]) else 1


if __name__ == "__main__":
    sys.exit(main())
