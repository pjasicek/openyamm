"""Reduce after weighting, freeze triangulation, unwrap the face, and export static texture handoffs."""
import bpy,json,sys,hashlib
from pathlib import Path
from mathutils import Matrix
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(Path('level_generation/creatures/mm6_bar1_claude/scripts').resolve()))
import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/pilots.blend'))
rig=bpy.data.objects['Rig'];rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis=Matrix.Identity(4)
body=bpy.data.objects['Body'];head=bpy.data.objects['Head'];report={}
for o in [body,head]:
 bpy.context.view_layer.objects.active=o;bpy.ops.object.select_all(action='DESELECT');o.select_set(True)
 before=sum(len(p.vertices)-2 for p in o.data.polygons)
 if o==body:
    prot=o.vertex_groups.new(name='_protect');gids={g.index for g in o.vertex_groups if any(x in g.name for x in ['Hand','Finger','Foot','Toe','Neck'])}
    for v in o.data.vertices:
        if sum(g.weight for g in v.groups if g.group in gids)>.25:prot.add([v.index],1,'REPLACE')
    mod=o.modifiers.new('ProductionReduction','DECIMATE');mod.ratio=8500/before;mod.vertex_group=prot.name;mod.invert_vertex_group=True
    bpy.ops.object.modifier_move_to_index(modifier=mod.name,index=0);bpy.ops.object.modifier_apply(modifier=mod.name);o.vertex_groups.remove(o.vertex_groups['_protect'])
 mod=o.modifiers.new('FrozenTriangles','TRIANGULATE');bpy.ops.object.modifier_move_to_index(modifier=mod.name,index=0);bpy.ops.object.modifier_apply(modifier=mod.name)
 after=len(o.data.polygons);assert all(len(p.vertices)==3 for p in o.data.polygons)
 if o==head:
    bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=1.15,island_margin=.004,area_weight=.2);bpy.ops.object.mode_set(mode='OBJECT')
 report[o.name]={'triangles_before':before,'triangles_after':after,'vertices':len(o.data.vertices)}
 for v in o.data.vertices:
    groups=sorted([(g.group,g.weight) for g in v.groups if g.weight>1e-5],key=lambda x:-x[1])
    assert groups,(o.name,v.index)
    for gi,w in groups[8:]:o.vertex_groups[gi].remove([v.index])
    groups=groups[:8]
    total=sum(w for gi,w in groups)
    for gi,w in groups:o.vertex_groups[gi].add([v.index],w/total,'REPLACE')
(P/'texturing').mkdir(exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/pilots_reduced.blend'))
for o in [body,head]:
 dup=o.copy();dup.data=o.data.copy();dup.parent=None;dup.modifiers.clear();dup.vertex_groups.clear();bpy.context.scene.collection.objects.link(dup)
 if o==body:
    for uv in list(dup.data.uv_layers):dup.data.uv_layers.remove(uv)
 bpy.ops.object.select_all(action='DESELECT');dup.select_set(True);bpy.context.view_layer.objects.active=dup
 path=P/f'texturing/{o.name.lower()}_upload.glb'
 bpy.ops.export_scene.gltf(filepath=str(path),use_selection=True,export_format='GLB',export_yup=True,export_skins=False,export_animations=False,export_materials='EXPORT')
 report[o.name]['upload_sha256']=hashlib.sha256(path.read_bytes()).hexdigest();bpy.data.objects.remove(dup,do_unlink=True)
(P/'work/geometry_delivery_counts.json').write_text(json.dumps(report,indent=2))
common.render_views(str(P/'review/reduced_rest'),1.5,3.3,views=('front','left','three_quarter'),resolution=(800,1100))
common.render_views(str(P/'review/reduced_head'),1.68,.60,views=('front','left','three_quarter'),resolution=(900,900),target=(0,-.03))
print('FROZEN_GEOMETRY',report)
