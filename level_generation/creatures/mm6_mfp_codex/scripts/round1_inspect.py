import bpy,sys,json,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/selected_lod0_polished.blend'));b=bpy.data.objects['Body'];r=bpy.data.objects['Rig'];k=bpy.data.objects['KnifeAsset'];sc=bpy.context.scene
r.animation_data.action=None
for pb in r.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.update();me=b.data;me.calc_loop_triangles();gn=[g.name for g in b.vertex_groups];W=np.zeros((len(me.vertices),len(gn)))
for v in me.vertices:
 for g in v.groups:W[v.index,g.group]=g.weight
np.savez_compressed(P/'work/round1/mesh.npz',co=np.array([v.co[:] for v in me.vertices]),normals=np.array([v.normal[:] for v in me.vertices]),tri=np.array([t.vertices[:] for t in me.loop_triangles]),uv=np.array([[me.uv_layers['UVMap'].data[i].uv[:] for i in t.loops]for t in me.loop_triangles]),mat=np.array([t.material_index for t in me.loop_triangles]),piece=np.array([v.value for v in me.attributes['piece'].data]),weights=W,names=np.array(gn))
report={'bones':{n:{'matrix':list(map(list,bo.matrix_local)),'head':list(bo.head_local),'tail':list(bo.tail_local),'parent':bo.parent.name if bo.parent else None}for n,bo in r.data.bones.items()},'attributes':[(a.name,a.domain,a.data_type)for a in me.attributes],'materials':{m.name:{n.name:n.image.filepath for n in m.node_tree.nodes if n.type=='TEX_IMAGE'and n.image}for m in me.materials}}
(P/'review/round1/inspect.json').write_text(json.dumps(report,indent=2))
for ob in list(sc.objects):
 if ob not in [b,k,r]:bpy.data.objects.remove(ob,do_unlink=True)
common.workbench_clay(sc,True)
for role,fr in [('Standing',0),('Hit',8),('Attack',10)]:
 r.animation_data.action=bpy.data.actions[role];r.animation_data.action_slot=r.animation_data.action.slots[0];sc.frame_set(fr)
 common.render_views(str(P/f'review/round1/before_{role}'),1.15,1.1,views=('front','three_quarter'),resolution=(600,800))
