"""60 Hz skin-contact screen using capped, closed anatomical skin proxies and actual club vertices."""
from pathlib import Path
import os,bpy,bmesh,json,math,sys
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/('work/'+__import__('os').environ.get('M480_MOTION_FILE','authored.blend'))))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];club=bpy.data.objects['Club'];me=body.data
names=[g.name for g in body.vertex_groups];wt=np.zeros((len(me.vertices),len(names)))
for v in me.vertices:
    for g in v.groups:wt[v.index,g.group]=g.weight
piece=np.array([x.value for x in me.attributes['piece'].data]);skin=piece==0
parts={}
for s in 'LR':
    for tag,keys,threshold in [('all',('UpperArm','Forearm','Hand','Finger'),.5),('forearm',('Forearm',),.6),('hand',('Hand','Finger'),.6)]:
        cols=[i for i,n in enumerate(names) if n.startswith('B_'+s+'_') and any(k in n for k in keys)]
        parts[s+'_'+tag]=(wt[:,cols].sum(1)>threshold)&skin
proxies={}
for s in 'LR':
    keep=skin&~parts[s+'_all'];bm=bmesh.new();bm.from_mesh(me);layer=bm.verts.layers.int.new('original')
    for v in bm.verts:v[layer]=v.index
    bmesh.ops.delete(bm,geom=[v for v in bm.verts if not keep[v.index]],context='VERTS')
    boundary=[e for e in bm.edges if e.is_boundary];bmesh.ops.holes_fill(bm,edges=boundary,sides=0)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bmesh.ops.triangulate(bm,faces=list(bm.faces))
    assert all(e.is_manifold for e in bm.edges),s
    if bm.calc_volume(signed=True)<0:bmesh.ops.reverse_faces(bm,faces=list(bm.faces))
    proxies[s]=[tuple(v[layer] for v in f.verts) for f in bm.faces];bm.free()
D=Vector((.813,.337,.474)).normalized()
def inside(tree,point):
    origin=point+D*.00001;hits=0
    for _ in range(40):
        loc,nrm,idx,d=tree.ray_cast(origin,D,5)
        if loc is None:break
        hits+=1;origin=loc+D*.00003
    return hits%2==1
def coords(obj):
    ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();co=[obj.matrix_world@v.co for v in mesh.vertices];ev.to_mesh_clear();return co
report={}
roles=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else ['Standing','Walking','Running','Attack','Hit','Death','Dead','Fidget']
for role in roles:
    act=bpy.data.actions[role];rig.animation_data.action=act
    if len(act.slots):rig.animation_data.action_slot=act.slots[0]
    row={}
    for f in np.arange(act.frame_range[0],act.frame_range[1]+.001,.5):
        bpy.context.scene.frame_set(int(f),subframe=float(f%1));co=coords(body);prop=coords(club)
        for s in 'LR':
            tree=BVHTree.FromPolygons(co,proxies[s],all_triangles=True)
            samples={s+'_forearm':[(i,co[i]) for i in np.where(parts[s+'_forearm'])[0]],s+'_hand':[(i,co[i]) for i in np.where(parts[s+'_hand'])[0]]}
            if s=='R':samples['club']=list(enumerate(prop))
            for name,points in samples.items():
                depth=0;vertex=None;count=0
                for i,point in points:
                    loc,nrm,idx,dist=tree.find_nearest(point)
                    if dist>.002 and (point-loc).dot(nrm)<-.5*dist and inside(tree,point):
                        count+=1
                        if dist>depth:depth=dist;vertex=int(i)
                if depth>row.get(name,{}).get('depth_m',0):row[name]={'depth_m':depth,'frame':float(f),'vertex':vertex,'count':count}
    report[role]=row;print('CONTACT',role,json.dumps(row),flush=True)
(p/'review/contacts.json').write_text(json.dumps({'method':'Closed skin-only capped arm exclusions; closest-normal candidates confirmed by ray parity; actual club mesh; 120 Hz; 2 mm threshold','clips':report},indent=2))

assert all(not findings for findings in report.values()), report
