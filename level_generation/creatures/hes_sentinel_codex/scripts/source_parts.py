import bpy,bmesh,json
from pathlib import Path
bpy.ops.wm.read_factory_settings(use_empty=True)
p=Path(__file__).resolve().parents[1]
bpy.ops.import_scene.gltf(filepath=str(p/'source/hes_egg_mound_export.glb'))
o=next(o for o in bpy.context.scene.objects if o.type=='MESH')
bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-5)
bm.verts.ensure_lookup_table();seen=set();comps=[]
for v in bm.verts:
 if v in seen:continue
 stack=[v];seen.add(v);vs=[]
 while stack:
  w=stack.pop();vs.append(w)
  for e in w.link_edges:
   u=e.other_vert(w)
   if u not in seen:seen.add(u);stack.append(u)
 fs={f for w in vs for f in w.link_faces};lo=[min(v.co[i] for v in vs) for i in range(3)];hi=[max(v.co[i] for v in vs) for i in range(3)]
 comps.append({'id':len(comps),'vertices':[v.index for v in vs],'tris':sum(len(f.verts)-2 for f in fs),'min':lo,'max':hi,'closed':all(e.is_manifold for v in vs for e in v.link_edges)})
(p/'work/source_components.json').write_text(json.dumps(comps,indent=2)+'\n')
for c in comps:print({k:v for k,v in c.items() if k!='vertices'})
bm.free()
