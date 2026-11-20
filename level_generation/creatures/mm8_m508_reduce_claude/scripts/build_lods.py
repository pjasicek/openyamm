"""work/r55_lod0.glb -> work/r55_lods.glb with LOD1-3 and shadow LODs (tools/build_actor_lods.py, 4 influences).
Ratios 0.5 / 0.25 / 0.145 of the 3,520-triangle LOD0 give about 1,760 / 880 / 510; the installed body LOD3 had 510.
Wind, DeathCloud and Lightning keep their own installed LOD chains. Blender's glTF importer turns the Air Elemental's
mesh nodes into an empty named like the node plus the mesh object '<node>.001'; the import is wrapped so the mesh object
carries the node name the generator looks up. Usage: blender -b -P build_lods.py"""
from pathlib import Path
import sys
import bpy
P = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(P.parents[2] / 'tools'))
from build_actor_lods import generate  # noqa: E402

_import = bpy.ops.import_scene.gltf


class _ImportScene:  # bpy.ops.import_scene builds a new submodule object per access, so replace the attribute itself
    @staticmethod
    def gltf(**kw):
        result = _import(**kw)
        for o in list(bpy.data.objects):
            if o.type != 'MESH' and o.name == 'Body':
                o.name = 'Body_node'
        mesh = bpy.data.objects.get('Body.001')
        if mesh is not None and mesh.type == 'MESH':
            mesh.name = 'Body'
        return result


bpy.ops.import_scene = _ImportScene()
generate(P / 'work/r55_lod0.glb', P / 'work/r55_lods.glb', 'Body', ratios=(.5, .25, .145), max_influences=4)
