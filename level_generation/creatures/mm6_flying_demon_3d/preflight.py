from pathlib import Path
import json, bpy, numpy as np
P=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(P/'work/texturing_master.blend'))
scene=bpy.context.scene;report={}
for o in scene.objects:
 if o.type!='MESH' or o.get('material_role')=='death_effect' or 'Ash' in o.name: continue
 m=o.data;uv=m.uv_layers.active.data;areas=[];groups={}
 for face in m.polygons:
  q=np.array([uv[i].uv for i in face.loop_indices]);area=abs(np.cross(q[1]-q[0],q[2]-q[0]))/2
  areas.append(float(area));groups[face.material_index]=groups.get(face.material_index,0)+int(area<1e-10)
 invalid=m.validate(verbose=True,clean_customdata=False)
 report[o.name]={'vertices':len(m.vertices),'triangles':len(m.polygons),'validation_required_repairs':invalid,'degenerate_uv_by_material':groups,
 'uv_area':float(sum(areas)), 'non_finite_vertices':sum(not all(np.isfinite(v.co)) for v in m.vertices),
 'unweighted_vertices':sum(sum(g.weight for g in v.groups)<.99 for v in m.vertices)}
 print('CHECK',o.name,report[o.name],flush=True)
(P/'work/preflight.json').write_text(json.dumps(report,indent=2)+'\n')
