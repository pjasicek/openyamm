"""Assemble a Noble variant for review and export: work/carapace_skinned.blend (body, rig, skinned carapace) + the clip
set's actions (work/clips_<set>.blend) + its weapons (scripts/weapons.json mounts, clips_lib.mount_matrix; a mount may name another weapon's `mesh`; each weapon's mesh placed at its
socket in the rest pose, in armature space, 100 % on the socket bone, so split_attachments turns it into the socket's
attachment) -> work/assembly_<out>.blend.
Args: -- <clip set[,clip set...]> <out> <weapon> [<weapon> ...]"""
import bpy, sys, os, json, math
from pathlib import Path
from mathutils import Matrix, Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import clips_lib as cl
P = Path(__file__).resolve().parents[1]
a = sys.argv[sys.argv.index('--') + 1:]
clipset, out, weapons = a[0], a[1], a[2:]
bpy.ops.wm.open_mainfile(filepath=str(P / 'work' / 'carapace_skinned.blend'))
rig = bpy.data.objects['Rig']; scene = bpy.context.scene
for act in [x for x in bpy.data.actions]:
    bpy.data.actions.remove(act)
for cs in clipset.split(','):                              # one or more clip sets (comma separated)
    with bpy.data.libraries.load(str(P / 'work' / f'clips_{cs}.blend'), link=False) as (src, dst):
        dst.actions = [n for n in src.actions if n.startswith(cs.capitalize() + '_')]
for act in bpy.data.actions: act.use_fake_user = True
MOUNTS = json.loads((P / 'scripts' / 'weapons.json').read_text())
# release sockets at weapon points (bones on the weapon's socket, armature-aligned frames)
rel = {n: (MOUNTS[w]['socket'], cl.mount_matrix(MOUNTS[w]) @ Vector(pt)) for w in weapons for n, pt in MOUNTS[w].get('release', {}).items()}
if rel:
    bpy.context.view_layer.objects.active = rig; bpy.ops.object.mode_set(mode='EDIT'); eb = rig.data.edit_bones
    for n, (sock, p) in rel.items():
        if n in eb: eb.remove(eb[n])
        b = eb.new(n); b.head = (0, 0, 0); b.tail = (0, 0.05, 0)
        b.matrix = Matrix.Translation(eb[sock].matrix @ p); b.parent = eb[sock]; b.use_deform = False
    bpy.ops.object.mode_set(mode='OBJECT')
rig.animation_data_create(); rig.animation_data.action = None
for pb in rig.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update()
for w in weapons:
    m = MOUNTS[w]
    mesh = m.get('mesh', w)
    with bpy.data.libraries.load(str(P / 'work' / 'weapons' / f'{mesh}.blend'), link=False) as (src, dst):
        dst.objects = ['W_' + mesh]
    ob = dst.objects[0]; scene.collection.objects.link(ob); ob.name = 'W_' + w
    if mesh != w:
        ob.data = ob.data.copy()
    MM = cl.mount_matrix(m)
    M = rig.matrix_world @ rig.data.bones[m['socket']].matrix_local @ MM
    ob.data.transform(rig.matrix_world.inverted() @ M); ob.matrix_world = rig.matrix_world
    if MM.to_3x3().determinant() < 0:
        ob.data.flip_normals()                                       # a mirrored (left-hand) copy
    ob.parent = rig; ob.matrix_parent_inverse = Matrix.Identity(4)
    for g in list(ob.vertex_groups): ob.vertex_groups.remove(g)
    ob.vertex_groups.new(name=m['socket']).add(list(range(len(ob.data.vertices))), 1.0, 'REPLACE')
    md = ob.modifiers.new('Armature', 'ARMATURE'); md.object = rig
    ob['socket'] = m['socket']
    print('WEAPON', w, m['socket'])
for o in bpy.data.objects:                                       # a weapon loaded twice shares its first material
    if o.type == 'MESH':
        for i, m in enumerate(o.data.materials):
            if m and '.' in m.name and m.name.rsplit('.', 1)[1].isdigit() and m.name.rsplit('.', 1)[0] in bpy.data.materials \
                    and not m.name.startswith('NB_WeaponGlow'):
                o.data.materials[i] = bpy.data.materials[m.name.rsplit('.', 1)[0]]
for o in [o for o in bpy.data.objects if o.type == 'MESH' and 'socket' in o.keys()]:   # each weapon its own glow material
    for i, m in enumerate(o.data.materials):                                             # (the split selects by material)
        if m and m.name.startswith('NB_WeaponGlow'):
            g = m.copy(); g.name = 'NB_WeaponGlow_' + o.name[2:]; o.data.materials[i] = g
scene.render.fps = 48
bpy.ops.wm.save_as_mainfile(filepath=str(P / 'work' / f'assembly_{out}.blend'))
print('ASSEMBLED', out, [x.name for x in bpy.data.actions]); sys.stdout.flush(); os._exit(0)
