"""User review 1: attach sleeve roots, belt-carry club, clean skin, library jog, smooth cloth."""
import bpy,bmesh,json,math,shutil,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
P=Path(__file__).resolve().parents[1];W=P/'work/review1';report={}
def curves(a):return [fc for l in a.layers for st in l.strips for cb in st.channelbags for fc in cb.fcurves]
def activate(r,a):
 r.animation_data.action=a
 if a and len(a.slots):r.animation_data.action_slot=a.slots[0]
def frame(f):bpy.context.scene.frame_set(int(f),subframe=float(f%1))
def smooth(x):x=np.clip(x,0,1);return float(x*x*(3-2*x))
bpy.ops.wm.open_mainfile(filepath=str(W/'run_retarget.blend'));r=bpy.data.objects['Rig'];s=bpy.context.scene
src=bpy.data.actions['ReviewRun'];a=bpy.data.actions['Running'];names=[n for n in r.pose.bones.keys() if n in ['B_Spine','B_Spine1','B_Spine2','B_Neck','B_Head'] or any(n==f'B_{sd}_{part}'for sd in 'LR'for part in ['Clavicle','UpperArm','Forearm','Hand'])]
activate(r,src);samples=[]
for f in range(78):
 frame(f);samples.append({n:r.pose.bones[n].rotation_quaternion.copy()for n in names})
# The FBX contains repeated jog strides; identify its cycle before matching the fitted .8-second foot cycle.
scores={period:sum(samples[i][f'B_{sd}_UpperArm'].rotation_difference(samples[i+period][f'B_{sd}_UpperArm']).angle**2 for i in range(78-period)for sd in 'LR')/(78-period) for period in range(18,34)}
period=min(scores,key=scores.get);report['running']={'source':'anim_library/mixamo/Jogging.fbx','source_cycle_frames':period,'duration_s':.8,'stride_m':1.302,'leg_fit':'Retained planted .8s IK stride, replaced all torso and arm source rotations.'}
activate(r,a);prev={}
for f in np.arange(0,24.0001,.25):
 t=float(f/24*period);i=min(int(t),76);w=t-i
 for n in names:
  q=samples[i][n].slerp(samples[i+1][n],w)
  # Match the endpoint to the cycle start without an export seam.
  q=q.slerp(samples[0][n],smooth((f-21)/3)) if f>21 else q
  if n in prev and q.dot(prev[n])<0:q=-q
  b=r.pose.bones[n];b.rotation_quaternion=q;prev[n]=q;b.keyframe_insert('rotation_quaternion',frame=float(f))
 for sd in 'LR':
  hand=r.pose.bones[f'B_{sd}_Hand'].rotation_quaternion;upper=r.pose.bones[f'B_{sd}_UpperArm'].rotation_quaternion
  for part,angle in [('ForearmTwist',.6*2*math.atan2(hand.y,hand.w)),('UpperArmTwist',-.5*2*math.atan2(upper.y,upper.w))]:
   b=r.pose.bones[f'B_{sd}_{part}'];b.rotation_quaternion=Quaternion((0,1,0),angle);b.keyframe_insert('rotation_quaternion',frame=float(f))
bpy.data.actions.remove(src)
# Smooth the entire cloth chain, including translation keys added by earlier per-frame collision corrections.
a=bpy.data.actions['Death'];activate(r,a);fs=np.arange(0,float(a.frame_range[1])+.001,.25);names=[n for n in r.pose.bones.keys()if n.startswith('Cloak_')];poses={n:[]for n in names}
for f in fs:
 frame(f)
 for n in names:
  b=r.pose.bones[n];q=b.rotation_quaternion.copy()
  if poses[n] and q.dot(Quaternion(poses[n][-1][:4]))<0:q=-q
  poses[n].append([*q,*b.location])
