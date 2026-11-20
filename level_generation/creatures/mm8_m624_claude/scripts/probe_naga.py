import bpy,bmesh,json,math,sys,numpy as np
from mathutils.bvhtree import BVHTree
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'export/mm8_m624.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];D=json.loads((P/'work/rig.json').read_text());co=np.array([v.co[:]for v in body.data.vertices]);ed=np.array([e.vertices[:]for e in body.data.edges]);rest=np.linalg.norm(co[ed[:,0]]-co[ed[:,1]],axis=1)
hands={}
for sd in D['hands']:
 ids=set(v.index for v in body.data.vertices if any(g.weight>.1 and body.vertex_groups[g.group].name.startswith(sd+'_') and ('Hand' in body.vertex_groups[g.group].name or any(s in body.vertex_groups[g.group].name for s in ['thumb','index','middle','ring','pinky'])) for g in v.groups));hands[sd]=np.array([a in ids and b in ids for a,b in ed])
# Close the open wrist cuts in an isolated 8 mm voxel query proxy, then transfer the original skin weights.
parts=np.array([v.value for v in body.data.attributes['part'].data]);limbs='--limbs'in sys.argv;arm=np.array([sum(g.weight for g in v.groups if body.vertex_groups[g.group].name[:2]in D['hands'])for v in body.data.vertices]);keep=((parts==0)&(arm<.3))if limbs else np.isin(parts,[0,100,101,102]);skinfaces=[list(f.vertices)for f in body.data.polygons if all(keep[i]for i in f.vertices)]
qm=bpy.data.meshes.new('ClosedSkinQuery');qm.from_pydata(co.tolist(),[],skinfaces);proxy=bpy.data.objects.new('ClosedSkinQuery',qm);bpy.context.collection.objects.link(proxy);bpy.ops.object.select_all(action='DESELECT');proxy.select_set(True);bpy.context.view_layer.objects.active=proxy;remesh=proxy.modifiers.new('CloseWristCuts','REMESH');remesh.mode='VOXEL';remesh.voxel_size=.012 if limbs else .008;remesh.use_smooth_shade=True;bpy.ops.object.modifier_apply(modifier=remesh.name)
qm=proxy.data;qm.calc_loop_triangles();queryfaces=[list(t.vertices)for t in qm.loop_triangles];uses={}
for f in queryfaces:
    for a,b in zip(f,f[1:]+f[:1]):key=tuple(sorted((a,b)));uses[key]=uses.get(key,0)+1
assert all(n==2 for n in uses.values()),'Query proxy must be a closed skin'
body.data.calc_loop_triangles();faces=[list(t.vertices)for t in body.data.loop_triangles];resttree=BVHTree.FromPolygons([Vector(v)for v in co],faces,all_triangles=True);W=np.zeros((len(co),len(body.vertex_groups)))
for v in body.data.vertices:
    for g in v.groups:W[v.index,g.group]=g.weight
for g in body.vertex_groups:proxy.vertex_groups.new(name=g.name)
for v in qm.vertices:
    loc,n,fi,dist=resttree.find_nearest(v.co);ids=faces[fi];xyz=co[ids];bary=np.linalg.lstsq(np.column_stack([xyz[1]-xyz[0],xyz[2]-xyz[0]]),np.array(loc)-xyz[0],rcond=None)[0];bary=np.clip(bary,0,1)
    if bary.sum()>1:bary/=bary.sum()
    w=W[ids[0]]*(1-bary.sum())+W[ids[1]]*bary[0]+W[ids[2]]*bary[1]
    for i in np.where(w>.00001)[0]:proxy.vertex_groups[int(i)].add([v.index],float(w[i]),'REPLACE')
mod=proxy.modifiers.new('QuerySkin','ARMATURE');mod.object=rig;proxy.parent=rig;proxy.hide_render=True
print('CLOSED_QUERY',len(qm.vertices),'vertices',len(queryfaces),'faces',flush=True)
samples={}
for sd in D['hands']:
 samples[sd]=[v.index for v in body.data.vertices if any(g.weight>.3 and body.vertex_groups[g.group].name.startswith(sd+'_') and 'Shoulder'not in body.vertex_groups[g.group].name and 'UpperArm'not in body.vertex_groups[g.group].name for g in v.groups)][::3]
