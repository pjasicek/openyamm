from pathlib import Path
import bpy,bmesh,sys,json,math
import numpy as np
p=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(p/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(p/'work/body_head_v1.blend'))
body=bpy.data.objects['Body'];bm=bmesh.new();bm.from_mesh(body.data)
piece=bm.verts.layers.int['piece']
# Both ear cups have a small unwanted hole at the root (13 edges each).
edges=[e for e in bm.edges if e.is_boundary and all(v[piece]==200 for v in e.verts)]
seen=set();filled=0
for e in edges:
    if e in seen:continue
    stack=[e];group=[]
    while stack:
        x=stack.pop()
        if x in seen:continue
        seen.add(x);group.append(x)
        stack.extend(y for v in x.verts for y in v.link_edges if y in edges and y not in seen)
    vs=set(v for e in group for v in e.verts)
    if len(group)==13 and min(v.co.z for v in vs)>1.59:
        bmesh.ops.holes_fill(bm,edges=group,sides=13);filled+=1
assert filled==2
bmesh.ops.recalc_face_normals(bm,faces=bm.faces[:]);bm.to_mesh(body.data);bm.free()
# Paired upper incisors; the generated head returned small pointed teeth instead.
for side in (-1,1):
    verts=[];faces=[]
    rings=[(0,.007,.004,0),(.010,.0065,.004,-.001),(.023,.004,.003,-.002),(.030,.0025,.002,-.001)]
    for depth,rx,ry,dy in rings:
        for k in range(8):
            a=2*math.pi*k/8
            verts.append((side*.008+rx*math.cos(a),-.391+dy+ry*math.sin(a),1.492-depth))
    for j in range(3):
        for k in range(8):faces.append((j*8+k,j*8+(k+1)%8,(j+1)*8+(k+1)%8,(j+1)*8+k))
    faces.extend([tuple(range(7,-1,-1)),tuple(range(24,32))])
    me=bpy.data.meshes.new('Incisor');me.from_pydata(verts,[],faces);me.update()
    me.attributes.new('piece','INT','POINT').data.foreach_set('value',[201]*len(verts))
    ob=bpy.data.objects.new('Incisor',me);bpy.context.collection.objects.link(ob)
    for f in me.polygons:f.use_smooth=True
for o in bpy.data.objects:o.select_set(o.type=='MESH')
bpy.context.view_layer.objects.active=body;bpy.ops.object.join()
if 'orig_co' in body.data.attributes:body.data.attributes.remove(body.data.attributes['orig_co'])
co=np.array([tuple(v.co) for v in body.data.vertices]);body.data.attributes.new('orig_co','FLOAT_VECTOR','POINT').data.foreach_set('vector',co.ravel())
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/step1.blend'))
common.workbench_clay(bpy.context.scene)
common.render_views(str(p/'review/head_detail_fixed'),1.54,.42,views=('front','three_quarter','left'),resolution=(800,800),target=(0,-.27))
print('HEAD_DETAIL',len(co),sum(len(f.vertices)-2 for f in body.data.polygons))
