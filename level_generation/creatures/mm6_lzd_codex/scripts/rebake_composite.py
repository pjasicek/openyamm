"""Keep the reviewed body byte-for-byte in mesh space and substitute the last passing bow."""
import bpy,bmesh,sys,json,subprocess,numpy as np,hashlib
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P/'scripts'))
from round3_candidate_gates import check
from rebake_render import render
from rebake_textures import bake
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rebake/near70final_baked.blend'));body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];keep_objects=set(bpy.data.objects);keep_actions=set(bpy.data.actions)
def signature(ob):
 me=ob.data;pv=[v.value for v in me.attributes['piece'].data];names=[g.name for g in ob.vertex_groups];rows=[]
 for f in me.polygons:
  if pv[f.vertices[0]]==201:continue
  corners=[]
  for vi,li in zip(f.vertices,f.loop_indices):
   v=me.vertices[vi];corners.append((tuple(v.co),tuple(me.uv_layers.active.data[li].uv),tuple(sorted((names[g.group],g.weight)for g in v.groups))))
  rows.append(tuple(sorted(corners)))
 return sorted(rows)
before=signature(body)
with bpy.data.libraries.load(str(P/'work/rebake/bow80_boundary_baked.blend'),link=False)as(src,dst):dst.objects=['Body']
prop=dst.objects[0];bpy.context.collection.objects.link(prop);prop.parent=None
for m in list(prop.modifiers):prop.modifiers.remove(m)
bm=bmesh.new();bm.from_mesh(prop.data);la=bm.verts.layers.int['piece'];bmesh.ops.delete(bm,geom=[v for v in bm.verts if v[la]!=201],context='VERTS');bm.to_mesh(prop.data);bm.free();material=prop.data.materials[prop.data.polygons[0].material_index]
old=next(i for i,m in enumerate(body.data.materials)if'Bow'in m.name);body.data.materials[old]=material
bm=bmesh.new();bm.from_mesh(body.data);la=bm.verts.layers.int['piece'];bmesh.ops.delete(bm,geom=[v for v in bm.verts if v[la]==201],context='VERTS');bm.to_mesh(body.data);bm.free();bpy.ops.object.select_all(action='DESELECT');body.select_set(True);prop.select_set(True);bpy.context.view_layer.objects.active=body;bpy.ops.object.join()
for ob in list(bpy.data.objects):
 if ob not in keep_objects:bpy.data.objects.remove(ob,do_unlink=True)
for a in list(bpy.data.actions):
 if a not in keep_actions:bpy.data.actions.remove(a)
assert signature(body)==before,'Reviewed body geometry/UV/skin changed'
meta=json.loads((P/'review/rebake/near70final_bake.json').read_text());meta['bow']=json.loads((P/'review/rebake/bow80_boundary_bake.json').read_text())['bow'];meta['bow']['material']=material.name
(P/'review/rebake/final0_bake.json').write_text(json.dumps(meta,indent=2));path=P/'work/rebake/final0_baked.blend';bpy.ops.wm.save_as_mainfile(filepath=str(path));r=check(path);(P/'review/rebake/final0_gates.json').write_text(json.dumps(r,indent=2));print('COMPOSITE_GATES',{k:v for k,v in r.items()if k!='motion'},r['motion']['issues'],flush=True);assert r['passed']
# Verify the material substitution on the independently animated arrow/string did not alter the body review.
render(path,'final0_body_verify',0,views=1,parts=['body'])
script="""from PIL import Image
import numpy as np,json
from pathlib import Path
P=Path(__import__('sys').argv[1]);a=np.array(Image.open(P/'review/rebake/near70final_body_l0_0.png')).astype(int);b=np.array(Image.open(P/'review/rebake/final0_body_verify_body_l0_0.png')).astype(int);r={'body_position_uv_named_weights_identical':True,'front_pixel_max_delta':int(abs(a-b).max()),'front_pixel_mean_delta':float(abs(a-b).mean()),'changed_pixels':int(np.any(a!=b,axis=2).sum())};(P/'review/rebake/body_retention.json').write_text(json.dumps(r,indent=2));print('BODY_RETAINED',r)
"""
subprocess.run(['/usr/bin/python3','-c',script,str(P)],check=True)
path=bake(P/'work/rebake/global1.blend','global1_selected',1);render(path,'global1_selected',1,parts=['actor']);metrics=json.loads(subprocess.check_output(['/usr/bin/python3',str(P/'scripts/rebake_measure.py'),'global1_selected','1','8','actor'],text=True));(P/'review/rebake/global1_selected_actor_metrics.json').write_text(json.dumps(metrics,indent=2));assert metrics['actor']['passed'],metrics
selection=json.loads((P/'review/rebake/final_selection.json').read_text());selection['0']={'tag':'final0','body_reference':'near70final','bow_reference':'bow80_boundary'};selection['1']={'tag':'global1_selected','gates':'global1_final_gates'};(P/'review/rebake/final_selection.json').write_text(json.dumps(selection,indent=2));print('FINAL_SELECTION',selection,flush=True)
