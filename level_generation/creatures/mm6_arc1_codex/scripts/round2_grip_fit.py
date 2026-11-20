import bpy,json,numpy as np
from pathlib import Path
from mathutils import Matrix,Vector
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_equipped.blend'));r=bpy.data.objects['Rig'];b=bpy.data.objects['Body'];a=bpy.data.actions['Standing'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];bpy.context.scene.frame_set(0)
ev=b.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();inv=r.pose.bones['Bow'].matrix.inverted();v=np.array([tuple(inv@x.co)for x in me.vertices]);ev.to_mesh_clear();piece=np.array([x.value for x in b.data.attributes['piece'].data]);lab=np.array([x.value for x in b.data.attributes['finger'].data]);b.data.calc_loop_triangles();pts=[];labs=[]
for t in b.data.loop_triangles:
 ids=list(t.vertices)
 if not all(piece[i]==2 for i in ids):continue
 for i in range(7):
  for j in range(7-i):
   w=np.array([i,j,6-i-j])/6;p=w@v[ids]
   if abs(p[2])<.052:pts.append(p);labs.append(int(lab[ids[np.argmax(w)]]))
pts=np.array(pts);labs=np.array(labs);best=None
for x in np.arange(-.006,.00601,.0005):
 for y in np.arange(-.006,.00601,.0005):
  rad=np.linalg.norm(pts[:,:2]-[x,y],axis=1);mins=[float(rad[labs==k].min())for k in range(6)];gap=max(abs(a-.0103)for a in mins);pen=max(0,.011-min(mins));score=max(0,gap-.002)**2*10+max(0,pen-.002)**2*40+(x*x+y*y)*.01
  if best is None or score<best[0]:best=(score,x,y,mins)
print('GRIP FIT',best,flush=True)
g=Matrix(json.loads((P/'work/bow_binding.json').read_text())['hand_local']);g.translation+=g.to_3x3()@Vector((best[1],best[2],0));(P/'work/round2_bow_binding.json').write_text(json.dumps({'hand_local':[list(row)for row in g],'grip_local_offset_m':[best[1],best[2],0],'surface_min_radii_m':best[3]},indent=2))
