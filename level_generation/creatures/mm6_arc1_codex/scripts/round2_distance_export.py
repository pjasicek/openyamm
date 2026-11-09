"""Export the capped, physically checked distance meshes and refresh all final evidence."""
import bpy,bmesh,sys,json,runpy,os,subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1];W=P/'work/round2';D=P/'review/round2/reduction';sys.dont_write_bytecode=True
S=json.loads((D/'selected.json').read_text())
for level in range(1,4):
 assert json.loads((P/f'review/round2/lod_gates/lod{level}/status.json').read_text())['pass']
 for part in ['body','bow','arrow']:
  bpy.ops.wm.open_mainfile(filepath=str(W/f'lod{level}.blend'));ob=bpy.data.objects['Body'if part=='body'else'BowAsset']
  if part!='body':
   bm=bmesh.new();bm.from_mesh(ob.data);layer=bm.faces.layers.int['bow_part'];bmesh.ops.delete(bm,geom=[f for f in bm.faces if (f[layer]>=3)!=(part=='arrow')],context='FACES');bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS');bm.to_mesh(ob.data);bm.free()
  path=W/f'{part}_l{level}_final.blend';bpy.ops.wm.save_as_mainfile(filepath=str(path));S[part][str(level)].update(blend=str(path.relative_to(P)),triangles=sum(len(f.vertices)-2 for f in ob.data.polygons),strategy='capped distance selection; physical surface fitting',rig_gates='pass_all_clips')
(D/'selected.json').write_text(json.dumps(S,indent=2))
for level in range(4):
 os.environ['ARC1_EXPORT_SOURCE']=str(W/f'lod{level}.blend');os.environ['ARC1_EXPORT_LEVEL']=str(level);runpy.run_path(str(P/'scripts/export_runtime.py'),run_name='__main__')
os.environ.pop('ARC1_EXPORT_SOURCE');os.environ.pop('ARC1_EXPORT_LEVEL')
for name in ['round2_pack_lods.py','pack_runtime.py']:subprocess.run(['/usr/bin/python3',str(P/'scripts'/name)],check=True)
for name in ['round2_assembled_metrics.py','round2_material_metrics.py','round2_endchecks.py']:runpy.run_path(str(P/'scripts'/name),run_name='__main__')
subprocess.run(['/usr/bin/python3',str(P/'scripts/round2_smoothness.py')],check=True)
