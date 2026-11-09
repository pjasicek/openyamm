"""Native-style straight sword: 180 triangles, projected from the generated front reference."""
from pathlib import Path
import bpy, math, json
from mathutils import Vector
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
verts=[]; faces=[]; rows=[]
def ring(y,rx,rz,n,row,diamond=False):
    ids=[]
    for i in range(n):
        a=2*math.pi*i/n
        ids.append(len(verts));verts.append((rx*math.cos(a),y,rz*math.sin(a)));rows.append(row)
    return ids
def tube(spec,n):
    rings=[ring(y,x,z,n,row) for y,x,z,row in spec]
    faces.append(tuple(reversed(rings[0])))
    for a,b in zip(rings[:-1],rings[1:]):
        for i in range(n):faces.append((a[i],a[(i+1)%n],b[(i+1)%n],b[i]))
    faces.append(tuple(rings[-1]))
# Diamond cross-section gives a real edge and central ridge.
tube([(.103,.027,.004,1100),(.30,.026,.0037,660),(.48,.018,.0028,245),(.565,.004,.001,42),(.575,.0003,.0003,20)],4)
tube([(-.085,.014,.014,1460),(.075,.014,.014,1205),(.092,.013,.013,1175)],8)
tube([(-.105,.013,.010,1510),(-.093,.019,.014,1480),(-.080,.016,.012,1455)],8)
# Simple crossguard, broad silhouette but no decoration.
a=len(verts)
for y in (.087,.102):
    for x,z in ((-.075,-.006),(.075,-.006),(.075,.006),(-.075,.006)):
        verts.append((x,y,z));rows.append(1140 if y<.095 else 1120)
faces.extend([(a,a+3,a+2,a+1),(a+4,a+5,a+6,a+7)])
for i in range(4):faces.append((a+i,a+(i+1)%4,a+(i+1)%4+4,a+i+4))
me=bpy.data.meshes.new('SwordMesh');me.from_pydata(verts,[],faces);me.update()
ob=bpy.data.objects.new('SwordMesh',me);bpy.context.collection.objects.link(ob)
uv=me.uv_layers.new(name='UVMap')
for f in me.polygons:
    for li,vi in zip(f.loop_indices,f.vertices):
        x,y,z=verts[vi];row=rows[vi]
        # Different physical width scales for blade, crossguard, grip and pommel.
        sx=2250 if y>.102 else (2025 if y>.08 else 3300)
        col=512+x*sx
        uv.data[li].uv=((col-330)/360,1-row/1536)
for o in bpy.context.selected_objects:o.select_set(False)
ob.select_set(True);bpy.context.view_layer.objects.active=ob
tri=ob.modifiers.new('Triangles','TRIANGULATE');bpy.ops.object.modifier_apply(modifier=tri.name)
me=ob.data
assert not me.validate(verbose=True)
assert len(me.polygons)<300,len(me.polygons)
print('SWORD',len(me.polygons),'triangles')
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/sword.blend'))
(p/'work/sword.json').write_text(json.dumps({'triangles':len(me.polygons),'handle_radius_m':.014,'guard_from_grip_m':.095,'tip_from_grip_m':.575,'length_m':.680,'source':'references_props/sword_front.png'},indent=2))
