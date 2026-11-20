"""User feedback v3: close visible holes and strengthen the three quiet reactions."""
import bpy,bmesh,math,json,sys
import numpy as np
from pathlib import Path
from mathutils import Matrix,Vector,Quaternion
P=Path(__file__).resolve().parents[1];R=P/'review/feedback_v3'
bpy.ops.wm.open_mainfile(filepath=str(R/'before/textured_uv.blend'))
o=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];s=bpy.context.scene
bm=bmesh.new();bm.from_mesh(o.data);bm.verts.ensure_lookup_table();bm.faces.ensure_lookup_table()
pl=bm.verts.layers.int['piece'];hl=bm.faces.layers.int['head'];uvs=list(bm.loops.layers.uv.values());new=[]
# This notch connects to the bodice's larger open boundary, so a whole-boundary fill would cap the neckline.
assert (bm.verts[180].co-Vector((.042826522,-.041888185,1.335582614))).length<1e-6
new.append(bm.faces.new([bm.verts[i] for i in (180,699,934)]))
edges={e for e in bm.edges if e.is_boundary}
while edges:
 e=edges.pop();todo=[e];es={e};vs=set(e.verts)
 while todo:
  e=todo.pop()
  for v in e.verts:
   for x in v.link_edges:
    if x in edges:edges.remove(x);es.add(x);vs.update(x.verts);todo.append(x)
 parts={v[pl] for v in vs}
 if len(es)<10:print('SMALL HOLE',parts,len(es),[list(v.co) for v in vs])
 if (parts=={20} and len(es)==5) or (parts=={11} and len(es)==4):
  before=set(bm.faces);edge=next(iter(es));ordered=list(edge.verts);remaining=es-{edge}
  while remaining:
   edge=next(e for e in remaining if ordered[-1] in e.verts);remaining.remove(edge);v=edge.other_vert(ordered[-1])
   if v!=ordered[0]:ordered.append(v)
  fs=[bm.faces.new(ordered)];bmesh.ops.triangulate(bm,faces=fs);new.extend(set(bm.faces)-before)
assert len(new)==6,len(new)
for f in new:
 f.smooth=True;f[hl]=int(f.verts[0][pl]!=0)
 for l in f.loops:
  for uv in uvs:
   near=[x for x in l.vert.link_loops if x.face not in new]
   assert near
   l[uv].uv=near[0][uv].uv
bm.normal_update()
for f in new:
 adjacent={x for e in f.edges for x in e.link_faces if x not in new}
 normal=sum((x.normal for x in adjacent),Vector())
 if f.normal.dot(normal)<0:f.normal_flip()
bm.to_mesh(o.data);bm.free();o.data.update()
def use(name,frame=0):
 rig.animation_data.action=None
 for b in rig.pose.bones:b.matrix_basis=Matrix()
 a=bpy.data.actions[name];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0]
 s.frame_set(int(frame),subframe=frame%1);bpy.context.view_layer.update();return a
def pose():return {b.name:(b.location.copy(),b.rotation_quaternion.copy()) for b in rig.pose.bones}
use('Standing');stand=pose()
def rotate(row,name,axis,degrees):
 loc,q=row[name];axis=rig.data.bones[name].matrix_local.to_3x3().inverted()@Vector(axis)
 row[name]=(loc,q@Quaternion(axis,math.radians(degrees)))
def write(name,rows):
 rig.animation_data.action=None;bpy.data.actions.remove(bpy.data.actions[name]);a=bpy.data.actions.new(name);a.use_fake_user=True;rig.animation_data.action=a
 for f,row in enumerate(rows):
  for n,(loc,q) in row.items():
   b=rig.pose.bones[n];b.rotation_mode='QUATERNION';b.location=loc;b.rotation_quaternion=q
   b.keyframe_insert('rotation_quaternion',frame=f);b.keyframe_insert('location',frame=f)
 a.use_frame_range=True;a.frame_start=0;a.frame_end=len(rows)-1
 return a
