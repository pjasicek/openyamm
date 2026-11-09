#!/usr/bin/env python3
"""Runs bob_fix.py over jobs.txt: work/<world>/<model>.glb (a copy of the installed source, taken once) to
export/<world>/<model>.glb. Run from the repository root; `--only <model>` limits it to models named on the command line.
"""
import argparse
import collections
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
FIX = ROOT / "level_generation/creatures/claude_shared/postprocess/bob_fix.py"


def jobs():
    result = collections.OrderedDict()
    for line in (HERE / "jobs.txt").read_text().splitlines():
        if line.strip() and not line.startswith("#"):
            world, model, clip, target = line.split()
            result.setdefault((world, model), []).append((clip, target))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--only", nargs="+")
    args = parser.parse_args()
    for (world, model), clips in jobs().items():
        if args.only and model not in args.only:
            continue
        base = HERE / "work" / world / f"{model}.glb"
        if not base.exists():
            base.parent.mkdir(parents=True, exist_ok=True)
            base.write_bytes((ROOT / "assets_source/worlds" / world / "models" / f"{model}.glb").read_bytes())
        output = HERE / "export" / world / f"{model}.glb"
        output.parent.mkdir(parents=True, exist_ok=True)
        command = ["python3", str(FIX), str(base), str(output)]
        for clip, target in clips:
            command += ["--clip", clip, target]
        print(f"== {world}/{model}", flush=True)
        subprocess.run(command, check=True)


if __name__ == "__main__":
    main()
