import bpy,sys,json,runpy,os
import numpy as np
from pathlib import Path
from mathutils import Vector,kdtree
P=Path(__file__).resolve().parents[1];E=Path(os.environ.get('FIGC_EXPORT_DIR',str(P/'export')));W=Path(os.environ.get('FIGC_VALIDATION_DIR',str(P/'work')));W.mkdir(exist_ok=True,parents=True)
bpy.ops.wm.open_mainfile(filepath=str(E/'mm6_figc_authoring.blend'));body=bpy.data.objects['FighterChain'];base=[body.matrix_world@v.co for v in body.data.vertices];attrs={n:[d.value for d in body.data.attributes[n].data] for n in ['piece','finger']};tree=kdtree.KDTree(len(base))
for i,p in enumerate(base):tree.insert(p,i)
tree.balance()
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.context.scene.render.fps=30;bpy.ops.import_scene.gltf(filepath=str(E/'mm6_figc_lod0.glb'));rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');rig.name='Rig';body=next(o for o in bpy.data.objects if o.type=='MESH');body.name='Body';mapping=[]
for v in body.data.vertices:_,i,d=tree.find(body.matrix_world@v.co);assert d<.0001;mapping.append(i)
for n,values in attrs.items():a=body.data.attributes.new(n,'INT','POINT');a.data.foreach_set('value',[values[i] for i in mapping])
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
for name in ['Axe','Shield']:
 for o in bpy.data.objects:o.select_set(o is body)
 bpy.context.view_layer.objects.active=body;bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='DESELECT');bpy.ops.object.mode_set(mode='OBJECT');idx=body.vertex_groups[name].index
 for v in body.data.vertices:v.select=any(e.group==idx and e.weight>.99 for e in v.groups)
 before=set(bpy.data.objects);bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.separate(type='SELECTED');bpy.ops.object.mode_set(mode='OBJECT');new=next(o for o in bpy.data.objects if o not in before);new.name=name
act=bpy.data.actions['Standing'];rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];bpy.context.scene.frame_set(0);bpy.context.view_layer.update();ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();co=np.array([tuple(body.matrix_world@v.co) for v in mesh.vertices]);ev.to_mesh_clear();height=float(co[:,2].max()-co[:,2].min());scale=247*.899994/height
(W/'scale_calibration.json').write_text(json.dumps({'native_visible_height_px':247,'native_frame_scale':.899994,'native_game_height':247*.899994,'standing_height_m':height,'standing_minimum_z_m':float(co[:,2].min()),'model_scale':scale,'z_offset':-float(co[:,2].min())*scale},indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(W/'export_validation.blend'))
(P/'work/master_full_gates.json').write_bytes((P/'work/full_gates.json').read_bytes())
sys.argv=['full_gates.py','--',str(W/'export_validation.blend')];runpy.run_path(str(P/'scripts/full_gates.py'),run_name='__main__')
(W/'export_full_gates.json').write_bytes((P/'work/full_gates.json').read_bytes())
