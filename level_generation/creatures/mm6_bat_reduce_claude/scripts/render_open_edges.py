"""Debug render: candidate mesh (rest pose, clay) from front/back/top with its open (boundary) edges projected and
listed; out review/holes/<tag>_<view>.png + <tag>_edges.json (2D segments per view)."""
import os, sys, json, math, bpy, bmesh
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
blend, name, tag = sys.argv[sys.argv.index('--') + 1:][:3]
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', blend))
o = bpy.data.objects[name]; rig = bpy.data.objects['Rig']; rig.animation_data.action = None
for b in rig.pose.bones: b.matrix_basis.identity()
for x in bpy.data.objects: x.hide_render = x is not o
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get(); me = o.evaluated_get(dg).to_mesh()
bm = bmesh.new(); bm.from_mesh(me)
segs = [(o.matrix_world @ e.verts[0].co, o.matrix_world @ e.verts[1].co) for e in bm.edges if e.is_boundary]
sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'; sh = sc.display.shading
sh.light = 'STUDIO'; sh.color_type = 'SINGLE'; sh.single_color = (.75, .72, .68); sc.render.resolution_x = sc.render.resolution_y = 900
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = float(os.environ.get('OE_SCALE', '1.1'))
c = Vector(json.loads(os.environ.get('OE_CENTER', '[0, 0, 0.17]')))
out = os.path.join(HERE, 'review', 'holes'); os.makedirs(out, exist_ok=True); res = {}
VIEWS = {'front': (0, -1, 0), 'back': (0, 1, 0), 'top': (0, 0, 1), 'below': (0, 0, -1), 'side': (1, 0, 0), 'q34': (.7, -.7, .2)}
for view, d in VIEWS.items():
    cam.location = c + Vector(d) * 4
    up = (0, 1, 0) if view in ('top', 'below') else (0, 0, 1)
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    bpy.context.view_layer.update()
    sc.render.filepath = os.path.join(out, f'{tag}_{view}.png'); bpy.ops.render.render(write_still=True)
    res[view] = [[list(world_to_camera_view(sc, cam, a))[:2], list(world_to_camera_view(sc, cam, b))[:2]] for a, b in segs]
json.dump(res, open(os.path.join(out, f'{tag}_edges.json'), 'w'))
