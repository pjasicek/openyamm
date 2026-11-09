import bpy,json,math,sys,numpy as np
from pathlib import Path
from mathutils import Vector,Quaternion
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import pose_helpers as ph,final_refinements
G=json.loads((P/'work/round1_grip.json').read_text());roles=['Walking','Running','Attack','Cast','Hit'];allroles=['Standing','Walking','Running','Attack','Cast','Hit','Death','Dead','Fidget']
bpy.ops.wm.open_mainfile(filepath=str(P/'review/round1/before/mm6_mep.blend'));r=bpy.data.objects['Rig'];b=bpy.data.objects['Mep'];sc=bpy.context.scene;ph.init(r)
for role in roles:bpy.data.actions.remove(bpy.data.actions[role])
with bpy.data.libraries.load(str(P/'work/round1_motion.blend'),link=False) as (src,dst):dst.actions=list(roles)
for a in dst.actions:a.use_fake_user=True
for role in roles:
 a=bpy.data.actions[role];ph.setact(a);rows=[]
 for f in np.arange(0,float(a.frame_range[1])+.001,.5):
  sc.frame_set(int(f),subframe=f%1);row=ph.capture();ph.apply(row)
  for sd,deg in [('L',-11.63773),('R',6.24394)]:ph.worldrot(f'B_{sd}_Foot',Quaternion((0,0,1),math.radians(deg))@r.pose.bones[f'B_{sd}_Foot'].matrix.to_quaternion())
  rows.append((f,ph.capture()));ph.setact(a)
 for f,row in rows:
  for n in [f'B_{s}_Foot' for s in 'LR']:
   pb=r.pose.bones[n];pb.rotation_quaternion=row[n][0];pb.keyframe_insert('rotation_quaternion',frame=f)
final_refinements.fit_running_stride(r)
# Set a distinct jog cadence; runtime still advances by the fitted 1.55x stride.
a=bpy.data.actions['Running']
for layer in a.layers:
 for strip in layer.strips:
  for bag in strip.channelbags:
   for fc in bag.fcurves:
    for key in fc.keyframe_points:key.co.x*=.75;key.handle_left.x*=.75;key.handle_right.x*=.75
    fc.update()
a.frame_end*=.75
# Correct grip and move axial wrist rotation into the forearm, preserving the hand's world frame.
for role in allroles:
 a=bpy.data.actions[role];ph.setact(a);rows=[]
 for f in np.arange(0,float(a.frame_range[1])+.001,.5):
  sc.frame_set(int(f),subframe=f%1);row=ph.capture();ph.apply(row)
  fade=1-ph.smooth((f-4.5)/8) if role=='Death' else 0 if role=='Dead' else 1
  for n,q in G['finger_local'].items():r.pose.bones[n].rotation_quaternion=Quaternion().slerp(Quaternion(q),fade)
  ph.update()
  for side in 'LR':
   fn,hn=f'B_{side}_Forearm',f'B_{side}_Hand';fb,hb=r.data.bones[fn],r.data.bones[hn];handmatrix=r.pose.bones[hn].matrix.copy();fore=r.pose.bones[fn].matrix.to_quaternion();neutral=fore@fb.matrix_local.to_quaternion().inverted()@hb.matrix_local.to_quaternion();rel=neutral.inverted()@handmatrix.to_quaternion();axis=hb.matrix_local.to_3x3().inverted()@(sum((r.data.bones[f'B_{side}_Finger{i}'].head_local for i in range(5)),Vector())/5-hb.head_local).normalized();tw=2*math.atan2(Vector((rel.x,rel.y,rel.z)).dot(axis),rel.w);tw=(tw+math.pi)%math.tau-math.pi
   amount=tw*.62;worldaxis=(r.pose.bones[hn].head-r.pose.bones[fn].head).normalized();ph.worldrot(fn,Quaternion(worldaxis,amount)@fore);r.pose.bones[hn].matrix=handmatrix;ph.update()
   # Helpers share the remaining forearm twist and remove half the humeral twist near the shoulder.
   for base,child,helper,factor in [('Forearm','Hand','ForearmTwist',.45),('UpperArm','Forearm','UpperArmTwist',-.5)]:
    bn=r.data.bones[f'B_{side}_{base}'];ax=(bn.matrix_local.inverted()@r.data.bones[f'B_{side}_{child}'].head_local).normalized()
    q=r.pose.bones[f'B_{side}_Hand'].rotation_quaternion if base=='Forearm' else r.pose.bones[bn.name].rotation_quaternion;ang=2*math.atan2(Vector((q.x,q.y,q.z)).dot(ax),q.w);ang=(ang+math.pi)%math.tau-math.pi;r.pose.bones[f'B_{side}_{helper}'].rotation_quaternion=Quaternion(ax,ang*factor)
  rows.append((float(f),ph.capture()));ph.setact(a)
 names=[n for n in ph.names if any(k in n for k in ['Forearm','Hand','Finger','Twist'])]
 for layer in a.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in list(bag.fcurves):
     if any(fc.data_path=='pose.bones[\"'+n+'\"].rotation_quaternion' for n in names):bag.fcurves.remove(fc)
 for f,row in rows:
  for n in names:
   pb=r.pose.bones[n];pb.rotation_quaternion=row[n][0];pb.keyframe_insert('rotation_quaternion',frame=f)
