import bpy,json,bmesh,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/round4/sources.blend'));r=bpy.data.objects['Rig'];ob=bpy.data.objects['Body'];r.animation_data.action=None
for b in r.pose.bones:b.matrix_basis.identity()
bpy.context.view_layer.update();d={'bones':{b.name:{'head':list(b.head_local),'matrix':[list(x)for x in b.matrix_local]}for b in r.data.bones},'parts':{}}
pv=[a.value for a in ob.data.attributes['piece'].data]
for piece in sorted(set(pv)):
 ids=[i for i,v in enumerate(pv)if v==piece];vs=[ob.data.vertices[i].co for i in ids];d['parts'][piece]={'verts':len(ids),'lo':[min(v[k]for v in vs)for k in range(3)],'hi':[max(v[k]for v in vs)for k in range(3)]}
bm=bmesh.new();bm.from_mesh(ob.data);bm.verts.ensure_lookup_table();edges=[e for e in bm.edges if e.is_boundary];d['boundary_edges']=[{'v':[v.index for v in e.verts],'co':[list(v.co)for v in e.verts],'piece':pv[e.verts[0].index]}for e in edges];bm.free()
(P/'work/round4/structure.json').write_text(json.dumps(d,indent=2));print('BOUNDARIES',len(edges),flush=True)
