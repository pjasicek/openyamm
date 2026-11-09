"""Resolve pinned reduction groups without a second bake; every level keeps the one atlas."""
import bpy,sys,json,shutil
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import reduction_common as C
source=P/'work/round2/body_lod0_rebaked.blend';shutil.copyfile(P/'work/round2/body_lod0.blend',source);entries=[]
for level,target in [(0,6990),(1,2400),(2,1730),(3,685)]:
 bpy.ops.wm.open_mainfile(filepath=str(source));C.reset();o=bpy.data.objects['Body'];group=o.vertex_groups['_reduction_protect']
 for v in o.data.vertices:
  w=next((g.weight for g in v.groups if g.group==group.index),0)
  if w:group.add([v.index],min(w,.65),'REPLACE')
 C.reduce(o,target/C.triangles(o));dest=P/f'work/round2/body_lod{level}.blend';bpy.ops.wm.save_as_mainfile(filepath=str(dest));entries.append({'blend':str(dest.relative_to(P)),'textures':'work/round2/shared_textures','triangles':C.triangles(o)})
selection=json.loads((P/'review/reduction/selection.json').read_text());selection['body']=entries;(P/'review/reduction/selection.json').write_text(json.dumps(selection,indent=2));p=P/'review/round2/reduction.json';d=json.loads(p.read_text());d['rebaked_triangles']=d['body'][0]['triangles'];d['body']=entries;d['correction']='The inherited protected group pinned vertices and stopped at 9381. Softened its weights to .65, collapsed to the requested counts using the existing UVs, and retained the single rebake.';p.write_text(json.dumps(d,indent=2));print('CORRECTED COUNTS',entries,flush=True)
