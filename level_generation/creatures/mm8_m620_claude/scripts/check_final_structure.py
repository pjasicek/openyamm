from pathlib import Path
import bpy,runpy,sys,json,struct
p=Path(__file__).resolve().parents[1]
runpy.run_path(str(p/'scripts/check_motion.py'),run_name='__main__',init_globals={'INPUT_BLEND':'rig_textured_uv.blend'})
# Final export must expose only the selected texture coordinates and no provisional rigging UV.
raw=(p/'export/mm8_m620.glb').read_bytes();n=struct.unpack_from('<I',raw,12)[0];j=json.loads(raw[20:20+n]);out=[]
for m in j['meshes']:
 triangles=0
 for q in m['primitives']:
  assert not any(k.startswith('TEXCOORD_') and k!='TEXCOORD_0' for k in q['attributes'])
  triangles+=j['accessors'][q['indices']]['count']//3
 out.append({'name':m.get('name'),'triangles':triangles,'primitives':len(m['primitives'])})
(p/'review/validation/export_structure.json').write_text(json.dumps({'meshes':out,'variants':j['extensions']['KHR_materials_variants']['variants'],'clips':[a['name'] for a in j['animations']]},indent=2)+'\n')
print('EXPORT_STRUCTURE_OK')
