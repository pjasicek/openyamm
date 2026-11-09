"""Place the reference cutlass on a calibrated Sword bone, preserving the body master."""
import bpy,sys,json,math
from pathlib import Path
from mathutils import Vector,Matrix
p=Path(__file__).resolve().parents[1];args=sys.argv[sys.argv.index('--')+1:];src,out=args
bpy.ops.wm.open_mainfile(filepath=src);rig=bpy.data.objects['Rig'];rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis=Matrix()
bpy.context.view_layer.update()
g=json.loads((p/'work/grip_pose.json').read_text());h=rig.data.bones['B_R_Hand'].matrix_local;c=h@Vector(g['handle_centre_hand_local']);axis=(h.to_3x3()@Vector(g['handle_axis_hand_local'])).normalized()
kn=rig.data.bones['B_R_Finger2'].head_local;edge=kn-c;edge=(edge-axis*edge.dot(axis)).normalized()
angle=math.radians(45);edge=(edge*math.cos(angle)+axis.cross(edge)*math.sin(angle)).normalized();flat=edge.cross(axis).normalized();R=Matrix([edge,axis,flat]).transposed();assert abs(R.determinant()-1)<1e-5
bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT');bone=rig.data.edit_bones.new('Sword');bone.head=c;bone.tail=c+axis*.15;bone.align_roll(flat);bone.parent=rig.data.edit_bones['B_R_Hand'];bpy.ops.object.mode_set(mode='OBJECT')
with bpy.data.libraries.load(str(p/'work/cutlass.blend'),link=False) as (_,dst):dst.objects=['CutlassMesh']
o=dst.objects[0];bpy.context.scene.collection.objects.link(o)
for v in o.data.vertices:v.co=c+R@v.co
o.vertex_groups.new(name='Sword').add(list(range(len(o.data.vertices))),1,'REPLACE');m=o.modifiers.new('Armature','ARMATURE');m.object=rig;o.parent=rig
assert (rig.data.bones['Sword'].matrix_local.to_3x3()-R).magnitude<1e-4 if hasattr(R,'magnitude') else True
bpy.ops.wm.save_as_mainfile(filepath=out)
(p/'work/cutlass_mount.json').write_text(json.dumps({'edge_roll_degrees':45,'blade_m':.72,'triangles':len(o.data.polygons),'basis':[list(r) for r in R],'centre':list(c)},indent=2))