weaponids={}
for ob in bpy.data.objects:
 if ob.type=='MESH'and ob.name.endswith('_Weapon'):
  sd=ob.name[:2];inv=rig.data.bones[sd+'_Sword'].matrix_local.inverted();weaponids[ob.name]=[v.index for v in ob.data.vertices if (inv@v.co).y>.1]
report_path=P/('work/limb_contacts.json'if limbs else'work/motion_gates.json');report=json.loads(report_path.read_text()) if '--attack-only' in sys.argv else {};sc=bpy.context.scene
for action in list(bpy.data.actions):
 if action.name not in ['Standing','Walk','Running','Fidget','Attack','Cast','Hit','Death','Dead']:continue
 if '--attack-only' in sys.argv and action.name!='Attack':continue
 rig.animation_data.action=action;out={'wrist_swing_deg':{},'hand_stretch_max':{},'weapon_floor':1000,'body_floor':1000,'contacts':{}};prev={};steps={};accels={};pstep={};backs=[]
 for frame in np.arange(action.frame_range[0],action.frame_range[1]+.25,.5):
  sc.frame_set(int(frame),subframe=frame%1);bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get();ev=body.evaluated_get(deps);c=np.array([(ev.matrix_world@v.co)[:]for v in ev.data.vertices]);stretch=np.linalg.norm(c[ed[:,0]]-c[ed[:,1]],axis=1)/np.maximum(rest,1e-5);out['body_floor']=min(out['body_floor'],float(c[:,2].min()))
  qev=proxy.evaluated_get(deps);query=[qev.matrix_world@v.co for v in qev.data.vertices];tree=BVHTree.FromPolygons(query,queryfaces,all_triangles=True)
  def contact(label,points):
   for p in points:
    p=Vector(p);loc,n,idx,dist=tree.find_nearest(p,.06)
    if loc is not None and dist>.006 and (p-loc).dot(n)<-.7*dist:
     if dist>out['contacts'].get(label,{}).get('depth_m',0):out['contacts'][label]={'depth_m':dist,'frame':float(frame)}
  if limbs:
   for sd,ids in samples.items():contact(sd+'_limb',c[ids])
  for sd,hand in D['hands'].items():
   pb=rig.pose.bones[sd+'_Hand'];delta=pb.matrix.to_3x3()@rig.data.bones[pb.name].matrix_local.to_3x3().inverted();fwd=delta@Vector(hand['forward']);fore=rig.pose.bones[sd+'_Forearm'];angle=math.degrees(fwd.angle(fore.tail-fore.head));out['wrist_swing_deg'][sd]=max(out['wrist_swing_deg'].get(sd,0),angle);out['hand_stretch_max'][sd]=max(out['hand_stretch_max'].get(sd,0),float(stretch[hands[sd]].max()))
  for ob in bpy.data.objects:
   if ob.type=='MESH' and ob.name.endswith('_Weapon'):
    ev=ob.evaluated_get(deps);contact(ob.name,[(ev.matrix_world@ev.data.vertices[i].co)for i in weaponids[ob.name]]);out['weapon_floor']=min(out['weapon_floor'],min((ev.matrix_world@v.co).z for v in ev.data.vertices))
  for pb in rig.pose.bones:
   q=pb.matrix.to_quaternion()
   if pb.name in prev:
    step=math.degrees(q.rotation_difference(prev[pb.name]).angle);step=min(step,360-step);steps[pb.name]=max(steps.get(pb.name,0),step)
    if pb.name in pstep:accels[pb.name]=max(accels.get(pb.name,0),abs(step-pstep[pb.name]))
    pstep[pb.name]=step
   prev[pb.name]=q
 out['max_rotation_step_deg_48fps']=sorted(steps.items(),key=lambda x:-x[1])[:6];out['max_rotation_second_difference_deg']=sorted(accels.items(),key=lambda x:-x[1])[:6];report[action.name]=out;print(action.name,json.dumps(out),flush=True)
(P/('work/limb_contacts.json'if limbs else'work/motion_gates.json')).write_text(json.dumps(report,indent=2))

assert all(not v['contacts']for v in report.values()),'Body contact detected'
assert all(max(v['hand_stretch_max'].values())<4.5 and max(v['wrist_swing_deg'].values())<60 and v['body_floor']>-.015 for v in report.values())
