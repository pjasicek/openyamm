import bpy,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common,reduction_common as C
bpy.ops.wm.open_mainfile(filepath=str(P/'work/runtime_lod0.blend'));C.reset();C.activate('Standing',0);body=bpy.data.objects['Body'];pv=[v.value for v in body.data.attributes['piece'].data];body.data.materials.clear()
colors={0:(.4,.22,.12,1),12:(1,0,0,1),15:(1,0,0,1),13:(0,1,0,1),16:(0,0,1,1)}
for color in list(colors.values())+[(.7,.7,.7,1)]:
 m=bpy.data.materials.new('Debug');m.diffuse_color=color;body.data.materials.append(m)
for poly in body.data.polygons:poly.material_index=list(colors).index(pv[poly.vertices[0]])if pv[poly.vertices[0]]in colors else len(colors)
sc=bpy.context.scene;common.workbench_clay(sc);sc.display.shading.color_type='MATERIAL';common.render_views(str(P/'review/round4_piece'),1.32,.95,views=('front','three_quarter'),resolution=(900,850))
