"""Validate limb edits preserve head/neck, topology, UVs, weights and safe animated bounds."""
import bpy,json,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1]
def geometry(o):
 return ([v.co[:] for v in o.data.vertices],[tuple(f.vertices) for f in o.data.polygons],
         [l.uv[:] for l in o.data.uv_layers.active.data],[f.material_index for f in o.data.polygons])
def headweights(o):
 return {v.index:{o.vertex_groups[g.group].name:g.weight for g in v.groups} for v in o.data.vertices if v.co.z>.55}
bpy.ops.wm.open_mainfile(filepath=str(P/'work/checkpoint_v4/export/mm6_drg1.blend'));old=geometry(bpy.data.objects['Body']);oldhead=headweights(bpy.data.objects['Body']);oldweights=[[(g.group,g.weight) for g in v.groups] for v in bpy.data.objects['Body'].data.vertices]
bpy.ops.wm.open_mainfile(filepath=str(P/'export/mm6_drg1.blend'));rig=bpy.data.objects['Rig'];o=bpy.data.objects['Body'];sc=bpy.context.scene
new=geometry(o)
assert new[1:]==old[1:],'Topology, UVs or materials changed'
assert all(new[0][i]==v for i,v in enumerate(old[0]) if v[2]>.55),'Approved upper neck/head geometry changed'
assert [[(g.group,g.weight) for g in v.groups] for v in o.data.vertices]==oldweights,'Skin weights changed'
assert headweights(o)==oldhead,'Approved upper neck/head weights changed'
report={'head_neck_geometry_topology_uvs_material_indices_and_weights_unchanged':True,'head_and_upper_neck_weights_unchanged':True,'clips':{}}
for name in ['Standing','Walking','Running','Fidget','Attack','Cast','Hit','Death','Dead']:
 rig.animation_data.action=bpy.data.actions[name];lo,hi=rig.animation_data.action.frame_range;mins=[];bounds=[]
 for f in np.arange(lo,hi+.1,.5):
  sc.frame_set(int(f),subframe=float(f%1));e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh();a=np.array([v.co[:] for v in m.vertices]);assert np.isfinite(a).all();mins.append(float(a[:,2].min()));bounds.append((a.min(0).tolist(),a.max(0).tolist()));e.to_mesh_clear()
 assert min(mins)>-.003,(name,min(mins))
 report['clips'][name]={'min_z':min(mins),'samples':len(mins),'start_bounds':bounds[0]}
(P/'review/limbs_v5/pose_validation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
