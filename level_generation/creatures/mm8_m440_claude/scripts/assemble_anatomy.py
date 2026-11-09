"""Fit the reviewed head and remove generated equipment absent from the native/reference views."""
from pathlib import Path
import bpy,bmesh,json,sys,math
sys.path.insert(0,str(Path(__file__).parent))
import common
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/st_v1_parts.blend'))
remove=[10,11,14,15,20,25,26,29,30,33,34,55,56,57,58,59,62,63,64]
for i in remove: bpy.data.objects.remove(bpy.data.objects[f'P{i:02}'],do_unlink=True)
with bpy.data.libraries.load(str(P/'work/head_v1_parts.blend'),link=False) as (src,dst):
    dst.objects=[n for n in src.objects if n.startswith('H')]
for o in dst.objects:bpy.context.scene.collection.objects.link(o)
# Both cuts fall below the jaw. The annular bridge preserves the torso and the selected head surface.
q=lambda v:v.co.z-.4*v.co.y
def cut(obj,z,upper):
    bm=bmesh.new();bm.from_mesh(obj.data)
    bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-6)
    bs={e for e in bm.edges if e.is_boundary};pending=set(bs)
    while pending:
        todo=[pending.pop()];component=set()
        while todo:
            e=todo.pop();component.add(e)
            for v in e.verts:
                for other in v.link_edges:
                    if other in pending:pending.remove(other);todo.append(other)
        vs=set(v for e in component for v in e.verts)
        if not upper and min(q(v) for v in vs)<z<max(q(v) for v in vs):
            bmesh.ops.holes_fill(bm,edges=list(component))
    bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=1e-7,
        plane_co=(0,0,z),plane_no=(0,-.4,1),clear_outer=upper,clear_inner=not upper)
    pending=set(bm.verts);components=[]
    while pending:
        stack=[pending.pop()];component=set()
        while stack:
            v=stack.pop();component.add(v)
            for e in v.link_edges:
                w=e.other_vert(v)
                if w in pending:pending.remove(w);stack.append(w)
        components.append(component)
    retained=max(components,key=len)
    removed=[v for v in bm.verts if v not in retained]
    if removed:bmesh.ops.delete(bm,geom=removed,context='VERTS')
    ring=[e for e in bm.edges if e.is_boundary and all(abs(q(v)-z)<1e-5 for v in e.verts)]
    print('NECK_RING',obj.name,len(ring),max(abs(v.co.x) for e in ring for v in e.verts))
    assert len(ring)>8
    bm.to_mesh(obj.data);bm.free()
body=bpy.data.objects['P00'];head=bpy.data.objects['H00']
cut(body,1.415,True);cut(head,1.425,False)
for o in bpy.data.objects:o.select_set(o in (body,head))
bpy.context.view_layer.objects.active=body;bpy.ops.object.join()
bm=bmesh.new();bm.from_mesh(body.data)
edges=[e for e in bm.edges if e.is_boundary and all(min(abs(q(v)-1.415),abs(q(v)-1.425))<1e-5 for v in e.verts)]
def ring(z):
    es=[e for e in edges if all(abs(q(v)-z)<1e-5 for v in e.verts)]
    vs=set(v for e in es for v in e.verts)
    assert all(sum(e in es for e in v.link_edges)==2 for v in vs)
    center=sum((v.co for v in vs),start=__import__('mathutils').Vector())/len(vs)
    loops=[];remaining=set(vs)
    while remaining:
        start=min(remaining,key=lambda v:math.atan2(v.co.y-center.y,v.co.x-center.x))
        ordered=[start];prev=None;cur=start
        while True:
            nxt=next(v for e in cur.link_edges if e in es for v in e.verts if v!=cur and v!=prev)
            if nxt==start:break
            ordered.append(nxt);prev,cur=cur,nxt
        remaining-=set(ordered);loops.append(ordered)
    print('RING_LOOPS',z,[(len(L),[round(sum(v.co[k] for v in L)/len(L),3) for k in range(3)]) for L in loops])
    area_of=lambda L:abs(sum(L[i].co.x*L[(i+1)%len(L)].co.y-L[(i+1)%len(L)].co.x*L[i].co.y for i in range(len(L))))
    print('RING_AREAS',z,[(len(L),round(area_of(L),5)) for L in loops])
    ordered=max(loops,key=area_of)
    for L in loops:
        if L is not ordered:
            bmesh.ops.holes_fill(bm,edges=[e for e in es if e.verts[0] in L and e.verts[1] in L])
    area=sum(ordered[i].co.x*ordered[(i+1)%len(ordered)].co.y-ordered[(i+1)%len(ordered)].co.x*ordered[i].co.y for i in range(len(ordered)))
    if area<0:ordered=[ordered[0]]+list(reversed(ordered[1:]))
    polar=sorted(ordered,key=lambda v:math.atan2(v.co.y-center.y,v.co.x-center.x))
    linked=sum(any(set(e.verts)=={polar[i],polar[(i+1)%len(polar)]} for e in es) for i in range(len(polar)))
    print('POLAR_ORDER',z,len(polar),linked)
    if linked==len(polar):
        return polar,[math.atan2(v.co.y-center.y,v.co.x-center.x) for v in polar]
    lengths=[(ordered[(i+1)%len(ordered)].co-ordered[i].co).length for i in range(len(ordered))]
    angles=[0.0]
    for L in lengths[:-1]:angles.append(angles[-1]+L/sum(lengths)*2*math.pi)
    return ordered,angles
lo,la=ring(1.415);hi,ha=ring(1.425)
i=j=0;created=[]
while i<len(lo) or j<len(hi):
    an=la[(i+1)%len(lo)]+(2*math.pi if i+1>=len(lo) else 0)
    bn=ha[(j+1)%len(hi)]+(2*math.pi if j+1>=len(hi) else 0)
    if i<len(lo) and (j==len(hi) or an<bn):
        created.append(bm.faces.new((lo[i%len(lo)],lo[(i+1)%len(lo)],hi[j%len(hi)])));i+=1
    else:
        created.append(bm.faces.new((lo[i%len(lo)],hi[(j+1)%len(hi)],hi[j%len(hi)])));j+=1
result={'faces':created}
neck=[v for v in bm.verts if 1.365<q(v)<1.485 and not (v.co.y<-.10 and v.co.z>1.385)]
for _ in range(12):
    bmesh.ops.smooth_vert(bm,verts=neck,factor=.30,use_axis_x=True,use_axis_y=True,use_axis_z=True)
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
bm.to_mesh(body.data);bm.free()
for o in bpy.data.objects:
    if o.type=='MESH':
        if o.name.startswith('H'):o.name=f'P{100+int(o.name[1:]):03}'
        o.data.materials.clear()
        m=bpy.data.materials.get('Clay') or bpy.data.materials.new('Clay');m.diffuse_color=(.55,.55,.55,1)
        o.data.materials.append(m)
        for f in o.data.polygons:f.use_smooth=True
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/anatomy_v2_parts.blend'))
common.workbench_clay(bpy.context.scene)
common.render_views(str(P/'review/anatomy_v2'),.85,2.1,views=('front','three_quarter','left','back'),resolution=(800,900))
common.render_views(str(P/'review/anatomy_v2_head'),1.47,.60,views=('front','left','back'),resolution=(650,650))
(P/'work/anatomy_v2_report.json').write_text(json.dumps({'removed_original_parts':remove,'head_source':'head_geometry_v1','neck_bridge_faces':len(result['faces']),'hands':'Four long fingers and thumb each; no digit added.'},indent=2))
