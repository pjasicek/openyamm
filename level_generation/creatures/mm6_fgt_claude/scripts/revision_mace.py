"""Refine the native mace silhouette without changing its fitted grip or authored motion."""
import bpy,bmesh,json,math,sys
from pathlib import Path
from mathutils import Vector,Matrix
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_revision1_body.blend'))
rig=bpy.data.objects['Rig'];old=bpy.data.objects['Mace'];rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis.identity()
bpy.context.view_layer.update()
g=json.loads((p/'work/grip_pose.json').read_text());hm=rig.data.bones['B_R_Hand'].matrix_local
centre=hm@Vector(g['handle_centre_hand_local']);axis=(hm.to_3x3()@Vector(g['handle_axis_hand_local'])).normalized()
u=axis.orthogonal().normalized();v=axis.cross(u)
verts=[];faces=[];classes=[]
def lathe(c,d,profile,n,cls):
 x=d.orthogonal().normalized();y=d.cross(x);start=len(verts)
 for h,r in profile:
  for j in range(n):verts.append(c+d*h+(x*math.cos(2*math.pi*j/n)+y*math.sin(2*math.pi*j/n))*r)
 for row in range(len(profile)-1):
  for j in range(n):faces.append((start+row*n+j,start+row*n+(j+1)%n,start+(row+1)*n+(j+1)%n,start+(row+1)*n+j));classes.append(cls)
 faces.extend([tuple(start+j for j in reversed(range(n))),tuple(start+(len(profile)-1)*n+j for j in range(n))]);classes.extend([cls,cls])
# Rounded collars and subtly tapered steel shaft; fitted grip radius stays 12 mm.
lathe(centre,axis,[(-.085,.0115),(-.081,.012),(.085,.012),(.095,.0115)],24,1)
lathe(centre,axis,[(-.099,.010),(-.098,.013),(-.095,.014),(-.087,.014),(-.084,.012)],24,2)
lathe(centre,axis,[(.090,.012),(.094,.015),(.101,.015),(.104,.010),(.330,.009),(.342,.012),(.350,.015),(.357,.015),(.363,.010)],24,2)
hc=centre+axis*.385
# Latitude rings keep the head round at close distance; independent forged spikes retain crisp silhouettes.
lathe(hc,axis,[(-.054,.00015)]+[(.054*math.cos(math.pi*i/12),.054*math.sin(math.pi*i/12)) for i in reversed(range(1,12))]+[(.054,.00015)],24,3)
for i in range(8):
 a=2*math.pi*i/8;d=u*math.cos(a)+v*math.sin(a)
 lathe(hc,d,[(.045,.012),(.050,.014),(.055,.0115),(.078,.0010),(.080,.0003)],8,3)
for sign in (-1,1):lathe(hc,axis*sign,[(.045,.012),(.051,.014),(.056,.011),(.077,.001),(.078,.0003)],8,3)
me=bpy.data.meshes.new('MaceDetailed');me.from_pydata(verts,[],faces);me.update()
# Recalculate normals from the closed shells and retain material classes through UV creation.
bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
attr=me.attributes.new('mace_class','INT','FACE');attr.data.foreach_set('value',classes)
bpy.data.objects.remove(old,do_unlink=True);mace=bpy.data.objects.new('Mace',me);bpy.context.scene.collection.objects.link(mace)
mace.parent=rig;mod=mace.modifiers.new('Armature','ARMATURE');mod.object=rig;mace.vertex_groups.new(name='Mace').add(list(range(len(me.vertices))),1,'REPLACE')
for cls,c in enumerate([(.15,.055,.02,1),(.38,.40,.42,1),(.025,.026,.027,1)],1):
 mat=bpy.data.materials.new('MaceClass'+str(cls));mat.diffuse_color=c;me.materials.append(mat)
for f,cls in zip(me.polygons,classes):f.material_index=cls-1;f.use_smooth=True
for o in bpy.context.selected_objects:o.select_set(False)
mace.select_set(True);bpy.context.view_layer.objects.active=mace
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=math.radians(60),island_margin=.015);bpy.ops.object.mode_set(mode='OBJECT')
me.uv_layers.active.name='UVMap'
(p/'work/mace_uv.json').write_text(json.dumps([{'cls':cls,'uv':[list(me.uv_layers.active.data[li].uv) for li in f.loop_indices]} for f,cls in zip(me.polygons,classes)]))
tris=sum(len(f.vertices)-2 for f in me.polygons)
assert 1000<tris<3000 and set(classes)=={1,2,3}
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/rig_revision1.blend'))
# Upload one static, upright prop with the same UVs; never send its humanoid rig to retexturing.
mod.show_viewport=False;mod.show_render=False
mace.parent=None;mace.matrix_world=Matrix.Identity(4)
rot=axis.rotation_difference(Vector((0,0,1))).to_matrix()
for vt in me.vertices:vt.co=rot@(vt.co-centre)
bpy.ops.export_scene.gltf(filepath=str(p/'texturing/fgt_mace_upload.glb'),use_selection=True,export_format='GLB',export_animations=False,export_skins=False,export_yup=True,export_attributes=False)
(p/'review/revision1/mace_geometry.json').write_text(json.dumps({'triangles':tris,'original_triangles':304,'grip_radius_m':.012,'spikes':10,'uv':'smart_project_60deg_normalized_margin_0.015','animation_changed':False},indent=2))
print('MACE',tris)
