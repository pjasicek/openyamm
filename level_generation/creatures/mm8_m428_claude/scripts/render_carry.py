"""Textured renders of a runtime body GLB with its dagger attachment GLB on the Dagger node (as the game attaches it),
front and side (her right side, facing image right), at given clip frames (30 fps). Workbench, texture colour.
Args: -- <body glb> <dagger glb> <out prefix> <action>:<frame> [...]"""
import bpy, sys, json, struct
from mathutils import Vector, Matrix, Quaternion
a = sys.argv[sys.argv.index('--') + 1:]
body_glb, dagger_glb, out = a[0], a[1], a[2]
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene; sc.render.fps = 30
bpy.ops.import_scene.gltf(filepath=body_glb)
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
for o in bpy.data.objects:
    if o.type == 'MESH' and ('LOD' in o.name or 'Shadow' in o.name or o.name.startswith('Icosphere')):
        o.hide_render = True
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=dagger_glb)
dag = [o for o in bpy.data.objects if o not in before and o.type == 'MESH']
for o in dag:
    if 'LOD' in o.name or 'Shadow' in o.name: o.hide_render = True
dag = [o for o in dag if not o.hide_render]; local = {o: o.matrix_world.copy() for o in dag}
# The importer re-orients bones (bone heuristic), so the Dagger pose bone frame is not the glTF node frame. The node's
# glTF rest world transform (from the GLB JSON, Y-up converted to Z-up) times the bone's posed deformation places
# the attachment exactly as the engine does.
raw = open(body_glb, 'rb').read(); doc = json.loads(raw[20:20 + struct.unpack_from('<I', raw, 12)[0]])
parent = {c: i for i, n in enumerate(doc['nodes']) for c in n.get('children', [])}
def trs(n):
    t = Matrix.Translation(n.get('translation', [0, 0, 0])); r = n.get('rotation', [0, 0, 0, 1])
    q = Quaternion((r[3], r[0], r[1], r[2])).to_matrix().to_4x4(); sc_ = n.get('scale', [1, 1, 1])
    S = Matrix.Diagonal((sc_[0], sc_[1], sc_[2], 1)); return t @ q @ S
di = next(i for i, n in enumerate(doc['nodes']) if n.get('name') == 'Dagger'); N = Matrix(); i = di
while i is not None:
    N = trs(doc['nodes'][i]) @ N; i = parent.get(i)
C = Matrix.Rotation(1.5707963267948966, 4, 'X'); NREST = C @ N @ C.inverted()
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'TEXTURE'; sh.show_cavity = False
sh.background_type = 'VIEWPORT'; sh.background_color = (0.35, 0.35, 0.35)
sc.render.resolution_x, sc.render.resolution_y = 520, 700
cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.ortho_scale = 1.9
cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
for spec in a[3:]:
    name, f = spec.split(':')
    act = next(x for x in bpy.data.actions if x.name == name or x.name.split('|')[0] == name)
    rig.animation_data_create(); rig.animation_data.action = act
    if len(act.slots): rig.animation_data.action_slot = act.slots[0]
    sc.frame_set(int(act.frame_range[0]) + int(f))
    pb = rig.pose.bones['Dagger']; bpy.context.view_layer.update()
    deform = rig.matrix_world @ pb.matrix @ pb.bone.matrix_local.inverted() @ rig.matrix_world.inverted()
    for o in dag:
        o.matrix_world = deform @ NREST @ local[o]
    for view, d in (('front', Vector((0, -1, 0))), ('side', Vector((-1, 0, 0)))):
        cam.location = Vector((0, 0, 0.92)) + d * 4; cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = f'{out}_{name}{int(f):03d}_{view}.png'; bpy.ops.render.render(write_still=True)
