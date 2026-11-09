"""Native straight sword and buckler, measured to the selected claws; later split into runtime attachments."""
from pathlib import Path
import bpy,math,json
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_v1.blend'))
rig=bpy.data.objects['Wasp_Rig'];body=bpy.data.objects['Wasp'];parts=[]
mat=bpy.data.materials.new('WaspEquipment');mat.diffuse_color=(.32,.4,.34,1);mat.use_nodes=True
# Each material class occupies a quadrant in the eventual tiny equipment atlas.
def finish(obj,name,owner,swatch):
 obj.name=name;bpy.context.view_layer.objects.active=obj;bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
 obj.data.materials.clear();obj.data.materials.append(mat)
 uv=obj.data.uv_layers.active or obj.data.uv_layers.new(name='UVMap')
 for item in uv.data:item.uv=((swatch%2+.5)/2,(swatch//2+.5)/2)
 obj.vertex_groups.new(name=owner).add(list(range(len(obj.data.vertices))),1,'REPLACE')
 for f in obj.data.polygons:f.use_smooth=True
 parts.append(obj)
def cylinder(name,center,radius,depth,owner,swatch):
 bpy.ops.mesh.primitive_cylinder_add(vertices=32,radius=radius,depth=depth,location=center,rotation=(math.pi/2,0,0));finish(bpy.context.object,name,owner,swatch)
# Steel blade: diamond cross-section, a real tapered point rather than a flat card.
c=Vector((.263,-.091,.459));verts=[]
for y,w,d in [(-.145,.007,.0013),(-.403,.004,.0009)]:
 verts.extend([(c.x-w,y,c.z),(c.x,y,c.z+d),(c.x+w,y,c.z),(c.x,y,c.z-d)])
verts.append((c.x,-.437,c.z));faces=[(3,2,1,0)]
for j in range(4):faces.append((j,(j+1)%4,(j+1)%4+4,j+4));faces.append((j+4,(j+1)%4+4,8))
data=bpy.data.meshes.new('SwordBlade');data.from_pydata(verts,[],faces);obj=bpy.data.objects.new('SwordBlade',data);bpy.context.collection.objects.link(obj);finish(obj,'SwordBlade','Sword',0)
cylinder('SwordGrip',(c.x,-.096,c.z),.0052,.067,'Sword',3)
cylinder('SwordPommel',(c.x,-.060,c.z),.0075,.009,'Sword',1)
bpy.ops.mesh.primitive_cube_add(size=1,location=(c.x,-.137,c.z));o=bpy.context.object;o.dimensions=(.042,.008,.009);finish(o,'SwordGuard','Sword',1)
sx,sy,sz=(-.263,-.111,.459)
cylinder('BucklerBody',(sx,sy,sz),.079,.008,'Shield',2)
for name,radius,minor,yy,swatch in [('BucklerRim',.077,.003,sy-.005,0),('BucklerGreenBand',.068,.006,sy-.0055,1)]:
 bpy.ops.mesh.primitive_torus_add(major_radius=radius,minor_radius=minor,major_segments=40,minor_segments=6,location=(sx,yy,sz),rotation=(math.pi/2,0,0));finish(bpy.context.object,name,'Shield',swatch)
bpy.ops.mesh.primitive_uv_sphere_add(segments=20,ring_count=8,radius=1,location=(sx,sy-.007,sz));o=bpy.context.object;o.scale=(.018,.004,.018);finish(o,'BucklerBoss','Shield',2)
cylinder('BucklerGrip',(sx,sy+.012,sz),.005,.028,'Shield',3)
bpy.ops.object.select_all(action='DESELECT');body.select_set(True)
for o in parts:o.select_set(True)
bpy.context.view_layer.objects.active=body;bpy.ops.object.join()
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_equipped_v1.blend'))
(P/'work/equipment_dimensions.json').write_text(json.dumps(dict(sword_blade_length=.292,sword_grip_radius=.0052,shield_radius=.079,sword_hand='Left',shield_hand='Right',bone_owners=['Sword','Shield'],source='native front/side attack, generated mesh claw measurements'),indent=2))
