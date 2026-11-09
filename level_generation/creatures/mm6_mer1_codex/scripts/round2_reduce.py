import bpy,sys,json,subprocess,shutil
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import reduction_common as C,round2_bake as B
bpy.ops.wm.open_mainfile(filepath=str(P/'work/round2/master.blend'));C.reset();o=bpy.data.objects['Body'];protection=C.protect(o,'body');before=C.triangles(o);C.reduce(o,7000/before,planar=True);folder=P/'work/round2/shared_textures';assert not (folder/'receipt.json').exists(),'Single rebake already completed'
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/round2/reduced_unbaked.blend'));B.bake(o,folder);subprocess.run(['/usr/bin/python3',str(P/'scripts/reduction_previews.py'),str(folder)],check=True);C.reset();bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/round2/body_lod0.blend'))
entries=[{'blend':'work/round2/body_lod0.blend','textures':'work/round2/shared_textures','triangles':C.triangles(o)}]
for level,target in [(1,2420),(2,1740),(3,690)]:
 bpy.ops.wm.open_mainfile(filepath=str(P/'work/round2/body_lod0.blend'));C.reset();o=bpy.data.objects['Body'];C.reduce(o,target/C.triangles(o));path=P/f'work/round2/body_lod{level}.blend';bpy.ops.wm.save_as_mainfile(filepath=str(path));entries.append({'blend':str(path.relative_to(P)),'textures':'work/round2/shared_textures','triangles':C.triangles(o)})
selection=json.loads((P/'work/round2/selection_round1.json').read_text());selection['body']=entries;(P/'review/reduction/selection.json').write_text(json.dumps(selection,indent=2));(P/'review/round2/reduction.json').write_text(json.dumps({'source_triangles':before,'body':entries,'protection':protection,'rebakes':1,'padding_px':16,'island_spacing_fraction':.035,'method':'One fixed ~7000-triangle rebake; all lower LODs preserve that atlas.'},indent=2))
print('ROUND2 REDUCTION',entries,flush=True)
