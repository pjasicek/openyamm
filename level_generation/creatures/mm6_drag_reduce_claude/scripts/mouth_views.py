"""Open-mouth close-ups (Attack frame with the widest jaw) of chosen meshes: review/teeth/<label>_<view>_<mode>.png.
Usage: blender -b -P mouth_views.py -- <blend> <Object[:label]>..."""
import os, sys, math, bpy
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
args = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(args[0]))
sc = bpy.context.scene; rig = bpy.data.objects['Rig']
items = [(a.split(':') + [a.split(':')[0]])[:2] for a in args[1:]]
rig.animation_data.action = bpy.data.actions['Attack']
jaw = rig.pose.bones['Jaw']; best = (0, 0)
for f in range(int(bpy.data.actions['Attack'].frame_range[1]) + 1):
    sc.frame_set(f); ang = jaw.matrix_basis.to_quaternion().angle
    best = max(best, (ang, f))
sc.frame_set(best[1]); print('JAW FRAME', best)
head = rig.matrix_world @ rig.pose.bones['Head'].head
mouth = None
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = float(os.environ.get('MOUTH_SCALE', '.075'))
sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); sun.data.energy = 3
sun.rotation_euler = (math.radians(30), 0, math.radians(-20)); sc.collection.objects.link(sun)
w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
w.node_tree.nodes['Background'].inputs['Color'].default_value = (.3, .3, .33, 1)
sc.view_settings.view_transform = 'Standard'; sc.render.resolution_x = sc.render.resolution_y = 640
for o in bpy.data.objects:
    if o.type == 'MESH': o.hide_render = True
for name, label in items:
    ob = bpy.data.objects[name]; ob.hide_render = False
    dg = bpy.context.evaluated_depsgraph_get(); ev = ob.evaluated_get(dg)
    # mouth centre: teeth/jaw region = evaluated vertices with Jaw weight, front-most
    me = ev.to_mesh(); pts = [ob.matrix_world @ v.co for v in me.vertices]
    part = ob.data.attributes['part'].data
    teeth = {16, 18, 19} | set(range(21, 38))
    jv = [pts[i] for i in range(len(pts)) if part[i].value in teeth]
    ev.to_mesh_clear()
    c = sum(jv, Vector()) / len(jv)
    for view, d in {'front': (0, -1, .15), 'q34': (.6, -.8, .25), 'side': (1, -.05, .05), 'under': (.2, -.7, -.6), 'left': (-.6, -.8, .1)}.items():
        dv = Vector(d).normalized(); cam.location = c + dv * .6
        cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
        for mode in ('tex', 'clay'):
            if mode == 'clay':
                sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.light = 'STUDIO'
                sc.display.shading.color_type = 'SINGLE'; sc.display.shading.show_cavity = True
            else:
                sc.render.engine = 'BLENDER_EEVEE'
            sc.render.filepath = os.path.join(HERE, 'review/teeth', f'{label}_{view}_{mode}.png')
            bpy.ops.render.render(write_still=True)
    ob.hide_render = True