for n in names:
 data=np.array(poses[n]);out=[]
 for f in fs:
  w=np.exp(-.5*((fs-f)/3.6)**2);w[abs(fs-f)>10.8]=0;v=w@data/w.sum();v[:4]/=np.linalg.norm(v[:4]);out.append(v)
 for f,v in zip(fs,out):
  b=r.pose.bones[n];b.rotation_quaternion=v[:4];b.location=v[4:];b.keyframe_insert('rotation_quaternion',frame=float(f));b.keyframe_insert('location',frame=float(f))
report['death_cloth']={'smoothed_bones':64,'sigma_s':.12,'samples_hz':120,'channels':['rotation_quaternion','location']}
# Belt socket is expressed in the rest pelvis frame. The grip cap stays against the right belt.
B=r.data.bones['Club'];axis=(B.tail_local-B.head_local).normalized();design=axis.to_track_quat('Z','Y').to_matrix().to_4x4();design.translation=B.head_local;bone_from_design=B.matrix_local.inverted()@design
park=Vector((-.235,.105,.91));q=Vector((-.16,.10,-1)).normalized().to_track_quat('Z','Y');parkM=q.to_matrix().to_4x4();parkM.translation=park;pelrest=r.data.bones['B_Pelvis'].matrix_local
for a in list(bpy.data.actions):
 if a.name not in ['Standing','Walking','Running','Attack','Hit','Death','Dead','Fidget']:continue
 activate(r,a);fs=np.arange(0,float(a.frame_range[1])+.001,.25);held=[]
 for f in fs:
  frame(f);held.append(r.pose.bones['Club'].matrix.copy())
 prev=None
 for f,old in zip(fs,held):
  frame(f);M=r.pose.bones['B_Pelvis'].matrix@pelrest.inverted()@parkM@bone_from_design.inverted()
  if a.name=='Attack':
   w=smooth(f/6)*smooth((float(a.frame_range[1])-f)/7.5)
   Q=M.to_quaternion().slerp(old.to_quaternion(),w);T=M.translation.lerp(old.translation,w);M=Q.to_matrix().to_4x4();M.translation=T
  b=r.pose.bones['Club'];b.matrix=M;q=b.rotation_quaternion.copy()
  if prev and q.dot(prev)<0:q=-q
  prev=q;b.rotation_quaternion=q;b.keyframe_insert('rotation_quaternion',frame=float(f));b.keyframe_insert('location',frame=float(f))
report['club']={'rest_handle_m':list(park),'socket':'Club','parent_motion':'B_Pelvis except drawn Attack','draw_s':.2,'return_s':.25}
# Dead must be the exact smoothed terminal frame, including the belt-mounted prop.
activate(r,bpy.data.actions['Death']);frame(float(r.animation_data.action.frame_range[1]));terminal={b.name:b.matrix_basis.copy()for b in r.pose.bones}
old=bpy.data.actions['Dead'];activate(r,None);bpy.data.actions.remove(old);a=bpy.data.actions.new('Dead');a.use_fake_user=True;activate(r,a)
for b in r.pose.bones:
 for f in [0,30]:
  b.matrix_basis=terminal[b.name]
  for field in ['location','rotation_quaternion','scale']:b.keyframe_insert(field,frame=f)
for a in bpy.data.actions:
 for fc in curves(a):
  for k in fc.keyframe_points:k.interpolation='LINEAR'
