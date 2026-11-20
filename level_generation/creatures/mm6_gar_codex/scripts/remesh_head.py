"""Close the generated head's overlapping/open surface patches at 0.4% of head height."""
import bpy,bmesh,sys,json
from pathlib import Path
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(Path('level_generation/creatures/mm6_bar1_claude/scripts').resolve()))
import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/head_geometry_v2.blend'))
mesh=bpy.data.objects['GargoyleHead']; bpy.context.view_layer.objects.active=mesh
for o in bpy.context.scene.objects: o.select_set(o==mesh)
bm=bmesh.new(); bm.from_mesh(mesh.data)
bmesh.ops.remove_doubles(bm,verts=bm.verts,dist=.003)
bmesh.ops.recalc_face_normals(bm,faces=bm.faces[:]); bm.to_mesh(mesh.data); bm.free()
shell=mesh.modifiers.new('CloseThinGeneratedPatches','SOLIDIFY'); shell.thickness=.010; shell.offset=0
bpy.ops.object.modifier_apply(modifier=shell.name)
mesh.data.remesh_voxel_size=.006
mesh.data.use_remesh_preserve_volume=True
bpy.ops.object.voxel_remesh()
for p in mesh.data.polygons: p.use_smooth=True
assert len(mesh.data.vertices)>5000 and len(mesh.data.vertices)<500000
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/head_geometry_clean.blend'))
scene=bpy.context.scene; scene.world=bpy.data.worlds.new('HeadReview'); common.workbench_clay(scene)
common.render_views(str(P/'review/head_geometry_clean'),.5,1.2,views=('front','left','three_quarter'),resolution=(900,900))
print('HEAD_CLEAN',len(mesh.data.vertices),len(mesh.data.polygons))
