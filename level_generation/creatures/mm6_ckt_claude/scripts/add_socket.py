"""Add Socket_Head (empty on the Head bone, just behind the beak tip) to work/anim_v1.blend: the cast glow focus."""
import bpy
from mathutils import Matrix, Vector
rig = bpy.data.objects['Ckt_Rig']
for o in [o for o in bpy.data.objects if o.name == 'Socket_Head']:
    bpy.data.objects.remove(o, do_unlink=True)
bone = rig.data.bones['Head']
at = rig.matrix_world @ (bone.head_local.lerp(bone.tail_local, 0.6) + Vector((0, 0, 0.02)))
sock = bpy.data.objects.new('Socket_Head', None); bpy.context.scene.collection.objects.link(sock)
sock.parent = rig; sock.parent_type = 'BONE'; sock.parent_bone = 'Head'
sock.matrix_world = Matrix.Translation(at); sock.empty_display_size = 0.02
bpy.ops.wm.save_mainfile()
print('SOCKET', tuple(round(x, 3) for x in at))
