import bpy,bmesh,sys,json,math,subprocess,runpy,numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P/'scripts'));import common,reduction_common as C,reduction_bake as B
W=P/'work/reduction';O=P/'review/reduction';W.mkdir(exist_ok=True);O.mkdir(exist_ok=True)
def render(folder,kind,level,texfolder=None,tiers=None):
 folder.mkdir(parents=True,exist_ok=True);s=bpy.context.scene;common.workbench_clay(s,True);s.display.shading.show_specular_highlight=False;
 s.render.engine='BLENDER_EEVEE';s.world.use_nodes=True;s.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.65,.65,.65,1);s.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.5
 if hasattr(s,'eevee') and hasattr(s.eevee,'taa_render_samples'):s.eevee.taa_render_samples=16
 for o in list(bpy.data.objects):
  if o.type=='LIGHT':bpy.data.objects.remove(o,do_unlink=True)
 for pos,power in [((4,-4,5),500),((-3,-1,3),300),((0,3,4),400)]:
  data=bpy.data.lights.new('Review softbox','AREA');data.energy=power;data.shape='DISK';data.size=5;light=bpy.data.objects.new('Review softbox',data);s.collection.objects.link(light);light.location=pos;light.rotation_euler=(Vector((0,0,.85))-light.location).to_track_quat('-Z','Y').to_euler()
 s.render.film_transparent=True;s.display.render_aa='16';s.render.resolution_x=820;s.render.resolution_y=820;s.render.resolution_percentage=100
 body=bpy.data.objects['Body'];prop=bpy.data.objects['ClubMesh'];body.hide_render=kind!='body';prop.hide_render=kind!='club';mat=body.data.materials[0];bs=mat.node_tree.nodes.get('Principled BSDF');node=bs.inputs['Base Color'].links[0].from_node;original=node.image
 for m in [*body.data.materials,*prop.data.materials]:
  bs=m.node_tree.nodes.get('Principled BSDF');m.node_tree.nodes.active=bs.inputs['Base Color'].links[0].from_node
 poses=[('Standing',0),('Running',.12),('Attack',.791667),('Death',.6)]if kind=='body'else[('Standing',0)]
 scale=1.7*820/700 if level==0 else 1.94*820/[0,550,220,88][level]
 for tier in (tiers or (['a','b','c']if kind=='body'else['a'])):
  if kind=='body':node.image=bpy.data.images.load(str((texfolder if texfolder else P/'textures')/f'mer1_{tier}_preview.png'),check_existing=True)
  for role,t in poses:
   C.activate(role,t)
   for i in range(8):
    angle=i*math.pi/4;target=Vector((0,0,.85));cam=common.ortho_camera('Reduction camera',tuple(target+Vector((math.sin(angle),-math.cos(angle),0))*6),(math.pi/2,0,angle),scale);s.camera=cam;s.render.filepath=str(folder/f'{tier}_{role}_{i}.png');bpy.ops.render.render(write_still=True);bpy.data.objects.remove(cam,do_unlink=True)
 node.image=original;body.hide_render=False;prop.hide_render=False
 return {'actor_height_px_lod0':700,'viewport_px':820,'orthographic_scale_m':scale,'switch_pixels':[None,550,220,88][level]}
