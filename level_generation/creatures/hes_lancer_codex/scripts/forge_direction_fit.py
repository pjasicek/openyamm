"""Fit rigid hull groups against visible skin, equipment and neighbouring closed plates."""
import bpy,sys,os,json,math,runpy
import numpy as np
from pathlib import Path
from mathutils import Vector,Quaternion,Matrix
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];S=P/'scripts';sys.path.insert(0,str(S));import armik
resume='--resume' in sys.argv
roles=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
roles=[x for x in roles if x!='--resume'] or ['Standing','Walking','Running','Attack','Hit','Fidget','Cast','Death','Dead']
src=P/('work/forge_direction_fit.blend' if resume else 'work/forge_collision_fit.blend');bpy.ops.wm.open_mainfile(filepath=str(src));r=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];sc=bpy.context.scene
# These narrow Lancer fillers occupy the new apron, not the concept's exposed layer.
removed={'abdomen_u','abdomen_upper','back_low','breast_L','breast_R','belt'}
spec=json.loads((S/'armour_forge.json').read_text());ids={i+1 for i,p in enumerate(spec['plates']) if p['name'] in removed}
for v in body.data.attributes['shell_hidden'].data:
 if v.value in ids:v.value=0
for name in [*['Arm_'+n for n in removed],'Apron_Strap_L','Apron_Strap_R']:
 if name in bpy.data.objects:bpy.data.objects.remove(bpy.data.objects[name],do_unlink=True)
spec['plates']=[p for p in spec['plates'] if p['name'] not in removed]
groups=[]
for side in 'LR':
 group=[bpy.data.objects[n] for n in (f'Arm_pauldron_{side}',f'Arm_pauldron_lower_{side}',f'Apron_Shoulder_{side}')];parent=f'B_{side}_UpperArm';bn=f'B_ForgeShoulder_{side}'
 groups.append((bn,parent,group))
 group=[bpy.data.objects[f'Arm_forearm_{side}']];groups.append((f'B_ForgeGauntlet_{side}',f'B_{side}_Forearm',group))
r.animation_data.action=None;bpy.context.view_layer.objects.active=r;bpy.ops.object.mode_set(mode='EDIT')
for bn,parent,obs in groups:
 b=r.data.edit_bones.get(bn) or r.data.edit_bones.new(bn);b.matrix=r.data.edit_bones[parent].matrix.copy();b.length=.08;b.parent=r.data.edit_bones[parent]
bpy.ops.object.mode_set(mode='OBJECT')
for bn,parent,obs in groups:
 for ob in obs:
  ob.vertex_groups.clear();ob.vertex_groups.new(name=bn).add(list(range(len(ob.data.vertices))),1,'REPLACE');ob['bone']=bn
  for p in spec['plates']:
   if ob.name=='Arm_'+p['name']:p['bone']=bn;p['shell']['bones']=[bn]
for side in ('Front','Back'):
 for k in range(3):
  ob=bpy.data.objects.get(f'Apron_{side}{k}')
  if ob:groups.append((ob.vertex_groups[0].name,None,[ob]))
(S/'armour_forge_concept.json').write_text(json.dumps(spec,indent=2)+'\n')
# One current frame is enough to initialize the exact shared G6 helpers and visible-skin masks.
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/forge_collision_base.blend'))
group_names=[(bn,parent,[o.name for o in obs]) for bn,parent,obs in groups]
sys.argv=['armour_gate.py','--',str(P/'work/forge_collision_base.blend'),'forge_fit_masks',str(S/'armour_forge_concept.json')];g=runpy.run_path(str(S/'armour_gate.py'),run_name='__main__');r=g['rig'];body=g['body'];sc=bpy.context.scene
groups=[(bn,parent,[bpy.data.objects[n] for n in ns]) for bn,parent,ns in group_names]
plates=g['plates'];faces={o.name:[tuple(p.vertices) for p in o.data.polygons if p.material_index==0] for o in plates};pv={n:np.array(sorted({i for f in ff for i in f}),int) for n,ff in faces.items()};BF=g['BFK'];visible=np.flatnonzero(g['HID']==0);gun=bpy.data.objects['Thunder_Maul'];inside=g['inside_closed']

