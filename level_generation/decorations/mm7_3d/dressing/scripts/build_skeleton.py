"""MM7 `dec19` (36 placements: 33 in out09, 3 in dungeons): a skeleton lying on its back, head to the right, seen
from its left side, pale bones blotched with dried flesh and rust, the ribcage darkest.

The MM6 bones batch's Meshy skeleton with its grafted Meshy skull, posed and thickened by skel_pose.py (pose
`lying`: work/skeleton_lying.blend, objects Skel_lying_L0..L3, 2850 / 1300 / 520 / 215 triangles). Here the LODs get
the recoloured texture sets dec19_bone and dec19_skull (bones_textures.py), are grounded (lowest point on z = 0),
and COLOR_0 = vertex occlusion (with the floor) x a darker, redder tint on the ribcage (the sprite's ribs are mostly
dried flesh). Writes work/dec19.blend and work/dec19_export.glb. Usage: blender --background --python build_skeleton.py"""
import math
import os
import sys

import bpy
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dlib  # noqa: E402

pl, u = dlib.pl, dlib.u
PROP = 'dec19'
RIB_TINT = np.array([0.78, 0.6, 0.52])
RIBS = ((16.0, 42.0), 16.0)            # x range and |y| of the ribcage (map units, posed)


def main():
    pl.reset()
    path = os.path.join(dlib.WORK, 'skeleton_lying.blend')
    names = [f'Skel_lying_L{k}' for k in range(4)]
    with bpy.data.libraries.load(path) as (src, dst):
        dst.objects = names
    mats = {'Bone': dlib.material('Bone', 'dec19_bone', extras={'openyamm_specular': 0.3}),
            'Skull': dlib.material('Skull', 'dec19_skull', extras={'openyamm_specular': 0.3})}
    lods = []
    lowest = None
    for k, obj in enumerate(dst.objects):
        bpy.context.scene.collection.objects.link(obj)
        obj.data = obj.data.copy()
        for i, m in enumerate(obj.data.materials):
            obj.data.materials[i] = mats['Skull' if m.name.startswith('Skull') else 'Bone']
        if lowest is None:
            lowest = min(v.co.z for v in obj.data.vertices)
        for v in obj.data.vertices:
            v.co.z -= lowest
        obj.data.update()
        obj.name = 'Skeleton' if k == 0 else f'Skeleton_LOD{k}'
        obj.data.name = obj.name
        occ = pl.vertex_occlusion(obj, rays=(48, 32, 16, 12)[k], distance=u(12), strength=0.5, floor=True)
        colour = obj.data.color_attributes['Color']
        c = np.empty(len(obj.data.vertices) * 4, np.float32); colour.data.foreach_get('color', c)
        c = c.reshape(-1, 4)
        co = np.array([v.co[:] for v in obj.data.vertices]) * dlib.UNITS_PER_METRE
        rng = np.random.default_rng(3)
        ribs = (co[:, 0] > RIBS[0][0]) & (co[:, 0] < RIBS[0][1]) & (np.abs(co[:, 1]) < RIBS[1])
        blend = 0.6 + 0.4 * rng.random(len(co))
        c[ribs, :3] *= (1 - blend[ribs, None]) + blend[ribs, None] * RIB_TINT
        colour.data.foreach_set('color', c.ravel())
        print('LEVEL', k, obj.name, 'tris', pl.triangles(obj), 'occlusion', round(occ, 3), 'rib verts',
              int(ribs.sum()))
        lods.append(obj)
    dlib.save(PROP, lods)


main()
