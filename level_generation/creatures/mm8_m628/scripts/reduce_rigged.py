"""Reduce weighted components, retaining rigid bone pieces, five fingers and the bow silhouette."""
import bpy,bmesh,json,sys
from pathlib import Path
import numpy as np
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/motion_complete.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis.identity()
bpy.context.view_layer.update();me=body.data
before=sum(len(f.vertices)-2 for f in me.polygons)
targets={0:1300,1:350,3:120,4:160,5:450,6:140,7:130,8:130,9:220,10:130,11:130,
    13:140,14:100,15:140,16:100,17:90,18:100,19:110,2000:2100,2001:350,2002:180,2003:180,
    4000:1000,4003:180,4004:520}
pieces=sorted({v.value for v in me.attributes['piece'].data});parts=[];report={}
for pid in pieces:
    bm=bmesh.new();bm.from_mesh(me);pl=bm.verts.layers.int['piece']
    bmesh.ops.delete(bm,geom=[v for v in bm.verts if v[pl]!=pid],context='VERTS')
    bmesh.ops.triangulate(bm,faces=list(bm.faces));mesh=bpy.data.meshes.new(f'Piece{pid}');bm.to_mesh(mesh);bm.free()
    ob=bpy.data.objects.new(mesh.name,mesh);bpy.context.collection.objects.link(ob)
    for g in body.vertex_groups:ob.vertex_groups.new(name=g.name)
    for mat in me.materials:mesh.materials.append(mat)
    n=len(mesh.polygons)
    target=targets.get(pid,n if pid>=4000 else max(16,round(n*(.65 if 3000<=pid<4000 else .32))))
    if n>target:
        bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
        mod=ob.modifiers.new('Budget','DECIMATE');mod.ratio=target/n;mod.use_collapse_triangulate=True
        bpy.ops.object.modifier_apply(modifier=mod.name)
    report[str(pid)]={'before':n,'after':len(ob.data.polygons)};parts.append(ob)
    assert len(ob.data.polygons)>=4,(pid,len(ob.data.polygons))
oldname=body.name;bpy.data.objects.remove(body,do_unlink=True)
bpy.ops.object.select_all(action='DESELECT')
for ob in parts:ob.select_set(True)
bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();body=bpy.context.object;body.name=oldname
body.parent=rig;mod=body.modifiers.new('Armature','ARMATURE');mod.object=rig
for v in body.data.vertices:
    total=sum(g.weight for g in v.groups);assert total>0
    for g in v.groups:body.vertex_groups[g.group].add([v.index],g.weight/total,'REPLACE')
assert all(abs(sum(g.weight for g in v.groups)-1)<1e-4 for v in body.data.vertices)
after=len(body.data.polygons);assert after<before*.5,(before,after)
(P/'work/reduction.json').write_text(json.dumps({'before':before,'after':after,'components':report},indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_reduced.blend'))
common.workbench_clay(bpy.context.scene)
for name,f in [('Standing',0),('Attack',25),('Death',31)]:
    a=bpy.data.actions[name];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0]
    bpy.context.scene.frame_set(f)
    common.render_views(str(P/f'review/reduced_{name}'),1.0,2.55,
        views=('front','left','three_quarter'),resolution=(450,675))
print('REDUCED',before,'to',after)
