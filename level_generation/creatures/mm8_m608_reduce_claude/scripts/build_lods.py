"""work/r82_lod0.glb (body and rubble LOD0 swapped) -> work/m608_lods.glb with LOD1-3 and shadow LODs: the creature's
own build order and settings (mm8_m608_codex/scripts/build.py: body, then rubble, ratios 0.5 / 0.25 / 0.125,
4 influences). The rubble's LOD1-2 take 0.6 / 0.28: at 0.5 the band (a fifth of the smaller rubble LOD0) turned
octagonal and lost its studs already at LOD1 (review/lods/sheet.png), where the installed LOD1 kept it round. Usage: blender -b -P build_lods.py"""
from pathlib import Path
import json, os, sys
import bpy
P = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(P.parents[2] / 'tools'))
from build_actor_lods import generate, read_glb  # noqa: E402
# the glTF importer gives the node name to an empty and calls the skinned mesh object after its mesh
# ('Juggernaut.003', 'BandShard'); rename after import so generate() finds the mesh object by node name (as m536)
_ops = bpy.ops.import_scene; _gltf = _ops.gltf
STATE = {}


def _import(**kw):
    r = _gltf(**kw)
    node, mesh_name = STATE['node'], STATE['mesh']
    if node in bpy.data.objects and bpy.data.objects[node].type != 'MESH':
        bpy.data.objects[node].name = node + '_node'
    next(o for o in bpy.data.objects if o.type == 'MESH' and o.data.name == mesh_name).name = node
    return r


class _ImportScene:  # bpy.ops.import_scene is rebuilt on each access, so replace the submodule
    gltf = staticmethod(_import)

    def __getattr__(self, name):
        return getattr(_ops, name)


bpy.ops.import_scene = _ImportScene()
PROTECT = json.loads((P / 'work/lod_protect.json').read_text()) if (P / 'work/lod_protect.json').exists() else {}
for node, a, b, ratios in [('Juggernaut', 'r82_lod0', 'body_lods', (.5, .25, .125)), ('Rubble', 'body_lods', 'm608_lods', (.6, .28, .125))]:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    doc, _ = read_glb(P / f'work/{a}.glb')
    STATE.update(node=node, mesh=doc['meshes'][next(n for n in doc['nodes'] if n.get('name') == node)['mesh']]['name'])
    generate(P / f'work/{a}.glb', P / f'work/{b}.glb', node, ratios=ratios, max_influences=4,
             protected_points=[tuple(p) for p in PROTECT.get(node, [])])
