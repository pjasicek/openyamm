"""MM9 reference renders for the Codex HD masters: textured bind pose on flat grey, views q34 (front three-quarter
from the creature's RIGHT, slightly above), front, left (creature's left side), back, right, top.
The creature faces -Y. FLIP=1 turns the armature 180 deg about the forward axis (the Lobber grown upright, root bulb
on the ground). Args: glb outdir prefix size ortho"""
import bpy, sys, math, os
from mathutils import Vector
argv = sys.argv[sys.argv.index('--') + 1:]
glb, outdir, prefix, size, ortho = argv[0], argv[1], argv[2], int(argv[3]), float(argv[4])
os.makedirs(outdir, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
sc = bpy.context.scene
for o in sc.objects:
    if o.name.startswith('Icosphere'):
        o.hide_render = True
arm = next(o for o in sc.objects if o.type == 'ARMATURE')
if arm.animation_data:
    arm.animation_data.action = None
for pb in arm.pose.bones:
    pb.matrix_basis.identity()
if os.environ.get('FLIP') == '1':
    arm.rotation_mode = 'XYZ'
    arm.rotation_euler = (0, math.pi, 0)
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
pts = []
for o in sc.objects:
    if o.type == 'MESH' and not o.hide_render:
        me = o.evaluated_get(dg).to_mesh()
        pts += [o.matrix_world @ v.co for v in me.vertices]
        o.evaluated_get(dg).to_mesh_clear()
c = Vector([(min(p[i] for p in pts) + max(p[i] for p in pts)) / 2 for i in range(3)])
if os.environ.get('CENTER_BONE'):
    c = arm.matrix_world @ arm.data.bones[os.environ['CENTER_BONE']].head_local + Vector(
        [float(x) for x in os.environ.get('CENTER_OFS', '0,0,0').split(',')])
EEVEE = os.environ.get('EEVEE') == '1'
if EEVEE:
    for eng in ('BLENDER_EEVEE', 'BLENDER_EEVEE_NEXT'):
        try:
            sc.render.engine = eng
            break
        except TypeError:
            pass
    for m in bpy.data.materials:
        if m.node_tree:
            bsdf = next((n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
            if bsdf:
                bsdf.inputs['Roughness'].default_value = 0.9
                for nm in ('Specular IOR Level', 'Specular'):
                    if nm in bsdf.inputs:
                        bsdf.inputs[nm].default_value = 0.0
else:
    try:
        sc.render.engine = 'BLENDER_WORKBENCH'
    except TypeError:
        pass
sh = sc.display.shading
sh.light = 'STUDIO'; sh.color_type = 'TEXTURE'; sh.show_backface_culling = False
sc.render.resolution_x = sc.render.resolution_y = size
sc.render.film_transparent = False
w = bpy.data.worlds.new('w'); sc.world = w
w.color = (0.42, 0.42, 0.42)
if EEVEE:
    w.use_nodes = True
    bg = next(n for n in w.node_tree.nodes if n.type == 'BACKGROUND')
    bg.inputs[0].default_value = (0.42, 0.42, 0.42, 1); bg.inputs[1].default_value = 1.6
    ld = bpy.data.lights.new('key', 'SUN'); ld.energy = 1.5
    lo = bpy.data.objects.new('key', ld); sc.collection.objects.link(lo); lo.rotation_euler = (0.7, 0.2, -0.6)
sc.display.shading.background_type = 'WORLD'
cd = bpy.data.cameras.new('cam'); cd.type = 'ORTHO'; cd.ortho_scale = ortho; cd.clip_end = 100
cam = bpy.data.objects.new('cam', cd); sc.collection.objects.link(cam); sc.camera = cam
dirs = {'q34': Vector((-1.0, -1.25, 0.55)), 'front': Vector((0, -1, 0.08)), 'left': Vector((1, 0, 0.08)),
        'back': Vector((0, 1, 0.08)), 'right': Vector((-1, 0, 0.08)), 'top': Vector((0, 0.0001, 1))}
for v, d in dirs.items():
    d = d.normalized()
    cam.location = c + d * 10
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(outdir, f'{prefix}_{v}.png')
    bpy.ops.render.render(write_still=True)
print('REFS', prefix)
