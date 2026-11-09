"""Render a blend's figure at given actions/frames from several views into tiles; scripts/sheet.py <out> joins them.
Args: -- <blend> <out.png> <spec> [<spec> ...]   spec = ACTION:FRAME (ACTION 'rest' = bind pose)
Env: FIXED=cx,cy,cz,size fixes the ortho frame (sheet.py GRID=1 draws 10 cm lines); VIEWS=front,side,back,threeq (default front,side,threeq), RES=512, HIDE=comma list of object name prefixes,
     ENGINE=EEVEE|WORKBENCH (default EEVEE). Each spec is a row, each view a column."""
import bpy, sys, os, math
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0]))
out = os.path.abspath(a[1]); specs = a[2:]
views = os.environ.get('VIEWS', 'front,side,threeq').split(',')
res = int(os.environ.get('RES', '512'))
hide = [h for h in os.environ.get('HIDE', '').split(',') if h]
sc = bpy.context.scene
for o in sc.objects:
    if any(o.name.startswith(h) for h in hide):
        o.hide_render = True
rig = bpy.data.objects['Rig']
PREVIEW = {'NB_Plate': ((0.80, 0.60, 0.25, 1), 0.8, 0.35, None), 'NB_Glow': ((1.0, 0.45, 0.1, 1), 0.0, 0.5, 4.0)}
for mn, (col, met, rough, em) in PREVIEW.items():          # untextured carapace materials: a preview colour
    m = bpy.data.materials.get(mn)
    if m and not (m.use_nodes and any(n.type == 'TEX_IMAGE' for n in m.node_tree.nodes)):
        m.use_nodes = True; b = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
        b.inputs['Base Color'].default_value = col; b.inputs['Metallic'].default_value = met
        b.inputs['Roughness'].default_value = rough
        if em:
            b.inputs['Emission Color'].default_value = col; b.inputs['Emission Strength'].default_value = em
eng = os.environ.get('ENGINE', 'EEVEE')
try:
    sc.render.engine = 'BLENDER_EEVEE_NEXT' if eng == 'EEVEE' else 'BLENDER_WORKBENCH'
except TypeError:
    sc.render.engine = 'BLENDER_EEVEE' if eng == 'EEVEE' else 'BLENDER_WORKBENCH'
if eng != 'EEVEE':
    sc.display.shading.color_type = 'TEXTURE'; sc.display.shading.light = 'STUDIO'
sc.render.resolution_x = sc.render.resolution_y = res
sc.render.film_transparent = False
w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
w.node_tree.nodes['Background'].inputs[0].default_value = (0.25, 0.25, 0.27, 1); w.node_tree.nodes['Background'].inputs[1].default_value = 1.2
for name, rot, en in [('K', (50, 0, -30), 3.0), ('F', (70, 0, 140), 1.5)]:
    L = bpy.data.lights.new(name, 'SUN'); L.energy = en
    o = bpy.data.objects.new(name, L); sc.collection.objects.link(o); o.rotation_euler = [math.radians(x) for x in rot]
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'
DIRS = {'front': Vector((0, -1, 0)), 'back': Vector((0, 1, 0)), 'side': Vector((1, 0, 0)), 'lside': Vector((-1, 0, 0)),
        'threeq': Vector((0.6, -0.8, 0)), 'threeq_back': Vector((-0.6, 0.8, 0)), 'top': Vector((0, -0.2, 1))}
tmp = []
for si, spec in enumerate(specs):
    act, fr = spec.rsplit(':', 1)
    rig.animation_data_create()
    if act == 'rest':
        rig.animation_data.action = None
        for pb in rig.pose.bones:
            pb.matrix_basis.identity()
    else:
        rig.animation_data.action = bpy.data.actions[act]
    sc.frame_set(int(float(fr)), subframe=float(fr) % 1)
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    pts = []
    for o in sc.objects:
        if o.type == 'MESH' and not o.hide_render:
            e = o.evaluated_get(dg); m = e.to_mesh()
            pts += [o.matrix_world @ v.co for v in list(m.vertices)[::7]]
            e.to_mesh_clear()
    lo = Vector([min(p[i] for p in pts) for i in range(3)]); hi = Vector([max(p[i] for p in pts) for i in range(3)])
    c = (lo + hi) / 2; size = max(hi - lo) * 1.08
    if os.environ.get('FIXED'):
        fx = [float(x) for x in os.environ['FIXED'].split(',')]; c = Vector(fx[:3]); size = fx[3]
    for vi, vn in enumerate(views):
        d = DIRS[vn].normalized()
        cam.location = c + d * 6
        cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
        cam.data.ortho_scale = size
        f = f'{out}.{si}_{vi}.png'; sc.render.filepath = f
        bpy.ops.render.render(write_still=True); tmp.append((si, vi, f))
import json
json.dump({'rows': len(specs), 'cols': len(views), 'res': res, 'tiles': tmp}, open(out + '.json', 'w'))
print('RENDERED', out)
sys.stdout.flush(); os._exit(0)
