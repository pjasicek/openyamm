import bpy,json,numpy as np,sys
from pathlib import Path
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(p/'review/viewer/mm6_nobl_a.glb'))
r=next(o for o in bpy.data.objects if o.type=='ARMATURE');sc=bpy.context.scene
a=bpy.data.actions['Dead'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];sc.frame_set(0)
o=next(o for o in bpy.data.objects if o.type=='MESH' and o.parent==r)
common.workbench_clay(sc,False);sc.display.shading.show_cavity=False
from mathutils import Vector
cam=common.ortho_camera('top',(0,-.65,2),(0,0,0),1.1);sc.camera=cam
sc.render.resolution_x=sc.render.resolution_y=750
for name in ['custom','recalc','textured']:
 if name=='recalc':o.data.normals_split_custom_set([(0,0,0)]*len(o.data.loops))
 if name=='textured':sc.display.shading.color_type='TEXTURE'
 sc.render.filepath=str(p/f'review/feet_cloak_20261011/glb_{name}.png');bpy.ops.render.render(write_still=True)
