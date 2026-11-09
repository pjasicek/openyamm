"""Join independently measured body/bow choices; export the exact accepted LOD geometry."""
import bpy,bmesh,json,sys,shutil
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True
selected=json.loads((P/'review/reduction/selected.json').read_text());roles={'Standing','Fidget','Walking','Running','Attack','Cast','Hit','Death','Dead'}
def keep(ob,bow):
 bm=bmesh.new();bm.from_mesh(ob.data);layer=bm.verts.layers.int['piece'];bmesh.ops.delete(bm,geom=[f for f in bm.faces if all(v[layer]==201 for v in f.verts)!=bow],context='FACES');bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS');bm.to_mesh(ob.data);bm.free()

def ground_corpse(rig,body):
 import numpy as np,math
 from mathutils import Vector
 sc=bpy.context.scene;pv=np.array([x.value for x in body.data.attributes['piece'].data]);root=rig.pose.bones['B_Pelvis'];inverse=rig.data.bones[root.name].matrix_local.to_3x3().inverted()
 for role in ['Death','Dead']:
  a=bpy.data.actions[role];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];N=int(a.frame_range[1]);positions=[];offset=np.full(N+1,-1e9)
  for f in range(N+1):sc.frame_set(f);positions.append(root.location.copy())
  for tick in range(N*4+1):
   f=tick/4;sc.frame_set(int(f),subframe=f%1);ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();low=min(v.co.z for v in me.vertices if pv[v.index]!=202);ev.to_mesh_clear()
   for i in {int(f),min(N,math.ceil(f))}:offset[i]=max(offset[i],.0004-low)
  for f,p in enumerate(positions):root.location=p+inverse@Vector((0,0,float(offset[f])));root.keyframe_insert('location',frame=f)
 rig.animation_data.action=None
 for b in rig.pose.bones:b.matrix_basis.identity()
 bpy.context.view_layer.update()

for level in range(4):
 bpy.ops.wm.open_mainfile(filepath=str(P/selected['body'][str(level)]['blend']));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];keep(body,False);actions=set(bpy.data.actions);objects=set(bpy.data.objects);bowmat=next(m for m in body.data.materials if m.name.split('.')[0]=='LizardBow_A')
 with bpy.data.libraries.load(str(P/selected['bow'][str(level)]['blend']),link=False)as(src,dst):dst.objects=['Body']
 bow=dst.objects[0];bpy.context.scene.collection.objects.link(bow);keep(bow,True);bow.data.materials.clear();bow.data.materials.append(bowmat)
 for f in bow.data.polygons:f.material_index=0
 for m in bow.modifiers:
  if m.type=='ARMATURE':m.object=rig
 bpy.ops.object.select_all(action='DESELECT')
 for o in [body,bow]:o.select_set(True);o.hide_render=False
 bpy.context.view_layer.objects.active=body;bpy.ops.object.join();body.name='Body'
 for o in list(bpy.data.objects):
  if o not in objects:bpy.data.objects.remove(o,do_unlink=True)
 for a in list(bpy.data.actions):
  if a not in actions:bpy.data.actions.remove(a)
 rig.animation_data.action=None
 for b in rig.pose.bones:b.matrix_basis.identity()
 bpy.context.view_layer.update()
 for mat in body.data.materials:
  if mat.use_nodes:
   bs=mat.node_tree.nodes.get('Principled BSDF')
   if bs:
    bs.inputs['Specular IOR Level'].default_value=.5;bs.inputs['Specular Tint'].default_value=(1,1,1,1);bs.inputs['IOR'].default_value=1.5
 ground_corpse(rig,body)
 path=P/f'work/round3_reduction/lod{level}.blend';bpy.ops.wm.save_as_mainfile(filepath=str(path))
 if level==0:shutil.copy2(path,P/'work/master.blend')
 else:
  bpy.ops.object.select_all(action='DESELECT');body.select_set(True);rig.select_set(True);body.name=body.data.name='Lizard';bpy.context.view_layer.objects.active=rig
  bpy.ops.export_scene.gltf(filepath=str(P/f'export/mm6_lzd_level{level}.glb'),use_selection=True,export_format='GLB',export_yup=True,export_animations=False,export_skins=True,export_all_influences=True,export_attributes=False,export_morph=False,export_image_format='AUTO')


 if level==0:
  sys.path.insert(0,str(P/'scripts'));import common
  rig.animation_data.action=bpy.data.actions['Dead'];rig.animation_data.action_slot=rig.animation_data.action.slots[0];bpy.context.scene.frame_set(0)
  ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();pieces=[x.value for x in body.data.attributes['piece'].data]
  (P/'review/corpse_floor.json').write_text(json.dumps({'body_floor_m':min(v.co.z for v in me.vertices if pieces[v.index]<201),'bow_floor_m':min(v.co.z for v in me.vertices if pieces[v.index]==201)},indent=2));ev.to_mesh_clear()
  common.workbench_clay(bpy.context.scene,True);common.render_views(str(P/'review/round3_corpse'),.35,2.7,views=('front','left','three_quarter'),resolution=(900,650))

# Certify the exact joined body + bow geometry, once per unique measured pair.
 if level==0:gate_cache={}
 pair=(selected['body'][str(level)]['blend'],selected['bow'][str(level)]['blend'])
 if pair not in gate_cache:
  sys.path.insert(0,str(P/'scripts'))
  from round3_candidate_gates import check
  gate_cache[pair]=check(path)
 (P/f'review/reduction/lod{level}_combined_gates.json').write_text(json.dumps(gate_cache[pair],indent=2))
 assert gate_cache[pair]['passed'],(level,gate_cache[pair])

print('MEASURED_LODS_EXPORTED')
