import bpy,sys,json,math
from pathlib import Path
import numpy as np
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/staff_geometry.blend'));o=bpy.data.objects['StaffMesh']
co=np.array([v.co[:] for v in o.data.vertices])
for z in [.05,.10,.15,.20,.25]:
 a=co[abs(co[:,2]-z)<.012];print('STAFF section',z,'centre',a.mean(0).tolist(),'width',np.ptp(a,axis=0).tolist())
print('STAFF triangles',sum(len(f.vertices)-2 for f in o.data.polygons))
# Bands bracket the grip; its 24 mm diameter is solved before attachment.
z=.16;a=co[abs(co[:,2]-z)<.04];centre=a.mean(0);centre[2]=z
rad=np.median(np.linalg.norm(a[:,:2]-centre[:2],axis=1));assert .002<rad<.03,rad
for v in o.data.vertices:
 v.co.x=(v.co.x-centre[0])*.012/rad;v.co.y=(v.co.y-centre[1])*.012/rad;v.co.z-=z
# Keep the original 3k topology for the hood and slender shaft; rigid LODs are reduced separately.
o.data.uv_layers.active=o.data.uv_layers[0] if o.data.uv_layers else o.data.uv_layers.new(name='UVMap')
for x in bpy.data.objects:x.select_set(x==o)
bpy.context.view_layer.objects.active=o
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=.01);bpy.ops.uv.pack_islands(margin=.01);bpy.ops.object.mode_set(mode='OBJECT')
m=bpy.data.materials.new('NeutralStaff');m.use_nodes=True;o.data.materials.clear();o.data.materials.append(m)
(P/'texturing').mkdir(exist_ok=True)
bpy.ops.export_scene.gltf(filepath=str(P/'texturing/staff_upload.glb'),use_selection=True,export_format='GLB',export_animations=False,export_skins=False)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/staff_prepared.blend'))
common.workbench_clay(bpy.context.scene);common.render_views(str(P/'review/staff_prepared'),-.16,1.55,views=('front','left','back'))
(P/'work/staff_fit.json').write_text(json.dumps({'grip_radius_m':.012,'grip_original_z':z,'transverse_scale':.012/rad,'height_m':1.34},indent=2))
