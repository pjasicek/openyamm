#!/usr/bin/env python3
"""Decision D-44: every model path a world's models/*.yml names (bodies, attachments, static models, decoration
bindings) lies in engine/, in the world itself, or in a world it declares in world.yml `dependencies`, and the file is
there.

  tools/xeen/model_dependencies.py [--root assets_dev] [world ...]

Without worlds it checks every world under <root>/worlds. MM6, MM7 and MM8 are exempt among themselves: they are
MMerge's merged base, mounted and shipped together, and their world.yml files declare no dependencies (MM7 binds 18 MM8
models for the monsters it shares with MM8). Declaring them would only make each refuse to load without the others,
which never happens, and changes three shipped manifests for nothing; any other borrowing of theirs is checked.
Prints one line per broken path and a summary per world; exits non-zero when any path is broken.
"""

import argparse
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
MODEL_PATH = re.compile(r"^(engine|worlds/[a-z0-9_]+)/\S+\.(glb|gltf|oymodel)$", re.IGNORECASE)
# The merged base worlds without manifests, which may borrow from one another (see the docstring).
MERGED_BASE = {"mm6", "mm7", "mm8"}


def model_paths(node):
    """Every scalar of a YAML tree that reads as a model path."""
    if isinstance(node, dict):
        for value in node.values():
            yield from model_paths(value)
    elif isinstance(node, list):
        for value in node:
            yield from model_paths(value)
    elif isinstance(node, str) and MODEL_PATH.match(node.strip()):
        yield node.strip()


def allowed_roots(root, world):
    manifest = root / "worlds" / world / "world.yml"
    allowed = {"engine", "worlds/" + world}

    if manifest.exists():
        data = yaml.safe_load(manifest.read_text()) or {}
        allowed |= {"worlds/" + dependency for dependency in data.get("dependencies") or [] if dependency != "engine"}

    if world in MERGED_BASE:
        allowed |= {"worlds/" + other for other in MERGED_BASE}

    return allowed


def check_world(root, world):
    allowed = allowed_roots(root, world)
    broken = []
    count = 0

    for path in sorted((root / "worlds" / world / "models").glob("*.yml")):
        for model in model_paths(yaml.safe_load(path.read_text())):
            count += 1
            prefix = "engine" if model.startswith("engine/") else "/".join(model.split("/")[:2])

            if prefix not in allowed:
                broken.append(f"{path.relative_to(root)}: {model} is in {prefix}, which {world} does not declare")
            elif not (root / model).exists():
                broken.append(f"{path.relative_to(root)}: {model} is not there")

    return count, broken


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", type=Path, default=ROOT / "assets_dev")
    parser.add_argument("worlds", nargs="*")
    args = parser.parse_args()
    worlds = args.worlds or sorted(path.name for path in (args.root / "worlds").iterdir() if path.is_dir())
    failed = False

    for world in worlds:
        count, broken = check_world(args.root, world)

        for line in broken:
            print(line)

        print(f"{world}: {count} model paths, {len(broken)} broken")
        failed = failed or bool(broken)

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
