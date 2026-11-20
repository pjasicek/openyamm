import bpy,sys,json,hashlib,numpy as np,math
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/export_reimport.blend'));rig=bpy.data.objects['Rig'];scene=bpy.context.scene
common.workbench_clay(scene,textured=True)
for mat in bpy.data.materials:
 if mat.node_tree:
  bs=next((n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None)
  if bs and bs.inputs['Base Color'].links:mat.node_tree.nodes.active=bs.inputs['Base Color'].links[0].from_node
# Grid belongs only to the review scene, not the creature export.
mat=bpy.data.materials.new('Review floor grid');mat.diffuse_color=(.32,.34,.36,1)
for axis in [0,1]:
 for coordinate in np.arange(-1,1.001,.1):
  bpy.ops.mesh.primitive_cube_add(size=1,location=(coordinate if axis==0 else 0,coordinate if axis==1 else 0,0));ob=bpy.context.object;ob.dimensions=(.001,2,.0005)if axis==0 else(2,.001,.0005);ob.data.materials.append(mat)
for name,t in [('Standing',0),('Fidget',1.75)]:
 a=bpy.data.actions[name];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];f=t*scene.render.fps;scene.frame_set(int(f),subframe=f%1)
 common.render_views(str(P/f'review/round2/feet_{name}'),.20,.95,views=('front','left','three_quarter'),resolution=(800,500))
# Independent exported-joint traces verify the floor repair never shifts the existing body or attack hand path.
trace={}
for tag,path in [('before',P/'work/round2_before/export/mm6_dwa1_runtime_lod0.glb'),('after',P/'export/mm6_dwa1_runtime_lod0.glb')]:
 bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(path));rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');scene=bpy.context.scene;trace[tag]={}
 for role in ['Standing','Walking','Attack','Fidget','Hit']:
  a=bpy.data.actions[role];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];duration=float(a.frame_range[1])/scene.render.fps;rows=[]
  for t in sorted(set([*np.arange(0,duration-1e-6,1/48),*np.arange(0,duration-1e-6,1/30),duration])):
   f=t*scene.render.fps;scene.frame_set(int(f),subframe=f%1);rows.append({n:list((rig.matrix_world@rig.pose.bones[n].matrix).translation)for n in ['B_Pelvis','B_Head','B_R_Forearm','B_R_Hand','B_L_Forearm','B_L_Hand','Axe']});rows[-1]['seconds']=float(t)
  trace[tag][role]=rows
report={}
for role in ['Standing','Walking','Attack','Fidget']:
 report[role]={n:max(float(np.linalg.norm(np.array(a[n])-np.array(b[n])))for a,b in zip(trace['before'][role],trace['after'][role]))for n in trace['before'][role][0]if n!='seconds'}
 assert report[role]['B_Pelvis']<1e-6 and report[role]['B_Head']<1e-6
 key={n:max(float(np.linalg.norm(np.array(a[n])-np.array(b[n])))for a,b in zip(trace['before'][role],trace['after'][role])if abs(a['seconds']*30-round(a['seconds']*30))<1e-5)for n in report[role]}
 assert max(key.values())<1e-5,(role,key)
 report[role]={'authored_key_max_delta_m':key,'playback_max_delta_m':report[role]}
new=trace['after'];report['Hit']={'duration_s':.5,'native_limit_s':.75,'endpoint_vs_standing_m':{n:float(np.linalg.norm(np.array(new['Hit'][-1][n])-new['Standing'][0][n]))for n in new['Hit'][0]if n!='seconds'},'max_displacement_from_rest_m':{n:max(float(np.linalg.norm(np.array(r[n])-new['Standing'][0][n]))for r in new['Hit'])for n in new['Hit'][0]if n!='seconds'}}
assert max(report['Hit']['endpoint_vs_standing_m'].values())<1e-5
assert report['Hit']['max_displacement_from_rest_m']['B_R_Hand']>.03 and report['Hit']['max_displacement_from_rest_m']['B_L_Hand']>.005
(P/'review/round2/joint_path_parity.json').write_text(json.dumps({'runtime_sha256':hashlib.sha256((P/'export/mm6_dwa1.glb').read_bytes()).hexdigest(),'clips':report,'pass':True},indent=2)+'\n')