def metrics(ref,cur):return json.loads(subprocess.run(['/usr/bin/python3',str(P/'scripts/reduction_metrics.py'),str(ref),str(cur)],check=True,capture_output=True,text=True).stdout)
def gates(path,tag):
 bpy.ops.wm.open_mainfile(filepath=str(path));rig=bpy.data.objects['Rig'];rig.animation_data.action=None;old=bpy.data.actions.get('Death')
 if old:bpy.data.actions.remove(old)
 with bpy.data.libraries.load(str(P/'work/reduction_master.blend'),link=False)as(src,dst):dst.actions=['Death']
 dst.actions[0].name='Death';dst.actions[0].use_fake_user=True;bpy.ops.wm.save_as_mainfile(filepath=str(path))
 for name in ['elbow_gate.py','audit_motion.py','candidate_palms.py','candidate_prop.py']:
  suffix={'elbow_gate.py':'elbow_gate','candidate_palms.py':'palms','candidate_prop.py':'prop'}.get(name)
  if suffix and (P/'review'/f'{tag}_{suffix}.json').exists():continue
  sys.argv=[name,'--',str(path.relative_to(P)),tag];runpy.run_path(str(P/'scripts'/name),run_name='__main__')
 surface=json.loads((P/'review'/f'{tag}_surface_gates.json').read_text());prop=json.loads((P/'review'/f'{tag}_prop.json').read_text());palms=json.loads((P/'review'/f'{tag}_palms.json').read_text())
 summary={k:max(r[k]for r in surface.values())for k in ['G4_arm_p99','G5_hand_max','G6_hand_body_mm','G6_forearm_body_mm','cloth_leg_mm','sleeve_hand_mm']};summary['prop_penetration_mm']=max(r['head_body_penetration_mm']for r in prop.values());summary['free_palm_angle_max_deg']=max(max(palms[k]['max'])for k in ['Standing','Walking','Running','Fidget']);elbows=json.loads((P/'review'/f'{tag}_elbow_gate.json').read_text());summary['elbows_pass']=all(sd['pass']for role in elbows['clips'].values()for sd in role.values());summary['pass']=summary['elbows_pass']and summary['G4_arm_p99']<2 and summary['G5_hand_max']<4.5 and max(summary[k]for k in ['G6_hand_body_mm','G6_forearm_body_mm','cloth_leg_mm','sleeve_hand_mm','prop_penetration_mm'])<2 and summary['free_palm_angle_max_deg']<45
 return summary
def search(kind,level,steps):
 tag=f'{kind}_lod{level}';source=P/'work/reduction_master.blend';bpy.ops.wm.open_mainfile(filepath=str(source));C.cleanup();C.reset();obj=bpy.data.objects['Body'if kind=='body'else'ClubMesh'];count0=C.triangles(obj);reference=O/tag/'reference';camera=render(reference,kind,level);C.reset();protection=C.protect(obj,'body'if kind=='body'else'club');base=W/f'{tag}_0.blend';bpy.ops.wm.save_as_mainfile(filepath=str(base));last=base;curve=[]
 for step in range(1,steps+1):
  bpy.ops.wm.open_mainfile(filepath=str(last));C.reset();obj=bpy.data.objects['Body'if kind=='body'else'ClubMesh'];
  if step==1 and kind=='body':
   bm=bmesh.new();bm.from_mesh(obj.data);layer=bm.verts.layers.int['piece'];hidden=[v for v in bm.verts if v[layer]==5];bmesh.ops.delete(bm,geom=hidden,context='VERTS');bm.to_mesh(obj.data);bm.free();print('REMOVED covered trouser vertices',len(hidden),flush=True)
  C.reduce(obj,.9,planar=step==1);count=C.triangles(obj);dest=W/f'{tag}_{step}.blend';tex=W/f'{tag}_{step}_textures';B.bake(obj,tex)
  if kind=='body':subprocess.run(['/usr/bin/python3',str(P/'scripts/reduction_previews.py'),str(tex)],check=True)
  bpy.ops.wm.save_as_mainfile(filepath=str(dest));folder=O/tag/f'step_{step:02}';render(folder,kind,level,tex if kind=='body'else None);visual=metrics(reference,folder);row={'step':step,'triangles':count,'ratio_to_original':count/count0,'blend':str(dest.relative_to(P)),'textures':str(tex.relative_to(P)),'visual':visual}
  if visual['pass']:row['gates']=gates(dest,tag+f'_s{step}')
  row['pass']=visual['pass']and row.get('gates',{}).get('pass',False);curve.append(row);receipt={'kind':kind,'level':level,'before':count0,'reference':str(source.relative_to(P)),'camera':camera,'protection':protection,'steps':curve,'accepted':str(last.relative_to(P))}
  if row['pass']:last=dest;receipt['accepted']=str(last.relative_to(P))
  (O/f'{tag}_curve.json').write_text(json.dumps(receipt,indent=2));print('REDUCTION',tag,step,count,'IoU',visual['min_iou'],'SSIM',visual['min_ssim'],'pass',row['pass'],flush=True)
  if not row['pass'] or (step>1 and count==curve[-2]['triangles']):break
if __name__=='__main__':
 config=json.loads((W/'config.json').read_text())
 for job in config['jobs']:search(job['kind'],job['level'],job.get('steps',20))
