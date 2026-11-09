import bpy,json,numpy as np
from pathlib import Path
from mathutils import Vector
root=Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_goblin/meshy_restart_20260923/quad_remesh_trial_01')
s=bpy.data.scenes['MM6 Goblin - Quad Remesher Trial 01'];bpy.context.window.scene=s
body=s.objects['Goblin_QR_Source_DensityGuided'];bpy.ops.object.select_all(action='DESELECT');body.select_set(True);bpy.context.view_layer.objects.active=body
mesh=body.data;co=np.empty(len(mesh.vertices)*3,dtype=np.float32);mesh.vertices.foreach_get('co',co);co=co.reshape(-1,3)
x,y,z=co.T
# Qualitative density guide: white neutral, red denser, cyan coarser (documented QR convention).
colors=np.ones((len(co),4),dtype=np.float32)
def smooth(v):
 v=np.clip(v,0,1);return v*v*(3-2*v)
skirt=smooth((z+.24)/.06)*smooth((.23-z)/.06)*smooth((.31-np.abs(x))/.05)
colors[:,0]-=.85*skirt
head=smooth((z-.62)/.12)
hands=smooth((np.abs(x)-.39)/.10)*smooth((.18-z)/.10)
dense=np.maximum(head*.6,hands*.5)
colors[:,0]=np.maximum(colors[:,0],dense)
colors[:,1]-=dense;colors[:,2]-=dense
attr=mesh.color_attributes.get('QR_Density') or mesh.color_attributes.new(name='QR_Density',type='BYTE_COLOR',domain='CORNER')
indices=np.empty(len(mesh.loops),dtype=np.int32);mesh.loops.foreach_get('vertex_index',indices)
attr.data.foreach_set('color_srgb',colors[indices].reshape(-1));mesh.color_attributes.active_color=attr;mesh.color_attributes.render_color_index=list(mesh.color_attributes).index(attr)
q=s.qremesher
settings={'target_count':9000,'adaptive_size':50.,'adapt_quad_count':False,'use_vertex_color':True,'use_materials':False,'use_normals':False,'autodetect_hard_edges':False,'symmetry_x':False,'symmetry_y':False,'symmetry_z':False,'hide_input':True}
for k,v in settings.items():setattr(q,k,v)
# Small separately modeled back rivets are for baking, not runtime geometry.
for o in s.objects:
 if o.type=='MESH' and len(o.data.polygons)==100 and o is not body:o.hide_set(True);o.hide_render=True
for area in bpy.context.screen.areas:
 if area.type=='VIEW_3D':
  sp=area.spaces.active;sp.show_region_ui=True;sp.shading.type='SOLID';sp.shading.color_type='SINGLE';sp.shading.single_color=(.53,.55,.57)
  sp.region_3d.view_location=(0,0,0);sp.region_3d.view_distance=3.3;sp.region_3d.view_rotation=Vector((0,-4,0)).to_track_quat('Z','Y');sp.region_3d.view_perspective='ORTHO'
report={'scene':s.name,'selected_source':body.name,'source_triangles':sum(len(p.vertices)-2 for p in mesh.polygons),'settings':settings,'density_guide':'white neutral; pale red head/hands; cyan belt/skirt/hip region; qualitative density guide, not exact local face budgets','operation':'Prepared only. User must click Remesh It in the Quad Remesh sidebar.','notes':['Source is repaired dense master; copied into an isolated scene.','Symmetry off: pouch and other asymmetric details must retain their side.','Separate plates excluded from remesh. Separate rivets hidden for later detail baking.','Skirt is still generated source geometry; this test evaluates density guidance and does not replace deliberate clothing simplification.','No texture colors; QR_Density is only a temporary remesh guide.','Actual output triangles and deformation must be reviewed.']}
(root/'prepared_settings.json').write_text(json.dumps(report,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(root/'prepared_trial.blend'),copy=True,compress=True)
print(json.dumps(report,indent=2))
