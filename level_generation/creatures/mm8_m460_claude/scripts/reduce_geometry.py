"""Reduce the weighted mesh per region, retaining hands and welded neck, then export the body paint input."""
from pathlib import Path
import bpy,bmesh,json,sys,numpy as np
from mathutils import kdtree
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(p/'work/motion_final.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];wand=bpy.data.objects['Staff'];rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis.identity()
bpy.context.view_layer.update();me=body.data
tri=lambda ob:sum(len(f.vertices)-2 for f in ob.data.polygons)
pv=[v.value for v in me.attributes['piece'].data]
keys={f.index:pv[f.vertices[0]] for f in me.polygons}
attr=me.attributes.get('reduce_region') or me.attributes.new('reduce_region','INT','FACE');attr.data.foreach_set('value',[keys[i] for i in range(len(me.polygons))])
original=body.copy();original.data=body.data.copy();original.name='BodyHigh';bpy.context.collection.objects.link(original);original.hide_set(True);original.hide_render=True
names=[g.name for g in body.vertex_groups];hand_before=[v.co.copy() for v in me.vertices if sum(e.weight for e in v.groups if 'Hand' in names[e.group] or 'Finger' in names[e.group])>.5]
targets={0:2400,1:2200,2:1200,5:240,6:160,7:80,8:80}
parts=[];report={}
for key in sorted(set(keys.values())):
 ob=body.copy();ob.data=body.data.copy();ob.name=f'Reduce_{key}';bpy.context.collection.objects.link(ob)
 bm=bmesh.new();bm.from_mesh(ob.data);region=bm.faces.layers.int['reduce_region'];bmesh.ops.delete(bm,geom=[f for f in bm.faces if f[region]!=key],context='FACES')
 loose=[v for v in bm.verts if not v.link_faces]
 if loose:bmesh.ops.delete(bm,geom=loose,context='VERTS')
 bm.to_mesh(ob.data);bm.free()
 prot=ob.vertex_groups.new(name='_protect');nms=[g.name for g in ob.vertex_groups]
 bm=bmesh.new();bm.from_mesh(ob.data);bm.verts.ensure_lookup_table();boundary={v.index for v in bm.verts if any(e.is_boundary for e in v.link_edges)};bm.free()
 for v in ob.data.vertices:
  hand=sum(e.weight for e in v.groups if 'Hand' in nms[e.group] or 'Finger' in nms[e.group])>.3
  protect=v.index in boundary or hand or (v.co.z>1.43 and abs(v.co.x)<.13)
  if protect:prot.add([v.index],1,'REPLACE')
 before=tri(ob);target=targets.get(key,before)
 if before>target:
  dec=ob.modifiers.new('Region reduction','DECIMATE');dec.ratio=target/before;dec.use_collapse_triangulate=True;dec.vertex_group='_protect';dec.invert_vertex_group=True;dec.vertex_group_factor=1000
  for o in bpy.context.view_layer.objects:o.select_set(o==ob)
  bpy.context.view_layer.objects.active=ob;bpy.ops.object.modifier_move_to_index(modifier=dec.name,index=0);bpy.ops.object.modifier_apply(modifier=dec.name)
 ob.vertex_groups.remove(ob.vertex_groups['_protect']);parts.append(ob);report[str(key)]=[before,tri(ob)]
 print('REDUCE_REGION',key,before,tri(ob),flush=True)
bpy.data.objects.remove(body,do_unlink=True);bpy.context.view_layer.update()
for o in bpy.context.view_layer.objects:o.select_set(o in parts)
bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();body=parts[0];body.name='Body'
bm=bmesh.new();bm.from_mesh(body.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-6);bm.to_mesh(body.data);bm.free()
count=len(body.data.polygons);unique={tuple(sorted(f.vertices)) for f in body.data.polygons};duplicates=count-len(unique)
fixed=body.data.validate(verbose=True,clean_customdata=False);print('BODY_VALIDATE',fixed,count,len(body.data.polygons),'duplicates',duplicates,flush=True);assert len(body.data.polygons)==count-duplicates
report['duplicate_faces_removed']=duplicates
tree=kdtree.KDTree(len(body.data.vertices))
for v in body.data.vertices:tree.insert(v.co,v.index)
tree.balance();hand_error=max(tree.find(v)[2] for v in hand_before);assert hand_error<.0002,hand_error
before=tri(wand)
for o in bpy.context.view_layer.objects:o.select_set(o==wand)
bpy.context.view_layer.objects.active=wand;dec=wand.modifiers.new('Staff reduction','DECIMATE');dec.ratio=600/before;dec.use_collapse_triangulate=True;bpy.ops.object.modifier_move_to_index(modifier=dec.name,index=0);bpy.ops.object.modifier_apply(modifier=dec.name)
report['wand']=[before,tri(wand)];report['body_total']=tri(body);report['total']=tri(body)+tri(wand);report['hand_position_error_m']=hand_error
assert report['total']<=11000,report
for ob in [body,wand]:
 for f in ob.data.polygons:f.use_smooth=True
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/rig_reduced.blend'))
(p/'review/reduction.json').write_text(json.dumps(report,indent=2)+'\n');print('REDUCED',report,flush=True)
common.workbench_clay(bpy.context.scene)
common.render_views(str(p/'review/reduced_body'),.85,1.9,views=('front','left','back','three_quarter'),resolution=(600,800))
common.render_views(str(p/'review/reduced_head'),1.50,.50,views=('front','left','back','three_quarter'),resolution=(700,700))
