"""Export the selected rebaked meshes; the shared rig and clips are authored only in LOD0."""
import bpy,json,sys,runpy,shutil,subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P/'scripts'))
selection=json.loads((P/'review/rebake/final_selection.json').read_text());counts={}
for level in range(4):
 tag=selection[str(level)]['tag'];bpy.ops.wm.open_mainfile(filepath=str(P/f'work/rebake/{tag}_baked.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];rig.animation_data.action=None
 for b in rig.pose.bones:b.matrix_basis.identity()
 bpy.context.scene.render.fps=30
 for material in body.data.materials:
  bs=material.node_tree.nodes.get('Principled BSDF');bs.inputs['Specular IOR Level'].default_value=.5;bs.inputs['Specular Tint'].default_value=(1,1,1,1);bs.inputs['IOR'].default_value=1.5
 pv=[v.value for v in body.data.attributes['piece'].data];bodytris=sum(len(f.vertices)-2 for f in body.data.polygons if pv[f.vertices[0]]!=201);bowtris=sum(len(f.vertices)-2 for f in body.data.polygons if pv[f.vertices[0]]==201);counts[str(level)]={'body':bodytris,'bow':bowtris,'tag':tag}
 bpy.ops.object.select_all(action='DESELECT');body.select_set(True);rig.select_set(True);bpy.context.view_layer.objects.active=rig
 if level==0:bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/master.blend'));continue
 body.name=body.data.name='Lizard'
 bpy.ops.export_scene.gltf(filepath=str(P/f'export/mm6_lzd_level{level}.glb'),use_selection=True,export_format='GLB',export_yup=True,export_animations=False,export_skins=True,export_all_influences=True,export_attributes=False,export_morph=False,export_image_format='AUTO')
(P/'review/reduction/selected.json').write_text(json.dumps({part:{i:{'triangles':v[part],'tag':v['tag']}for i,v in counts.items()}for part in ['body','bow']},indent=2))
(P/'review/rebake/final_counts.json').write_text(json.dumps(counts,indent=2));print('SELECTED_COUNTS',counts,flush=True)
runpy.run_path(str(P/'scripts/export_check.py'),run_name='__main__')
# The new bakes already use glTF's +Y tangent normal convention; do not flip them a second time.
shutil.copyfile(P/'export/mm6_lzd_raw.glb',P/'export/mm6_lzd_lod0.glb')
subprocess.run(['/usr/bin/python3',str(P/'scripts/rebake_pack.py')],check=True)
runpy.run_path(str(P/'scripts/review_exports.py'),run_name='__main__')
runpy.run_path(str(P/'scripts/angular_acceleration.py'),run_name='__main__')
print('ROUND3_EXPORT_REVIEW_COMPLETE',flush=True)
