import bpy,json
from pathlib import Path
s=bpy.data.scenes['Goblin - Meshy Rig Diagnosis'];bpy.context.window.scene=s;arm=next(o for o in s.objects if o.type=='ARMATURE');mesh=max((o for o in s.objects if o.type=='MESH'),key=lambda o:len(o.data.vertices));names={g.index:g.name for g in mesh.vertex_groups}
regions={'head':lambda p:p.z>1.48,'neck':lambda p:1.33<p.z<1.49 and abs(p.x)<.10,'belt':lambda p:1.00<p.z<1.05 and abs(p.x)<.21,'right_hand':lambda p:p.x<-.43 and p.z<.96,'left_shin_armor':lambda p:p.x>.04 and .13<p.z<.47 and p.y<-.025}
report={}
for name,test in regions.items():
 verts=[v for v in mesh.data.vertices if test(mesh.matrix_world@v.co)];total={}
 for v in verts:
  for g in v.groups:total[names[g.group]]=total.get(names[g.group],0)+g.weight
 report[name]={'vertices':len(verts),'mean_weights':{k:round(v/len(verts),4) for k,v in sorted(total.items(),key=lambda p:-p[1])},'max_influences':max([len(v.groups) for v in verts] or [0])}
a=bpy.data.actions['Idle_3'];arm.animation_data.action=a;arm.animation_data.action_slot=a.slots[0];arm.data.pose_position='POSE';s.frame_set(61)
report['idle_bones']=[{'name':b.name,'world_head':list(arm.matrix_world@b.head),'basis_quaternion':list(b.matrix_basis.to_quaternion())} for b in arm.pose.bones if b.name.split(':')[-1] in ['Hips','Spine','Spine1','Spine2','Neck','Head']]
Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_goblin/meshy_restart_20260923/rig_review_01/weights_audit.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
