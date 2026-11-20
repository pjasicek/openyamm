import bpy, bmesh, sys, json
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(P/'scripts'))
from common_rat import render_ortho
bpy.ops.wm.open_mainfile(filepath=str(P/'work/smart_topology_v2_body.blend'))
mesh=bpy.data.objects['Rat']
# Native side length/height 226/71 and front width/height 57/71.
for v in mesh.data.vertices:
    v.co.x*=.62
    v.co.z*=.80
bm=bmesh.new();bm.from_mesh(mesh.data);bm.verts.ensure_lookup_table()
unseen=set(bm.verts);comps=[]
while unseen:
    seed=unseen.pop();group={seed};stack=[seed]
    while stack:
        for e in stack.pop().link_edges:
            for v in e.verts:
                if v in unseen: unseen.remove(v);group.add(v);stack.append(v)
    comps.append(group)
comps.sort(key=len,reverse=True)
report=[]
for i,c in enumerate(comps):
    lo=[min(v.co[k] for v in c) for k in range(3)];hi=[max(v.co[k] for v in c) for k in range(3)]
    report.append({'component':i,'vertices':len(c),'bounds':[lo,hi]})
(P/'work/components.json').write_text(json.dumps(report,indent=2))
print('CONNECTED COMPONENTS',len(report))
# Keep the connected body, two eyeballs and paw/claw pieces; replace tangled facial wisps.
remove=set().union(*(c for i,c in enumerate(comps) if i not in (0,3,4) and max(v.co.y for v in c)<-.30))
bmesh.ops.delete(bm,geom=list(remove),context='VERTS')
bm.to_mesh(mesh.data);bm.free()
verts=[tuple(v.co) for v in mesh.data.vertices];faces=[tuple(f.vertices) for f in mesh.data.polygons]
parts=[0]*len(verts)
for v in mesh.data.vertices:
    if (v.co.y<-.4 and v.co.z>.204 and .001<abs(v.co.x)<.025): parts[v.index]=1
# Six whiskers, three gently curved tapered segments each, replace the disconnected generated tangle.
import math
from mathutils import Matrix
for side in (-1,1):
    for j in (-1,0,1):
        points=[Vector((side*(.012+.018*k),-.474+.011*k+j*.004,.193+j*.006+k*j*.002)) for k in range(4)]
        start=len(verts)
        for k,point in enumerate(points):
            tangent=(points[min(k+1,3)]-points[max(k-1,0)]).normalized()
            a=tangent.cross(Vector((0,0,1))).normalized();b=tangent.cross(a).normalized()
            radius=.0011*(1-k/3)+.0002
            for q in range(4):
                verts.append(tuple(point+radius*(a*math.cos(q*math.pi/2)+b*math.sin(q*math.pi/2))));parts.append(4)
        for k in range(3):
            for q in range(4):
                faces.append((start+k*4+q,start+k*4+(q+1)%4,start+(k+1)*4+(q+1)%4,start+(k+1)*4+q))
        faces.append(tuple(start+q for q in (3,2,1,0)));faces.append(tuple(start+12+q for q in range(4)))
# Paired broad rodent incisors, rigidly owned by the upper or lower jaw.
for part,z0,z1,y in [(2,.164,.184,-.477),(3,.169,.176,-.466)]:
    for x in (-.006,.004):
        start=len(verts)
        for z in (z0,z1):
            for dx,dy in [(-.0035,-.003),(.0035,-.003),(.0035,.003),(-.0035,.003)]:
                verts.append((x+dx,y+dy,z));parts.append(part)
        faces.extend(tuple(start+i for i in f) for f in [(3,2,1,0),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)])
me=bpy.data.meshes.new('RatClean');me.from_pydata(verts,[],faces);me.update();mesh.data=me
attr=me.attributes.new('anatomy','INT','POINT');attr.data.foreach_set('value',parts)
for f in me.polygons:f.use_smooth=True
bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
print('CLEANED',len(remove),'removed; retained',len(me.vertices),'vertices')
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/fit_body.blend'))
for name,loc,target,scale in [('side',(3,0,.16),(0,0,.16),1.12),('front',(0,-3,.16),(0,-.05,.16),.62),('head',(1,-1,.36),(0,-.4,.21),.4)]:
    render_ortho(loc,target,scale,str(P/f'review/fit_{name}.png'),res=(1200,900))
