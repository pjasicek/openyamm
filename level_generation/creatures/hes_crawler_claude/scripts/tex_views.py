"""Textured rest views (workbench, texture colour). Args: -- <basecolor png rel. to project> <out prefix> [clip frame]
Views: quarter, side, front, back, top, under, head close-up; writes <prefix>_sheet.jpg."""
import bpy, os, sys, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'anim_v1.blend'))
mesh = bpy.data.objects[C.MESH]; rig = bpy.data.objects[C.RIG]
mat = bpy.data.materials.new('tex'); mat.use_nodes = True
n = mat.node_tree.nodes.new('ShaderNodeTexImage'); n.image = bpy.data.images.load(os.path.join(HERE, a[0]))
bsdf = next(x for x in mat.node_tree.nodes if x.type == 'BSDF_PRINCIPLED')
mat.node_tree.links.new(n.outputs['Color'], bsdf.inputs['Base Color']); mat.node_tree.nodes.active = n
mesh.data.materials.clear(); mesh.data.materials.append(mat)
if len(a) > 2:
    act = bpy.data.actions[a[2]]; rig.animation_data.action = act
    if len(getattr(act, 'slots', [])):
        rig.animation_data.action_slot = act.slots[0]
    bpy.context.scene.frame_set(int(a[3]) if len(a) > 3 else 0)
else:
    rig.animation_data.action = None
    for b in rig.pose.bones:
        b.matrix_basis.identity()
bpy.context.scene.display.shading.light = 'FLAT'
V = dict(C.VIEWS)
V['head'] = ((-0.45, -0.9, 0.35), (0, -0.42, 0.17))
paths = []
for v in ('quarter', 'side', 'front', 'back', 'top', 'under', 'head'):
    loc, tgt = V[v]
    p = os.path.join(HERE, f'{a[1]}_{v}.png')
    C.render(loc, tgt, 0.45 if v == 'head' else 1.15, p, res=(640, 460), textured=True, floor=False)
    bpy.context.scene.display.shading.light = 'FLAT'
    paths.append(p)
compose = """
import sys
from PIL import Image
out = sys.argv[1]; ims = [Image.open(p) for p in sys.argv[2:]]; w, h = ims[0].size
o = Image.new('RGB', (w * 4, h * 2), (60, 60, 60))
for i, im in enumerate(ims): o.paste(im, ((i % 4) * w, (i // 4) * h))
o.save(out, quality=88)
"""
subprocess.run(['/usr/bin/python3', '-c', compose, os.path.join(HERE, f'{a[1]}_sheet.jpg')] + paths, check=True)
print('TEXVIEWS done')
