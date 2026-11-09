"""Preview local two-handed weapon sources before Meshy modelling."""
from pathlib import Path
import bpy,json,math,sys,bmesh
import numpy as np
from mathutils import Vector
P=Path(__file__).resolve().parents[1]; R=P.parents[2]
sys.path.insert(0,str(R/'level_generation/creatures/mm8_m612_claude/scripts'))
import common
out=P/'motion/source_preview';out.mkdir(parents=True,exist_ok=True)
candidates={'2Hand Axe':['2HandAxeAttack1','2HandAxeAttack2','2HandAxeAttack3'],
'2Hand Spear':['2HandSpearIdle','2HandSpearAttack1','2HandSpearAttack6','2HandSpearAttack7','2HandSpearGetHitF1','2HandSpearDeath1']}
rows=[];measures=[]
for library,names in candidates.items():
 bpy.ops.wm.read_factory_settings(use_empty=True)
 source=R/'anim_library/humanoid_set'/(library+'.glb')
 bpy.context.scene.render.fps=30
 bpy.ops.import_scene.gltf(filepath=str(source))
 rig=next(o for o in bpy.data.objects if o.type=='ARMATURE')
 rig.rotation_mode='XYZ';rig.rotation_euler=(0,0,math.pi)
 scene=bpy.context.scene;scene.render.fps=30;common.workbench_clay(scene)
 for name in names:
  matches=[a for a in bpy.data.actions if a.name.split('@')[-1].split('|')[-1].endswith(name)]
  assert len(matches)==1,(name,[a.name for a in bpy.data.actions])
  act=matches[0];rig.animation_data.action=act
  if act.slots:rig.animation_data.action_slot=act.slots[0]
  start,end=act.frame_range
  scene.frame_set(int(start+(end-start)*.3))
  W=rig.matrix_world;hand=W@rig.pose.bones['B_R_Hand'].matrix;centres=[]
  for j in (1,2,3,4):
   pts=np.array([W@rig.pose.bones[f'B_R_Finger{j}'+suffix].head for suffix in ('','1','2')])
   mid=pts.mean(0);u,sv,vt=np.linalg.svd(pts-mid);xy=np.stack([(pts-mid)@vt[0],(pts-mid)@vt[1]],1)
   sol=np.linalg.lstsq(np.column_stack([2*xy,np.ones(3)]),(xy**2).sum(1),rcond=None)[0]
   centres.append(mid+sol[0]*vt[0]+sol[1]*vt[1])
  centres=np.array(centres);centre=centres.mean(0);axis=np.linalg.svd(centres-centre)[2][0]
  idx=np.array(W@rig.pose.bones['B_R_Finger1'].head);pink=np.array(W@rig.pose.bones['B_R_Finger4'].head)
  if np.dot(idx-pink,axis)<0:axis=-axis
  c=hand.inverted()@Vector(centre);axis=(hand.inverted().to_3x3()@Vector(axis)).normalized()
  side=axis.orthogonal().normalized();flat=axis.cross(side);k=1/hand.to_scale()[0]
  mesh=bpy.data.meshes.new('PropPreview');bm=bmesh.new()
  for a0,a1,w,th in ((-.55,.85,.018,.018),(.85,1.15,.15,.015)):
   vs=[bm.verts.new(c+axis*(a*k)+side*(sx*w*k*(.12 if a==1.15 else 1))+flat*(sy*th*k)) for a in (a0,a1) for sx in (-1,1) for sy in (-1,1)]
   for f in ((0,1,3,2),(4,6,7,5),(0,4,5,1),(2,3,7,6),(0,2,6,4),(1,5,7,3)):bm.faces.new([vs[j] for j in f])
  bm.to_mesh(mesh);bm.free();prop=bpy.data.objects.new('PropPreview',mesh);scene.collection.objects.link(prop)
  mat=bpy.data.materials.new('PropPreview');mat.diffuse_color=(.05,.55,.1,1);mesh.materials.append(mat)
  measures.append({'source':str(source.relative_to(R)),'clip':name,'frames':[start,end],'fps':30,'duration':(end-start)/30})
  row=[]
  for i in range(7):
   f=start+(end-start)*i/6;scene.frame_set(int(f),subframe=f-int(f))
   prop.matrix_world=rig.matrix_world@rig.pose.bones['B_R_Hand'].matrix
   path=common.render_views(str(out/f'{name}_{i}'),1.3,4.2,views=('three_quarter',),resolution=(240,320))[0]
   row.append([path,f'{name} {f:.1f}'])
  rows.append(row)
  bpy.data.objects.remove(prop,do_unlink=True)
(out/'frames.json').write_text(json.dumps(rows,indent=2)+'\n')
(P/'motion/source_preview.json').write_text(json.dumps(measures,indent=2)+'\n')
