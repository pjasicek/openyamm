"""Restore missing finger/toe using the neighbouring native-shaped digit; union roots into palm/foot."""
import bpy,bmesh,json,sys,math
import numpy as np
from mathutils import Vector
from pathlib import Path
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(Path('level_generation/creatures/mm6_bar1_claude/scripts').resolve()))
import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/geometry_v1.blend'))
mesh=bpy.data.objects['Gargoyle']; co=np.array([v.co[:] for v in mesh.data.vertices])
report=[]
templates={
    'finger':((co[:,0]>.39)&(co[:,1]<-.155)&(co[:,2]<.94)&(co[:,2]>.72),Vector((-.001,.060,-.004))),
    'toe':((co[:,0]>.17)&(co[:,0]<.27)&(co[:,1]<.107)&(co[:,2]<.14),Vector((.052,-.013,0)))
}
# Rebuild the sampled neighbour as closed rings; the source has non-manifold finger edges.
additions=[]
for kind,(mask,offset) in templates.items():
    src=co[mask]; axis=2 if kind=='finger' else 1; other=[a for a in range(3) if a!=axis]
    assert len(src)>25,(kind,len(src))
    controls=np.array([[.390,-.090,.945],[.472,-.199,.887],[.464,-.216,.790],[.435,-.211,.738]]) if kind=='finger' else np.array([[.245,.180,.070],[.241,.074,.094],[.231,.010,.031],[.228,-.032,.002]])
    rings=[]
    for i in range(14):
        u=i/13
        c=(1-u)**3*controls[0]+3*(1-u)**2*u*controls[1]+3*(1-u)*u*u*controls[2]+u**3*controls[3]
        taper=1-.25*u/.6 if u<.6 else .75*((1-u)/.4)**.65
        radius=np.array([.018,.013] if kind=='finger' else [.017,.020])*max(.025,taper)
        rings.append((c,radius))
    for side in (1,-1):
        points=[]
        for c,radius in rings:
            for j in range(12):
                v=Vector(c)+offset
                v[other[0]]+=radius[0]*math.cos(j*2*math.pi/12)
                v[other[1]]+=radius[1]*math.sin(j*2*math.pi/12)
                v.x*=side
                if side==-1: v+=Vector((-.014,-.018,.085) if kind=='finger' else (-.061,.084,0))
                points.append(v)
        faces=[[j for j in range(11,-1,-1)]]
        for i in range(13):
            for j in range(12): faces.append([i*12+j,i*12+(j+1)%12,(i+1)*12+(j+1)%12,(i+1)*12+j])
        faces.append([13*12+j for j in range(12)])
        data=bpy.data.meshes.new(f'{kind}_{side}_added')
        data.from_pydata(points,[],faces); data.update()
        obj=bpy.data.objects.new(data.name,data); bpy.context.scene.collection.objects.link(obj)
        bm=bmesh.new(); bm.from_mesh(data)
        bmesh.ops.recalc_face_normals(bm,faces=bm.faces[:])
        assert all(len(e.link_faces)==2 for e in bm.edges),(kind,'digit copy is not closed')
        bm.to_mesh(data); bm.free(); additions.append((kind,side,obj))
def component_count(data):
    adjacency=[[] for _ in data.vertices]
    for edge in data.edges:
        a,b=edge.vertices; adjacency[a].append(b); adjacency[b].append(a)
    seen=set(); count=0
    for i in range(len(adjacency)):
        if i in seen: continue
        count+=1; stack=[i]; seen.add(i)
        while stack:
            a=stack.pop()
            for b in adjacency[a]:
                if b not in seen: seen.add(b); stack.append(b)
    return count
initial_components=component_count(mesh.data)
for kind,side,obj in additions:
    bpy.context.view_layer.objects.active=mesh
    mod=mesh.modifiers.new(f'Add_{kind}_{side}','BOOLEAN'); mod.operation='UNION'; mod.solver='EXACT'; mod.object=obj
    before=len(mesh.data.vertices)
    bpy.ops.object.modifier_apply(modifier=mod.name)
    assert len(mesh.data.vertices)>before+20,(kind,side,'union lost added digit')
    assert component_count(mesh.data)==initial_components,(kind,side,'digit root did not join body')
    report.append({'kind':kind,'side':side,'vertices_added':len(mesh.data.vertices)-before})
    bpy.data.objects.remove(obj,do_unlink=True)
bm=bmesh.new(); bm.from_mesh(mesh.data)
centres=[Vector((.423,-.085,.930)),Vector((-.437,-.103,1.015)),Vector((.29,.105,.082)),Vector((-.351,.189,.082))]
seams=[v for v in bm.verts if min((v.co-c).length for c in centres)<.045]
for _ in range(6): bmesh.ops.smooth_vert(bm,verts=seams,factor=.22,use_axis_x=True,use_axis_y=True,use_axis_z=True)
bmesh.ops.recalc_face_normals(bm,faces=bm.faces[:])
bmesh.ops.triangulate(bm,faces=bm.faces[:]); bm.to_mesh(mesh.data); bm.free()
if mesh.data.has_custom_normals: mesh.data.normals_split_custom_set([(0,0,0)]*len(mesh.data.loops))
for poly in mesh.data.polygons: poly.use_smooth=True
co=np.array([v.co[:] for v in mesh.data.vertices]); assert np.isfinite(co).all()
(P/'work/digit_repair.json').write_text(json.dumps(report,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/geometry_digits.blend'))
scene=bpy.context.scene; scene.world=bpy.data.worlds.new('ReviewWorld'); common.workbench_clay(scene)
mesh.color=(.52,.55,.57,1); scene.display.shading.color_type='OBJECT'
for name,c,h in [('repaired_left_hand',(.42,-.10,.88),.5),('repaired_left_foot',(.31,.045,.12),.5),('repaired_right_hand',(-.42,-.10,.88),.5)]:
    common.render_views(str(P/'review'/name),c[2],h,views=('front','left','three_quarter'),resolution=(650,650),target=c[:2])
print('DIGIT_REPAIR',report,'triangles',len(mesh.data.polygons))
