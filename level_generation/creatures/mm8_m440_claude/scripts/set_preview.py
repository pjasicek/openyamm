"""Preview clips of the RPG humanoid set on its own character mesh (about 2.4 m tall); the armature is turned 180
degrees so the character faces -Y like our rigs.
Frames go to <out_dir>/<clip>_<i>.png with frames.json for compose_sheet.py.
Args: -- <set glb> <out_dir> <view> <frames per clip> clip [clip ...]   (clip names without the vendor prefix)"""
import bpy, bmesh, sys, os, json, math
from mathutils import Vector, Matrix
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
a = sys.argv[sys.argv.index('--') + 1:]
glb, out, view, n = a[0], a[1], a[2], int(a[3]); clips = a[4:]
os.makedirs(out, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.abspath(glb))
arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
arm.rotation_mode = 'XYZ'                       # imported as QUATERNION: an Euler edit alone is silently ignored
arm.rotation_euler = (0.0, 0.0, math.pi)
bpy.context.view_layer.update()
for o in bpy.data.objects:
    if o.type == 'MESH' and o.parent is not arm:
        o.hide_render = True                      # a stray icosphere in the set files
# a club-envelope stand-in on the grip derived by grip_from_source.py (handle axis through the finger-curl centres)
GRIP = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'work', 'grip_source.json')
sword = None
if os.path.exists(GRIP):
    g = json.load(open(GRIP))
    c, ax = Vector(g['centre_hand']), Vector(g['axis_hand']).normalized()
    side = ax.orthogonal().normalized(); flat = ax.cross(side)
    hb = arm.pose.bones['B_R_Hand']
    s_world = (W := arm.matrix_world) @ hb.matrix
    k = 1.0 / s_world.to_scale()[0]                  # hand-space units per metre
    smesh = bpy.data.meshes.new('sword'); sbm = bmesh.new()
    for a0, a1, w, t in ((-0.14, 0.20, 0.035, 0.035), (0.20, 0.68, 0.07, 0.07), (0.68, 1.08, 0.12, 0.12)):
        corners = [c + ax * (a * k) + side * (sx * w * k) + flat * (sy * t * k) for a in (a0, a1) for sx in (-1, 1) for sy in (-1, 1)]
        vs = [sbm.verts.new(v) for v in corners]
        for q in ((0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)):
            sbm.faces.new([vs[i] for i in q])
    sbm.to_mesh(smesh); sbm.free()
    sword = bpy.data.objects.new('sword', smesh); bpy.context.scene.collection.objects.link(sword)
scene = bpy.context.scene; common.workbench_clay(scene)
acts = {x.name.split('@')[-1].split('|')[-1]: x for x in bpy.data.actions}
rows = []
for c in clips:
    act = acts.get(c) or next(x for k, x in acts.items() if k.endswith(c))
    arm.animation_data.action = act
    if getattr(act, 'slots', None) is not None and len(act.slots):
        arm.animation_data.action_slot = act.slots[0]
    f0, f1 = act.frame_range
    row = []
    for i in range(n):
        f = f0 + (f1 - f0) * i / max(n - 1, 1)
        scene.frame_set(int(f), subframe=f - int(f))
        if sword is not None:
            sword.matrix_world = arm.matrix_world @ arm.pose.bones['B_R_Hand'].matrix
        p = common.render_views(os.path.join(out, f'{c}_{i}'), 1.4, 4.0, views=(view,), resolution=(240, 320))[0]
        row.append([p, f'{c} {f:.0f}'])
    rows.append(row)
json.dump(rows, open(os.path.join(out, 'frames.json'), 'w'))
print('PREVIEW', len(rows), 'clips')
