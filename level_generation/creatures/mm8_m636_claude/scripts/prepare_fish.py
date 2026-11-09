"""Fit a compact fish rig, reduce after weighting, and unwrap a static texture upload."""
import bpy, json, math
from pathlib import Path
from mathutils import Vector
import numpy as np

P = Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/fish_import.blend'))
fish = bpy.data.objects['Fish']
bpy.ops.object.select_all(action='DESELECT')
fish.select_set(True)
bpy.context.view_layer.objects.active = fish
fish.data.materials.clear()
material = bpy.data.materials.new('FishMaterial')
material.use_nodes = True
fish.data.materials.append(material)
for face in fish.data.polygons: face.use_smooth = True

# Ownership is measured from disconnected fin pieces, with a smooth tail-chain blend on the body.
adj = [[] for v in fish.data.vertices]
for e in fish.data.edges:
    a,b = e.vertices
    adj[a].append(b); adj[b].append(a)
pending = set(range(len(adj)))
components = []
while pending:
    todo = [pending.pop()]; indices = []
    while todo:
        v = todo.pop(); indices.append(v)
        for n in adj[v]:
            if n in pending: pending.remove(n); todo.append(n)
    components.append(indices)
components.sort(key=len, reverse=True)
report = []
fin_owner = {}
for ids in components:
    co = np.array([fish.data.vertices[i].co[:] for i in ids])
    lo,hi = co.min(0),co.max(0)
    center = co.mean(0)
    # A pectoral piece is lateral to the flank and behind the gill, not an eye or a belly fin.
    owner = None
    if len(ids) < len(components[0]) and abs(center[0]) > .07 and -.29 < center[1] < .06:
        owner = 'FinL' if center[0] > 0 else 'FinR'
        for i in ids: fin_owner[i] = owner
    report.append({'count':len(ids),'lo':lo.tolist(),'hi':hi.tolist(),'center':center.tolist(),'owner':owner})
(P/'work/fish_components.json').write_text(json.dumps(report,indent=2)+'\n')

arm = bpy.data.armatures.new('FishRig')
rig = bpy.data.objects.new('FishRig',arm)
bpy.context.collection.objects.link(rig)
bpy.context.view_layer.objects.active = rig
rig.select_set(True)
bpy.ops.object.mode_set(mode='EDIT')
joints = {'Body':((0,-.25,-.025),(0,.08,-.025),None),
    'Tail1':((0,.08,-.025),(0,.28,-.025),'Body'),
    'Tail2':((0,.28,-.025),(0,.50,-.025),'Tail1'),
    'FinL':((.055,-.22,-.045),(.16,-.10,-.09),'Body'),
    'FinR':((-.055,-.22,-.045),(-.16,-.10,-.09),'Body')}
for name,(head,tail,parent) in joints.items():
    b = arm.edit_bones.new(name); b.head=head; b.tail=tail
    if parent: b.parent=arm.edit_bones[parent]
bpy.ops.object.mode_set(mode='OBJECT')
groups = {name:fish.vertex_groups.new(name=name) for name in joints}
for v in fish.data.vertices:
    if v.index in fin_owner:
        groups[fin_owner[v.index]].add([v.index],1,'REPLACE')
        continue
    y=v.co.y
    if y < -.04: weights={'Body':1}
    elif y < .18:
        t=(y+.04)/.22;weights={'Body':1-t,'Tail1':t}
    elif y < .34:
        t=(y-.18)/.16;weights={'Tail1':1-t,'Tail2':t}
    else: weights={'Tail2':1}
    for name,w in weights.items():
        if w>1e-6: groups[name].add([v.index],w,'REPLACE')
fish.parent=rig
fish.modifiers.new('FishRig','ARMATURE').object=rig
bpy.context.view_layer.objects.active=fish
bpy.ops.object.select_all(action='DESELECT');fish.select_set(True)
dec=fish.modifiers.new('Silhouette budget','DECIMATE');dec.ratio=650/1941
bpy.ops.object.modifier_move_up(modifier=dec.name)
bpy.ops.object.modifier_apply(modifier=dec.name)
for uv in list(fish.data.uv_layers): fish.data.uv_layers.remove(uv)
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(angle_limit=math.radians(75),island_margin=.006,area_weight=0)
bpy.ops.uv.pack_islands(margin=.006,rotate=True)
bpy.ops.object.mode_set(mode='OBJECT')
assert all(v.groups and abs(sum(g.weight for g in v.groups)-1)<1e-4 for v in fish.data.vertices)
triangles=sum(len(f.vertices)-2 for f in fish.data.polygons)
assert triangles*12 < 9000
print('FISH_REDUCED',triangles,'school',triangles*12,'components',[(x['count'],x['owner']) for x in report],flush=True)

sc=bpy.context.scene;sc.camera.hide_set(False)
sc.camera.data.ortho_scale=1.4
for pose,tail in [('neutral',0),('tail_left',.5),('tail_right',-.5)]:
    rig.pose.bones['Tail1'].rotation_mode='XYZ';rig.pose.bones['Tail1'].rotation_euler.z=tail*.5
    rig.pose.bones['Tail2'].rotation_mode='XYZ';rig.pose.bones['Tail2'].rotation_euler.z=tail
    for view,direction in [('side',(1,0,.15)),('quarter',(1,-1,.3))]:
        camera=sc.camera;center=Vector((0,0,0));camera.location=Vector(direction).normalized()*4
        camera.rotation_euler=(center-camera.location).to_track_quat('-Z','Y').to_euler()
        sc.render.filepath=str(P/f'review/rig_{pose}_{view}.png');bpy.ops.render.render(write_still=True)
for b in rig.pose.bones: b.matrix_basis.identity()
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/fish_rig.blend'))
dup=fish.copy();dup.data=fish.data.copy();dup.modifiers.clear();dup.parent=None
bpy.context.collection.objects.link(dup)
bpy.ops.object.select_all(action='DESELECT');dup.select_set(True)
bpy.context.view_layer.objects.active=dup
bpy.ops.export_scene.gltf(filepath=str(P/'work/fish_neutral_upload.glb'),use_selection=True,export_format='GLB',export_yup=True,export_skins=False,export_animations=False)
(P/'work/fish_rig_info.json').write_text(json.dumps({'triangles':triangles,'school_fish':12,'school_triangles':triangles*12,'bones_per_fish':5,'joints':joints},indent=2)+'\n')
