#!/usr/bin/env python3
"""Install an accepted 3D model (creature, attachment, decoration or prop) as a source, and its runtime copy.

The accepted GLB goes to assets_source/<scope>/models/<name>.glb, the authoritative source (scope: worlds/<world> or
engine; --world-items uses engine/world_items, and with --world <world> a world's own ground items in
worlds/<world>/world_items, such as MM9's). Decoration models of every world (<world>_deco_*.glb) are engine content and need --engine. A model matching COOKED_MODELS (decorations since 2026-10-12) is then cooked into assets_dev
(tools/cook_models.py --only <path>). Any other model, until the switch to cooked models (ASSET_COOKING_PLAN.md
section 12), gets an uncooked runtime copy at the same relative path in assets_dev, with hidden back faces culled
(tools/model_backface_split.py).

    tools/install_model.py <accepted.glb> [--world mm6 | --engine | --world-items [--world mm9]] [--name <file name>]

Install the unprocessed export: never copy a runtime copy back over a project export or a source.
Installs are serialised (an exclusive lock on assets_source/.cook-cache/install.lock): several sessions may install
at once, and concurrent cooks would race on the cook receipts.
"""
import argparse
import fcntl
import fnmatch
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent
# Models whose runtime copy is cooked: every model since the switch (2026-10-14). Each install cooks its model for
# desktop; Android cooks only on demand (tools/cook_android.sh).
COOKED_MODELS = ("*",)


def copy_atomically(source, target):
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=target.parent, prefix=target.name + ".", suffix=".tmp",
                                     delete=False) as handle:
        temporary = Path(handle.name)
    try:
        shutil.copyfile(source, temporary)
        temporary.chmod(0o644)
        os.replace(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("model", type=Path, help="the accepted, unprocessed GLB (usually the project's export)")
    parser.add_argument("--world", help="world package (default mm6); with --world-items, that world's own ground items")
    parser.add_argument("--engine", action="store_true", help="the engine package (shared models such as satchels)")
    parser.add_argument("--world-items", action="store_true",
                        help="ground items: the engine's isolated WIP (excluded from releases), or --world's own")
    parser.add_argument("--name", help="installed file name (default: the model's file name)")
    args = parser.parse_args()
    if args.engine and (args.world or args.world_items):
        raise SystemExit("--engine excludes --world and --world-items")
    model = args.model.resolve(strict=True)
    if model.suffix.lower() != ".glb":
        raise SystemExit(f"{model}: not a .glb")
    name = args.name or model.name
    if fnmatch.fnmatch(name, "mm*_deco_*.glb") and not args.engine:
        raise SystemExit(f"{name}: decoration models are engine content (any world binds them); use --engine")
    if Path(name).name != name or Path(name).suffix.lower() != ".glb":
        raise SystemExit("--name must be a GLB filename, without directories")
    if args.world_items:
        scope_path = f"worlds/{args.world}/world_items" if args.world else "engine/world_items"
    else:
        scope_path = "engine" if args.engine else f"worlds/{args.world or 'mm6'}"
    relative = Path(scope_path) / "models" / name
    source = ROOT / "assets_source" / relative
    runtime = ROOT / "assets_dev" / relative
    if model in (source, runtime):
        raise SystemExit("Install from the project's export, not from an installed copy")
    lock_path = ROOT / "assets_source" / ".cook-cache" / "install.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        return install(model, source, runtime, relative)


def install(model, source, runtime, relative):
    copy_atomically(model, source)
    print(f"source: {source.relative_to(ROOT)}")
    if any(fnmatch.fnmatch(relative.as_posix(), pattern) for pattern in COOKED_MODELS):
        subprocess.run([sys.executable, str(ROOT / "tools/cook_models.py"), "--profile", "desktop", "--only",
                        relative.as_posix()], check=True)
        return 0
    copy_atomically(source, runtime)
    subprocess.run([sys.executable, str(ROOT / "tools/model_backface_split.py"), str(runtime)], check=True)
    print(f"runtime copy (uncooked): {runtime.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
