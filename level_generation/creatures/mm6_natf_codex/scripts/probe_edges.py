import bpy,json
from pathlib import Path
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_cloth.blend'));ob=bpy.data.objects['Body'];r=json.loads((P/'review/cloth/geometry_audit.json').read_text())
for role,dd in r.items():
 e=dd['worst_edges']['0'];print('EDGE',role,e,flush=True)
 for i in e['vertices']:
  v=ob.data.vertices[i];print(i,list(v.co),{ob.vertex_groups[g.group].name:round(g.weight,4)for g in v.groups},flush=True)
