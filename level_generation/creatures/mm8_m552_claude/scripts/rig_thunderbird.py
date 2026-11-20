"""Fit an anatomy-owned flyer rig to the retained T2.5 mesh and repair folded primary feathers."""
import json
from pathlib import Path
import bpy, bmesh
import numpy as np
from mathutils import Vector
P = Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/import_v2.blend'))
mesh = next(o for o in bpy.data.objects if o.type == 'MESH')
for o in list(bpy.data.objects):
    if o != mesh: bpy.data.objects.remove(o, do_unlink=True)
mesh.parent = None
bpy.context.view_layer.objects.active = mesh
mesh.select_set(True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
mesh.name = mesh.data.name = 'Thunderbird'
parts = json.loads((P/'work/components_v2.json').read_text())['vertices']
co = np.array([tuple(v.co) for v in mesh.data.vertices])
labels = np.zeros(len(co), dtype=int)
for part, ids in enumerate(parts): labels[ids] = part
attribute = mesh.data.attributes.new('anatomy_part','INT','POINT')
for v, part in zip(attribute.data, labels): v.value = int(part)
# Replace only eight folded primary shells, fitted to each preserved feather's measured plane and span.
repair = {}
bm=bmesh.new();bm.from_mesh(mesh.data);layer=bm.verts.layers.int['anatomy_part']
for part in [12,14,16,19,23,24,29,31]:
    points=co[parts[part]];center=points.mean(0)
    _,_,axes=np.linalg.svd(points-center,full_matrices=False)
    u,v,n=axes
    if u[0]*center[0]<0:u=-u
    if n[2]<0:n=-n
    v=np.cross(n,u);v/=np.linalg.norm(v);n=np.cross(u,v)
    along=(points-center)@u;across=(points-center)@v
    lo,hi=along.min(),along.max();length=hi-lo
    radius=float(np.percentile(abs(across),85))
    root=center+u*lo;old=[a for a in bm.verts if a[layer]==part]
    bmesh.ops.delete(bm,geom=old,context='VERTS')
    rows=[]
    for t,w in [(0,.12),(.12,.62),(.30,.93),(.50,1),(.70,.92),(.85,.73),(.94,.45),(1,.03)]:
        row=[]
        for j,k in enumerate([-1,0,1,1,0,-1]):
            h=(.00045 if abs(k)==1 else .0018)*(1 if j<3 else -1)
            xyz=root+u*(length*t)+v*(radius*w*k)+n*h
            vert=bm.verts.new(xyz);vert[layer]=part;row.append(vert)
        rows.append(row)
    for a,b in zip(rows[:-1],rows[1:]):
        for j in range(6):bm.faces.new((a[j],a[(j+1)%6],b[(j+1)%6],b[j]))
    bm.faces.new(tuple(reversed(rows[0])));bm.faces.new(tuple(rows[-1]))
    repair[part]={'source_length':float(length),'fitted_half_width':radius,'new_vertices':48,'reason':'folded/open primary tip shell'}
bmesh.ops.delete(bm, geom=[v for v in bm.verts if v[layer]>=50], context='VERTS')
# The source curled toes touch into loops. Retain the ankles and give each foot three separate toes plus a hallux.
foot_geom=[f for f in bm.faces if all(v[layer]==0 and v.co.y>.075 and abs(v.co.x)>.015 for v in f.verts)]
cut=bmesh.ops.bisect_plane(bm,geom=list(set(foot_geom+[e for f in foot_geom for e in f.edges]+[v for f in foot_geom for v in f.verts])),dist=1e-6,plane_co=(0,0,-.139),plane_no=(0,0,1),clear_inner=True)
edges=[e for e in cut['geom_cut'] if isinstance(e,bmesh.types.BMEdge) and e.is_boundary]
if edges:bmesh.ops.holes_fill(bm,edges=edges,sides=0)
toes={}
for side,sign in [('L',1),('R',-1)]:
    for digit in range(4):
        part=100+(0 if sign>0 else 4)+digit
        dx=(digit-1)*.007 if digit<3 else 0
        root=np.array([sign*.039+dx,.109 if digit<3 else .119,-.14])
        direction=np.array([(digit-1)*.007 if digit<3 else sign*.004,-.03 if digit<3 else .025,0])
        centers=[root,root+direction*.35+[0,0,-.006],root+direction*.8+[0,0,-.012],root+direction+[0,0,-.009],root+direction*.93+[0,0,-.018]]
        radii=[.0045,.004,.0032,.0024,.00025];rows=[]
        for k,(c,r) in enumerate(zip(centers,radii)):
            tangent=np.array(centers[min(k+1,4)])-np.array(centers[max(k-1,0)]);tangent/=np.linalg.norm(tangent)
            u=np.cross(tangent,[1,0,0]);u/=np.linalg.norm(u);v=np.cross(tangent,u)
            row=[]
            for j in range(6):
                angle=j*np.pi/3;vert=bm.verts.new(c+r*(u*np.cos(angle)+v*np.sin(angle)));vert[layer]=part;row.append(vert)
            rows.append(row)
        for a,b in zip(rows[:-1],rows[1:]):
            for j in range(6):bm.faces.new((a[j],a[(j+1)%6],b[(j+1)%6],b[j]))
        bm.faces.new(tuple(reversed(rows[0])));bm.faces.new(tuple(rows[-1]))
        toes[part]={'bone':f'Toe_{side}_{digit+1}','side':side,'root':root.tolist(),'tip':np.array(centers[-1]).tolist()}
bmesh.ops.triangulate(bm,faces=list(bm.faces))
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
bm.to_mesh(mesh.data);bm.free()
co=np.array([tuple(v.co) for v in mesh.data.vertices]);labels=np.array([x.value for x in mesh.data.attributes['anatomy_part'].data])
# Source mesh is already metre-scaled and forward -Y; only ground and centre it.
offset=np.array([-.002,0,co[:,2].min()]);co-=offset
for v,xyz in zip(mesh.data.vertices,co):v.co=xyz
for face in mesh.data.polygons:face.use_smooth=True

def point(xyz):return Vector(np.array(xyz)-offset)
arm=bpy.data.armatures.new('Thunderbird_Rig');rig=bpy.data.objects.new('Thunderbird_Rig',arm)
bpy.context.scene.collection.objects.link(rig);bpy.context.view_layer.objects.active=rig
bpy.ops.object.mode_set(mode='EDIT')
chains={}
def bone(name,a,b,parent=None):
    e=arm.edit_bones.new(name);e.head=point(a);e.tail=point(b);e.align_roll(Vector((0,0,1)))
    if parent:e.parent=arm.edit_bones[parent]
    chains[name]={'head':list(e.head),'tail':list(e.tail),'parent':parent}
    return e
bone('Root',(0,.035,-.09),(0,-.015,-.083))
bone('Chest',(0,-.015,-.083),(0,-.095,-.078),'Root')
bone('Neck',(0,-.095,-.078),(0,-.145,-.077),'Chest')
bone('Head',(0,-.145,-.077),(0,-.205,-.083),'Neck')
bone('Tail',(0,.065,-.097),(0,.205,-.103),'Root')
for side,sign in [('L',1),('R',-1)]:
    joint=[(sign*.042,-.015,-.072),(sign*.16,-.035,-.034),(sign*.29,-.055,.03),(sign*.39,-.025,.095)]
    for i,name in enumerate(['UpperWing','ForeWing','HandWing']):
        bone(name+'_'+side,joint[i],joint[i+1],'Chest' if i==0 else ['UpperWing','ForeWing'][i-1]+'_'+side)
    bone('Thigh_'+side,(sign*.028,.055,-.105),(sign*.035,.086,-.125),'Root')
    bone('Shin_'+side,(sign*.035,.086,-.125),(sign*.039,.112,-.146),'Thigh_'+side)
    bone('Foot_'+side,(sign*.039,.112,-.146),(sign*.039,.101,-.164),'Shin_'+side)
for part,t in toes.items():bone(t['bone'],t['root'],t['tip'],'Foot_'+t['side'])
feathers={}
tail_parts={25,28,33,34,41,42,44,45,47}
for part in range(4,50):
    if part==5 or part in tail_parts:continue
    points=co[labels==part]+offset
    if len(points)<10:continue
    side='L' if points[:,0].mean()>0 else 'R';sign=1 if side=='L' else -1
    roots=points[points[:,1]<np.percentile(points[:,1],20)]
    root=roots.mean(0);tip=points[np.argmax(np.linalg.norm(points-root,axis=1))]
    x=abs(root[0]);parent=('UpperWing' if x<.13 else 'ForeWing' if x<.26 else 'HandWing')+'_'+side
    name=f'Feather_{part:02}'
    bone(name,root,tip,parent);feathers[part]={'bone':name,'side':side,'root':root.tolist(),'tip':tip.tolist()}
socket=bone('HeadSocket',(0,-.20,-.082),(0,-.214,-.082),'Head');socket.use_deform=False
bpy.ops.object.mode_set(mode='OBJECT')
groups={b.name:mesh.vertex_groups.new(name=b.name) for b in arm.bones if b.use_deform}

def blend(a,b,t):
    t=float(np.clip(t,0,1));return {a:1-t,b:t}
for i,xyz in enumerate(co+offset):
    part=int(labels[i]);x,y,z=xyz;side='L' if x>-.002 else 'R'
    if part in toes:weights={toes[part]['bone']:1.}
    elif part in feathers:weights={feathers[part]['bone']:1.}
    elif part in tail_parts:weights={'Tail':1.}
    elif part in [3,5]:weights={'Head':1.}
    elif part in [1,2]:
        u=abs(x)
        if u<.14:weights=blend('UpperWing_'+side,'ForeWing_'+side,(u-.11)/.09)
        else:weights=blend('ForeWing_'+side,'HandWing_'+side,(u-.235)/.085)
    elif y>.058 and z<-.117 and abs(x)>.016:
        if y<.092:weights=blend('Thigh_'+side,'Shin_'+side,(y-.075)/.022)
        else:weights=blend('Shin_'+side,'Foot_'+side,(-z-.132)/.016)
    elif y<-.125:weights=blend('Neck','Head',(-y-.125)/.025)
    elif y<-.07:weights=blend('Chest','Neck',(-y-.075)/.035)
    else:weights=blend('Root','Chest',(.025-y)/.075)
    assert abs(sum(weights.values())-1)<1e-6
    for name,weight in weights.items():
        if weight>1e-6:groups[name].add([i],weight,'REPLACE')
mesh.parent=rig;mod=mesh.modifiers.new('Anatomical skin','ARMATURE');mod.object=rig
for b in rig.pose.bones:b.rotation_mode='QUATERNION'
assert all(0<len(v.groups)<=2 for v in mesh.data.vertices)
report={'source':'smart_topology_v2','feather_repairs':repair,'removed_sliver_parts':list(range(50,54)), 'offset':offset.tolist(),'bones':chains,'feathers':feathers,'toes':toes,'tail_parts':list(tail_parts)}
(P/'work/rig.json').write_text(json.dumps(report,indent=2)+'\n')
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_v1.blend'))
print('RIG',len(arm.bones),'vertices',len(mesh.data.vertices))
