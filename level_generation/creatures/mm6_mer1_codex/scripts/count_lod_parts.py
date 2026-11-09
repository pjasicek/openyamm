import bpy
from pathlib import Path
from collections import Counter
P=Path(__file__).resolve().parents[1]
for name in ['body_lod0_4_final','body_lod2_14_final','body_lod3_22_probe']:
 bpy.ops.wm.open_mainfile(filepath=str(P/f'work/reduction/{name}.blend'));m=bpy.data.objects['Body'].data;p=[x.value for x in m.attributes['piece'].data];c=Counter()
 for f in m.polygons:c[Counter(p[i]for i in f.vertices).most_common(1)[0][0]]+=len(f.vertices)-2
 print(name,dict(sorted(c.items())),flush=True)