rows=[]
for f in range(121):
 use('Standing',f);row=pose();t=f/120;wave=math.sin(2*math.pi*t);breath=math.sin(math.pi*t)**2
 for n in ('B_Spine','B_Spine1','B_Spine2','B_Neck','B_Head','B_L_Clavicle','B_R_Clavicle','B_L_UpperArm','B_R_UpperArm'):
  loc,q=row[n];dq=stand[n][1].rotation_difference(q)
  if dq.w<0:dq.negate()
  row[n]=(loc,stand[n][1]@Quaternion(dq.axis,dq.angle*1.8))
 rotate(row,'B_Spine1',(0,1,0),.7*wave);rotate(row,'B_Head',(0,0,1),2.2*wave)
 for side,sign in [('L',1),('R',-1)]:rotate(row,f'B_{side}_UpperArm',(1,0,0),sign*1.4*wave)
 rows.append(row)
write('Standing',rows)
rows=[]
for f in range(46):
 use('Fidget',f);row=pose();t=f/45;env=math.sin(math.pi*t)**2;wave=math.sin(2*math.pi*t)*env
 rotate(row,'B_Head',(0,0,1),-6*wave);rotate(row,'B_Head',(0,1,0),3*env)
 rotate(row,'B_Spine1',(0,0,1),3*wave);rotate(row,'B_R_UpperArm',(1,0,0),-7*env)
 rotate(row,'B_R_Forearm',(1,0,0),-7*env);rotate(row,'B_L_Clavicle',(0,1,0),2.5*env)
 rows.append(row)
write('Fidget',rows)
with bpy.data.libraries.load(str(P/'work/hit_library_trials.blend')) as (d,out):out.actions=['TrialF2']
trial=out.actions[0];upper=[n for n in rig.pose.bones.keys() if n in json.loads(s['rig_offsets']) and not any(x in n for x in ('Pelvis','Thigh','Calf','Foot','Toe'))]
rows=[]
for f in range(46):
 sf=float(np.interp(f,[0,8,21,45],[0,4,8,15]));use(trial.name,sf);source=pose();row={n:(l.copy(),q.copy()) for n,(l,q) in stand.items()}
 fade=min(1,f/6,(45-f)/9);fade=fade*fade*(3-2*fade)
 for n in upper:row[n]=(row[n][0],row[n][1].slerp(source[n][1],fade))
 rows.append(row)
write('Hit',rows);bpy.data.actions.remove(trial)
# Re-bake the existing twist helpers for the changed arm motion; leave all weights and other clips alone.
for name in ['Standing','Fidget','Hit']:
 a=use(name)
 for f in range(int(a.frame_range[1])+1):
  s.frame_set(f)
  for side in 'LR':
   for base,child,helper,factor in [('Forearm','Hand','ForearmTwist',.6),('UpperArm','Forearm','UpperArmTwist',-.5)]:
    b=rig.data.bones[f'B_{side}_{base}'];c=rig.data.bones[f'B_{side}_{child}'];axis=(b.matrix_local.inverted()@c.head_local).normalized()
    if base=='Forearm':
     rel=(rig.pose.bones[b.name].matrix.inverted()@rig.pose.bones[c.name].matrix).to_quaternion();rest=(b.matrix_local.inverted()@c.matrix_local).to_quaternion();q=rel@rest.inverted()
    else:q=rig.pose.bones[b.name].rotation_quaternion
    angle=(2*math.atan2(Vector((q.x,q.y,q.z)).dot(axis),q.w)+math.pi)%(2*math.pi)-math.pi
    pb=rig.pose.bones[f'B_{side}_{helper}'];pb.rotation_quaternion=Quaternion(axis,angle*factor);pb.keyframe_insert('rotation_quaternion',frame=f)
for a in bpy.data.actions:
 for l in a.layers:
  for st in l.strips:
   for bag in st.channelbags:
    for fc in bag.fcurves:
     for k in fc.keyframe_points:k.interpolation='LINEAR'
use('Standing');s.render.fps=60
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/feedback_motion.blend'))
(R/'motion_geometry.json').write_text(json.dumps({'added_faces':6,'triangles':len(o.data.polygons),'hit_source':'anim_library/humanoid_set/Unarmed.glb:UnarmedGetHitF2','hit_adaptation':'Planted relaxed stance, upper-body library recoil with relaxed entry/recovery; 0.75 seconds','standing':'1.8x original upper-body breathing plus slight head/arm sway','fidget':'Larger head turn and small shoulder/arm adjustment; original 0.75-second timing'},indent=2))
sys.path.insert(0,str(P/'scripts'));import common
common.workbench_clay(s);s.display.shading.color_type='SINGLE';s.display.shading.single_color=(.6,.6,.6)
common.render_views(str(R/'repaired_face'),1.45,.6,views=('front',),resolution=(900,900))
