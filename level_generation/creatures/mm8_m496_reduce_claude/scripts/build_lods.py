"""work/r55_lod0.glb -> work/r55_lods.glb with LOD1-3 and shadow LODs (tools/build_actor_lods.py, 4 influences).
Ratios 0.5 / 0.25 / 0.145 of the 3,570-triangle LOD0 give about 1,785 / 892 / 518; the installed body LOD3 had 516.
Flame, Ash, Burst and Tongues keep their own installed LOD chains. The eyes' front outline (per eye, the eye-swatch
vertices nearest its front-facing plane, about a third of them) is protected: without it the eyes of LOD2-3 collapsed
to triangles, where the installed LODs keep six-sided eyes. Blender's glTF importer turns these
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


def eye_outline():
    import numpy as np
    bpy.ops.import_scene.gltf(filepath=str(P / 'work/r55_lod0.glb'))
    body = bpy.data.objects['Body']; uv = body.data.uv_layers.active.data
    eye = set()
    for poly in body.data.polygons:
        if max(uv[li].uv.x for li in poly.loop_indices) < 16 / 1040:
            eye.update(poly.vertices)
    co = np.array([tuple(body.matrix_world @ body.data.vertices[i].co) for i in sorted(eye)])
    points = []
    for side in (co[:, 0] < 0, co[:, 0] >= 0):
        c = co[side]; dy = np.abs(c[:, 1] - np.median(c[:, 1]))
        points += [tuple(x) for x in c[dy <= np.quantile(dy, .33)]]
    bpy.ops.wm.read_factory_settings(use_empty=True)
    print('EYE OUTLINE points', len(points), 'of', len(co))
    return points


generate(P / 'work/r55_lod0.glb', P / 'work/r55_lods.glb', 'Body', ratios=(.5, .25, .145), max_influences=4,
         protected_points=eye_outline())
