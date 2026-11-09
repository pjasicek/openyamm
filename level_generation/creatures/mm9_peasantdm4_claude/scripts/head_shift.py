"""Centre the head on the skeleton's midline (PeasantDM4, 2026-11-02): Meshy put the separate head shell (face, beard,
hair) and the cap 1.3 cm toward -x (eye cups at x -0.041 / +0.0135, head bbox centre -0.0125; no yaw, the eyes level and
at the same depth) while the body and the Head joint are centred. Every vertex of a face with `head` = 1 moves by DX.
The head parts are loose shells (head_split.py: whole parts, no span), so nothing tears. Before the UV pass.
Args (Blender): <in blend> <out blend> [dx 0.0135]"""
import bpy, sys, bmesh
argv = sys.argv[sys.argv.index('--') + 1:]
src, dst = argv[0], argv[1]
dx = float(argv[2]) if len(argv) > 2 else 0.0135
bpy.ops.wm.open_mainfile(filepath=src)
ob = bpy.data.objects['Body']
me = ob.data
bm = bmesh.new(); bm.from_mesh(me)
hl = bm.faces.layers.int.get('head')
vs = {v for f in bm.faces if f[hl] == 1 for v in f.verts}
shared = {v for v in vs if any(f[hl] != 1 for f in v.link_faces)}
for v in vs:
    v.co.x += dx
bm.to_mesh(me); bm.free()
bpy.ops.wm.save_as_mainfile(filepath=dst)
print('HEADSHIFT', len(vs), 'verts moved by', dx, 'shared with body faces', len(shared))
