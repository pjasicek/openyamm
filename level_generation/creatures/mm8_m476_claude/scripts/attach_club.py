"""Fit the Meshy skull club to the measured left-hand grip; preserve its texture UVs."""
import bpy,sys,json
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(globals().get('SOURCE_BLEND',p/'work/rig_v5.blend')))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis.identity()
G=json.loads((p/'work/grip_pose.json').read_text());Hm=rig.data.bones['B_L_Hand'].matrix_local
c=Hm@Vector(G['handle_centre_hand_local']);axis=(Hm.to_3x3()@Vector(G['handle_axis_hand_local'])).normalized()
a=bpy.data.actions['Standing'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];bpy.context.scene.frame_set(0)
Hp=rig.pose.bones['B_L_Hand'].matrix
# Horns upright in the carry; rest basis is transformed back with the hand.
posed_ax=(Hp.to_3x3()@Vector(G['handle_axis_hand_local'])).normalized();up=Vector((0,0,1));up=(up-posed_ax*up.dot(posed_ax)).normalized()
restup=(Hm.to_3x3()@Hp.to_3x3().inverted()@up).normalized();Y=restup.cross(axis).normalized();Z=axis.cross(Y).normalized()
M=Matrix((axis,Y,Z)).transposed().to_4x4();M.translation=c
rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis.identity()
before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(p/'meshy/club_geometry_v1/model_urls_glb.glb'))
parts=[o for o in set(bpy.data.objects)-before if o.type=='MESH']
for o in bpy.data.objects:o.select_set(o in parts)
bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();club=bpy.context.object
bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
co=np.array([tuple(v.co) for v in club.data.vertices]);handle=co[(co[:,0]>-.43)&(co[:,0]<-.27)]
center=np.array([-.36, float(np.median(handle[:,1])),float(np.median(handle[:,2]))]);rad=np.quantile(np.linalg.norm(handle[:,1:]-center[1:],axis=1),.85)*.72
for v in club.data.vertices:
 q=np.array(v.co)-center;q*=.72
 # Leather grip fits the palm, blending back into the unchanged shaft/head.
 influence=float(np.clip((-.18-float(v.co.x))/.08,0,1));q[1:]*=1+influence*(.0175/rad-1)
 v.co=M@Vector(q)
club.name=club.data.name='SkullClub';club.matrix_world=Matrix()
for o in bpy.data.objects:o.select_set(o==rig)
bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT')
b=rig.data.edit_bones.new('Club');b.head=c;b.tail=c+axis*.15;b.parent=rig.data.edit_bones['B_L_Hand'];b.align_roll(Z)
bpy.ops.object.mode_set(mode='OBJECT')
club.vertex_groups.clear();club.vertex_groups.new(name='Club').add(list(range(len(club.data.vertices))),1.,'REPLACE')
m=club.modifiers.new('Armature','ARMATURE');m.object=rig
club.parent=rig
report={'length_m':.72,'raw_handle_radius_at_scale':float(rad),'fitted_radius_m':.0175,'bone':'Club','hand':'B_L_Hand','tris':len(club.data.polygons)}
(p/'work/club_fit.json').write_text(json.dumps(report,indent=2));print('CLUBFIT',report)
bpy.ops.wm.save_as_mainfile(filepath=str(globals().get('OUTPUT_BLEND',p/'work/rig_club.blend')))
