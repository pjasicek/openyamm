from pathlib import Path
import sys,numpy as np,bpy
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'))
from common import coordinates,render
bpy.ops.wm.open_mainfile(filepath=str(P/'work/anim_v1.blend'))
m=bpy.data.objects['Wyvern'];r=bpy.data.objects['Wyvern_Rig'];r.animation_data.action=bpy.data.actions['Dead'];bpy.context.scene.frame_set(1)
co=coordinates(m);v=np.array([tuple(v.co) for v in m.data.vertices]);e=np.array([list(e.vertices) for e in m.data.edges]);rest=np.linalg.norm(v[e[:,0]]-v[e[:,1]],axis=1);length=np.linalg.norm(co[e[:,0]]-co[e[:,1]],axis=1);delta=length-rest
for i in np.argsort(delta)[-12:]:
    print('EDGE',round(float(delta[i]),4),'rest',v[e[i]].round(3).tolist(),'pose',co[e[i]].round(3).tolist(),'weights',[[(m.vertex_groups[g.group].name,round(g.weight,2)) for g in m.data.vertices[j].groups] for j in e[i]])
render('corpse_close','front',.8,(0,-.15,.07));render('corpse_close_quarter','quarter',1.2,(0,-.05,.08))
