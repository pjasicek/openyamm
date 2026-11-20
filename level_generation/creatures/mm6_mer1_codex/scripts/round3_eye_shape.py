import bpy,bmesh,sys,numpy as np,json
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common,reduction_common as C
bpy.ops.wm.open_mainfile(filepath=str(P/'work/round3/master.blend'));C.reset();o=bpy.data.objects['Body'];bm=bmesh.new();bm.from_mesh(o.data);bm.verts.ensure_lookup_table();layer=bm.verts.layers.int['piece'];rep=[]
for pid in [14,15]:
 eye=[v.co.copy()for v in bm.verts if v[layer]==pid];center=sum(eye,Vector())/len(eye);candidates=[v for v in bm.verts if v[layer]==0 and v.is_boundary and abs(v.co.x-center.x)<.033 and abs(v.co.z-center.z)<.03 and v.co.y<.015];before=[v.co.copy()for v in candidates];changes={}
 for v in candidates:
  d=v.co-center;ang=np.arctan2(d.z/.007,d.x/.018);target=v.co.copy();target.x=center.x+.018*np.cos(ang);target.z=center.z+.007*np.sin(ang);changes[v.index]=target-v.co
 # Blend the displacement into two adjacent rings; preserve existing UVs and eye aperture topology.
 ring={v.index for v in candidates};seen=set(ring)
 for factor in [1,.35,.12]:
  todo={}
  for i in ring:
   v=bm.verts[i];delta=changes[i]*factor;v.co+=delta
   for e in v.link_edges:
    n=e.other_vert(v)
    if n.index not in seen and n[layer]==0:todo.setdefault(n.index,[]).append(changes[i])
  ring=set(todo);seen|=ring
  for i,ds in todo.items():changes[i]=sum(ds,Vector())/len(ds)
 rep.append({'piece':pid,'boundary_vertices':len(candidates),'center':list(center),'aperture_half_width_m':.018,'aperture_half_height_m':.007})
bm.normal_update();bm.to_mesh(o.data);bm.free();bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/round3/master.blend'));C.activate('Standing');common.workbench_clay(bpy.context.scene,True);bpy.context.scene.display.shading.show_specular_highlight=False;common.render_views(str(P/'review/round3/eye_aperture'),1.52,.43,views=('front','left','three_quarter'),resolution=(800,800));(P/'review/round3/eye_aperture.json').write_text(json.dumps(rep,indent=2))
