"""Fit heat-weighted joints, allocate face UV density and export the fixed texturing input."""
import bpy
import json
import os
import sys
from pathlib import Path
import numpy as np
from mathutils import Vector

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / 'scripts'))
sys.path.insert(0, str(PROJECT.parent / 'claude_shared'))
from uv_head_density import scale_head_islands
import posing
bpy.ops.wm.open_mainfile(filepath=str(PROJECT / 'work/body.blend'))
mesh = bpy.data.objects['Hound']
co = np.array([v.co[:] for v in mesh.data.vertices])
chains = {
    'Spine': (None, [(0,.12,.67),(0,-.12,.70),(0,-.42,.73),(0,-.64,.79)]),
    'Neck': ('Spine3', [(0,-.64,.79),(0,-.87,.85)]),
    'Head': ('Neck1', [(0,-.87,.85),(0,-1.17,.77)]),
    'Jaw': ('Head', [(0,-1.015,.775),(0,-1.19,.700)]),
}
tail = [(0,.21,.65)]
for y in np.linspace(.36,1.19,6):
    slab = co[(abs(co[:,1]-y)<.035)&(co[:,2]>.32)&(abs(co[:,0])<.12)]
    assert len(slab)>0
    tail.append(tuple(np.median(slab,axis=0)))
chains['Tail'] = ('Spine1', tail)
names = {'Spine':['Spine1','Spine2','Spine3'],'Neck':['Neck1'],'Head':['Head'],'Jaw':['Jaw'],
         'Tail':[f'Tail{i}' for i in range(1,7)]}
for side,sign in [('L',1),('R',-1)]:
    chains['Front_'+side] = ('Spine3',[(sign*.20,-.56,.72),(sign*.24,-.63,.32),
        (sign*.255,-.72,.115),(sign*.30,-.84,.02)])
    chains['Hind_'+side] = ('Spine1',[(sign*.18,.10,.69),(sign*.22,.14,.43),
        (sign*.28,.30,.12),(sign*.33,.20,.02)])
    names['Front_'+side] = [f'UpperArm_{side}',f'ForeArm_{side}',f'FrontPaw_{side}']
    names['Hind_'+side] = [f'Thigh_{side}',f'Shin_{side}',f'HindPaw_{side}']
rig = bpy.data.objects.new('Hound_Rig',bpy.data.armatures.new('Hound_Rig'))
bpy.context.scene.collection.objects.link(rig)
bpy.ops.object.select_all(action='DESELECT')
rig.select_set(True)
bpy.context.view_layer.objects.active=rig
bpy.ops.object.mode_set(mode='EDIT')
for key,(parent,pts) in chains.items():
    prev=rig.data.edit_bones.get(parent) if parent else None
    for i,name in enumerate(names[key]):
        bone=rig.data.edit_bones.new(name)
        bone.head=pts[i]
        bone.tail=pts[i+1]
        bone.parent=prev
        bone.use_connect=prev is not None and i>0
        bone.align_roll(Vector((0,0,1)) if key in ['Spine','Neck','Head','Jaw','Tail'] else Vector((0,-1,0)))
        prev=bone
bpy.ops.object.mode_set(mode='OBJECT')
mesh.select_set(True)
bpy.ops.object.parent_set(type='ARMATURE_AUTO')
# Disconnected claws inherit the nearest continuous skin's heat weights.
adj=[[] for _ in mesh.data.vertices]
for e in mesh.data.edges:
    a,b=e.vertices
    adj[a].append(b)
    adj[b].append(a)
seen=set()
parts=[]
for start in range(len(adj)):
    if start in seen: continue
    seen.add(start)
    part=[start]
    for a in part:
        for b in adj[a]:
            if b not in seen:
                seen.add(b)
                part.append(b)
    parts.append(part)
parts.sort(key=len,reverse=True)
main=parts[0]
assert all(mesh.data.vertices[i].groups for i in main), 'Heat weighting failed on continuous skin'
for part in parts[1:]:
    for i in part:
        j=main[int(np.argmin(np.sum((co[main]-co[i])**2,axis=1)))]
        weights=[(g.group,g.weight) for g in mesh.data.vertices[j].groups]
        for vg in mesh.vertex_groups: vg.remove([i])
        for group,weight in weights: mesh.vertex_groups[group].add([i],weight,'REPLACE')
bpy.context.view_layer.objects.active=mesh
bpy.ops.object.vertex_group_limit_total(limit=4)
bpy.ops.object.vertex_group_normalize_all(lock_active=False)
# Reduce only after weights exist; this keeps their interpolation on the final topology.
mod=mesh.modifiers.new('LOD0Budget','DECIMATE')
mod.ratio=.74
bpy.ops.object.modifier_apply(modifier=mod.name)
assert all(v.groups and abs(sum(g.weight for g in v.groups)-1)<1e-4 for v in mesh.data.vertices)
posing.reset(rig)
bpy.ops.object.select_all(action='DESELECT')
mesh.select_set(True)
for uv in list(mesh.data.uv_layers): mesh.data.uv_layers.remove(uv)
mesh.data.uv_layers.new(name='UVMap')
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.quads_convert_to_tris(quad_method='BEAUTY',ngon_method='BEAUTY')
bpy.ops.uv.smart_project(angle_limit=1.15,island_margin=.004,area_weight=0.,scale_to_bounds=False)
scale_head_islands(mesh,('Head','Jaw'),factor=2.5)
bpy.ops.uv.pack_islands(margin=.004,rotate=True)
bpy.ops.object.mode_set(mode='OBJECT')
me=mesh.data
me.calc_loop_triangles()
uv=me.uv_layers.active.data
u=np.array([[tuple(uv[l].uv) for l in t.loops] for t in me.loop_triangles],dtype=np.float32)
xyz=np.array([[tuple(me.vertices[v].co) for v in t.vertices] for t in me.loop_triangles],dtype=np.float32)
assert np.isfinite(u).all() and u.min()>=0 and u.max()<=1
assert np.all(np.abs(np.cross(u[:,1]-u[:,0],u[:,2]-u[:,0]))>1e-12)
np.savez(PROJECT/'work/uv3d.npz',uv=u,xyz=xyz,part=np.zeros(len(u),dtype=np.int32))
report={'bones':len(rig.data.bones),'unweighted':0,'components':[len(p) for p in parts],
        'joints':chains,'triangles':len(me.loop_triangles),'vertices':len(me.vertices),
        'head_uv_density_multiplier':2.5,'padding_fraction':.004}
(PROJECT/'work/rig_report.json').write_text(json.dumps(report,indent=2)+'\n')
bpy.ops.wm.save_as_mainfile(filepath=str(PROJECT/'work/rig_uv.blend'))
dup=mesh.copy()
dup.data=mesh.data.copy()
dup.modifiers.clear()
dup.parent=None
bpy.context.scene.collection.objects.link(dup)
bpy.ops.object.select_all(action='DESELECT')
dup.select_set(True)
bpy.context.view_layer.objects.active=dup
bpy.ops.export_scene.gltf(filepath=str(PROJECT/'export/hound_neutral_upload.glb'),use_selection=True,
    export_format='GLB',export_yup=True,export_skins=False,export_animations=False,export_materials='NONE')
print(json.dumps(report),flush=True)
sys.stdout.flush()
sys.stderr.flush()
os._exit(0)
