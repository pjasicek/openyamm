"""Run the unchanged lighting producer against each isolated map, in one background Blender."""
import json
from pathlib import Path
import runpy
import sys

project = Path(__file__).resolve().parents[1]
config = json.loads((project / "source/ships.json").read_text())
producer = project / "playtest/tools/lighting/bake_outdoor.py"
for entry in config["maps"]:
    stem = Path(entry["map"]).stem
    sys.argv = [str(producer), "--", "--profile", str(project / "source/profiles" / (stem + ".json")),
                "--output", str(project / "bake" / stem)]
    print("SHIP_LIGHTING_BEGIN " + stem, flush=True)
    runpy.run_path(str(producer), run_name="__main__")
    print("SHIP_LIGHTING_COMPLETE " + stem, flush=True)
