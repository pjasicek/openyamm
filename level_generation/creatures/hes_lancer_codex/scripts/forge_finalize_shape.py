"""Keep hot shoulder seams on their plate bones and add the same frame/UV conventions."""
import bpy,bmesh,sys,os
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/forge_concept_grounded.blend'));rig=bpy.data.objects['Rig']
body=bpy.data.objects['Body'];spec=__import__('json').loads((P/'scripts/armour_forge.json').read_text());old_shoulders={i+1 for i,p in enumerate(spec['plates']) if 'pauldron' in p['name']}
for v in body.data.attributes['shell_hidden'].data:
 if v.value in old_shoulders:v.value=0
for side in 'LR':
 for name in (f'Arm_pauldron_{side}',f'Arm_pauldron_lower_{side}',f'Apron_Shoulder_{side}'):
  ob=bpy.data.objects[name];mesh=ob.data;V=[v.co.copy() for v in mesh.vertices];F=[tuple(p.vertices) for p in mesh.polygons];mi=[p.material_index for p in mesh.polygons];uvfaces=[[mesh.uv_layers[0].data[i].uv.copy() for i in p.loop_indices] for p in mesh.polygons];nu,nv=9,4
  a=rig.data.bones[f'B_{side}_UpperArm'].head_local;b=rig.data.bones[f'B_{side}_Forearm'].head_local;axis=(b-a).normalized();first=len(V)
  for i in range(nu):
   p=V[(nv-1)*nu+i];rad=(p-a)-axis*(p-a).dot(axis);rad.normalize()
   for z in (0,.003):
    for d in (-.003,.003):V.append(p+axis*d+rad*(.002+z))
  # Closed strip following the lower edge of each lame, no emissive texture.
  for i in range(nu-1):
   k=first+4*i;q=k+4
   for face in ((k,q,q+1,k+1),(k+2,k+3,q+3,q+2),(k,k+2,q+2,q),(k+1,q+1,q+3,k+3)):
    F.append(face);mi.append(1);uvfaces.append([(0,0)]*4)
  for face in ((first,first+1,first+3,first+2),(first+4*(nu-1),first+4*(nu-1)+2,first+4*(nu-1)+3,first+4*(nu-1)+1)):
   F.append(face);mi.append(1);uvfaces.append([(0,0)]*4)
  new=bpy.data.meshes.new(name+'_hot');new.from_pydata(V,[],F);new.materials.append(bpy.data.materials['HKR_Plate']);new.materials.append(bpy.data.materials['HKR_Glow']);uv=new.uv_layers.new(name='UVMap')
  for face,mat,coords in zip(new.polygons,mi,uvfaces):
   face.material_index=mat
   for li,co in zip(face.loop_indices,coords):uv.data[li].uv=co
  bm=bmesh.new();bm.from_mesh(new);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bmesh.ops.triangulate(bm,faces=list(bm.faces));bm.to_mesh(new);bm.free();ob.data=new;ob.vertex_groups.clear();ob.vertex_groups.new(name=f'B_{side}_UpperArm').add(list(range(len(new.vertices))),1,'REPLACE')
# Bake the fixed bib anchors too, so playback never depends on the preceding action.
anchors={b.name:b.matrix_basis.copy() for b in rig.pose.bones if b.name in ('B_ForgeApron_Front_0','B_ForgeApron_Back_0')}
for clip in ('Forge_Death','Forge_Dead'):
 a=bpy.data.actions[clip];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0]
 for f in (float(a.frame_range[0]),float(a.frame_range[1])):
  for n,m in anchors.items():
   b=rig.pose.bones[n];b.matrix_basis=m;b.rotation_mode='QUATERNION';b.keyframe_insert('rotation_quaternion',frame=f);b.keyframe_insert('location',frame=f)
rig.animation_data.action=None
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/forge_concept_grounded.blend'));sys.stdout.flush();os._exit(0)
