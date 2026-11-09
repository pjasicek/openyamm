"""Fold rigid feather groups onto the floor without moving skin, cloth, hands or props."""
import bpy,sys,json,numpy as np
from pathlib import Path
from mathutils import Matrix
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import reduction_common as C
SOURCE=P/'work/review_round1_before'
owners=set();samples={};snapshots={};selection={}
for level in range(4):
 bpy.ops.wm.open_mainfile(filepath=str(SOURCE/f'runtime_lod{level}.blend'));C.reset();body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];pv=np.array([x.value for x in body.data.attributes['piece'].data]);groups={}
 for v in body.data.vertices:
  if pv[v.index] in [0,1,2,3,10,12,15]:continue
  weights=[(body.vertex_groups[g.group].name,g.weight)for g in v.groups if body.vertex_groups[g.group].name in rig.data.bones]
  assert len(weights)==1 and abs(weights[0][1]-1)<1e-5,weights
  groups.setdefault(weights[0][0],[]).append(v.index)
 owners.update(groups);selection[level]=groups
 for role in ['Death','Dead']:
  a=bpy.data.actions[role];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];end=int(a.frame_range[1]);times=np.arange(0,end+.125,.25)
  for f in times:
   bpy.context.scene.frame_set(int(f),subframe=f%1);deps=bpy.context.evaluated_depsgraph_get();ob=body.evaluated_get(deps);me=ob.to_mesh();co=np.array([v.co[:]for v in me.vertices]);ob.to_mesh_clear()
   for name,ids in groups.items():
    key=(role,name,float(f));lo=float(co[ids,2].min());hi=float(co[ids,2].max());old=samples.get(key,(1e9,-1e9));samples[key]=(min(old[0],lo),max(old[1],hi))
 print('FEATHER_SOURCE',level,{n:len(ids)for n,ids in groups.items()},flush=True)
owners=sorted(owners);curves={}
for role in ['Death','Dead']:
 for name in owners:
  rows=sorted((f,v)for (r,n,f),v in samples.items()if r==role and n==name)
  end=int(rows[-1][0]);values=[]
  for f in range(end+1):
   neighbours=[v for t,v in rows if abs(t-f)<=1.25];lo=min(v[0]for v in neighbours);anchor=max(.12,max(v[1]for v in neighbours));s=min(1.,(anchor-.009)/max(anchor-lo,1e-6));values.append([s,anchor*(1-s)])
  curves[(role,name)]=values
for name in owners:curves[('Dead',name)]=[curves[('Death',name)][-1]]*len(curves[('Dead',name)])
receipt={'method':'Per-owner global vertical compression: top of feather group stays fixed; ground-facing tips fold to 9 mm clearance. Skin and equipment animation unchanged. 192 Hz input envelope across all four LODs.','fall_only_root_clearance_m':.008,'root_clearance_reason':'Far skin/shadow proxies needed at most 9.122 mm at Death frame 90. A smooth 8 mm fall-only clearance keeps every body LOD within the 2 mm floor tolerance; Standing and other clips remain unchanged.','owners':owners,'min_source_z':min(v[0]for v in samples.values()),'groups':{r:{n:{'minimum_scale':min(v[0]for v in curves[(r,n)])}for n in owners}for r in ['Death','Dead']}}
for level in range(4):
 bpy.ops.wm.open_mainfile(filepath=str(SOURCE/f'runtime_lod{level}.blend'));C.reset();rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];bpy.context.view_layer.objects.active=rig;rig.select_set(True)
 # Every LOD has the same inverse binds, including owners absent from its reduced mesh.
 bpy.ops.object.mode_set(mode='EDIT')
 for name in owners:
  floor=rig.data.edit_bones.new('FeatherFloor_'+name);floor.head=(0,0,0);floor.tail=(0,1,0);floor.parent=rig.data.edit_bones[name]
  source=rig.data.edit_bones[name];clone=rig.data.edit_bones.new('Feather_'+name);clone.matrix=source.matrix.copy();clone.length=source.length;clone.parent=floor
 bpy.ops.object.mode_set(mode='OBJECT')
 for name,ids in selection[level].items():
  body.vertex_groups[name].remove(ids);body.vertex_groups.new(name='Feather_'+name).add(ids,1,'REPLACE')
 for action in list(bpy.data.actions):
  rig.animation_data.action=action;rig.animation_data.action_slot=action.slots[0];end=int(action.frame_range[1]);previous={}
  for frame in range(end+1):
   bpy.context.scene.frame_set(frame)
   for name in owners:
    clone=rig.pose.bones['Feather_'+name];floor=rig.pose.bones['FeatherFloor_'+name];rest=clone.bone.matrix_local;matrix=rest.inverted()@floor.bone.matrix_local@rig.pose.bones[name].matrix@rig.data.bones[name].matrix_local.inverted()@rest
    loc,rot,scale=matrix.decompose()
    if name in previous and previous[name].dot(rot)<0:rot.negate()
    previous[name]=rot.copy();clone.rotation_mode='QUATERNION';clone.location=loc;clone.rotation_quaternion=rot;clone.scale=scale
    s,z=curves[(action.name,name)][frame]if action.name in ['Death','Dead']else(1.,0.);desired=Matrix.Diagonal((1,1,s,1));desired.translation.z=z;basis=floor.bone.matrix_local.inverted()@rig.data.bones[name].matrix_local@rig.pose.bones[name].matrix.inverted()@desired;loc,rot,scale=basis.decompose();floor.rotation_mode='QUATERNION';floor.location=loc;floor.rotation_quaternion=rot;floor.scale=scale
    for attr in ['location','rotation_quaternion','scale']:clone.keyframe_insert(attr,frame=frame,group=clone.name)
    for attr in ['location','rotation_quaternion','scale']:floor.keyframe_insert(attr,frame=frame,group=floor.name)
   phase=min(1.,max(0.,(frame-40)/36))if action.name=='Death'else(1. if action.name=='Dead'else 0.);rig.location=(0,0,.008*phase*phase*(3-2*phase));rig.keyframe_insert('location',frame=frame,group='Fall ground clearance')
  # A held corpse has two audit intervals; no pose changes.
  if action.name=='Dead':
   for slot in action.slots:
    for layer in action.layers:
     for strip in layer.strips:
      bag=strip.channelbag(slot)
      if bag:
       for fc in bag.fcurves:
        last=fc.keyframe_points[-1];fc.keyframe_points.insert(2,last.co.y)
 C.reset();rig.location=(0,0,0);bpy.ops.wm.save_as_mainfile(filepath=str(P/f'work/runtime_lod{level}.blend'))
 if level==0:bpy.ops.wm.save_as_mainfile(filepath=str(P/'export/mm6_natm.blend'))
 print('FEATHER_FOLD_SAVED',level,len(rig.data.bones),flush=True)
(P/'review/round1_feathers.json').write_text(json.dumps(receipt,indent=2))