# Filter the fitted key rotations (not frame numbers) to remove IK pole quantisation.
for role in ['Walking','Running','Attack','Cast','Hit']:
 a=bpy.data.actions[role];ph.setact(a);frames=np.arange(0,float(a.frame_range[1])+.001,.5);names=[n for n in ph.names if any(k in n for k in ['UpperArm','Forearm','Hand','Twist','Spine','Neck','Head'])];rows=[]
 for f in frames:sc.frame_set(int(f),subframe=f%1);rows.append({n:r.pose.bones[n].rotation_quaternion.copy() for n in names})
 for j,f in enumerate(frames):
  for n in names:
   anchor=rows[j][n];v=np.zeros(4)
   width=48 if role=='Attack' else 12
   for off,w in [(k-width//2,math.comb(width,k)) for k in range(width+1)]:
    ix=(j+off)%(len(rows)-1) if role in ['Walking','Running'] else min(len(rows)-1,max(0,j+off));q=rows[ix][n];v+=np.array(q)*w*(1 if anchor.dot(q)>=0 else -1)
   q=Quaternion(v.tolist());q.normalize();pb=r.pose.bones[n];pb.rotation_quaternion=q;pb.keyframe_insert('rotation_quaternion',frame=float(f))
ph.setact(None)
for pb in r.pose.bones:pb.matrix_basis.identity()
ph.update();bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/round1_actions.blend'))
# Keep the selected geometry and topology; only garment skin weights and map bindings change.
for level in range(4):
 bpy.ops.wm.open_mainfile(filepath=str(P/f'review/round1/before/final_lod{level}.blend'));r=bpy.data.objects['Rig'];b=bpy.data.objects['Body'];sc=bpy.context.scene;ph.init(r);ph.setact(None)
 for pb in r.pose.bones:pb.matrix_basis.identity()
 for a in list(bpy.data.actions):bpy.data.actions.remove(a)
 with bpy.data.libraries.load(str(P/'work/round1_actions.blend'),link=False) as (src,dst):dst.actions=list(allroles)
 for a in dst.actions:a.use_fake_user=True
 delta=r.data.bones['B_R_Hand'].matrix_local.to_3x3()@Vector(G.get('shift_hand_local',[0,0,0]))
 for v in b.data.vertices:
  if b.data.attributes['piece'].data[v.index].value==100:v.co+=delta
 bpy.context.view_layer.objects.active=r;bpy.ops.object.mode_set(mode='EDIT')
 for name in ['Staff','Socket_Staff_Head']:
  eb=r.data.edit_bones[name];eb.head+=delta;eb.tail+=delta
 bpy.ops.object.mode_set(mode='OBJECT')
 M=r.data.bones['Staff'].matrix_local;inv=M.inverted()
 for v in b.data.vertices:
  if b.data.attributes['piece'].data[v.index].value==100:
   x=inv@v.co;fac=1+.06*max(0,min(1,(.14-abs(x.y))/.055));x.x*=fac;x.z*=fac;v.co=M@x
 M=r.data.bones['Staff'].matrix_local;inv=M.inverted();handgroup=b.vertex_groups['B_R_Hand'].index
 for v in b.data.vertices:
  if sum(g.weight for g in v.groups if g.group==handgroup)<.75:continue
  x=inv@v.co;radius=math.hypot(x.x,x.z)
  if abs(x.y)<.065 and .012<radius<.04:
   shift=min(radius-.012,.0025*max(0,min(1,(.04-radius)/.018)));factor=(radius-shift)/radius;x.x*=factor;x.z*=factor;v.co=M@x

 me=b.data;piece=np.array([v.value for v in me.attributes['piece'].data]);head=np.array([x.value for x in me.attributes['head'].data]);headverts={int(i) for f in me.polygons if head[f.index] for i in f.vertices};groups={g.name:g for g in b.vertex_groups};W=np.zeros((len(me.vertices),len(groups)))
 for v in me.vertices:
  for g in v.groups:W[v.index,g.group]=g.weight
 fixed=[]
 for v in me.vertices:
  if piece[v.index]!=0 or v.index in headverts or v.co.z<1.21:continue
  side='L' if v.co.x>0 else 'R';w=W[v.index];wrong=[g.index for g in groups.values() if g.name in ['B_Head','B_Neck'] or (g.name.startswith('B_') and any(z in g.name for z in ['UpperArm','Clavicle']) and f'B_{side}_' not in g.name)]
  moved=sum(w[i] for i in wrong);w[wrong]=0;w[groups['B_Spine2'].index]+=moved;fixed.append(v.index)
 # Rebuild the garment's shoulder gradient. Foreign arm/head weights on the chest made folds collapse.
 for i in fixed:
  v=me.vertices[i];side='L' if v.co.x>0 else 'R';arm=ph.smooth((abs(v.co.x)-.105)/.15);ub=r.data.bones[f'B_{side}_UpperArm'];fb=r.data.bones[f'B_{side}_Forearm'];seg=fb.head_local-ub.head_local;t=(v.co-ub.head_local).dot(seg)/seg.length_squared;fore=ph.smooth((t-.65)/.50);W[i]=0
  torso=ph.smooth((v.co.z-1.20)/.12);W[i,groups['B_Spine1'].index]=(1-arm)*(1-torso);W[i,groups['B_Spine2'].index]=(1-arm)*torso
  W[i,groups[f'B_{side}_UpperArm'].index]=arm*(1-fore);W[i,groups[f'B_{side}_Forearm'].index]=arm*fore
 # Diffuse only within the connected shoulder cloth, keeping chest and sleeve ends as anchors.
 adj=[[] for _ in me.vertices]
 for edge in me.edges:
  i,j=edge.vertices
  if piece[i]==piece[j]==0:adj[i].append(j);adj[j].append(i)
 blend=[i for i in fixed if .08<abs(me.vertices[i].co.x)<.28 and me.vertices[i].co.z>1.24]
 for _ in range(14):
  previous=W.copy()
  for i in blend:
   if adj[i]:W[i]=previous[i]*.55+previous[adj[i]].mean(0)*.45
 for i in fixed:
  w=W[i];w[np.argsort(w)[:-8]]=0;w/=w.sum()
  for g in list(me.vertices[i].groups):b.vertex_groups[g.group].remove([i])
  for gi in np.flatnonzero(w>1e-7):b.vertex_groups[int(gi)].add([i],float(w[gi]),'REPLACE')
 print('SHOULDER_WEIGHTS',level,len(fixed),len(blend),flush=True)
 # Seat the sash just outside the torso, without including the sleeve cuffs in its envelope.
 coords=np.array([v.co[:] for v in me.vertices])
 for v in me.vertices:
  if piece[v.index]==7:v.co.x*=1.075;v.co.y=.008+(v.co.y-.008)*1.035
  if piece[v.index]==1:
   radius=math.hypot(v.co.x,v.co.y-.01);inset=.022*ph.smooth((v.co.z-.85)/.10);factor=max(.5,1-inset/max(radius,1e-5));v.co.x*=factor;v.co.y=.01+(v.co.y-.01)*factor

 if level==3:
  for v in me.vertices:
   if piece[v.index]==1 and v.co.y<-.04 and abs(v.co.x)<.10:v.co.x*=1-.65*ph.smooth((v.co.z-.88)/.06)
 # Transfer one weight set per button so its triangles cannot shear into separate flecks.
 coatids=np.flatnonzero(piece==0)
 for part in [9,*range(14,100)]:
  ids=np.flatnonzero(piece==part)
  if not len(ids):continue
  center=coords[ids].mean(0);nearest=int(coatids[np.argmin(np.linalg.norm(coords[coatids]-center,axis=1))]);weights=[(g.group,g.weight) for g in me.vertices[nearest].groups]
  for i in ids:
   v=me.vertices[int(i)]
   for g in list(v.groups):b.vertex_groups[g.group].remove([int(i)])
   for gi,w in weights:b.vertex_groups[gi].add([int(i)],w,'REPLACE')

 # Keep the concealed upper trousers attached to the same moving coat surface during the fall.
 if level>=2:
  from mathutils.bvhtree import BVHTree
  from mathutils.geometry import barycentric_transform
  faces=[list(f.vertices) for f in me.polygons if all(piece[i]==0 and me.vertices[i].co.z<1.12 for i in f.vertices)]
  tree=BVHTree.FromPolygons([v.co[:] for v in me.vertices],faces,all_triangles=True)
  for v in me.vertices:
   if piece[v.index]!=1 or v.co.z<=.82:continue
   loc,normal,face,dist=tree.find_nearest(v.co);ids=faces[face]
   bary=barycentric_transform(loc,*[me.vertices[i].co for i in ids],Vector((1,0,0)),Vector((0,1,0)),Vector((0,0,1)))
   target=np.zeros(len(groups))
   for i,share in zip(ids,bary):
    for g in me.vertices[i].groups:target[g.group]+=g.weight*max(0,share)
   target/=target.sum();weight=ph.smooth((v.co.z-.82)/.08);current=np.zeros(len(groups))
   for g in v.groups:current[g.group]=g.weight
   current=current*(1-weight)+target*weight;current[np.argsort(current)[:-8]]=0;current/=current.sum()
   for g in list(v.groups):b.vertex_groups[g.group].remove([v.index])
   for gi in np.flatnonzero(current>1e-7):b.vertex_groups[int(gi)].add([v.index],float(current[gi]),'REPLACE')

 if level==3:
  fit=json.loads((P/'work/round1_hem_fix.json').read_text());point=np.array(fit['point']);distance=np.array([np.linalg.norm(np.array(v.co)-point) if piece[v.index]==1 else 1e6 for v in me.vertices]);assert distance.min()<1e-5
  for i in np.flatnonzero(distance<1e-5):me.vertices[int(i)].co+=Vector(fit['delta'])

 for mat in me.materials:
  prefix='mep_head' if 'Head' in mat.name else 'mep_staff' if 'Staff' in mat.name else 'mep'
  for node in mat.node_tree.nodes:
   if node.type!='TEX_IMAGE' or not node.image:continue
   path=Path(node.image.filepath);key='basecolor' if 'base' in node.image.name.lower() else 'normal' if 'normal' in node.image.name.lower() else 'orm' if 'orm' in node.image.name.lower() else None
   if key:
    im=bpy.data.images.load(str(P/f'textures/lod{level}/{prefix}_{key}.png'),check_existing=False);im.colorspace_settings.name='sRGB' if key=='basecolor' else 'Non-Color';node.image=im;im.pack()
 ph.update();final_refinements.ground_running(r,b)
 death=bpy.data.actions['Death'];ph.setact(death);released=[]
 for f in np.arange(4.5,float(death.frame_range[1])+.001,.5):
  sc.frame_set(int(f),subframe=f%1);row=ph.capture();ph.apply(row);pb=r.pose.bones['Staff'];m=pb.matrix.copy();t=min(1,(f-4.5)/21.5);m.translation.x-=.12*math.sin(math.pi*t);pb.matrix=m;ph.update()
  ev=b.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();low=min(mesh.vertices[int(i)].co.z for i in np.flatnonzero(piece==100));ev.to_mesh_clear()
  if low<.004:m=pb.matrix.copy();m.translation.z+=.004-low;pb.matrix=m;ph.update()
  released.append((float(f),pb.rotation_quaternion.copy(),pb.location.copy()));ph.setact(death)
 for f,q,l in released:
  pb=r.pose.bones['Staff'];pb.rotation_quaternion=q;pb.location=l;pb.keyframe_insert('rotation_quaternion',frame=f);pb.keyframe_insert('location',frame=f)
 ph.setact(death);sc.frame_set(int(death.frame_range[1]));held=ph.capture();ph.write('Dead',[held]*31);ph.setact(bpy.data.actions['Dead'])
 for frame in [0,30]:
  r.pose.bones['Staff'].location=held['Staff'][1];r.pose.bones['Staff'].keyframe_insert('location',frame=frame)
 ph.setact(None)
 for pb in r.pose.bones:pb.matrix_basis.identity()
 for a in bpy.data.actions:
  for layer in a.layers:
   for strip in layer.strips:
    for bag in strip.channelbags:
     for fc in bag.fcurves:
      for key in fc.keyframe_points:key.interpolation='LINEAR'
 for a in bpy.data.actions:
  for layer in a.layers:
   for strip in layer.strips:
    for bag in strip.channelbags:
     tracks={}
     for fc in bag.fcurves:
      if fc.data_path.endswith('rotation_quaternion'):tracks.setdefault(fc.data_path,{})[fc.array_index]=fc
     for track in tracks.values():
      keys=[track[i].keyframe_points for i in range(4)];previous=None
      assert len({len(k) for k in keys})==1
      for j in range(len(keys[0])):
       q=np.array([keys[i][j].co.y for i in range(4)]);q/=np.linalg.norm(q)
       if previous is not None and q@previous<0:q=-q
       for i in range(4):keys[i][j].co.y=float(q[i])
       previous=q
 bpy.ops.wm.save_as_mainfile(filepath=str(P/f'work/final_lod{level}.blend'))
 if level==0:
  b.name=b.data.name='Mep';bpy.ops.wm.save_as_mainfile(filepath=str(P/'export/mm6_mep.blend'))
