"""Final authoring geometry, UV, weights and packed-map checks."""
from pathlib import Path
import bpy, numpy as np, json
P=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(P/'delivery/mm6_flying_demon.blend'))
scene=bpy.context.scene;report={'meshes':{},'images':[]};uv_dump={}
for o in scene.objects:
 if o.type!='MESH':continue
 m=o.data;role=o.get('material_role');living=role not in ('death_effect',None) and 'Ash' not in o.name
 invalid=m.validate(verbose=True,clean_customdata=False);assert not invalid,o.name
 assert all(np.isfinite(v.co).all() for v in m.vertices),o.name
 row={'vertices':len(m.vertices),'triangles':len(m.polygons),'role':role,'validation_required_repairs':invalid}
 if living:
  weights=[sum(g.weight for g in v.groups) for v in m.vertices]
  row.update(unweighted_vertices=sum(w<.999 for w in weights),maximum_weight_sum_error=max(abs(w-1) for w in weights),maximum_influences=max(sum(g.weight>1e-7 for g in v.groups) for v in m.vertices))
  assert row['unweighted_vertices']==0 and row['maximum_weight_sum_error']<1e-5 and row['maximum_influences']<=8,(o.name,row)
  uv=m.uv_layers.active.data;coords=np.array([[tuple(uv[i].uv) for i in f.loop_indices] for f in m.polygons])
  a,b=coords[:,1]-coords[:,0],coords[:,2]-coords[:,0];areas=abs(a[:,0]*b[:,1]-a[:,1]*b[:,0])/2
  row.update(degenerate_uv_triangles=int(sum(areas<1e-11)),uv_bounds=[coords.min(axis=(0,1)).tolist(),coords.max(axis=(0,1)).tolist()],uv_area=float(areas.sum()))
  assert row['degenerate_uv_triangles']==0,(o.name,row)
  assert coords.min()>=0 and coords.max()<=1,(o.name,'UV outside atlas')
  # Pupil/iris/bone constant materials do not consume body PBR texture space.
  indices=[f.index for f in m.polygons if f.material_index==0]
  uv_dump[o.name]=coords[indices]
 report['meshes'][o.name]=row
for im in bpy.data.images:
 if im.users and im.source=='FILE':
  assert im.packed_file,im.name
  report['images'].append({'name':im.name,'size':list(im.size),'packed':True,'packed_bytes':im.packed_file.size,'color_space':im.colorspace_settings.name})
assert len(bpy.data.scenes)==1,len(bpy.data.scenes)
report['living_triangles']=sum(v['triangles'] for v in report['meshes'].values() if v['role'] not in ('death_effect',None))
report['rig_joints']=len(next(o for o in scene.objects if o.type=='ARMATURE').data.bones)
report['scene_count']=len(bpy.data.scenes)
np.savez_compressed(P/'work/final_uv_triangles.npz',**uv_dump)
(P/'review/geometry_validation.json').write_text(json.dumps(report,indent=2)+'\n')
print('Final living mesh',report['living_triangles'],'triangles;',report['rig_joints'],'joints;',len(report['images']),'packed image maps.',flush=True)

# Temporary UV-checker material; the packed delivery master stays untouched.
checker=bpy.data.materials.new('Temporary_UV_Checker');checker.use_nodes=True
n=checker.node_tree.nodes;links=checker.node_tree.links;texture=n.new('ShaderNodeTexChecker')
texture.inputs['Color1'].default_value=(.16,.16,.16,1);texture.inputs['Color2'].default_value=(.8,.8,.8,1);texture.inputs['Scale'].default_value=50
coord=n.new('ShaderNodeTexCoord');links.new(coord.outputs['UV'],texture.inputs['Vector']);links.new(texture.outputs['Color'],n.get('Principled BSDF').inputs['Base Color'])
for o in scene.objects:
 if o.get('material_role') in ('body','wing','wing_strut'):o.data.materials[0]=checker
scene.frame_set(6);scene.render.resolution_x=scene.render.resolution_y=640
scene.render.image_settings.file_format='JPEG';scene.render.image_settings.quality=92
from mathutils import Vector
for view,direction in [('front',(0,-6,0)),('profile',(6,0,0)),('back',(0,6,0))]:
 direction=Vector(direction);scene.camera.location=Vector((0,.12,1.1))+direction
 scene.camera.rotation_euler=(-direction).to_track_quat('-Z','Y').to_euler();scene.camera.data.ortho_scale=3.1
 scene.render.filepath=str(P/'review'/('checker_'+view+'.jpg'));bpy.ops.render.render(write_still=True)
