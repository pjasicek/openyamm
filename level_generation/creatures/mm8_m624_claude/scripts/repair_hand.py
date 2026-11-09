import bpy,bmesh,json
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/step1.blend'))
obj=bpy.data.objects['Body'];J=json.loads((P/'work/joints_final.json').read_text())['joints']
bm=bmesh.new();bm.from_mesh(obj.data);layer=bm.verts.layers.int['part']
for k in [1,2,3]:
    wl=Vector(J['L'+str(k)+'_Hand']);wr=Vector(J['R'+str(k)+'_Hand']);dl=(wl-Vector(J['L'+str(k)+'_Forearm'])).normalized();dr=(wr-Vector(J['R'+str(k)+'_Forearm'])).normalized()
    cutl=wl-dl*.018;cutr=wr-dr*.018
    src=bm.copy();sl=src.verts.layers.int['part']
    bmesh.ops.delete(src,geom=[v for v in src.verts if v[sl]!=0 or (v.co-wl).length>.37 or (v.co-wl).dot(dl)<-.05],context='VERTS')
    bmesh.ops.bisect_plane(src,geom=src.verts[:]+src.edges[:]+src.faces[:],plane_co=cutl,plane_no=dl,clear_inner=True)
    remaining=set(src.verts);components=[]
    while remaining:
        q=[remaining.pop()];comp=[]
        while q:
            v=q.pop();comp.append(v)
            for edge in v.link_edges:
                w=edge.other_vert(v)
                if w in remaining:remaining.remove(w);q.append(w)
        components.append(comp)
    chosen=set(min(components,key=lambda c:min((v.co-wl).length for v in c)))
    bmesh.ops.delete(src,geom=[v for v in src.verts if v not in chosen],context='VERTS')
    region=[v for v in bm.verts if v[layer]==0 and v.co.x<wr.x+.065 and (v.co-wr).length<.38 and (v.co-wr).dot(dr)>-.07]
    vset=set(region);geom=region+[e for e in bm.edges if all(v in vset for v in e.verts)]+[f for f in bm.faces if all(v in vset for v in f.verts)]
    bmesh.ops.bisect_plane(bm,geom=geom,plane_co=cutr,plane_no=dr)
    bmesh.ops.delete(bm,geom=[v for v in bm.verts if v[layer]==0 and v.co.x<wr.x+.065 and (v.co-wr).length<.38 and (v.co-cutr).dot(dr)>1e-6],context='VERTS')
    mirror=Matrix.Diagonal((-1,1,1));rot=(mirror@dl).rotation_difference(dr).to_matrix();mapping={}
    for v in src.verts:
        nv=bm.verts.new(wr+rot@mirror@(v.co-wl));nv[layer]=99+k;mapping[v]=nv
    for f in src.faces:bm.faces.new([mapping[v]for v in reversed(f.verts)])
bmesh.ops.recalc_face_normals(bm,faces=bm.faces[:]);bm.to_mesh(obj.data);bm.free();src.free()
me=obj.data
for f in me.polygons:f.use_smooth=True
co=np.array([v.co[:]for v in me.vertices]);pa=np.array([v.value for v in me.attributes['part'].data]);e=np.array([x.vertices[:]for x in me.edges]);me.calc_loop_triangles();tri=np.array([t.vertices[:]for t in me.loop_triangles])
np.savez(P/'work/geometry.npz',co=co,parts=pa,edges=e,tri=tri)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/fitted_body.blend'))
(P/'work/hand_repair.json').write_text(json.dumps({'fault':'Right-hand digit topology was unsuitable for six independent grips.','repair':'Mirror each verified five-digit left hand into its paired right forearm frame; wrist cuts sit beneath cuffs.','vertices':len(co),'triangles':len(tri),'right_hand_parts':[100,101,102]},indent=2))
