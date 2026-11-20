"""Fit the covered shirt to the mantle; seat the rigid medallion on the waist belt."""
import bpy,numpy as np,json,math
from pathlib import Path
p=Path(__file__).resolve().parents[1];out=p/'review/shoulder_buckle_20261011'
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_v12.blend'))
r=bpy.data.objects['Rig'];o=bpy.data.objects['Body'];me=o.data;sc=bpy.context.scene
co=np.array([v.co[:] for v in me.vertices]);pv=np.zeros(len(co),np.int32);me.attributes['piece'].data.foreach_get('value',pv)
def smooth(x,a,b):
 t=float(np.clip((x-a)/(b-a),0,1));return t*t*(3-2*t)
def weights(i,w):
 for g in list(me.vertices[i].groups):o.vertex_groups[g.group].remove([i])
 total=sum(w.values())
 for n,v in w.items():
  if v>1e-6:o.vertex_groups[n].add([i],v/total,'REPLACE')
# Match only the covered shirt shoulder to the established mantle deformation.
# The cape's two layers and fall animation already have accepted clearance.
for i in np.flatnonzero(pv==1):
 i=int(i);x,y,z=co[i]
 t=smooth(z,1.255,1.33)*(1-smooth(z,1.43,1.48))*smooth(abs(x),.065,.11)*(1-smooth(abs(x),.29,.36))
 if t<=1e-6:continue
 old={o.vertex_groups[g.group].name:g.weight for g in me.vertices[i].groups}
 arm=.7*smooth(abs(x),.17,.33);side='L' if x>0 else 'R'
 new={'B_Spine2':1-arm,f'B_{side}_UpperArm':arm}
 w={k:v*(1-t) for k,v in old.items()}
 for k,v in new.items():w[k]=w.get(k,0)+v*t
 weights(i,w)
for i in np.flatnonzero(pv==18):me.vertices[int(i)].co.z-=.028
# Reuse clean waist fabric for the shirt faces carrying Meshy's duplicate painted buckle.
# UV-only correction keeps all PBR channels consistent without repainting the atlas.
uv=me.uv_layers['UVMap'].data;uv_faces=[]
for face in me.polygons:
 ids=list(face.vertices);xyz=co[ids]
 if pv[ids[0]]!=1 or xyz[:,2].max()>1.125 or xyz[:,1].mean()>-.11 or abs(xyz[:,0].mean())>.10:continue
 for li in face.loop_indices:
  x,y,z=co[me.loops[li].vertex_index]
  uv[li].uv=((178.5+x*45)/1024,1-(405.5-(z-1.075)*90)/1024)
 uv_faces.append(face.index)
# Reuse a continuous clean leather swatch around the waist; no patch boundary behind the buckle.
belt_uv_faces=[]
for face in me.polygons:
 ids=list(face.vertices);xyz=co[ids]
 if pv[ids[0]]!=11:continue
 for li in face.loop_indices:
  x,y,z=co[me.loops[li].vertex_index]
  uv[li].uv=((554.5+7*math.atan2(x,-y-.04))/1024,1-(573.5-(z-1.045)*280)/1024)
 belt_uv_faces.append(face.index)
assert len(belt_uv_faces)>5
assert len(uv_faces)>10
(out/'repair.json').write_text(json.dumps({'shirt_uv_faces':uv_faces,'belt_uv_faces':belt_uv_faces,'buckle_shift_z_m':-.028,'buckle_and_belt_bone':'B_Pelvis','cape_geometry_weights_and_animation_unchanged':True},indent=1))
for part in [10,11,18]:
 assert all(len([g for g in me.vertices[int(i)].groups if g.weight>1e-6])==1 and o.vertex_groups[me.vertices[int(i)].groups[0].group].name=='B_Pelvis' for i in np.flatnonzero(pv==part))
r.animation_data.action=None
for b in r.pose.bones:b.matrix_basis.identity()
bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/rig_v13.blend'))
