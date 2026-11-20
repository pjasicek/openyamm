"""Close clay renders of one hand with the fitted finger chains as coloured spheres. Args: -- <rig blend> <side> <out prefix>"""
import bpy, sys, os, json, math
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
blend, sd, out = sys.argv[sys.argv.index('--') + 1:]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']
FJ = json.load(open(os.path.join(HERE, 'work', 'finger_joints.json')))[sd]
cols = [(1, 0, 0, 1), (1, 0.5, 0, 1), (0.1, 0.8, 0.1, 1), (0.1, 0.4, 1, 1), (0.8, 0.1, 0.9, 1)]
for k, p in FJ.items():
    f = int(k.split('Finger')[1][0])
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.004, location=p)
    s = bpy.context.active_object; m = bpy.data.materials.new(k); m.diffuse_color = cols[f]; s.data.materials.append(m)
body.data.materials.clear(); mb = bpy.data.materials.new('b'); mb.diffuse_color = (0.8, 0.8, 0.8, 0.35); body.data.materials.append(mb)
body.show_wire = True
c = rig.data.bones[f'B_{sd}_Hand'].head_local + Vector((0, 0, -0.08))
scene = bpy.context.scene; common.workbench_clay(scene); scene.display.shading.color_type = 'MATERIAL'
scene.display.shading.show_xray = True; scene.display.shading.xray_alpha = 0.5
common.render_views(out, c.z, 0.26, views=('front', 'left' if sd == 'L' else 'right', 'back'), resolution=(600, 600), target=(c.x, c.y))
