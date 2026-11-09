import bpy,bmesh,json,numpy as np,sys
from pathlib import Path
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(p/'work/reduced.blend'));o=bpy.data.objects['Body'];r=bpy.data.objects['Rig']
for i in (4363,4465):print('POKE VERTEX',i,list(o.data.vertices[i].co),'piece',o.data.attributes['piece'].data[i].value)
bm=bmesh.new();bm.from_mesh(o.data);pv=bm.verts.layers.int['piece']
for part in (0,1,100):
 es={e for e in bm.edges if e.is_boundary and all(v[pv]==part for v in e.verts)}
 groups=[]
 while es:
  seed=es.pop();gr={seed};stack=list(seed.verts)
  while stack:
   v=stack.pop()
   for e in v.link_edges:
    if e in es:es.remove(e);gr.add(e);stack.extend(e.verts)
  vs={v for e in gr for v in e.verts};P=np.array([v.co[:] for v in vs])
  groups.append({'edges':len(gr),'lo':P.min(0).round(4).tolist(),'hi':P.max(0).round(4).tolist()})
 print('BOUNDARIES',part,groups)
common.workbench_clay(bpy.context.scene)
for name,f in [('Death',36),('Walking',16)]:
 a=bpy.data.actions[name];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];bpy.context.scene.frame_set(f)
 lo,hi=common.world_bounds([o]);c=(lo+hi)*.5
 common.render_views(str(p/f'review/poke_{name}_{f}'),c.z,max(hi-lo)*1.3,views=('front','left','back','three_quarter'),resolution=(900,800),target=(c.x,c.y))
