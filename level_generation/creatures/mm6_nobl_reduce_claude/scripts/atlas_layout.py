"""Final atlas layout, 3104 x 2080 (rows top-down): head 1024 at (0, 0), body 1024 at (0, 1056), front detail 2048 at
(1056, 0); 32 px gutters. Remaps the runtime UVs of work/ladder_detail.blend (3136 x 1024 strip: body | head | detail
at 1024) -> work/ladder_final.blend. Usage: blender -b -P atlas_layout.py"""
import os, bpy
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OW, W, H = 3136, 3104, 2080
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'ladder_detail.blend'))
me = bpy.data.objects['Cand_62'].data; uv = me.uv_layers[0].data; counts = [0, 0, 0]
for p in me.polygons:
    us = [uv[li].uv[0] * OW for li in p.loop_indices]; c = sum(us) / len(us)
    sec = 0 if c < 1040 else (1 if c < 2096 else 2)
    counts[sec] += 1
    for li in p.loop_indices:
        x, v = uv[li].uv[0] * OW, uv[li].uv[1]
        if sec == 0:                                    # body: left column, bottom
            uv[li].uv = (x / W, v * 1024 / H)
        elif sec == 1:                                  # head: left column, top
            uv[li].uv = ((x - 1056) / W, (1056 + v * 1024) / H)
        else:                                           # detail: 2048 square on the right, top-aligned
            uv[li].uv = ((1056 + (x - 2112) / 1024 * 2048) / W, (32 + v * 2048) / H)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'ladder_final.blend'))
print('LAYOUT faces body/head/detail', counts)
