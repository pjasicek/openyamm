"""Reduce after weight transfer; retain the face and each digit's silhouette."""
import bpy, numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/full_timed.blend'))
body=bpy.data.objects['Body']; body.parent.animation_data.action=None
for pb in body.parent.pose.bones: pb.matrix_basis.identity()
me=body.data
pv=np.zeros(len(me.vertices),np.int32); me.attributes['piece'].data.foreach_get('value',pv)
protect=body.vertex_groups.new(name='_protect')
for v in me.vertices:
    if pv[v.index]==0 and v.co.z-.4*v.co.y>1.45: protect.add([v.index],1,'REPLACE')
counts={int(k):sum(len(f.vertices)-2 for f in me.polygons if pv[f.vertices[0]]==k) for k in np.unique(pv)}
targets={k:max(24,int(n*.55)) for k,n in counts.items()}
targets.update({0:8000,1:1500,2:1100,3:1100,4:500,5:500})
report={}
for part,target in targets.items():
    for o in bpy.data.objects: o.select_set(o==body)
    bpy.context.view_layer.objects.active=body
    me=body.data; pv=np.zeros(len(me.vertices),np.int32); me.attributes['piece'].data.foreach_get('value',pv)
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='DESELECT'); bpy.ops.object.mode_set(mode='OBJECT')
    for v in me.vertices: v.select=bool(pv[v.index]==part)
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.separate(type='SELECTED'); bpy.ops.object.mode_set(mode='OBJECT')
    obj=next(o for o in bpy.context.selected_objects if o!=body)
    before=sum(len(f.vertices)-2 for f in obj.data.polygons)
    if before>target:
        bpy.context.view_layer.objects.active=obj
        mod=obj.modifiers.new('Budget','DECIMATE'); mod.ratio=target/before
        if part==0: mod.vertex_group='_protect'; mod.invert_vertex_group=True
        bpy.ops.object.modifier_move_to_index(modifier=mod.name,index=0)
        bpy.ops.object.modifier_apply(modifier=mod.name)
    after=sum(len(f.vertices)-2 for f in obj.data.polygons)
    report[part]=[before,after]
    for o in bpy.data.objects: o.select_set(o in (body,obj))
    bpy.context.view_layer.objects.active=body; bpy.ops.object.join()
body.vertex_groups.remove(body.vertex_groups['_protect'])
# Normalize/prune interpolated weights to the engine's four influences.
for v in body.data.vertices:
    weights=sorted([(e.weight,e.group) for e in v.groups if e.weight>1e-5],reverse=True)[:4]
    assert weights
    for e in list(v.groups): body.vertex_groups[e.group].remove([v.index])
    total=sum(w for w,g in weights)
    for w,g in weights: body.vertex_groups[g].add([v.index],w/total,'REPLACE')
triangles=sum(len(p.vertices)-2 for p in body.data.polygons)
assert triangles<19000
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/full_reduced.blend'))
import json
(P/'work/reduction_report.json').write_text(json.dumps({'parts':report,'total_triangles':triangles},indent=2)+'\n')
print('REDUCE',report,'TOTAL',triangles)
