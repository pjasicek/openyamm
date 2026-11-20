import bpy,sys,json,numpy as np
from pathlib import Path
from mathutils import Vector
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(p/'work/all_body.blend'))
ob=bpy.data.objects['Body'];r=bpy.data.objects['Rig'];me=ob.data
pv=np.array([a.value for a in me.attributes['piece'].data])
me.calc_loop_triangles()
for part in (3,4):
 ts=[t for t in me.loop_triangles if all(pv[i]==part for i in t.vertices)]
 c=np.array([v.co[:] for v in me.vertices if pv[v.index]==part]).mean(0)
 vol=sum(np.dot(np.array(me.vertices[t.vertices[0]].co)-c,np.cross(np.array(me.vertices[t.vertices[1]].co)-c,np.array(me.vertices[t.vertices[2]].co)-c))/6 for t in ts)
 print('SIGNED_VOLUME',part,vol)
for i in (90,2581,5,1507):
 print('WEIGHT',i,me.vertices[i].co[:],[(ob.vertex_groups[g.group].name,round(g.weight,3)) for g in me.vertices[i].groups])
common.workbench_clay(bpy.context.scene)
for name,f,z,h,target in [('Standing',0,1.12,.7,(0,-.13)),('Death',60,.34,.85,(0,-.65)),('Hit',5,1.1,.9,(0,-.12))]:
 a=bpy.data.actions[name];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];bpy.context.scene.frame_set(f)
 common.render_views(str(p/f'review/detail_{name}'),z,h,views=('front','left','three_quarter'),resolution=(700,700),target=target)
 print(name,'HAND',[(s,r.pose.bones[f'B_{s}_Hand'].head[:]) for s in 'LR'])
