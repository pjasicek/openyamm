"""Bake each UV set separately while retaining the other surface as an occluder."""
import bpy,bmesh,runpy,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/textured_master.blend'));body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
for o in bpy.data.objects:
 if o.type=='MESH' and o is not body:o.hide_render=True
print('UV LAYERS',[(u.name,u.active_render) for u in body.data.uv_layers],flush=True)
for u in list(body.data.uv_layers):
 if u.name!='UVMap':body.data.uv_layers.remove(u)
body.data.uv_layers.active_index=0;body.data.uv_layers[0].active_render=True
parts=[]
for slot,name in [(0,'body'),(1,'head')]:
 o=body.copy();o.data=body.data.copy();o.name='Bake_'+name;bpy.context.collection.objects.link(o);bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.delete(bm,geom=[f for f in bm.faces if f.material_index!=slot],context='FACES');bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS');bm.to_mesh(o.data);bm.free();parts.append(o)
 print('AO',name,'faces',len(o.data.polygons),'UV',o.data.uv_layers.active.name,'long UV edges',sum(max((o.data.uv_layers.active.data[l].uv-o.data.uv_layers.active.data[f.loop_indices[0]].uv).length for l in f.loop_indices)>.4 for f in o.data.polygons),flush=True)
body.hide_render=True
for o,name in zip(parts,['body','head']):
 sys.argv=['bake_creature_ao.py','--',o.name,str(P/'texturing'/f'{name}_ao.png'),'.045','1024'];runpy.run_path(str(P.parent/'claude_shared/bake_creature_ao.py'),run_name='__main__')
