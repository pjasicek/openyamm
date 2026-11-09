import bpy,sys,json,math,subprocess,os,runpy,numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));from reduction_mesh import *
from bake_reduction import rebake
from garment_margin import clear_garment
ROOT=P/'review/reduction_soft';W=P/'work/reduction_soft';ROOT.mkdir(exist_ok=True);W.mkdir(exist_ok=True)

def render(folder,level,texture_dir):
 folder.mkdir(parents=True,exist_ok=True);sc=bpy.context.scene;common.setup_render((820,820));assert sc.render.engine!='BLENDER_WORKBENCH';sc.render.film_transparent=True
 for o in list(bpy.data.objects):
  if o.type=='LIGHT':bpy.data.objects.remove(o,do_unlink=True)
 sc.world.use_nodes=True;sc.world.node_tree.nodes.get('Background').inputs['Color'].default_value=(.35,.35,.35,1);sc.world.node_tree.nodes.get('Background').inputs['Strength'].default_value=.6
 for label,pos,power in [('key',(-3,-4,6),600),('fill',(4,0,4),450),('back',(0,4,3),450)]:
  data=bpy.data.lights.new(label,'AREA');data.energy=power;data.shape='DISK';data.size=4;light=bpy.data.objects.new(label,data);sc.collection.objects.link(light);light.location=pos;light.rotation_euler=(Vector((0,0,.8))-light.location).to_track_quat('-Z','Y').to_euler()
 sc.view_settings.view_transform='Standard';sc.view_settings.look='None';sc.view_settings.exposure=0;sc.view_settings.gamma=1
 sc.render.resolution_x=820;sc.render.resolution_y=820;sc.render.resolution_percentage=100
 pixels=[700,550,220,88][level];span=1.65*820/pixels;body=bpy.data.objects['Body'];knife=bpy.data.objects['KnifeAsset'];camera_data=bpy.data.cameras.new('Metric camera');camera_data.type='ORTHO';camera_data.ortho_scale=span;camera=bpy.data.objects.new('Metric camera',camera_data);sc.collection.objects.link(camera);sc.camera=camera
 for tier in ['mfp_a','mfp_b','mfp_c']:
  originals=[]
  for mi,stem in enumerate(['mfp','mfp_head']):
   nt=body.data.materials[mi].node_tree;bs=nt.nodes.get('Principled BSDF');node=bs.inputs['Base Color'].links[0].from_node;originals.append((node,node.image));node.image=bpy.data.images.load(str(texture_dir/f'{stem}_{tier}.png'),check_existing=True);nt.nodes.active=node
  for role,t in [('Standing',0),('Attack',.4375)]:
   activate(role,t);target=Vector((0,0,.825));knife.hide_render=role=='Standing'
   for i in range(8):
    az=i*math.pi/4;camera.location=target+Vector((math.sin(az),-math.cos(az),0))*5;camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler();sc.render.filepath=str(folder/f'{tier}_{role}_{i}.png');bpy.ops.render.render(write_still=True)
  for node,image in originals:node.image=image
 knife.hide_render=False;bpy.data.objects.remove(camera,do_unlink=True)

def metrics(ref,folder):return json.loads(subprocess.run(['/usr/bin/python3',str(P/'scripts/image_metrics.py'),str(ref),str(folder)],capture_output=True,text=True,check=True).stdout)
def textures(folder,level):
 rebake(folder,[1024,512,256,128][level]);subprocess.run(['/usr/bin/python3',str(P/'scripts/bake_tiers.py'),str(folder)],check=True)
