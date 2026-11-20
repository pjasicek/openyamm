"""Push the cloak/capelet surface of a reduced candidate outward (world-space vertex normals, REA_PUSH_MM, default 4)
so the dark shoulder sleeves do not poke through the capelet in wide arm poses (coarser triangles cut deeper chords).
Cloak faces: UV centroid on the installed region mask's red channel (work/region_mask.png).
Usage: REA_LADDER=face REA_CAND=Cand_62 blender -b -P push_cloak.py  -> work/ladder_<ladder>push.blend"""
import os, bpy
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
label = os.environ.get('REA_LADDER', 'face'); push = float(os.environ.get('REA_PUSH_MM', '4')) / 1000
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', f'ladder_{label}.blend'))
rig = bpy.data.objects['Rig']; rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
cand = bpy.data.objects[os.environ.get('REA_CAND', 'Cand_62')]; me = cand.data
mask = bpy.data.images.load(os.path.join(HERE, 'work', 'region_mask.png'))
W, H = mask.size; px = np.array(mask.pixels[:], np.float32).reshape(H, W, 4)   # rows bottom-up
uv = me.uv_layers.active.data; cloak = set()
for p in me.polygons:
    u = np.mean([uv[li].uv[0] for li in p.loop_indices]); v = np.mean([uv[li].uv[1] for li in p.loop_indices])
    if px[min(int(v * H), H - 1), min(int(u * W), W - 1), 0] > .5:
        cloak.update(p.vertices)
mw = cand.matrix_world; inv = mw.inverted()
for i in cloak:
    vtx = me.vertices[i]; n = (mw.to_3x3() @ vtx.normal).normalized()
    vtx.co = inv @ (mw @ vtx.co + n * push)
me.update()
print('PUSHED', len(cloak), 'cloak vertices by', push * 1000, 'mm')
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', f'ladder_{label}push.blend'))
