"""Replace the FX socket empties of work/anim_base.blend with non-deform bones (exported as glTF nodes, as the
guardian's): Socket_Mouth on Head, Socket_Antenna_L/R at the long antennae's tips. Idempotent; saves anim_base.blend."""
import bpy, os
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
path = os.path.join(HERE, 'work', 'anim_base.blend')
bpy.ops.wm.open_mainfile(filepath=path)
rig = bpy.data.objects['Pede_Rig']
socks = {}
for o in list(bpy.data.objects):
    if o.name.startswith('Socket_') and o.type == 'EMPTY':
        socks[o.name] = (o.matrix_world.translation.copy(), o.parent_bone)
        bpy.data.objects.remove(o, do_unlink=True)
if not socks:
    print('SOCKETS already bones', [b.name for b in rig.data.bones if b.name.startswith('Socket_')])
else:
    bpy.context.view_layer.objects.active = rig
    for o in bpy.data.objects: o.select_set(o == rig)
    bpy.ops.object.mode_set(mode='EDIT')
    eb = rig.data.edit_bones
    for name, (p, parent) in socks.items():
        b = eb.new(name); b.head = p; b.tail = p + Vector((0, -0.03, 0)); b.parent = eb[parent]; b.use_deform = False
    bpy.ops.object.mode_set(mode='OBJECT')
    print('SOCKETS', {k: ([round(x, 3) for x in v[0]], v[1]) for k, v in socks.items()})
    bpy.ops.wm.save_as_mainfile(filepath=path)
