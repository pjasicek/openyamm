"""Fit the wolf's quadruped rig to measured mesh slices; retain the original Meshy output."""
import bpy
import json
import math
import sys
from pathlib import Path
import numpy as np
from mathutils import Vector, Matrix

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT.parent / 'mm6_rat_claude/scripts'))
import posing
bpy.ops.wm.open_mainfile(filepath=str(PROJECT / 'work/mesh_v1.blend'))
mesh = bpy.data.objects['Wolf']
# Meshy's primary-view head turn is removed before skinning, feathered through the neck.
pivot = Vector((.02, -.30, .32))
for v in mesh.data.vertices:
    w = min(1., max(0., (-v.co.y - .29) / .075))
    w *= min(1., max(0., (v.co.z - .18) / .055))
    w = w * w * (3 - 2 * w)
    v.co = pivot + Matrix.Rotation(math.radians(-35) * w, 3, 'Z') @ (v.co - pivot)
co = np.array([v.co[:] for v in mesh.data.vertices])
chains = {
    'Spine': (None, [(0,.17,.37),(0,.045,.35),(0,-.10,.33),(0,-.23,.32)]),
    'Neck': ('Spine3', [(0,-.23,.32),(0,-.345,.32)]),
    'Head': ('Neck1', [(0,-.345,.32),(0,-.53,.29)]),
    'Jaw': ('Head', [(.025,-.435,.245),(.03,-.515,.218)]),
}
tail = [(0,.22,.415)]
for y in np.linspace(.275,.485,6):
    slab = co[(abs(co[:,1]-y)<.018)&(co[:,2]>.40)&(abs(co[:,0])<.13)]
    assert len(slab)>0
    tail.append(tuple(np.median(slab,axis=0)))
chains['Tail'] = ('Spine1', tail)
leg_samples = {}
for side,sign in [('L',1),('R',-1)]:
    for kind, y0,y1,zs in [('Front',-.40,-.16,[.31,.17,.06]),('Hind',.10,.38,[.34,.235,.115])]:
        pts=[]
        for z in zs:
            slab=co[(co[:,0]*sign>.06)&(co[:,1]>y0)&(co[:,1]<y1)&(abs(co[:,2]-z)<.018)]
            assert len(slab)>3,(side,kind,z)
            pt=np.median(slab,axis=0);pt[2]=z;pts.append(pt.tolist())
        if kind=='Front':
            pts[0]=[sign*.10,-.225,.32]
            paw=[sign*.155,-.35,.022]
        else:
            pts[0]=[sign*.10,.19,.35]
            paw=[sign*.19,.21,.022]
        pts.append(paw)
        chains[kind+'_'+side]=('Spine3' if kind=='Front' else 'Spine1',pts)
        leg_samples[kind+'_'+side]=pts
names={'Spine':['Spine1','Spine2','Spine3'],'Neck':['Neck1'],'Head':['Head'],'Jaw':['Jaw'],
       'Tail':[f'Tail{i}' for i in range(1,7)]}
for side in 'LR':
    names['Front_'+side]=[f'UpperArm_{side}',f'ForeArm_{side}',f'FrontPaw_{side}']
    names['Hind_'+side]=[f'Thigh_{side}',f'Shin_{side}',f'HindPaw_{side}']
rig=bpy.data.objects.new('Wolf_Rig',bpy.data.armatures.new('Wolf_Rig'))
bpy.context.scene.collection.objects.link(rig)
bpy.ops.object.select_all(action='DESELECT')
rig.select_set(True);bpy.context.view_layer.objects.active=rig
bpy.ops.object.mode_set(mode='EDIT')
for key,(parent,pts) in chains.items():
    prev=rig.data.edit_bones.get(parent) if parent else None
    for i,name in enumerate(names[key]):
        bone=rig.data.edit_bones.new(name);bone.head=pts[i];bone.tail=pts[i+1]
        bone.parent=prev;bone.use_connect=prev is not None and i>0
        bone.align_roll(Vector((0,0,1)) if key in ['Spine','Neck','Head','Jaw','Tail'] else Vector((0,-1,0)))
        prev=bone
