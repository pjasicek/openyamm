import bpy,json,math,traceback
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.kdtree import KDTree
ROOT=Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_goblin/meshy_restart_20260923');OUT=ROOT/'rig_review_01';s=bpy.data.scenes['Goblin - Centered Rig and Retarget'];bpy.context.window.scene=s;arm=s.objects['Goblin_Centered_Rig'];old=s.objects['Goblin_CenteredRig_Mesh']
with bpy.data.libraries.load(str(ROOT/'meshy_rig_test_01/meshy_upload.blend'),link=False) as (a,b):b.scenes=[a.scenes[0]]
ref=b.scenes[0];orig=next(o for o in ref.objects if o.type=='MESH');mesh=orig.copy();mesh.data=orig.data.copy();mesh.name='Goblin_FinalRig_10577';s.collection.objects.link(mesh)
coords=[orig.matrix_world@v.co for v in orig.data.vertices];zmin=min(v.z for v in coords);zmax=max(v.z for v in coords);scale=1.7/(zmax-zmin);mesh.matrix_world=Matrix.Translation((0,0,-zmin*scale))@Matrix.Diagonal((scale,scale,scale,1))@orig.matrix_world
mesh.vertex_groups.clear()
for g in old.vertex_groups:mesh.vertex_groups.new(name=g.name)
kd=KDTree(len(old.data.vertices))
for v in old.data.vertices:kd.insert(old.matrix_world@v.co,v.index)
kd.balance();errors=[]
for v in mesh.data.vertices:
 _,i,d=kd.find(mesh.matrix_world@v.co);errors.append(d)
 for g in old.data.vertices[i].groups:mesh.vertex_groups[g.group].add([v.index],g.weight,'REPLACE')
mat=mesh.matrix_world.copy();mesh.parent=arm;mesh.matrix_world=mat;mod=mesh.modifiers.new('Corrected goblin skin','ARMATURE');mod.object=arm
old.hide_render=True;old.hide_set(True)
uv=mesh.data.uv_layers.active.data;garment=set()
for p in mesh.data.polygons:
 if any(uv[i].uv.x>.49999 or uv[i].uv.y>.49999 for i in p.loop_indices):garment.update(p.vertices)
changes={}
def setw(v,w,tag):
 for g in list(v.groups):mesh.vertex_groups[g.group].remove([v.index])
 total=sum(w.values())
 for name,value in w.items():
  if value>1e-6:mesh.vertex_groups['mixamorig:'+name].add([v.index],value/total,'REPLACE')
 changes[tag]=changes.get(tag,0)+1
for v in mesh.data.vertices:
 p=mesh.matrix_world@v.co;x,y,z=p;side='Left' if x>0 else 'Right'
 if v.index in garment:
  t=min(.35,max(0,(.973-z)/.24*.35)) if z<.973 else 0;setw(v,{'Hips':1-t,side+'UpLeg':t},'all_garment_surfaces')
 elif abs(x)<.18 and .972<z<1.115:
  t=max(0,min(1,(z-1.055)/.060));setw(v,{'Hips':1-t,'Spine':t},'covered_waist')
 elif abs(x)>.18 and z>1.52-abs(x) and z>1.19:
  setw(v,{side+'Arm':1},'shoulder_cap_and_upper_arm')
 elif abs(x)>.30 and .85<z<1.2:
  elbow=arm.data.bones['mixamorig:'+side+'ForeArm'].head_local;wrist=arm.data.bones['mixamorig:'+side+'Hand'].head_local;axis=wrist-elbow;t=(p-elbow).dot(axis)/axis.length_squared;dist=(p-(elbow+axis*t)).length
  if dist<.12 and t>.22:
   w=max(0,min(1,(t-.90)/.18));setw(v,{side+'ForeArm':1-w,side+'Hand':w},'bracer_wrist_transition')
# Match coincident UV-split vertices exactly to avoid skin cracks at seams.
by_pos={}
for v in mesh.data.vertices:by_pos.setdefault(tuple(round(c,5) for c in v.co),[]).append(v)
for verts in by_pos.values():
 if len(verts)<2:continue
 weights={}
 for v in verts:
  for g in v.groups:weights[g.group]=weights.get(g.group,0)+g.weight/len(verts)
 weights=dict(sorted(weights.items(),key=lambda a:-a[1])[:4]);total=sum(weights.values())
 for v in verts:
  for g in list(v.groups):mesh.vertex_groups[g.group].remove([v.index])
  for i,w in weights.items():mesh.vertex_groups[i].add([v.index],w/total,'REPLACE')
report={'restored_triangles':sum(len(p.vertices)-2 for p in mesh.data.polygons),'meshy_return_triangles':sum(len(p.vertices)-2 for p in old.data.polygons),'nearest_weight_transfer_max_distance':max(errors),'nearest_weight_transfer_mean_distance':sum(errors)/len(errors),'vertices_over_1mm':sum(d>.001 for d in errors),'changes':changes};(OUT/'geometry_restore_report.json').write_text(json.dumps(report,indent=2));assert report['restored_triangles']==10577
jobs=[]
for key in ['Idle_3','Walking','Right_Hand_Sword_Slash']:
 a=bpy.data.actions['Goblin_Fixed_'+key]
 for t in [.25,.6]:jobs.append((key+'_'+str(t),a,a.frame_range[0]+t*(a.frame_range[1]-a.frame_range[0])))
def step():
 try:
  bpy.context.window.scene=s
  if not jobs:
   bpy.data.libraries.write(str(OUT/'rig_repair_working.blend'),{s},fake_user=True,compress=True);(OUT/'restored_done.txt').write_text('complete');return None
  name,a,f=jobs.pop(0);arm.animation_data.action=a;arm.animation_data.action_slot=a.slots[0];s.frame_set(int(f),subframe=f-int(f));s.render.filepath=str(OUT/('repaired_'+name+'.png'));bpy.ops.render.render(write_still=True);return .1
 except Exception:(OUT/'restored_error.txt').write_text(traceback.format_exc());return None
bpy.app.timers.register(step,first_interval=.1);print(json.dumps(report))
