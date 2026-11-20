"""Measure the physical roller/band clearance through the complete roll."""
import bpy,sys,json,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_uv.blend'))
sys.path.insert(0,str(P/'scripts'));import motion as M
body=M.body
band=sorted({v for f in body.data.polygons if body.data.attributes['band'].data[f.index].value for v in f.vertices})
roller_groups={body.vertex_groups[r['name']].index for r in M.roller_info}
roller=sorted(v.index for v in body.data.vertices if any(g.group in roller_groups and g.weight>.99 for g in v.groups))
gap=100;floor=100
for t in np.linspace(0,1,97):
 M.pose('Walking',float(t));obj=body.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=obj.to_mesh();z=np.array([(obj.matrix_world@v.co).z for v in mesh.vertices]);obj.to_mesh_clear()
 gap=min(gap,float(z[band].min()-z[roller].max()));floor=min(floor,float(z[roller].min()))
assert gap>.015 and floor>=0,(gap,floor)
report={'samples':97,'min_band_roller_gap_m':gap,'min_roller_floor_m':floor,'radial_scale':.94,'stride_m':1.11,'corpse_height_m':json.loads((P/'work/animation_info.json').read_text())['clips']['Dead']['max_z'],'native_corpse_live_ratio':60/199}
(P/'work/contact_audit.json').write_text(json.dumps(report,indent=2));print(report)
