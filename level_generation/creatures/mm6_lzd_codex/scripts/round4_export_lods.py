"""Use one rebaked texture set for a protected, strictly decreasing LOD chain."""
import bpy,sys,runpy,shutil,json
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P/'scripts'))
bpy.ops.wm.open_mainfile(filepath=str(P/'work/round4/round4_shared_baked.blend'))
for ob in list(bpy.data.objects):
 if ob.name.startswith('BakeSource'):bpy.data.objects.remove(ob,do_unlink=True)
body=bpy.data.objects['Body']
for a in list(body.data.attributes):
 if a.name.startswith('_source_index'):body.data.attributes.remove(a)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/round4/near_runtime.blend'))
shutil.copyfile(P/'work/round4/near_runtime.blend',P/'work/master.blend')
runpy.run_path(str(P/'scripts/export_runtime.py'),run_name='__main__')
runpy.run_path(str(P/'scripts/patch_string_export.py'),run_name='__main__')
shutil.copyfile(P/'export/mm6_lzd_raw.glb',P/'export/mm6_lzd_lod0.glb')
from rebake_reduce import build
selection={'0':{'blend':'work/round4/near_runtime.blend','tag':'round4_shared'}}
for level,ratio,bow in [(1,.45,.54),(2,.22,.219),(3,.07,.065)]:
 tag=f'round4_lod{level}';path=build(tag,ratio,level,bow,major_shells=level>=2,source_path=P/'work/round4/near_runtime.blend',contact_poses=(('Standing',0),),budget_scale=.95 if level==2 else .94 if level==3 else 1.)
 body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];bpy.ops.object.select_all(action='DESELECT');body.select_set(True);rig.select_set(True);bpy.context.view_layer.objects.active=rig;body.name=body.data.name='Lizard'
 bpy.ops.export_scene.gltf(filepath=str(P/f'export/mm6_lzd_level{level}.glb'),use_selection=True,export_format='GLB',export_yup=True,export_animations=False,export_skins=True,export_all_influences=True,export_attributes=False,export_morph=False,export_image_format='AUTO')
 selection[str(level)]={'blend':str(path.relative_to(P)),'tag':tag,'counts':json.loads((P/f'review/rebake/{tag}_counts.json').read_text())}
(P/'review/round4/lod_selection.json').write_text(json.dumps(selection,indent=2))