activate(r,None)
for b in r.pose.bones:b.matrix_basis.identity()
bpy.ops.wm.save_as_mainfile(filepath=str(W/'motion.blend'))
selection=json.loads((P/'review/reduction/selection.json').read_text());files=[{'blend':'work/reduction_master.blend'}]+selection['body'];report['geometry']=[]
for level,entry in enumerate(files):
 source=W/'reduction_master.blend' if level==0 else P/entry['blend'];backup=W/(source.stem+'_before.blend')
 if not backup.exists():shutil.copyfile(source,backup)
 bpy.ops.wm.open_mainfile(filepath=str(backup));o=bpy.data.objects['Body'];r=bpy.data.objects['Rig'];activate(r,None)
 for b in r.pose.bones:b.matrix_basis.identity()
 for a in list(bpy.data.actions):bpy.data.actions.remove(a)
 with bpy.data.libraries.load(str(W/'motion.blend'),link=False)as(src,dst):dst.actions=['Standing','Walking','Running','Attack','Hit','Death','Dead','Fidget']
 for a in dst.actions:a.use_fake_user=True
 bm=bmesh.new();bm.from_mesh(o.data);part=bm.verts.layers.int['piece'];deform=bm.verts.layers.deform.active;uv=bm.loops.layers.uv.active;before=sum(len(f.verts)-2 for f in bm.faces);added=[]
 torso=[v for v in bm.verts if v[part]==1]
 for sd,pid in [('R',8),('L',9)]:
  edges=[e for e in bm.edges if e.is_boundary and all(v[part]==pid for v in e.verts)];roots={v for e in edges if min(v.co.z for v in e.verts)>1.18 for v in e.verts};assert roots
  # Pin the submerged sleeve root to the same torso skin field. This prevents it travelling with the arm.
  for v in roots:
   near=min(torso,key=lambda t:(t.co-v.co).length_squared);v[deform].clear()
   for gi,w in near[deform].items():v[deform][gi]=w
  # Blend the next ring into the socket, retaining arm motion beyond the shoulder fold.
  outer={q for v in roots for e in v.link_edges if (q:=e.other_vert(v))not in roots}
  for v in outer:
   near=min(torso,key=lambda t:(t.co-v.co).length_squared);old=dict(v[deform]);v[deform].clear()
   for gi,w in old.items():v[deform][gi]=w*.7
   for gi,w in near[deform].items():v[deform][gi]=v[deform].get(gi,0)+w*.3
  # Cap all unintended sleeve openings, including the small right-elbow tear.
  for e in edges:
   if not e.is_valid:continue
  new=bmesh.ops.holes_fill(bm,edges=edges,sides=100)['faces']
  for f in new:
   f.material_index=0
   for l in f.loops:
    neighbors=[ol for ol in l.vert.link_loops if ol.face not in new]
    l[uv].uv=neighbors[0][uv].uv if neighbors else (0,0)
  added.extend(new)
 # A narrow leather loop wraps the grip and returns to the belt, all pelvis-weighted.
 beltface=next(f for f in bm.faces if all(v[part]==12 for v in f.verts));beltuv=[l[uv].uv.copy()for l in beltface.loops]
 gi=o.vertex_groups['B_Pelvis'].index;ring=[]
 for z in [.901,.920]:
  row=[]
  for j in range(8):
   t=2*math.pi*j/8;v=bm.verts.new(Vector((park.x+.021*math.cos(t),park.y+.021*math.sin(t),z)));v[part]=12;v[deform][gi]=1;row.append(v)
  ring.append(row)
 for j in range(8):
  f=bm.faces.new((ring[0][j],ring[0][(j+1)%8],ring[1][(j+1)%8],ring[1][j]));f.material_index=0
  for k,l in enumerate(f.loops):l[uv].uv=beltuv[k%len(beltuv)]
  added.append(f)
 bmesh.ops.recalc_face_normals(bm,faces=added);bmesh.ops.triangulate(bm,faces=added);bm.to_mesh(o.data);bm.free();o.data.update()
 after=sum(len(f.vertices)-2 for f in o.data.polygons);report['geometry'].append({'file':entry['blend'],'before_triangles':before,'triangles':after,'added_triangles':after-before})
 if level:entry['triangles']=after
 # Record existing hand UV charts so the same clean skin is applied to all texture resolutions.
 handfaces=[];parts=[v.value for v in o.data.attributes['piece'].data];layer=o.data.uv_layers.active
 for f in o.data.polygons:
  if all(parts[i]in[3,4]for i in f.vertices):handfaces.append([list(layer.data[j].uv)for j in f.loop_indices])
 (W/f'hand_uv_{level}.json').write_text(json.dumps(handfaces))
 bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(P/entry['blend']))
(P/'review/reduction/selection.json').write_text(json.dumps(selection,indent=2));(P/'review/review1_changes.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True)
