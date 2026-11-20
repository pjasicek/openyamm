"""Refine only the sword blade silhouette from the supplied concept; retain the fitted hilt and rig."""
import bpy,bmesh,json,sys,numpy as np
from pathlib import Path
from mathutils import Matrix,Vector
p=Path(__file__).resolve().parents[1];out=p/'review/sword_concept_20261011'
sys.path.insert(0,str(p/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_v13.blend'))
r=bpy.data.objects['Rig'];s=bpy.data.objects['SwordMesh'];old=s.data
r.animation_data.action=None
for b in r.pose.bones:b.matrix_basis.identity()
bpy.context.view_layer.update()
M=r.data.bones['Sword'].matrix_local.copy()
classes=json.loads(s['sword_classes'])
blade_faces=[f.index for f,k in zip(old.polygons,classes) if k in ('blade','edge')]
blade_vertices=sorted({v for i in blade_faces for v in old.polygons[i].vertices})
assert blade_vertices==list(range(112,129)),blade_vertices
verts=[tuple(v.co) for v in old.vertices[:112]];faces=[];newclasses=[];materials=[]
for f,k in zip(old.polygons,classes):
 if f.index in blade_faces:continue
 faces.append(tuple(f.vertices));newclasses.append(k);materials.append(f.material_index)
mat_by_class={k:f.material_index for f,k in zip(old.polygons,classes)}
profile=[(.062,.024,.0045),(.115,.032,.005),(.19,.021,.0045),(.54,.0175,.0035),(.625,.021,.004),(.69,.035,.005),(.758,.022,.003)]
rings=[]
for a,w,t in profile:
 rings.append(len(verts))
 verts.extend(tuple(M@Vector(c)) for c in [(-w,a,0),(0,a,t),(w,a,0),(0,a,-t)])
for a,b in zip(rings,rings[1:]):
 for j in range(4):
  faces.append((a+j,b+j,b+(j+1)%4,a+(j+1)%4));k='edge' if j%2==0 else 'blade';newclasses.append(k);materials.append(mat_by_class[k])
tip=len(verts);verts.append(tuple(M@Vector((0,.785,0))))
for j in range(4):
 faces.append((rings[-1]+j,tip,rings[-1]+(j+1)%4));newclasses.append('edge');materials.append(mat_by_class['edge'])
mesh=bpy.data.meshes.new('SwordConceptMesh');mesh.from_pydata(verts,[],faces);mesh.update()
for m in old.materials:mesh.materials.append(m)
bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(mesh);bm.free()
for f,k,mi in zip(mesh.polygons,newclasses,materials):f.material_index=mi;f.use_smooth=k in ['grip','gold','gold_dark']
s.data=mesh
s.vertex_groups.clear();s.vertex_groups.new(name='Sword').add(list(range(len(verts))),1,'REPLACE')
mesh.attributes.new('piece','INT','POINT').data.foreach_set('value',[999]*len(verts))
s['sword_classes']=json.dumps(newclasses)
oldtris=sum(len(f.vertices)-2 for f in old.polygons);newtris=sum(len(f.vertices)-2 for f in mesh.polygons)
assert oldtris==232 and newtris==256,(oldtris,newtris)
assert np.array_equal(np.array([v.co[:] for v in old.vertices[:112]]),np.array(verts[:112]))
bodytris=sum(len(f.vertices)-2 for f in bpy.data.objects['Body'].data.polygons)
assert bodytris+newtris<=10000
(out/'geometry.json').write_text(json.dumps({'source':'work/rig_v13.blend','result':'work/rig_v14.blend','sword_triangles_before':oldtris,'sword_triangles_after':newtris,'added_triangles':newtris-oldtris,'combined_triangles':bodytris+newtris,'unchanged_hilt_vertices':112,'profile_axis_halfwidth_halfthickness_m':profile,'tip_axis_m':.785,'grip_and_sword_bone_unchanged':True},indent=1))
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/rig_v14.blend'))
# True mesh comparison, viewed square-on to the broad blade face.
for o in bpy.data.objects:
 if o.type=='MESH':o.hide_render=True
s.hide_render=False
before=bpy.data.objects.new('PreviousSword',old);bpy.context.scene.collection.objects.link(before)
shift=M.to_3x3()@Vector((.18,0,0));before.location=-shift;s.location=shift
sc=bpy.context.scene;common.workbench_clay(sc,False);sc.display.shading.show_cavity=True
cam=common.ortho_camera('SwordComparison',(0,0,0),(0,0,0),1.08)
C=Matrix.Diagonal((1,-1,-1,1));C.translation=Vector((0,.331,-2));cam.matrix_world=M@C;sc.camera=cam
sc.render.resolution_x=900;sc.render.resolution_y=1100;sc.render.filepath=str(out/'sword_comparison.png')
bpy.ops.render.render(write_still=True)
print('SWORD_CONCEPT',oldtris,'->',newtris,'combined',bodytris+newtris)
