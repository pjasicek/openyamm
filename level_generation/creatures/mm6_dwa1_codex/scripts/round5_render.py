"""Same-camera PBR comparisons using accepted tier ramps and normal maps at the requested actor sizes."""
import bpy,sys,json,math,numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P/'scripts'));import round4_search as S
W=P/'work/round5';R=P/'review/round5';config=json.loads((W/'config.json').read_text())
def aim(ob,target):ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler()
def render(blend,folder,maps,level=0,tiers=('dwa1_a',),poses=(('Standing',0),),silhouette=False):
 bpy.ops.wm.open_mainfile(filepath=str(blend));S.cleanup();S.activate('Standing');scene=bpy.context.scene;body=bpy.data.objects['Body'];axe=bpy.data.objects['Axe']
 if silhouette:S.common.workbench_clay(scene,False);scene.display.shading.show_cavity=False;scene.display.shading.light='FLAT';scene.display.shading.color_type='SINGLE'
 else:
  scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=16;scene.cycles.use_denoising=True;scene.cycles.max_bounces=2
  scene.world=bpy.data.worlds.new('ReductionWorld');scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.55,.55,.55,1);scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.8
 scene.render.film_transparent=True;scene.render.resolution_x=800;scene.render.resolution_y=800;scene.render.resolution_percentage=100;scene.view_settings.view_transform='Standard';scene.view_settings.look='None';scene.view_settings.exposure=0;scene.view_settings.gamma=1
 # Fixed original Standing bounds determine both actor height and camera centre.
 cal=R/'camera.json'
 if cal.exists():bounds=json.loads(cal.read_text())
 else:
  ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();co=np.array([tuple(body.matrix_world@v.co)for v in me.vertices]);ev.to_mesh_clear();bounds={'z_min':float(co[:,2].min()),'z_max':float(co[:,2].max())};cal.write_text(json.dumps(bounds))
 height=bounds['z_max']-bounds['z_min'];pixels=[700,550,220,88][level];center=(0,0,(bounds['z_max']+bounds['z_min'])/2)
 for tier in tiers:
  if not silhouette:
   for ob in [body,axe]:
    for mat in ob.data.materials:
     if not mat:continue
     name=mat.name.split('.')[0];nodes=mat.node_tree.nodes;nodes.clear();out=nodes.new('ShaderNodeOutputMaterial');bs=nodes.new('ShaderNodeBsdfPrincipled');bs.inputs['Metallic'].default_value=0;bs.inputs['Specular IOR Level'].default_value=.5;mat.node_tree.links.new(bs.outputs['BSDF'],out.inputs['Surface'])
     for mode in ['base','orm','normal']:
      path=maps/f'{name}_{tier if mode=="base"else mode}.png';im=bpy.data.images.load(str(path),check_existing=True);im.colorspace_settings.name='sRGB'if mode=='base'else'Non-Color';tex=nodes.new('ShaderNodeTexImage');tex.image=im
      if mode=='base':mat.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color']);nodes.active=tex
      elif mode=='orm':
       sep=nodes.new('ShaderNodeSeparateColor');mat.node_tree.links.new(tex.outputs['Color'],sep.inputs['Color']);mat.node_tree.links.new(sep.outputs['Green'],bs.inputs['Roughness']);spec=nodes.new('ShaderNodeMath');spec.operation='MULTIPLY';spec.inputs[1].default_value=.5;mat.node_tree.links.new(sep.outputs['Red'],spec.inputs[0]);mat.node_tree.links.new(spec.outputs[0],bs.inputs['Specular IOR Level'])
      else:
       normal=nodes.new('ShaderNodeNormalMap');mat.node_tree.links.new(tex.outputs['Color'],normal.inputs['Color']);mat.node_tree.links.new(normal.outputs['Normal'],bs.inputs['Normal'])
  if config.get('albedo_only'):
   for ob in [body,axe]:
    for mat in ob.data.materials:
     if mat and mat.node_tree:
      nodes=mat.node_tree.nodes;bs=next(n for n in nodes if n.type=='BSDF_PRINCIPLED');out=next(n for n in nodes if n.type=='OUTPUT_MATERIAL');em=nodes.new('ShaderNodeEmission');mat.node_tree.links.new(bs.inputs['Base Color'].links[0].from_socket,em.inputs['Color']);mat.node_tree.links.new(em.outputs['Emission'],out.inputs['Surface'])
  for role,time in poses:
   S.activate(role,time)
   for view in range(config.get('view_count',8)):
    angle=view*math.pi/4;camdata=bpy.data.cameras.new('Camera');camdata.type='ORTHO';camdata.ortho_scale=height*800/pixels;cam=bpy.data.objects.new('Camera',camdata);scene.collection.objects.link(cam);cam.location=Vector(center)+Vector((math.sin(angle),-math.cos(angle),0))*4;aim(cam,center);scene.camera=cam
    lights=[]
    if not silhouette:
     for offset,power,size in [((2,-3,4),180,4),((-3,-1,2),75,3)]:
      x,y,z=offset;data=bpy.data.lights.new('Softbox','AREA');data.energy=power;data.shape='DISK';data.size=size;ob=bpy.data.objects.new('Softbox',data);scene.collection.objects.link(ob);ob.location=(x*math.cos(angle)-y*math.sin(angle),x*math.sin(angle)+y*math.cos(angle),z);aim(ob,center);lights.append(ob)
    folder.mkdir(parents=True,exist_ok=True);scene.render.filepath=str(folder/f'{tier}_{role}_{view}.png');bpy.ops.render.render(write_still=True)
    for ob in [cam,*lights]:bpy.data.objects.remove(ob,do_unlink=True)
 return {'actor_height_px':pixels,'viewport_px':800,'reference_height_m':height,'tier_ramps':'unchanged engine equation','normal_maps':'glTF tangent PBR'}
if __name__=='__main__':
 for job in config['render_jobs']:
  render(P/job['blend'],P/job['folder'],P/job['maps'],job.get('level',0),tuple(job.get('tiers',['dwa1_a'])),tuple(tuple(x)for x in job.get('poses',[['Standing',0]])),job.get('silhouette',False))
