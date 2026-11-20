"""Textured torso/arm close-ups of a runtime body GLB (default material = tier A; LOD and shadow meshes hidden), Standing
frame 0, EEVEE with a key light from the upper front and a soft fill: front, three-quarter (his right front, the
viewer's 'quarter') and right side, orthographic on the chest. Writes <out_prefix>_{front,tq,side}.png.
Args: -- <glb> <out_prefix> [ortho height]"""
import bpy, sys, os, math
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
glb, out = a[0], a[1]; OH = float(a[2]) if len(a) > 2 else 1.05
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.abspath(glb))
sc = bpy.context.scene
for o in bpy.data.objects:
    if o.type == 'MESH' and ('LOD' in o.name or 'Shadow' in o.name):
        o.hide_render = True
arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
act = next(x for x in bpy.data.actions if x.name.split('|')[-1] == 'Standing' or x.name == 'Standing')
arm.animation_data.action = act
if len(act.slots):
    arm.animation_data.action_slot = act.slots[0]
sc.frame_set(0)
if os.environ.get('UNLIT'):                                     # debug: base colour as emission (no lighting)
    for m in bpy.data.materials:
        if not m.use_nodes:
            continue
        nt = m.node_tree; bsdf = next((n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'), None)
        out_n = next((n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL'), None)
        if bsdf is None or out_n is None:
            continue
        em = nt.nodes.new('ShaderNodeEmission')
        src = bsdf.inputs['Base Color']
        if src.links:
            nt.links.new(src.links[0].from_socket, em.inputs['Color'])
        else:
            em.inputs['Color'].default_value = src.default_value
        nt.links.new(em.outputs['Emission'], out_n.inputs['Surface'])
for eng in ('BLENDER_EEVEE_NEXT', 'BLENDER_EEVEE'):
    try:
        sc.render.engine = eng; break
    except TypeError:
        pass
sc.render.resolution_x = sc.render.resolution_y = 700
w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
bg = next(n for n in w.node_tree.nodes if n.type == 'BACKGROUND'); bg.inputs[0].default_value = (0.42, 0.44, 0.47, 1); bg.inputs[1].default_value = 0.7
sun = bpy.data.objects.new('key', bpy.data.lights.new('key', 'SUN')); sc.collection.objects.link(sun)
sun.data.energy = 3.0; sun.rotation_euler = (math.radians(50), 0, math.radians(-25))
# the model faces +Y after the glTF import (-Y in Blender before export with export_yup); find its front
tgt = Vector((0, 0, 1.22))
fwd = None
hd = next((b for b in arm.pose.bones if b.name == 'B_Head'), None)
pel = next((b for b in arm.pose.bones if b.name == 'B_Pelvis'), None)
dirs = {}
for name, az in (('front', 0), ('tq', -40), ('side', -90)):
    dirs[name] = az
for name, az in dirs.items():
    # glTF import keeps Blender -Y as the model front (export_yup round trip)
    r = math.radians(az)
    loc = tgt + Vector((math.sin(r), -math.cos(r), 0.12)) * 6
    cam = bpy.data.objects.new('c', bpy.data.cameras.new('c')); sc.collection.objects.link(cam)
    cam.data.type = 'ORTHO'; cam.data.ortho_scale = OH
    cam.location = loc; cam.rotation_euler = (tgt - loc).to_track_quat('-Z', 'Y').to_euler()
    sc.camera = cam
    sc.render.filepath = os.path.abspath(f'{out}_{name}.png')
    bpy.ops.render.render(write_still=True)
