import bpy,json
from pathlib import Path
from mathutils import Vector,Matrix
P=Path(__file__).resolve().parents[1]
def build(rig):
 G=json.loads((P/'work/grip_pose.json').read_text());M=Matrix(json.loads((P/'work/axe_attachment.json').read_text())['hand_local_matrix']);Hm=rig.data.bones['B_R_Hand'].matrix_local;c=Vector(G['handle_centre_hand_local']);ax=Vector(G['handle_axis_hand_local'])
 rig.animation_data.action=None
 for pb in rig.pose.bones:pb.matrix_basis.identity()
 bpy.context.view_layer.update()
 with bpy.data.libraries.load(str(P/'work/axe_clay.blend'),link=False)as(src,dst):dst.objects=['Axe']
 ob=dst.objects[0];bpy.context.collection.objects.link(ob);ob.data.transform(Hm@M);ob.matrix_world=Matrix.Identity(4)
 for o in bpy.data.objects:o.select_set(o==rig)
 bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT');b=rig.data.edit_bones.get('Axe')or rig.data.edit_bones.new('Axe');b.head=Hm@c;b.tail=b.head+(Hm.to_3x3()@ax)*.1;b.parent=rig.data.edit_bones['B_R_Hand'];bpy.ops.object.mode_set(mode='OBJECT')
 ob.vertex_groups.new(name='Axe').add(list(range(len(ob.data.vertices))),1,'REPLACE');mod=ob.modifiers.new('Rig','ARMATURE');mod.object=rig;ob.parent=rig;return ob
