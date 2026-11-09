from pathlib import Path
import bpy,sys,runpy,os,numpy as np,json,math,bmesh
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common
os.environ['FA']='.6';os.environ['FA_RAMP']='.15,.85'
s=p/'scripts/twist_bones.py';sys.argv=[str(s),'--',str(p/'work/pilot_raw.blend'),str(p/'work/rig_twist.blend')];runpy.run_path(str(s),run_name='__main__')
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.update();me=body.data
# Keep the neck trim and arm band rigid after twist weights are distributed.
for v in me.vertices:
 piece=me.attributes['piece'].data[v.index].value;bone='B_R_UpperArm' if piece==2 else 'B_Spine2' if 3<=piece<=8 else None
 if bone:
  for ge in list(v.groups):body.vertex_groups[ge.group].remove([v.index])
  body.vertex_groups[bone].add([v.index],1,'REPLACE')
# Protect the single eye, mouth, profile and hands; broad body planes carry the reduction.
headv={vi for f in me.polygons if me.attributes['head'].data[f.index].value for vi in f.vertices}
boundary=set();uses={}
for f in me.polygons:
 for vi in f.vertices:uses.setdefault(vi,set()).add(me.attributes['head'].data[f.index].value)
boundary={vi for vi,values in uses.items() if len(values)>1}
vg=body.vertex_groups.new(name='Reduction');fingerids={g.index for g in body.vertex_groups if 'Hand' in g.name or 'Finger' in g.name}
for v in me.vertices:
 protect=v.index in boundary or any(g.group in fingerids and g.weight>.1 for g in v.groups) or (v.index in headv and v.co.y<.03)
 vg.add([v.index],0.0 if protect else 1.,'REPLACE')
tris=lambda:sum(len(f.vertices)-2 for f in body.data.polygons);before=tris()
for ob in bpy.data.objects:ob.select_set(ob==body)
bpy.context.view_layer.objects.active=body
mod=body.modifiers.new('Budget','DECIMATE');mod.ratio=.76;mod.vertex_group='Reduction';mod.vertex_group_factor=1
bpy.ops.object.modifier_move_to_index(modifier=mod.name,index=0);bpy.ops.object.modifier_apply(modifier=mod.name)
body.vertex_groups.remove(body.vertex_groups['Reduction']);me=body.data
report={'before':before,'after':tris(),'protected':'face profile, single eye, lips, hands, neck texture boundary'};assert 15000<tris()<21000,report
print('BUDGET',report,flush=True);(p/'work/budget.json').write_text(json.dumps(report,indent=2))
# Use the existing face region and reserve its own UV map for the detailed head pass.
for ob in bpy.data.objects:ob.select_set(ob==body)
bpy.context.view_layer.objects.active=body
if 'HeadUV' not in me.uv_layers:me.uv_layers.new(name='HeadUV')
me.uv_layers.active=me.uv_layers['HeadUV']
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='DESELECT');bpy.ops.object.mode_set(mode='OBJECT')
for f in me.polygons:f.select=bool(me.attributes['head'].data[f.index].value)
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=.012);bpy.ops.uv.pack_islands(margin=.012);bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/rig_surface.blend'))
(p/'texturing').mkdir(exist_ok=True)
for kind in ['body','head']:
 ob=body.copy();ob.data=body.data.copy();bpy.context.scene.collection.objects.link(ob);ob.parent=None;ob.matrix_world=body.matrix_world.copy();ob.modifiers.clear();ob.vertex_groups.clear()
 if kind=='head':
  bm=bmesh.new();bm.from_mesh(ob.data);layer=bm.faces.layers.int['head'];bmesh.ops.delete(bm,geom=[f for f in bm.faces if not f[layer]],context='FACES');bm.to_mesh(ob.data);bm.free()
 uv='HeadUV' if kind=='head' else 'UVMap'
 for layer in list(ob.data.uv_layers):
  if layer.name!=uv:ob.data.uv_layers.remove(layer)
 ob.data.materials.clear();mat=bpy.data.materials.new('Neutral');mat.use_nodes=True;ob.data.materials.append(mat)
 for f in ob.data.polygons:f.material_index=0
 for obj in bpy.data.objects:obj.select_set(obj==ob)
 bpy.context.view_layer.objects.active=ob
 bpy.ops.export_scene.gltf(filepath=str(p/f'texturing/m520_{kind}_upload.glb'),use_selection=True,export_format='GLB',export_yup=True,export_animations=False,export_skins=False,export_morph=False,export_attributes=False)
 bpy.data.objects.remove(ob,do_unlink=True)
common.workbench_clay(bpy.context.scene)
common.render_views(str(p/'review/reduced_body'),1.2,2.7,views=('front','left','back','three_quarter'),resolution=(650,850))
common.render_views(str(p/'review/reduced_head'),2.2,.5,views=('front','left','three_quarter'),resolution=(700,700))
