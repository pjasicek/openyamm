"""work/r65_lod0.glb -> work/r65_lods.glb with LOD1-3 and shadow LODs: the same ratios and influence budget as
mm8_m536_claude/scripts/build_lods.py (0.5 / 0.25 / 0.125, 4 influences), on the body alone (the fire shell keeps its
own LODs, the flask remains are untouched). Usage: blender -b -P build_lods.py"""
from pathlib import Path
import sys
import bpy
P = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(P.parents[2] / 'tools'))
from build_actor_lods import generate  # noqa: E402
bpy.ops.wm.read_factory_settings(use_empty=True)
# the glTF importer gives the name 'Body' to an empty for the skinned node and the mesh object becomes 'Body.NNN';
# rename after import so generate() finds the mesh object by node name
_ops = bpy.ops.import_scene
_gltf = _ops.gltf


def _import(**kw):
    r = _gltf(**kw)
    mesh = next(o for o in bpy.data.objects if o.type == 'MESH' and o.data.name.startswith('Body') and o.name != 'Body')
    if 'Body' in bpy.data.objects and bpy.data.objects['Body'].type != 'MESH':
        bpy.data.objects['Body'].name = 'Body_node'
    mesh.name = 'Body'
    return r




class _ImportScene:  # bpy.ops.import_scene is rebuilt on each access, so replace the submodule
    gltf = staticmethod(_import)

    def __getattr__(self, name):
        return getattr(_ops, name)


bpy.ops.import_scene = _ImportScene()
import json  # noqa: E402
# the horn tips (rest z > 2.975, work/lod_top_points.json) are kept in every LOD: LOD3 otherwise ended 1 cm short and
# picking bounds use the coarsest LOD
top = [tuple(p) for p in json.loads((P / 'work/lod_top_points.json').read_text())]
generate(P / 'work/r65_lod0.glb', P / 'work/r65_lods.glb', 'Body', ratios=(.5, .25, .125), max_influences=4,
         protected_points=top)
