import bpy,json,os,bmesh
p=os.path.dirname(os.path.dirname(__file__))
bpy.ops.wm.open_mainfile(filepath=p+'/work/st_v2_parts.blend')
for name in ('P02',):
 o=bpy.data.objects[name];bm=bmesh.new();bm.from_mesh(o.data);bm.verts.ensure_lookup_table()
 print('SPIKES',name,'long edges',[(e.verts[0].index,e.verts[1].index,round(e.calc_length(),3)) for e in bm.edges if e.calc_length()>0.12])
 for v in bm.verts:
  if v.co.z<0.36:
   print('OUTLIER',v.index,list(v.co),'neighbors',[(e.other_vert(v).index,list(e.other_vert(v).co)) for e in v.link_edges])
 bm.free()