bpy.ops.object.mode_set(mode='OBJECT')
mesh.select_set(True)
bpy.ops.object.parent_set(type='ARMATURE_AUTO')
empty=[v.index for v in mesh.data.vertices if not v.groups]
print('Heat-weight leftovers before loose-part transfer:',len(empty),flush=True)
# Teeth and loose fur must follow their local anatomy instead of drifting between distant joints.
adj=[[] for _ in mesh.data.vertices]
for e in mesh.data.edges:
    a,b=e.vertices;adj[a].append(b);adj[b].append(a)
seen=set();parts=[]
for start in range(len(adj)):
    if start in seen:continue
    seen.add(start);part=[start]
    for a in part:
        for b in adj[a]:
            if b not in seen:seen.add(b);part.append(b)
    parts.append(part)
parts.sort(key=len,reverse=True)
main=parts[0];main_co=co[main]
assert not set(empty).intersection(main), 'Main body has unweighted vertices'
for part in parts[1:]:
    for i in part:
        j=main[int(np.argmin(np.sum((main_co-co[i])**2,axis=1)))]
        weights=[(g.group,g.weight) for g in mesh.data.vertices[j].groups]
        for vg in mesh.vertex_groups:vg.remove([i])
        for group,weight in weights:mesh.vertex_groups[group].add([i],weight,'REPLACE')
# Feather mane ownership through the shoulder so short fur edges cannot split at a weight boundary.
def smooth_weight(value):
    value=min(1.,max(0.,value))
    return value*value*(3-2*value)
limb_names=['UpperArm_L','UpperArm_R','ForeArm_L','ForeArm_R','FrontPaw_L','FrontPaw_R']
for v in mesh.data.vertices:
    fraction=max(smooth_weight((v.co.z-.235)/.13)*smooth_weight((-v.co.y-.10)/.10),
                 smooth_weight((-v.co.y-.24)/.10)*smooth_weight((v.co.z-.12)/.08))
    removed=0.
    for g in list(v.groups):
        vg=mesh.vertex_groups[g.group]
        if vg.name in limb_names:
            removed+=g.weight*fraction
            vg.add([v.index],g.weight*(1-fraction),'REPLACE')
    neck=smooth_weight((-v.co.y-.20)/.13)
    if removed:
        mesh.vertex_groups['Neck1'].add([v.index],removed*neck,'ADD')
        mesh.vertex_groups['Spine3'].add([v.index],removed*(1-neck),'ADD')
# Small teeth retain one anatomical owner so individual teeth cannot bend.
for part in parts[1:]:
    center=co[part].mean(0)
    if len(part)<150 and center[1]<-.40:
        totals={}
        for i in part:
            for g in mesh.data.vertices[i].groups:
                name=mesh.vertex_groups[g.group].name
                totals[name]=totals.get(name,0)+g.weight
        owner=max(totals,key=totals.get)
        if owner not in ['Head','Jaw','Neck1']:continue
        for i in part:
            for vg in mesh.vertex_groups:vg.remove([i])
            mesh.vertex_groups[owner].add([i],1,'REPLACE')
bpy.context.view_layer.objects.active=mesh
bpy.ops.object.vertex_group_limit_total(limit=4)
bpy.ops.object.vertex_group_normalize_all(lock_active=False)
bad=[v.index for v in mesh.data.vertices if not v.groups or abs(sum(g.weight for g in v.groups)-1)>1e-4]
assert not bad, f'Invalid normalized weights: {bad[:20]}'
posing.reset(rig)
bpy.ops.wm.save_as_mainfile(filepath=str(PROJECT/'work/rig_v1.blend'))
report={'bones':len(rig.data.bones),'unweighted':0,'components':[len(p) for p in parts],
        'joints':chains,'leg_slices':leg_samples,'head_correction_degrees':-35}
(PROJECT/'work/rig_report.json').write_text(json.dumps(report,indent=2)+'\n')
print('RIG',len(rig.data.bones),'bones; components', [len(p) for p in parts[:20]], flush=True)
