from pathlib import Path
import bpy,json,numpy as np
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_uv.blend'))
body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];scene=bpy.context.scene
for n in ['Body','BodyHigh','HeadSource','Wand']:
 ob=bpy.data.objects.get(n)
 if ob:print('SMOOTH',n,len(ob.data.polygons),sum(f.use_smooth for f in ob.data.polygons),[(m.name,m.type) for m in ob.modifiers],flush=True)
a=bpy.data.actions['Dead'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];scene.frame_set(0);bpy.context.view_layer.update()
ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();P=np.array([tuple(v.co) for v in me.vertices]);piece=np.array([x.value for x in body.data.attributes['piece'].data]);cape=np.array([x.value for x in body.data.attributes['cape'].data]);loin=np.array([x.value for x in body.data.attributes['loin'].data])
for n,mask in [('skin',np.isin(piece,[0,2,3,4])),('cape',cape>0),('loin',loin>0),('cloth',piece==1)]:print('FLOOR',n,P[mask,2].min(),P[mask,2].max(),flush=True)
ev.to_mesh_clear()


order=np.argsort(P[:,2])[:18]
for i in order:print('LOW_VERTEX',int(i),'piece',int(piece[i]),'cape',int(cape[i]),'rest',list(body.data.vertices[i].co),'posed',P[i].tolist(),'weights',[(body.vertex_groups[e.group].name,e.weight) for e in body.data.vertices[i].groups],flush=True)
from mathutils.bvhtree import BVHTree
from mathutils import Vector
skin=np.isin(piece,[0,2,3,4]);faces=[tuple(f.vertices) for f in body.data.polygons if all(skin[i] for i in f.vertices)];tree=BVHTree.FromPolygons(P.tolist(),faces);worst=0
for i in np.flatnonzero(cape):
 loc,n,fi,d=tree.find_nearest(Vector(P[i]),.1)
 if loc is not None and (Vector(P[i])-loc).dot(n)<-.7*d:worst=max(worst,d)
print('CAPE_DEPTH',worst,flush=True)
