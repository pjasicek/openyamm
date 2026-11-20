"""Prepare a Meshy weapon return for painting: import meshy/<job>/model_urls_glb.glb, put its flat side in the XZ plane
(the smallest principal axis along Y), its long axis along +Z (tip up unless FLIP), centred, scaled to LENGTH metres;
save work/weapons/<name>.blend (object W_<name>) and render the paint guides: review/weapons/<name>_guide_{front,back}.png
(orthographic along +Y and -Y, flat grey with cavity outline, 1024 px, frame recorded in work/weapons/<name>_frame.json).
Args: -- <job> <name> <length_m> [flip]"""
import bpy, sys, os, json, math
import numpy as np
from mathutils import Vector, Matrix
P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
a = sys.argv[sys.argv.index('--') + 1:]
job, name, length = a[0], a[1], float(a[2]); flip = len(a) > 3 and a[3] == 'flip'
os.makedirs(os.path.join(P, 'work', 'weapons'), exist_ok=True); os.makedirs(os.path.join(P, 'review', 'weapons'), exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.join(P, 'meshy', job, 'model_urls_glb.glb'))
ob = next(o for o in bpy.data.objects if o.type == 'MESH')
ob.parent = None
ob.data.transform(ob.matrix_world); ob.matrix_world = Matrix.Identity(4)
for o in [o for o in bpy.data.objects if o is not ob]:
    bpy.data.objects.remove(o, do_unlink=True)
ob.name = ob.data.name = 'W_' + name
X = np.array([tuple(v.co) for v in ob.data.vertices])
c = X.mean(0); U, S, Vt = np.linalg.svd(X - c, full_matrices=False)
long_ax, mid_ax, thin_ax = Vt[0], Vt[1], Vt[2]
R = np.array([mid_ax, thin_ax, long_ax])             # rows: new x, y, z
if np.linalg.det(R) < 0: R[0] *= -1
Y = (X - c) @ R.T
# tip up: the end of the long axis whose cross-section is thinner is the tip (blades, barrels); FLIP overrides
top = Y[:, 2] > np.percentile(Y[:, 2], 85); bot = Y[:, 2] < np.percentile(Y[:, 2], 15)
if (np.ptp(Y[top][:, 0]) > np.ptp(Y[bot][:, 0])) != flip:
    Y[:, 2] *= -1; Y[:, 0] *= -1
Y -= (Y.max(0) + Y.min(0)) / 2
Y *= length / np.ptp(Y[:, 2])
for v, p in zip(ob.data.vertices, Y):
    v.co = Vector(p)
ob.data.update()
mn, mx = Y.min(0), Y.max(0)
sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'SINGLE'
sc.display.shading.single_color = (0.75, 0.75, 0.75); sc.display.shading.show_cavity = True
sc.display.shading.cavity_type = 'BOTH'; sc.display.shading.show_object_outline = True
sc.render.resolution_x = sc.render.resolution_y = 1024; sc.render.film_transparent = False
sc.world = bpy.data.worlds.new('W'); sc.world.color = (0.05, 0.05, 0.05)
cam = bpy.data.objects.new('C', bpy.data.cameras.new('C')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; size = float(max(mx[0] - mn[0], mx[2] - mn[2]) * 1.08); cam.data.ortho_scale = size
frame = {'size': size, 'centre': [0, 0, 0], 'res': 1024, 'length': length, 'bounds': [mn.tolist(), mx.tolist()]}
for view, d in [('front', Vector((0, -1, 0))), ('back', Vector((0, 1, 0)))]:
    cam.location = d * 5; cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(P, 'review', 'weapons', f'{name}_guide_{view}.png'); bpy.ops.render.render(write_still=True)
json.dump(frame, open(os.path.join(P, 'work', 'weapons', f'{name}_frame.json'), 'w'), indent=1)
bpy.data.objects.remove(cam, do_unlink=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(P, 'work', 'weapons', f'{name}.blend'))
print('PREP', name, 'tris', sum(len(p.vertices) - 2 for p in ob.data.polygons), 'size', [round(float(x), 3) for x in mx - mn])
sys.stdout.flush(); os._exit(0)
