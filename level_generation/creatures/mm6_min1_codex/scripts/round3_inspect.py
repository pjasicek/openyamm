import bpy,bmesh,json
from pathlib import Path
P=Path(__file__).resolve().parents[1]
results={}
for file in ['production_master','round1_lod1','round1_lod2','round1_lod3','rig_v6']:
 bpy.ops.wm.open_mainfile(filepath=str(P/f'work/{file}.blend'));o=bpy.data.objects['Body'];me=o.data
 bm=bmesh.new();bm.from_mesh(me);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-6);bm.verts.ensure_lookup_table();layer=bm.verts.layers.int.get('piece')
 edges=[e for e in bm.edges if e.is_boundary];remaining=set(edges);loops=[]
 while remaining:
  seed=remaining.pop();es={seed};vs=set(seed.verts);todo=list(seed.verts)
  while todo:
   v=todo.pop()
   for e in v.link_edges:
    if e in remaining:
     remaining.remove(e);es.add(e)
     for w in e.verts:
      if w not in vs:vs.add(w);todo.append(w)
  loops.append({'edges':len(es),'min':[min(v.co[i] for v in vs) for i in range(3)],'max':[max(v.co[i] for v in vs) for i in range(3)],'piece':sorted(set(v[layer] for v in vs)) if layer else [],'branched':any(sum(e in es for e in v.link_edges)!=2 for v in vs)})
 results[file]={'verts':len(me.vertices),'faces':len(me.polygons),'attributes':[(a.name,a.domain,a.data_type) for a in me.attributes],'boundaries':len(edges),'loops':loops}
 print(file,json.dumps(results[file]),flush=True);bm.free()
(P/'review/round3/native_topology_before.json').write_text(json.dumps(results,indent=2))
