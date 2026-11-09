"""Fit the native wyvern anatomy to measured Meshy vertices, then probe heat weights."""
from pathlib import Path
import json, sys
import bpy, bmesh
import numpy as np
from mathutils import Vector
from mathutils.kdtree import KDTree
P = Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/body_import.blend'))
m=bpy.data.objects['Wyvern']
# Meshy supplied two intersecting sheets per wing; keep the inspected clean side, rendered double-sided.
bm=bmesh.new();bm.from_mesh(m.data);bm.verts.ensure_lookup_table()
seen=set();parts_before=[]
for v in bm.verts:
    if v.index in seen:continue
    stack=[v];piece=[];seen.add(v.index)
    while stack:
        w=stack.pop();piece.append(w)
        for e in w.link_edges:
            n=e.other_vert(w)
            if n.index not in seen:seen.add(n.index);stack.append(n)
    parts_before.append(piece)
parts_before.sort(key=len,reverse=True)
assert [len(a) for a in parts_before[:5]]==[5244,131,130,130,128]
bmesh.ops.delete(bm,geom=parts_before[3]+parts_before[4],context='VERTS')
bm.to_mesh(m.data);bm.free();m.data.update()
co=np.array([tuple(v.co) for v in m.data.vertices])
z0=float(co[:,2].min())
for v in m.data.vertices:
    v.co.z-=z0
co[:,2]-=z0

def point(x,y,z):
    return Vector((x,y,z-z0))

def wingpoint(x,y):
    d=np.linalg.norm(co[:,:2]-[x,y],axis=1)
    ids=np.argsort(d)[:8]
    return Vector((x,y,float(np.median(co[ids,2]))))

bones=[]
def chain(names,pts,parent):
    for a,b,name in zip(pts[:-1],pts[1:],names):
        bones.append((name,a,b,parent));parent=name
    return parent

chain(['Spine1','Spine2'],[point(-.003,-.065,-.105),point(-.003,-.15,-.075),point(-.003,-.235,-.060)],None)
chain(['Neck1','Neck2','Neck3','Neck4','Neck5'],[point(-.003,-.235,-.060),point(-.003,-.256,-.020),point(-.003,-.278,.015),point(-.003,-.322,.023),point(-.003,-.365,.003),point(-.003,-.421,-.026)],'Spine2')
chain(['Head'],[point(-.003,-.421,-.026),point(-.003,-.49,-.047)],'Neck5')
chain(['Jaw'],[point(-.003,-.434,-.043),point(-.003,-.492,-.058)],'Head')
tail=[point(-.003,-.065,-.105)]
for y in np.linspace(.015,.495,9):
    rows=co[(abs(co[:,1]-y)<.018)&(co[:,2]>(-.165-z0))]
    assert len(rows)>0, y
    tail.append(Vector((float(np.median(rows[:,0])),float(y),float(np.quantile(rows[:,2],.35)))))
chain([f'Tail{i}' for i in range(1,10)],tail,'Spine1')
for side,s in [('L',1),('R',-1)]:
    shoulder=point(s*.025-.003,-.22,-.061)
    elbow=wingpoint(s*.13-.003,-.205);wrist=wingpoint(s*.255-.003,-.235)
    chain([f'UpperWing_{side}',f'ForeWing_{side}'],[shoulder,elbow,wrist],'Spine2')
    for k,mid,tip in [(1,(.365,-.154),(.495,-.103)),(2,(.335,-.075),(.36,.038)),(3,(.280,-.11),(.29,.018)),(4,(.19,-.105),(.14,-.065))]:
        chain([f'Wing{k}a_{side}',f'Wing{k}b_{side}'],[wrist,wingpoint(s*mid[0]-.003,mid[1]),wingpoint(s*tip[0]-.003,tip[1])],f'ForeWing_{side}')
    chain([f'Thigh_{side}',f'Shin_{side}',f'Foot_{side}'],[point(s*.026-.003,-.065,-.105),point(s*.049-.003,-.064,-.145),point(s*.045-.003,-.005,-.170),point(s*.045-.003,.035,-.201)],'Spine1')
arm=bpy.data.armatures.new('Wyvern_Rig');rig=bpy.data.objects.new('Wyvern_Rig',arm);bpy.context.collection.objects.link(rig)
for o in bpy.data.objects:o.select_set(o==rig)
bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT')
for name,a,b,parent in bones:
    bone=arm.edit_bones.new(name);bone.head=a;bone.tail=b;bone.align_roll(Vector((0,0,1)))
    if parent:bone.parent=arm.edit_bones[parent]
