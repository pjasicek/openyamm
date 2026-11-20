import sys,json,subprocess,os
from pathlib import Path
P=Path(__file__).resolve().parents[1];R=P/'review/round3';D=R/'rebake/export_lod0';sys.path.insert(0,str(P/'scripts'));import compare_exported_lods as C
C.O=R/'rebake/physical';C.O.mkdir(exist_ok=True);C.PHYSICAL=True
for label,path,tier in [('reference',R/'before/export/mm6_figc_lod0.glb',P/'work'),('rebaked',D/'rebaked.glb',D/'textures')]:
 C.TIER_DIR=tier
 if label!='reference':C.render(path,0,label)
subprocess.run(['/usr/bin/python3',str(P/'scripts/measure_reduction.py'),str(C.O/'reference_lod0'),str(C.O/'rebaked_lod0'),str(C.O/'metrics.json')],check=True)
