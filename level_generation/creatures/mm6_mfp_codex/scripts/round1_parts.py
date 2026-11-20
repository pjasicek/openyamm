import bpy,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/round1/lod0.blend'));b=bpy.data.objects['Body'];r=bpy.data.objects['Rig'];sc=bpy.context.scene
for ob in list(sc.objects):
 if ob not in [b,r]:bpy.data.objects.remove(ob,do_unlink=True)
pv=[v.value for v in b.data.attributes['piece'].data];b.data.materials.clear();colors=[(.7,.3,.3,1),(.2,.8,.2,1),(.1,.3,.1,1),(.1,.3,.1,1),(.1,.4,.9,1),(.1,.4,.9,1),(1,.8,.05,1)]
for i in range(max(pv)+1):m=bpy.data.materials.new(str(i));m.diffuse_color=colors[i]if i<len(colors)else(.7,.7,.7,1);b.data.materials.append(m)
for f in b.data.polygons:f.material_index=pv[f.vertices[0]]
common.workbench_clay(sc);sc.display.shading.light='FLAT';r.animation_data.action=bpy.data.actions['Standing'];r.animation_data.action_slot=r.animation_data.action.slots[0];sc.frame_set(0);common.render_views(str(P/'review/round1/surface_parts'),1.22,.8,views=('front','three_quarter'),resolution=(600,800))
