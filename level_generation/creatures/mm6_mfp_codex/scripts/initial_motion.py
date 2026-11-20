import bpy,bmesh,sys,runpy,json,numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'))
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_v1.blend'))
b=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];me=b.data
bm=bmesh.new();bm.from_mesh(me)
vs=[v for v in bm.verts if (v.co-Vector((-.279,-.056,1.022))).length<.028]
for _ in range(5):bmesh.ops.smooth_vert(bm,verts=vs,factor=.65,use_axis_x=True,use_axis_y=True,use_axis_z=True)
bmesh.ops.recalc_face_normals(bm,faces=bm.faces[:]);bm.to_mesh(me);bm.free()
# Anatomical ownership, including sash and rigid jewelry; unrelated limbs never share weights.
piece=np.zeros(len(me.vertices),np.int32);me.attributes['piece'].data.foreach_get('value',piece)
def setweights(i,w):
 for g in b.vertex_groups:g.remove([i])
 for n,v in w.items():
  if v>1e-6:b.vertex_groups[n].add([i],float(v),'REPLACE')
for v in me.vertices:
 i=v.index;p=v.co;sd='L' if p.x>0 else 'R';part=piece[i]
 if part in [4,5]:
  E=rig.data.bones[f'B_{sd}_Forearm'].head_local;W=rig.data.bones[f'B_{sd}_Hand'].head_local;S=rig.data.bones[f'B_{sd}_UpperArm'].head_local
  t=(p-E).dot(W-E)/(W-E).length_squared
  h=np.clip((t-.87)/.22,0,1);u=np.clip((.13-t)/.26,0,1)
  setweights(i,{f'B_{sd}_UpperArm':u,f'B_{sd}_Forearm':(1-u)*(1-h),f'B_{sd}_Hand':(1-u)*h})
 elif part==3:setweights(i,{'B_Head':1})
 elif p.z>1.415:setweights(i,{'B_Head':1})
 elif part==6:
  q=np.clip((p.z-1.00)/.23,0,1);setweights(i,{'B_Pelvis':1-q,'B_Spine2':q})
 elif part in [7,10,11,12,18,21]:setweights(i,{f'B_{sd}_Forearm':1})
 elif part in [13,14,16,17]:setweights(i,{f'B_{sd}_Foot':1})
 elif part in [22,23,24,25,26,27]:setweights(i,{f'B_{sd}_Calf':1})
 elif part>27 and p.z<1.395:setweights(i,{'B_Spine2':1})
 elif part==1:setweights(i,{'B_Pelvis':1})
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_weighted.blend'))
sys.argv=['finger_weights.py','--',str(P/'work/rig_weighted.blend'),str(P/'work/rig_weighted.blend')];runpy.run_path(str(P/'scripts/finger_weights.py'),run_name='__main__')
# Keep invisible upper legs out of the garment interior; preserve the full visible lower calves.
b=bpy.data.objects['Body'];bm=bmesh.new();bm.from_mesh(b.data);pc=bm.verts.layers.int['piece']
remove=[f for f in bm.faces if all(v[pc]==0 and .40<v.co.z<.875 for v in f.verts)]
bmesh.ops.delete(bm,geom=remove,context='FACES');bm.to_mesh(b.data);bm.free()
print('HIDDEN_LEG_FACES_REMOVED',len(remove))
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_weighted.blend'))
runpy.run_path(str(P/'scripts/export_uploads.py'),run_name='__main__')
items=['Relax.glb:RelaxIdle:Standing','Relax.glb:RelaxWalkFemale3:Walking','Relax.glb:RelaxRunForward:Running','1Hand.glb:DaggerAttackR3:Attack','Unarmed.glb:UnarmedGetHitF1:Hit','Relax.glb:RelaxLaydownLayDown:Death']
sys.argv=['retarget.py','--',str(P/'work/rig_uv.blend'),str(P/'work/rig_animated.blend')]+[str(P.parents[2]/'anim_library/humanoid_set'/it) for it in items]
runpy.run_path(str(P/'scripts/retarget.py'),run_name='__main__')
