"""Same-camera comparison of actual exports and the accepted GLB; also quantify the old fixed-ratio LODs."""
import bpy,json,math,subprocess,sys
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];R=P/'review/round3';O=R/'export_comparison';O.mkdir(exist_ok=True);sys.path.insert(0,str(P.parents[2]/'tools'))
from build_actor_lods import read_glb,write_glb
TIER_DIR=P/'work';PHYSICAL=False
cal=json.loads((R/'camera.json').read_text());reports={}
def render(path,level,label):
 bpy.ops.wm.read_factory_settings(use_empty=True);scene=bpy.context.scene;scene.render.fps=30;bpy.ops.import_scene.gltf(filepath=str(path));rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');a=bpy.data.actions['Standing'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];scene.frame_set(0)
 for mat in bpy.data.materials:
  if not mat.use_nodes:continue
  prefix='FighterChainHead_A' if 'Head' in mat.name else 'FighterChainGear_A' if 'Gear' in mat.name else 'FighterChain_A';nt=mat.node_tree;node=nt.nodes.new('ShaderNodeTexImage');node.image=bpy.data.images.load(str(TIER_DIR/f'tier_figc_a_{prefix}.png'),check_existing=True);nt.links.new(node.outputs['Color'],nt.nodes.get('Principled BSDF').inputs['Base Color']);nt.nodes.active=node
 scene.render.engine='BLENDER_WORKBENCH';sh=scene.display.shading;sh.light='STUDIO';sh.color_type='TEXTURE';sh.show_shadows=False;sh.show_cavity=False;sh.show_specular_highlight=True;scene.render.film_transparent=True;scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA';scene.view_settings.view_transform='Standard';scene.view_settings.look='None';size=[1024,768,384,192][level];pixels=[800,550,220,88][level];scene.render.resolution_x=size;scene.render.resolution_y=size;scene.render.resolution_percentage=100;scene.display.render_aa='32'
 if PHYSICAL:
  scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=32;scene.cycles.use_denoising=True;scene.render.threads_mode='FIXED';scene.render.threads=4;scene.world=bpy.data.worlds.new('comparison_world');scene.world.use_nodes=True;bg=scene.world.node_tree.nodes.get('Background');bg.inputs['Color'].default_value=(.3,.3,.3,1);bg.inputs['Strength'].default_value=.8
  ld=bpy.data.lights.new('comparison_softbox','AREA');ld.energy=120;ld.size=4;light=bpy.data.objects.new('comparison_softbox',ld);scene.collection.objects.link(light);light.location=(0,-3,4);light.rotation_euler=(Vector((0,0,1))-light.location).to_track_quat('-Z','Y').to_euler()
 center=Vector(cal['centres']['Body']);data=bpy.data.cameras.new('fixed');data.type='ORTHO';data.ortho_scale=cal['body_diameter_m']*size/pixels;cam=bpy.data.objects.new('fixed',data);scene.collection.objects.link(cam);scene.camera=cam;out=O/f'{label}_lod{level}';out.mkdir(exist_ok=True)
 for i in range(8):
  a=i*math.pi/4;cam.location=center+Vector((math.sin(a),-math.cos(a),.08))*6;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(out/f'{i}.png');bpy.ops.render.render(write_still=True)
 return out
if __name__=='__main__':
 for level in range(4):
  ref=render(R/'before/export/mm6_figc_lod0.glb',level,'reference');new=render(P/'export/mm6_figc_lod0.glb' if level==0 else R/f'export_lod{level}/mm6_figc_lod0.glb',level,'new');output=O/f'new_lod{level}.json';subprocess.run(['/usr/bin/python3',str(P/'scripts/measure_reduction.py'),str(ref),str(new),str(output)],check=True);reports[str(level)]={'new':json.loads(output.read_text())}
  if level:
   d,b=read_glb(R/'before/export/mm6_figc_lods.glb');n=next(n for n in d['nodes'] if n.get('name')=='FighterChain');n['mesh']=d['meshes'][n['mesh']]['extras']['openyamm_lods'][level-1];old=O/f'old_lod{level}.glb';write_glb(old,d,b);folder=render(old,level,'old');output=O/f'old_lod{level}.json';subprocess.run(['/usr/bin/python3',str(P/'scripts/measure_reduction.py'),str(ref),str(folder),str(output)],check=True);reports[str(level)]['old']=json.loads(output.read_text())
  print('EXPORT_VISUAL_GATE',level,{k:{x:v[x] for x in ['minimum_iou','minimum_ssim','pass']} for k,v in reports[str(level)].items()},flush=True)
 (O/'results.json').write_text(json.dumps(reports,indent=2)+'\n')
