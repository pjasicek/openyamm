"""Debug renders of the head of a blend's Body: faces coloured by a per-triangle label npy (loop-triangle order), cut
away at x > CUT (optional), with a wireframe overlay. Args: <blend> <labels.npy|-> <outdir> <prefix> <views> [cut]
Labels: 0 skin (shaded by jaw weight), 1 red, 2 green, 3 yellow, 4 cyan."""
import bpy, bmesh, sys, os, math
import numpy as np
from mathutils import Vector
argv = sys.argv[sys.argv.index('--') + 1:]
blend, lab, outdir, prefix, views = argv[:5]
cut = float(argv[5]) if len(argv) > 5 else None
os.makedirs(outdir, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=blend)
sc = bpy.context.scene
ob = bpy.data.objects.get('Body') or bpy.data.objects.get('Sea')
for o in list(bpy.data.objects):
    if o != ob and o.type == 'MESH':
        bpy.data.objects.remove(o)
arm = ob.parent
if arm and arm.animation_data:
    arm.animation_data.action = None
if arm:
    for pb in arm.pose.bones:
        pb.matrix_basis.identity()
me = ob.data
me.calc_loop_triangles()
if lab == 'mlab':
    ml = np.array([d.value for d in me.attributes['mlab'].data])
    labels = np.array([{0: 0, 1: 1, 2: 2, 3: 3, 4: 4}[int(ml[list(t.vertices)].max())] for t in me.loop_triangles])
else:
    labels = np.load(lab) if lab != '-' else np.zeros(len(me.loop_triangles), int)
jaw = np.zeros(len(me.vertices))
if 'Bone08' in ob.vertex_groups:
    gi = ob.vertex_groups['Bone08'].index
    for v in me.vertices:
        for g in v.groups:
            if g.group == gi:
                jaw[v.index] = g.weight
poly_lab = {}
for t, l in zip(me.loop_triangles, labels):
    poly_lab[t.polygon_index] = max(poly_lab.get(t.polygon_index, 0), int(l))
pal = {1: (1, 0.15, 0.15), 2: (0.1, 0.8, 0.1), 3: (1, 0.9, 0.1), 4: (0.1, 0.9, 0.9)}
ca = me.color_attributes.new('dbg', 'FLOAT_COLOR', 'CORNER')
for p in me.polygons:
    l = poly_lab.get(p.index, 0)
    for li in p.loop_indices:
        if l:
            c = pal[l]
        else:
            j = jaw[me.loops[li].vertex_index]
            c = (0.35 + 0.5 * j, 0.4, 0.85 - 0.5 * j)
        ca.data[li].color = (*c, 1)
me.color_attributes.active_color = ca
ob.modifiers.clear()
if cut is not None:
    bm = bmesh.new(); bm.from_mesh(me)
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.calc_center_median().x > cut], context='FACES')
    bm.to_mesh(me); bm.free()
wf = ob.copy(); wf.data = me.copy(); sc.collection.objects.link(wf)
m = wf.modifiers.new('wf', 'WIREFRAME'); m.thickness = 0.0025; m.use_replace = True
mat = bpy.data.materials.new('k'); mat.diffuse_color = (0.02, 0.02, 0.02, 1); wf.data.materials.clear(); wf.data.materials.append(mat)
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading
sh.light = 'STUDIO'; sh.color_type = 'VERTEX'; sh.show_backface_culling = False
sc.render.resolution_x = sc.render.resolution_y = 800
sc.render.image_settings.file_format = 'PNG'
cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.ortho_scale = 0.75
cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
ctr = Vector((0.03, -1.68, 0.42))
D = {'front': (0, -1, 0.15), 'side': (-1, 0, 0), 'sidel': (1, 0, 0), 'low': (0, -1, -0.5), 'top': (0, -0.2, 1),
     'q34': (-0.7, -1, 0.3), 'inner': (1, -0.25, 0.1)}
for v in views.split(','):
    d = Vector(D[v]).normalized()
    cam.location = ctr + d * 5
    cam.rotation_euler = (ctr - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(outdir, f'{prefix}_{v}.png')
    bpy.ops.render.render(write_still=True)
