"""Normalize the generated club to its grip axis and preserve the spiked silhouette at the prop budget."""
from pathlib import Path
import bpy,sys,json,math,numpy as np
from mathutils import Vector
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common
common.clear_scene();bpy.ops.import_scene.gltf(filepath=str(p/'meshy/club_geometry_v1/model_urls_glb.glb'))
obj=next(o for o in bpy.data.objects if o.type=='MESH')
for o in bpy.data.objects:o.select_set(o==obj)
bpy.context.view_layer.objects.active=obj;bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
co=np.array([tuple(v.co) for v in obj.data.vertices]);center=co.mean(0);axis=np.linalg.svd(co-center)[2][0]
t=(co-center)@axis;rad=np.linalg.norm(co-center-np.outer(t,axis),axis=1)
if np.quantile(rad[t<np.quantile(t,.15)],.8)>np.quantile(rad[t>np.quantile(t,.85)],.8):axis=-axis
rot=Vector(axis).rotation_difference(Vector((0,0,1)));co=np.array([tuple(rot@Vector(v-center)) for v in co]);co*=1.05/(co[:,2].max()-co[:,2].min());co[:,2]-=co[:,2].min()+.14
shaft=(co[:,2]>-.06)&(co[:,2]<.06);centre=co[shaft,:2].mean(0);co[:,:2]-=centre
radius=np.median(np.linalg.norm(co[shaft,:2],axis=1));co[:,:2]*=.025/radius
for v,c in zip(obj.data.vertices,co):v.co=c
obj.name='ClubMesh';obj.data.name='ClubMesh'
base=sum(len(f.vertices)-2 for f in obj.data.polygons)
mod=obj.modifiers.new('Prop silhouette budget','DECIMATE');mod.ratio=min(1,1400/base);bpy.ops.object.modifier_apply(modifier=mod.name)
tri=obj.modifiers.new('Final triangles','TRIANGULATE');bpy.ops.object.modifier_apply(modifier=tri.name)
obj.data.materials.clear();mat=bpy.data.materials.new('ClubNeutral');mat.use_nodes=True;obj.data.materials.append(mat)
for f in obj.data.polygons:f.use_smooth=True
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=.01);bpy.ops.object.mode_set(mode='OBJECT')
(p/'texturing').mkdir(exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/club.blend'))
bpy.ops.export_scene.gltf(filepath=str(p/'texturing/club_upload.glb'),use_selection=True,export_format='GLB',export_animations=False)
common.workbench_clay(bpy.context.scene);common.render_views(str(p/'review/club'),.385,1.2,views=('front','left','back','three_quarter'),resolution=(450,800))
report={'length_m':1.05,'grip_from_butt_m':.14,'handle_radius_m':.025,'source_triangles':base,'triangles':len(obj.data.polygons)}
(p/'work/club_geometry.json').write_text(json.dumps(report,indent=2));print('CLUB',report)