def tree(V,F):return BVHTree.FromPolygons(V.tolist(),F)
def bounds(V):return V.min(0),V.max(0)
def near(V,box,pad=.012):return np.flatnonzero(np.all((V>box[0]-pad)&(V<box[1]+pad),axis=1))
def penetration(t,V,skip=()):
 d,k=inside(t,V,2.5,skip)
 if k<0:return None
 loc,n,fi,_=t.find_nearest(Vector(V[k]));return d,np.array(n)

HF=[tuple(f.vertices) for f in body.data.polygons if all(sum(e.weight for e in body.data.vertices[i].groups if body.vertex_groups[e.group].name in {'B_Head','Bone_025','headfront','Bone_041','Bone_036'})>.5 for i in f.vertices)]
report=json.loads((P/'review/forge_direction_fit.json').read_text()) if resume else {}
for role in roles:
 if 'Forge_'+role in report:continue
 a=bpy.data.actions['Forge_'+role];r.animation_data.action=None
 for bn,_,_ in groups:
  pass
 r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];cache=[];maxd=0.;errors=[]
 for f in np.arange(a.frame_range[0],a.frame_range[1]+.001,.5):
  sc.frame_set(int(f),subframe=float(f%1))
  # The shoulder lames follow arm elevation, without the upper arm's axial twist.
  chest=armik.W(r,'B_Spine2');turn=chest.to_3x3()@r.data.bones['B_Spine2'].matrix_local.to_3x3().inverted()
  cap_directions={}
  for side in 'LR':
   upper=r.data.bones[f'B_{side}_UpperArm'];restaxis=(r.data.bones[f'B_{side}_Forearm'].head_local-upper.head_local).normalized();posedaxis=(armik.W(r,f'B_{side}_Forearm').translation-armik.W(r,upper.name).translation).normalized()
   up=Vector((0,0,1));up=(up-restaxis*up.dot(restaxis)).normalized();lateral=turn@Vector((1 if side=='L' else -1,0,0));outer=lateral-posedaxis*lateral.dot(posedaxis)
   if outer.length<.15:outer=turn@Vector((0,0,1));outer-=posedaxis*outer.dot(posedaxis)
   outer.normalize();restbasis=Matrix((restaxis,up,restaxis.cross(up))).transposed();posebasis=Matrix((posedaxis,outer,posedaxis.cross(outer))).transposed();rot=posebasis@restbasis.transposed()
   m=(rot@upper.matrix_local.to_3x3()).to_4x4();m.translation=armik.W(r,upper.name).translation;armik.set_world(r,f'B_ForgeShoulder_{side}',m);cap_directions[side]=outer

  bpy.context.view_layer.update();B,_=g['ev'](body);BT=tree(B,BF);G,_=g['ev'](gun);V={o.name:g['ev'](o)[0] for o in plates};T={n:tree(v,faces[n]) for n,v in V.items()};BB={n:bounds(v) for n,v in V.items()};M={bn:armik.W(r,bn).copy() for bn,_,_ in groups};D={bn:np.zeros(3) for bn,_,_ in groups}
  HT=tree(B,HF)
  for_round=[]
  # Alternating projection keeps the hanging plates clear of one another, as well as the skin.
  for sweep in range(4 if role in ('Death','Dead') else 8):
   sweep_move=0.
   for bn,parent,obs in groups:
    own={o.name for o in obs};total=np.zeros(3)
    chest=armik.W(r,'B_Spine2');side=1 if bn.endswith('_L') else -1
    outward=np.array(cap_directions['L' if side==1 else 'R'])
    for iteration in range(32 if role in ('Death','Dead') else 80):
     constraints=[]
     for ob in obs:
      n=ob.name;v=V[n];box=BB[n];points=v[pv[n]]
      c=penetration(BT,points,g['HIDFK'])
      if c and c[0]>.0015:constraints.append((c[0],c[1]))
      ix=near(B[visible],box)
      if len(ix):
       c=penetration(T[n],B[visible[ix]])
       if c and c[0]>.0015:constraints.append((c[0],-c[1]))
      for other in V:
       if other in own or np.any(box[0]>BB[other][1]+.006) or np.any(BB[other][0]>box[1]+.006):continue
       c=penetration(T[other],points)
       if c and c[0]>.0015:constraints.append((c[0],c[1]))
       c=penetration(T[n],V[other][pv[other]])
       if c and c[0]>.0015:constraints.append((c[0],-c[1]))
      gx=near(G,box);c=penetration(T[n],G[gx]) if len(gx) else None
      if c and c[0]>.0015:constraints.append((c[0],-c[1]))
      if bn.startswith('B_ForgeShoulder_') and HT.overlap(tree(v,[tuple(p.vertices) for p in ob.data.polygons])):constraints.append((.004,outward))
      if role not in ('Death','Dead') and v[:,2].min()<.002:constraints.append((.002-float(v[:,2].min()),np.array([0.,0.,1.])))
     if not constraints:break
     dep,normal=max(constraints,key=lambda x:x[0]);delta=normal*min(.025,dep+.004)
     total+=delta;D[bn]+=delta;sweep_move+=float(np.linalg.norm(delta))
     if np.linalg.norm(D[bn])>.22:
      for ob in obs:
       n=ob.name;print('FAILED_FIT',n,'body',penetration(BT,V[n][pv[n]],g['HIDFK']),'skin',penetration(T[n],B[visible]),'head',len(HT.overlap(tree(V[n],[tuple(p.vertices) for p in ob.data.polygons]))),'gun',penetration(T[n],G),flush=True)
       for other in V:
        if other not in own:
         c=penetration(T[other],V[n][pv[n]]);cc=penetration(T[n],V[other][pv[other]])
         if (c and c[0]>.0015) or (cc and cc[0]>.0015):print('FAILED_PAIR',n,other,c,cc,flush=True)
      raise AssertionError((role,float(f),bn,'excessive armour displacement',D[bn]))
     for ob in obs:
      n=ob.name;V[n]+=delta;T[n]=tree(V[n],faces[n]);BB[n]=bounds(V[n])
    maxd=max(maxd,float(np.linalg.norm(D[bn])))
   for_round.append(maxd)
   if sweep_move<.0005:break
  # Bake the solved world positions parent first; a parent correction must not move its child twice.
  pose={}
  for bn,_,obs in groups:
   m=M[bn];m.translation+=Vector(D[bn]);armik.set_world(r,bn,m);pose[bn]=r.pose.bones[bn].matrix_basis.copy()
  cache.append((float(f),pose))
  if int(f*2)%30==0:print('RIGID_HULL_FIT',role,f,'max correction',round(maxd,4),flush=True)
 previous={}
 for f,pose in cache:
  for bn,m in pose.items():
   b=r.pose.bones[bn];q=m.to_quaternion()
   if bn in previous and q.dot(previous[bn])<0:q=-q
   previous[bn]=q.copy();b.rotation_mode='QUATERNION';b.rotation_quaternion=q;b.location=m.translation;b.keyframe_insert('rotation_quaternion',frame=f);b.keyframe_insert('location',frame=f)
 for layer in a.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:
     if any(bn in fc.data_path for bn,_,_ in groups):
      for key in fc.keyframe_points:key.interpolation='LINEAR'
 report[a.name]={'max_world_correction_m':maxd};bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/forge_direction_fit.blend'));(P/'review/forge_direction_fit.json').write_text(json.dumps(report,indent=2)+'\n')
r.animation_data.action=None;bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/forge_direction_fit.blend'));sys.stdout.flush();os._exit(0)
