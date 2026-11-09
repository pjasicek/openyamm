import runpy,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import search_reduction as S
for path,tag in [('work/reduction/body_lod0_4_final.blend','near_final_all_surfaces'),('work/reduction/body_lod1_17_final.blend','far1_final_all_surfaces')]:
 print('FINAL SURFACE CHECK',path,S.gates(P/path,tag),flush=True)