bpy.ops.object.mode_set(mode='OBJECT')
for o in bpy.data.objects:o.select_set(o in [m,rig])
bpy.context.view_layer.objects.active=rig
bpy.ops.object.parent_set(type='ARMATURE_AUTO')
empty=[v.index for v in m.data.vertices if not v.groups or sum(g.weight for g in v.groups)<1e-6]
print('HEAT_UNWEIGHTED',len(empty),flush=True)
# A disconnected rigid spike follows its attachment, rather than drifting between remote bones.
parent=list(range(len(co)))
def find(x):
    while parent[x]!=x:parent[x]=parent[parent[x]];x=parent[x]
    return x
for e in m.data.edges:
    a,b=(find(i) for i in e.vertices);parent[b]=a
parts={}
for i in range(len(co)):parts.setdefault(find(i),[]).append(i)
main=max(parts.values(),key=len)
tree=KDTree(len(main))
for i in main:tree.insert(Vector(co[i]),i)
tree.balance()
# Membranes belong to the wing even where the torso is geometrically closer.
membrane_ids={i for ids in parts.values() if 100<len(ids)<200 and np.ptp(co[ids,0])>.2 for i in ids}
for i,v in enumerate(m.data.vertices):
    x,y,z=co[i]
    if i not in membrane_ids and not (abs(x+.003)>.04 and y<-.035 and z>.12):continue
    side='L' if x>-.003 else 'R'
    candidates=[]
    for name,a,b,_ in bones:
        if not ('Wing' in name and name.endswith('_'+side)):continue
        aa=np.array(a);ab=np.array(b)-aa
        t=np.clip(np.dot(co[i]-aa,ab)/np.dot(ab,ab),0,1)
        distance=np.linalg.norm(co[i]-(aa+t*ab))
        candidates.append((distance,name))
    candidates.sort();candidates=candidates[:3]
    weights=np.array([1/(d+.012)**3 for d,_ in candidates]);weights/=weights.sum()
    trunk=float(np.clip((.075-abs(x+.003))/.045,0,1))
    for g in list(v.groups):m.vertex_groups[g.group].remove([i])
    for (_,name),w in zip(candidates,weights):m.vertex_groups[name].add([i],float(w*(1-trunk)),'REPLACE')
    if trunk>0:m.vertex_groups['Spine2'].add([i],trunk,'REPLACE')
for ids in parts.values():
    if ids is main:continue
    a=co[ids]
    # Large thin membrane sheets need interpolated local weights, not one rigid transform.
    flexible=len(ids)>100 and np.ptp(a[:,0])>.2
    if flexible:
        continue
    else:
        near=tree.find(Vector(a.mean(0)))[1]
        weights=[(g.group,g.weight) for g in m.data.vertices[near].groups]
        for i in ids:
            for g in list(m.data.vertices[i].groups):m.vertex_groups[g.group].remove([i])
            for group,w in weights:m.vertex_groups[group].add([i],w,'REPLACE')
weighted=[v.index for v in m.data.vertices if sum(g.weight for g in v.groups)>1e-6]
assert weighted,'Automatic weights failed entirely; use a measured proxy or anatomy weights'
tree=KDTree(len(weighted))
for i in weighted:tree.insert(Vector(co[i]),i)
tree.balance()
for v in m.data.vertices:
    if sum(g.weight for g in v.groups)>1e-6:continue
    near=tree.find(v.co)[1]
    for g in m.data.vertices[near].groups:m.vertex_groups[g.group].add([v.index],g.weight,'REPLACE')
for o in bpy.data.objects:o.select_set(o==m)
bpy.context.view_layer.objects.active=m
bpy.ops.object.vertex_group_limit_total(limit=4)
bpy.ops.object.vertex_group_normalize_all(lock_active=False)
assert all(abs(sum(g.weight for g in v.groups)-1)<1e-4 for v in m.data.vertices)
assert len(arm.bones)<128
for b in rig.pose.bones:b.rotation_mode='QUATERNION'
(P/'work/joints.json').write_text(json.dumps({n:{'head':list(a),'tail':list(b),'parent':parent} for n,a,b,parent in bones},indent=2)+'\n')
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_v1.blend'))
print('RIGGED',len(arm.bones),'bones',len(parts),'parts',flush=True)
