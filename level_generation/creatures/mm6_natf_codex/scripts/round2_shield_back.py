import bpy,json
from pathlib import Path
P=Path(__file__).resolve().parents[1];sel=json.loads((P/'review/reduction_selected.json').read_text())
bpy.ops.wm.open_mainfile(filepath=str(P/sel['LeafShield']['3']['blend']));rig=bpy.data.objects['Rig'];ob=bpy.data.objects['LeafShield'];M=rig.data.bones['LeafShield'].matrix_local;inv=M.inverted();count=0
for v in ob.data.vertices:
 q=inv@v.co
 if abs(q.x)<.001 and .024<q.y<.028:q.y=-.021;v.co=M@q;count+=1
assert count==9,count
path=P/'work/round2_shield_lod3.blend';bpy.ops.wm.save_as_mainfile(filepath=str(path));sel['LeafShield']['3']['blend']=str(path.relative_to(P));sel['Body']['3']['blend']='work/round2_contact/lod3.blend';(P/'review/reduction_selected.json').write_text(json.dumps(sel,indent=2))
(P/'review/round2/shield_back_correction.md').write_text('LOD3 back face incorrectly bowed toward the hand by 47 mm (local centre y +0.026 vs the full-detail -0.021). Restored the same concave rear surface as LOD0, keeping 156 triangles and all UVs. Rejected the 45.7 mm far-hand projection and retained the earlier 9.15 mm grip fitting. The near hand projection is retained.\n')
