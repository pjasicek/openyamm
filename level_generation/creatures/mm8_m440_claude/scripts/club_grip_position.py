import bpy,json
from pathlib import Path
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/club_clean.blend'))
o=bpy.data.objects['ClubMesh']
if not o.get('grip_shift'):
 for v in o.data.vertices:v.co.z+=.04
 o['grip_shift']=.04
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/club_clean.blend'))
d=json.loads((p/'work/club_geometry.json').read_text());d['grip_from_butt_m']=.10;d['cleanup']='Removed 12 collapsed sliver triangles; shifted grip 4 cm toward butt to clear calf during recovery.';(p/'work/club_geometry.json').write_text(json.dumps(d,indent=2))
