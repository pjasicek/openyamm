"""Close-up textured renders of the sensor head and a ring rim (rest pose, no clip). Args: basecolor out_png"""
import bpy, sys, os, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common_rob1 as C
args = sys.argv[sys.argv.index('--') + 1:]
img = bpy.data.images.load(args[0])
mat = bpy.data.materials.new('P'); mat.use_nodes = True; nt = mat.node_tree
n = nt.nodes.new('ShaderNodeTexImage'); n.image = img
nt.links.new(n.outputs['Color'], next(x for x in nt.nodes if x.type == 'BSDF_PRINCIPLED').inputs['Base Color'])
me = bpy.data.objects['Robot'].data; me.materials.clear(); me.materials.append(mat)
rig = bpy.data.objects['Robot_Rig']; rig.animation_data.action = None
for b in rig.pose.bones: b.matrix_basis.identity()
bpy.context.view_layer.update()
out = args[1]; cells = []
for name, loc, tgt, sc in (('s_front', (0.2, -0.6, 1.2), (0, -0.03, 0.93), 0.3), ('s_side', (-0.7, -0.1, 1.1), (0, -0.03, 0.93), 0.3),
                           ('s_top', (0.25, 0.3, 1.5), (0, -0.03, 0.93), 0.3), ('rim', (-0.9, -1.5, 1.3), (0, -0.2, 0.55), 0.7)):
    p = out.replace('.png', f'_{name}.png'); C.render_ortho(loc, tgt, sc, p, res=(400, 400), textured=True); cells.append(p)
subprocess.run(['/usr/bin/python3', '-c', """
import sys
from PIL import Image
ims=[Image.open(p) for p in sys.argv[2:]]; o=Image.new('RGB',(400*len(ims),400))
[o.paste(im,(i*400,0)) for i,im in enumerate(ims)]; o.save(sys.argv[1])
""", out] + cells, check=True)
for p in cells: os.remove(p)
