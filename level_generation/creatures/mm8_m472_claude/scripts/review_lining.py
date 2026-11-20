from pathlib import Path
import bpy,sys
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_textured_uv.blend'))
o=bpy.data.objects['Body'];r=bpy.data.objects['Rig'];sc=bpy.context.scene
for ob in bpy.data.objects:
 if ob.type=='MESH':ob.hide_render=ob!=o
o.data.materials.clear()
for name,col in [('Body',(.25,.3,.35,1)),('Metal',(.8,.8,.8,1)),('Lining',(.008,.008,.008,1))]:
 mat=bpy.data.materials.new(name);mat.diffuse_color=col;o.data.materials.append(mat)
for face in o.data.polygons:face.material_index=1 if o.data.attributes['rigid_plate'].data[face.index].value else (2 if o.data.attributes['armour_lining'].data[face.index].value else 0)
common.workbench_clay(sc)
for name,frames in [('Standing',[0]),('Attack',[12,20,24,30]),('Walking',[6]),('Running',[6]),('Hit',[4]),('Death',[12])]:
 a=bpy.data.actions[name];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0]
 for f in frames:
  sc.frame_set(f);common.render_views(str(p/f'review/lining_fix/{name}-{f}'),1.33,.85,views=('front','three_quarter','back'),resolution=(700,700))
