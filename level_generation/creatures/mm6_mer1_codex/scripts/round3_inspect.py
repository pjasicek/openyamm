import bpy,sys,json,math
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/round2/master.blend'));s=bpy.context.scene;r=bpy.data.objects['Rig'];b=bpy.data.objects['Body'];common.workbench_clay(s,True)
info={'materials':[(m.name,[(n.name,n.image.filepath if n.image else None)for n in m.node_tree.nodes if n.type=='TEX_IMAGE'])for m in b.data.materials],'parts':{}}
pv=[v.value for v in b.data.attributes['piece'].data]
for pid in set(pv):info['parts'][pid]={'vertices':pv.count(pid),'triangles':sum(len(f.vertices)-2 for f in b.data.polygons if pv[f.vertices[0]]==pid)}
(P/'review/round3/high_info.json').write_text(json.dumps(info,indent=2))
for role,t in [('Standing',0),('Attack',.375),('Death',1.3)]:
 a=bpy.data.actions[role];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];s.frame_set(int(t*30),subframe=t*30%1)
 common.render_views(str(P/'review/round3'/('high_'+role)),1.1,1.35,views=('front','left','three_quarter'),resolution=(800,900))
 if role=='Standing':
  ev=b.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();coords=[v.co.copy() for v in me.vertices];ev.to_mesh_clear()
  for name,ids,scale in [('face',[i for i,x in enumerate(pv)if x in [0,11,14,15]],.43),('hand',[i for i,x in enumerate(pv)if x==3],.23)]:
   center=sum((coords[i] for i in ids),Vector())/len(ids)
   common.render_views(str(P/'review/round3'/('high_'+name)),center.z,scale,views=('front','left','three_quarter'),target=(center.x,center.y),resolution=(800,800))

