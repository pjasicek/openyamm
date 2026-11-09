"""Model the native slender staff from the selected isolated reference silhouette."""
from pathlib import Path
import bpy,bmesh,math,json,sys
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common
profile=json.loads((p/'textures/props/staff_profile.json').read_text());rows=profile['rows'];px=1.8/(1499-30)
bpy.ops.wm.read_factory_settings(use_empty=True)
bm=bmesh.new();uvl=bm.loops.layers.uv.new('UVMap')
def z(y):return (1499-y)*px-1.2
def uv(x,y):return ((x-464)/96,1-y/1536)
def ring(y,sides):
    lo,hi=rows[str(y)];centre=(lo+hi)/2;radius=max(.0008,(hi-lo)*.5*px*.65)
    return [(bm.verts.new((radius*math.cos(k*2*math.pi/sides),radius*math.sin(k*2*math.pi/sides),z(y))),k*2*math.pi/sides) for k in range(sides)]
shaft_rows=[136,145,150,154,158,162,169,175,180,200,205,210,216,420,426,433,458,465,470,812,819,825,855,862,868,1190,1198,1205,1230,1238,1244,1402,1408,1415,1420,1426,1455,1460,1466,1472,1478,1485,1492,1499]
previous=None
for y in shaft_rows:
    cur=ring(y,12)
    if previous:
        py,prev=previous
        for k in range(12):
            j=(k+1)%12;face=bm.faces.new((prev[k][0],cur[k][0],cur[j][0],prev[j][0]))
            for loop,(theta,yy) in zip(face.loops,[(prev[k][1],py),(cur[k][1],y),(cur[j][1] if j else math.tau,y),(prev[j][1] if j else math.tau,py)]):
                lo,hi=rows[str(yy)];x=lo+2+(hi-lo-4)*abs(theta-math.pi)/math.pi;loop[uvl].uv=uv(x,yy)
    else:
        face=bm.faces.new([v for v,t in reversed(cur)])
        for loop in face.loops:loop[uvl].uv=uv(513,y)
    previous=(y,cur)
face=bm.faces.new([v for v,t in previous[1]])
for loop in face.loops:loop[uvl].uv=uv(513,1490)
# A small faceted leaf/diamond finial, with front/back ridge and no large blade.
tip=bm.verts.new((0,0,z(30)));prev=None
for y in [42,65,90,105,125,136]:
    lo,hi=rows[str(y)];half=(hi-lo)*px*.5*.65;depth=min(.006,half*.45)
    cur=[(bm.verts.new((x,yy,z(y))),u) for x,yy,u in [(-half,0,lo),(0,-depth,513),(half,0,hi),(0,depth,513)]]
    for k in range(4):
        j=(k+1)%4
        if prev:
            face=bm.faces.new((prev[k][0],cur[k][0],cur[j][0],prev[j][0]));tex=[(prev[k][1],py),(cur[k][1],y),(cur[j][1],y),(prev[j][1],py)]
        else:face=bm.faces.new((tip,cur[k][0],cur[j][0]));tex=[(513,30),(cur[k][1],y),(cur[j][1],y)]
        for loop,(x,yy) in zip(face.loops,tex):loop[uvl].uv=uv(x,yy)
    py=y;prev=cur
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
me=bpy.data.meshes.new('Staff');bm.to_mesh(me);bm.free();obj=bpy.data.objects.new('Staff',me);bpy.context.collection.objects.link(obj)
for f in me.polygons:f.use_smooth=f.center.z<z(136)
mat=bpy.data.materials.new('Staff');mat.use_nodes=True;bsdf=mat.node_tree.nodes.get('Principled BSDF');bsdf.inputs['Roughness'].default_value=.65
tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(p/'textures/props/staff_basecolor.png'));tex.image.pack();mat.node_tree.links.new(tex.outputs['Color'],bsdf.inputs['Base Color']);me.materials.append(mat)
obj['length_m']=1.8;obj['grip_from_butt_m']=1.2
assert sum(len(f.vertices)-2 for f in me.polygons)<1200
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/staff.blend'))
common.workbench_clay(bpy.context.scene,textured=True);common.render_views(str(p/'review/staff'),-.3,2.0,views=('front','left','three_quarter'),resolution=(320,960))
print('STAFF triangles',sum(len(f.vertices)-2 for f in me.polygons))
