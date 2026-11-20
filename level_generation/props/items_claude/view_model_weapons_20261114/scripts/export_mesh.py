"""Step 5a (README.md): the locked layout as arrays for post.py: work/<kind>/maps/mesh.npz with per triangle corner
the glTF position, split normal and UV (glTF v down), per triangle the region (vmw.REGIONS), and the same mesh's
bounds. A kind with kinds.py `compress` (z_a, z_b, k) has its plain shaft between z_a and z_b shortened to k of its length
(same triangles and UVs; README.md "Held length"). Usage: blender --background --python export_mesh.py -- <kind>"""
import os
import sys

import bpy
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)
KIND = sys.argv[sys.argv.index('--') + 1]
sys.path.insert(0, HERE)
from kinds import KINDS  # noqa: E402
WORK = os.path.join(PROJECT, 'work', KIND)
os.makedirs(os.path.join(WORK, 'maps'), exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=os.path.join(WORK, 'layout.blend'))
obj = next(o for o in bpy.data.objects if o.type == 'MESH' and o.name != 'upload')
me = obj.data
co = np.array([v.co for v in me.vertices], np.float64)
if 'compress' in KINDS[KIND]:
    za, zb, k = KINDS[KIND]['compress']
    z = co[:, 2]
    co[:, 2] = np.where(z <= za, z, np.where(z >= zb, z - (zb - za) * (1 - k), za + (z - za) * k))
if 'shift' in KINDS[KIND]:
    # Moved along the long axis (Blender Z; README.md "Club"): the fist holds the club higher up its wrap, so the knob
    # reaches the top of the idle frame; the blaster lifted up the fist (README.md "Blaster"). Same triangles, UVs and
    # paint.
    co[:, 2] += KINDS[KIND]['shift']
normals =np.array([n.vector for n in me.corner_normals], np.float64)
uvs = np.array([d.uv[:] for d in me.uv_layers['UVMap'].data], np.float64)
loops = np.array([p.loop_indices[:] for p in me.polygons], np.int64)
verts = np.array([p.vertices[:] for p in me.polygons], np.int64)
region = np.array([d.value for d in me.attributes['region'].data], np.int32)
to_gltf = lambda a: np.stack([a[..., 0], a[..., 2], -a[..., 1]], -1)
if KINDS[KIND].get('turn'):
    # Turned half a turn about the vertical (a rigid turn: UVs and paint unchanged; README.md "Blaster").
    co[:, :2] *= -1.0
    normals[:, :2] *= -1.0
if 'aim' in KINDS[KIND]:
    # The muzzle raised about the palm (the node's +Z, Blender -Y; README.md "Blaster"): a rigid turn after `turn`.
    a = np.radians(KINDS[KIND]['aim'])
    pitch = np.array([[np.cos(a), 0.0, -np.sin(a)], [0.0, 1.0, 0.0], [np.sin(a), 0.0, np.cos(a)]])
    co = co @ pitch.T
    normals = normals @ pitch.T
if KINDS[KIND].get('mount'):
    # A rigid placement from the build frame into the node the weapon is held in (README.md "Crossbow hold": the
    # crossbow from the left hand's Torch frame into the right hand's Weapon node, kinds.weapon_from_build, which the
    # crossbow set's clip bake uses too). It is given in glTF coordinates: applied here between to_gltf and its
    # inverse. UVs and paint unchanged.
    from kinds import weapon_from_build  # noqa: E402
    place = weapon_from_build(KINDS[KIND]['mount'])
    gltf = np.array([[1.0, 0.0, 0.0], [0.0, 0.0, 1.0], [0.0, -1.0, 0.0]])
    turn = gltf.T @ place[:3, :3] @ gltf
    co = co @ turn.T + gltf.T @ place[:3, 3]
    normals = normals @ turn.T
pos = to_gltf(co[verts])
nrm = to_gltf(normals[loops])
uv = uvs[loops].copy()
uv[..., 1] = 1.0 - uv[..., 1]
np.savez(os.path.join(WORK, 'maps', 'mesh.npz'), pos=pos, nrm=nrm, uv=uv, region=region, blender_pos=co[verts])
print('EXPORT', KIND, len(verts), 'tris')
