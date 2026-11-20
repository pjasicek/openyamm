from pathlib import Path
import bpy,sys
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(p/'export/mm8_m488_runtime_lod0.glb'))
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');a=next(a for a in bpy.data.actions if a.name.startswith('Standing'));rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];bpy.context.scene.frame_set(0)
common.workbench_clay(bpy.context.scene,textured=True)
out=p/'review/textured';out.mkdir(exist_ok=True)
common.render_views(str(out/'standing'),1.05,2.5,views=('front','left','back','three_quarter'),resolution=(640,640))
common.render_views(str(out/'head'),1.84,.7,views=('front','left','back'),resolution=(640,640))
