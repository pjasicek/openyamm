"""work/g82_lod0.glb -> export/mm8_m632.glb (or argv after --) with LOD1-3 and shadow LODs: the creature's own builder
settings (../mm8_m632_claude/scripts/build_lods.py: 0.5 / 0.25 / 0.125, 8 influences, helmet-horn tips and sole ends
protected, plus horn_points.py curve points and floor_points.py Dead/Death floor contacts; the crossbow points of that list are left out because the crossbow is a separate file).
Usage: blender -b -P build_lods.py [-- <in lod0.glb> <out.glb>]"""
import json, sys
from pathlib import Path
P = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(P.parents[2] / 'tools'))
from build_actor_lods import generate  # noqa: E402
args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [str(P / 'work/g82_lod0.glb'), str(P / 'export/mm8_m632.glb')]
points = json.loads((P.parent / 'mm8_m632_claude/review/lod_protected_points.json').read_text())[:10]
horn = P / 'work/horn_points.json'  # horn_points.py: curve points along both horns
points += json.loads(horn.read_text()) if horn.exists() else []
floor = P / 'work/floor_points.json'  # floor_points.py: Dead/Death floor contacts (LOD3 corpse floated 2 cm)
points += json.loads(floor.read_text()) if floor.exists() else []
generate(Path(args[0]), Path(args[1]), 'DarkDwarf', ratios=(.5, .25, .125), max_influences=8,
         protected_points=[tuple(x) for x in points])
