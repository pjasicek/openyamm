"""Half-frame body contacts: closed anatomical shells; proximity only for hair and armour."""
import bpy,bmesh,sys,json
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
args=sys.argv[sys.argv.index('--')+1:];PTH=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=args[0]);rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];me=body.data
names=[g.name for g in body.vertex_groups];w=np.zeros((len(me.vertices),len(names)))
for v in me.vertices:
    for e in v.groups:w[v.index,e.group]=e.weight
part=np.array([x.value for x in me.attributes['garment'].data]);faces=[tuple(f.vertices) for f in me.polygons]
arm={s:w[:,[i for i,n in enumerate(names) if n.startswith(f'B_{s}_') and any(k in n for k in ['Clavicle','UpperArm','Forearm','Hand','Finger'])]].sum(1)>.2 for s in 'LR'}
samples={}
for s in 'LR':
 for key,keys in [('forearm',['Forearm']),('hand',['Hand','Finger'])]:samples[s+'_'+key]=w[:,[i for i,n in enumerate(names) if n.startswith(f'B_{s}_') and any(k in n for k in keys)]].sum(1)>.5
# Close only the diagnostic surface's cuff/neck/cut loops, using existing vertices; no changed model geometry.
def closed(mask):
    mesh=bpy.data.meshes.new('ContactSurface');mesh.from_pydata([v.co[:] for v in me.vertices],[],[f for f in faces if all(mask[i] for i in f)])
    bm=bmesh.new();bm.from_mesh(mesh);bm.verts.ensure_lookup_table()
    ids=bm.verts.layers.int.new('original')
    for v in bm.verts:v[ids]=v.index
    bmesh.ops.holes_fill(bm,edges=[e for e in bm.edges if e.is_boundary],sides=0)
    bmesh.ops.triangulate(bm,faces=list(bm.faces));bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    out=[tuple(v[ids] for v in f.verts) for f in bm.faces];bm.free();bpy.data.meshes.remove(mesh);return out
closed_sets={s:closed(np.isin(part,[0,1,3])&~arm[s]) for s in 'LR'}
closed_sets['sword']=closed(np.isin(part,[0,1,3])&~arm['R']&~arm['L'])
report={}
for an in args[1:]:
 ac=bpy.data.actions[an];rig.animation_data.action=ac;rig.animation_data.action_slot=ac.slots[0];worst={}
 for f in np.arange(0,ac.frame_range[1]+.01,.5):
    bpy.context.scene.frame_set(int(f),subframe=float(f-int(f)));ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();co=[v.co.copy() for v in m.vertices];ev.to_mesh_clear()
    trees={k:BVHTree.FromPolygons(co,fs) for k,fs in closed_sets.items()}
    for key,mask in samples.items():
        tree=trees[key[0]]
        for vi in np.where(mask)[0]:
            p=co[vi];loc,nrm,idx,dist=tree.find_nearest(p,.08)
            if loc is not None and (p-loc).dot(nrm)<-.7*dist and dist>worst.get(key,{}).get('depth_m',.001):worst[key]={'depth_m':dist,'frame':float(f),'vertex':int(vi),'hit_face':list(closed_sets[key[0]][idx]),'hit_bones':[names[int(np.argmax(w[j]))] for j in closed_sets[key[0]][idx]]}
    sw=rig.pose.bones['Socket_Sword'].matrix
    for t in np.linspace(-.289,1.361,90):
        # The grasp itself intentionally touches both hands; the guard, pommel and full blade are tested.
        for x in (-.022,0,.022) if t>.10 else (0,):
            p=sw@Vector((x,float(t),0));loc,nrm,idx,dist=trees['sword'].find_nearest(p,.08)
            if loc is not None and (p-loc).dot(nrm)<-.7*dist and dist>worst.get('sword',{}).get('depth_m',.001):worst['sword']={'depth_m':dist,'frame':float(f),'along_m':float(t)}
 report[an]=worst;print('G6',an,json.dumps(worst),flush=True)
(PTH/'work/g6_contacts.json').write_text(json.dumps(report,indent=1))
