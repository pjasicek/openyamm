"""Assemble the independently measured body, bow and arrow candidates at each distance."""
import bpy,json,sys,runpy,os
from pathlib import Path
P=Path(__file__).resolve().parents[1];W=P/'work/round2';S=json.loads((P/'review/round2/reduction/selected.json').read_text());sys.dont_write_bytecode=True
def mesh_from(path,name):
 before=set(bpy.data.objects);acts=set(bpy.data.actions)
 with bpy.data.libraries.load(str(path),link=False)as(src,dst):dst.objects=[name]
 obj=dst.objects[0];data=obj.data.copy()
 for o in set(bpy.data.objects)-before:bpy.data.objects.remove(o,do_unlink=True)
 for a in set(bpy.data.actions)-acts:bpy.data.actions.remove(a)
 return data
for level in range(4):
 bpy.ops.wm.open_mainfile(filepath=str(W/'unreduced.blend'));body=bpy.data.objects['Body'];prop=bpy.data.objects['BowAsset']
 body.data=mesh_from(P/S['body'][str(level)]['blend'],'Body')
 prop.data=mesh_from(P/S['bow'][str(level)]['blend'],'BowAsset')
 arrow=prop.copy();arrow.data=mesh_from(P/S['arrow'][str(level)]['blend'],'BowAsset');bpy.context.collection.objects.link(arrow)
 bpy.ops.object.select_all(action='DESELECT');prop.select_set(True);arrow.select_set(True);bpy.context.view_layer.objects.active=prop;bpy.ops.object.join()
 bpy.ops.wm.save_as_mainfile(filepath=str(W/f'lod{level}.blend'))
 if level==0:
  bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_equipped.blend'));bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_textured.blend'))
 os.environ['ARC1_EXPORT_SOURCE']=str(W/f'lod{level}.blend');os.environ['ARC1_EXPORT_LEVEL']=str(level)
 runpy.run_path(str(P/'scripts/export_runtime.py'),run_name='__main__')
os.environ.pop('ARC1_EXPORT_SOURCE');os.environ.pop('ARC1_EXPORT_LEVEL')
