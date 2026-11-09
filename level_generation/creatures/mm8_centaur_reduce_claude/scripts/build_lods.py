"""work/r82_lod0.glb -> work/r82_lods.glb with LOD1-3 and shadow LODs: the m532 project's ratios (build_actor_lods
defaults 0.5 / 0.18 / 0.06, 4 influences) on the body alone (bow and quiver stay their own installed attachments).
Usage: blender -b -P build_lods.py"""
from pathlib import Path
import sys
P = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(P.parents[2] / 'tools'))
from build_actor_lods import generate  # noqa: E402
generate(P / 'work/r82_lod0.glb', P / 'work/r82_lods.glb', 'Body', ratios=(.5, .18, .06), max_influences=4)
