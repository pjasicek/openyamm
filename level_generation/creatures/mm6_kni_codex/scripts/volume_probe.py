import bpy,numpy as np,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/clay.blend'));body=bpy.data.objects['Body'];me=body.data
pv=np.array([d.value for d in me.attributes['piece'].data]);co=np.array([tuple(v.co) for v in me.vertices]);me.calc_loop_triangles()
for p in [0,1,4,5,7,8,9,10,100]:
 tri=np.array([t.vertices for t in me.loop_triangles if pv[t.vertices[0]]==p]);vol=np.sum(np.einsum('ij,ij->i',co[tri[:,0]],np.cross(co[tri[:,1]],co[tri[:,2]])))/6;print('VOLUME',p,vol)