config=json.loads((W/'config.json').read_text());selection=json.loads((ROOT/'selection.json').read_text())if(ROOT/'selection.json').exists()else{}
for level in config.get('levels',[0]):
 source=P/'work/rig_textured.blend'if level==0 else P/selection[str(level-1)]['blend'];bpy.ops.wm.open_mainfile(filepath=str(source));cleanup();reset();start=triangles(bpy.data.objects['Body'])+triangles(bpy.data.objects['KnifeAsset']);reference=W/f'reference_lod{level}';reference.mkdir(exist_ok=True)
 # Source texture sets already describe the unreduced surface; copy their pixels for reference tier evaluation.
 from shutil import copyfile
 for mi,stem in enumerate(['mfp','mfp_head']):
  mat=bpy.data.objects['Body'].data.materials[mi];node=mat.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].links[0].from_node;copyfile(bpy.path.abspath(node.image.filepath),reference/f'{stem}_basecolor.png');mask=P/'textures'/f'{stem}_region_mask.png'if level==0 else Path(selection[str(level-1)]['textures'])/f'{stem}_region_mask.png';copyfile(mask,reference/f'{stem}_region_mask.png')
 subprocess.run(['/usr/bin/python3',str(P/'scripts/bake_tiers.py'),str(reference)],check=True);render(ROOT/f'lod{level}/reference',level,reference);reset();protection={}
 for name,kind in [('Body','body'),('KnifeAsset','knife')]:protection[name]=protect(bpy.data.objects[name],kind)
 baseline=W/f'lod{level}_step0.blend';bpy.ops.wm.save_as_mainfile(filepath=str(baseline));last=baseline;accepted=None;curve=[]
 for step in range(1,config.get('steps',18)+1):
  bpy.ops.wm.open_mainfile(filepath=str(last));cleanup();reset()
  for name in ['Body','KnifeAsset']:
   ob=bpy.data.objects[name]
   if level>0 or name=='Body'or triangles(ob)>1120:reduce(ob,.9,planar=step==1,factor=[1000,5,.5,.1][level])
  clearance={'applied':False};folder=W/f'lod{level}_step{step}';path=W/f'lod{level}_step{step}.blend';bpy.ops.wm.save_as_mainfile(filepath=str(path));os.environ.update(GATE_BLEND=str(path),GATE_REPORT=str(ROOT/f'lod{level}_step{step}_clothfit.json'),GATE_RENDER='0',FIT_CLOTH='1');runpy.run_path(str(P/'scripts/initial_checks.py'),run_name='__main__');os.environ.pop('FIT_CLOTH');reset();textures(folder,level);bpy.ops.wm.save_as_mainfile(filepath=str(path));counts={n:triangles(bpy.data.objects[n])for n in ['Body','KnifeAsset']};renders=ROOT/f'lod{level}/step{step}';render(renders,level,folder);scores=metrics(ROOT/f'lod{level}/reference',renders);passed=scores['pass']if level==0 else scores['pooled_iou']>=.97;gate=None
  if passed:
   from gates_summary import summarize
   report=ROOT/f'lod{level}_step{step}_gates.json';os.environ.update(GATE_BLEND=str(path),GATE_REPORT=str(report),GATE_RENDER='0');runpy.run_path(str(P/'scripts/initial_checks.py'),run_name='__main__');gate=summarize(json.loads(report.read_text()));passed=gate['pass']
  row={'garment_clearance':clearance,'rig_gate':gate,'step':step,'triangles':sum(counts.values()),'counts':counts,'visual':scores,'pass':passed,'blend':str(path.relative_to(P)),'textures':str(folder)};curve.append(row);(ROOT/f'lod{level}_curve.json').write_text(json.dumps({'initial_triangles':start,'protected':protection,'projected_height_px':[700,550,220,88][level],'steps':curve},indent=2));print('REDUCTION',level,step,counts,scores['min_iou'],scores['min_ssim'],scores['pooled_iou'],passed,flush=True)
  if not passed:break
  accepted=row;last=path
  if level>0 and sum(counts.values())<selection['0']['triangles']*[1,.50,.22,.085][level]:break
 assert accepted is not None,('No reduction step passed',level)
 selection[str(level)]=accepted;(ROOT/'selection.json').write_text(json.dumps(selection,indent=2));print('SELECTED',level,accepted['triangles'],flush=True)
